#!/usr/bin/env python3
"""Attention-vs-MLP patching on manually confirmed real sibling pairs."""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.anchor_eval import process_margin  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import (  # noqa: E402
    candidate_first_token_id,
    get_transformer_layers,
    is_local_model,
    load_causal_lm,
    load_tokenizer,
    model_device,
    visible_device_label,
)

SPAN_NAMES = ["problem_span", "trace_span", "support_error_span", "final_answer_span"]
MODULE_NAMES = ["self_attn", "linear_attn", "mlp"]


def verifier_prompt_process_only(row: dict[str, Any]) -> str:
    return (
        "You are auditing a mathematical reasoning trace. Judge only whether the mathematical "
        "reasoning steps are valid; do not penalize missing final-answer formatting, truncation, "
        "or extra text after the answer. If any mathematical step is wrong, answer No. If the "
        "visible reasoning steps are mathematically valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {row['problem']}\n"
        f"Reasoning trace: {row['completion']}\n"
        "Are the visible reasoning steps mathematically valid? Answer:"
    )


def find_positions(tokenizer, prompt: str, target: str | None) -> list[int]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
    if target is None:
        return [int(enc["attention_mask"].sum().item()) - 1]
    start = prompt.find(target)
    if start >= 0:
        end = start + len(target)
        try:
            enc2 = tokenizer(prompt, return_tensors="pt", add_special_tokens=True, return_offsets_mapping=True)
            positions = []
            for idx, (a, b) in enumerate(enc2["offset_mapping"][0].tolist()):
                if a == b == 0:
                    continue
                if max(a, start) < min(b, end):
                    positions.append(idx)
            if positions:
                return positions
        except Exception:  # noqa: BLE001
            pass
    target_ids = tokenizer.encode(target, add_special_tokens=False)
    ids = enc["input_ids"][0].tolist()
    for idx in range(max(0, len(ids) - len(target_ids) + 1)):
        if ids[idx : idx + len(target_ids)] == target_ids:
            return list(range(idx, idx + len(target_ids)))
    return [int(enc["attention_mask"].sum().item()) - 1]


def span_target(pair: dict[str, Any], row: dict[str, Any], side: str, span: str) -> str | None:
    if span == "problem_span":
        return row["problem"]
    if span == "trace_span":
        return row["completion"]
    if span == "support_error_span":
        return pair["support_span"] if side == "valid" else pair["error_span"]
    if span == "final_answer_span":
        return pair.get("final_span_valid") if side == "valid" else pair.get("final_span_bad")
    raise KeyError(span)


def encoded_to_device(tokenizer, prompt: str, device: torch.device) -> dict[str, torch.Tensor]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
    return {k: v.to(device) for k, v in enc.items()}


def _extract_module_output(output):
    if isinstance(output, tuple):
        return output[0]
    return output


def _replace_module_output(output, patched_hidden):
    if isinstance(output, tuple):
        return (patched_hidden,) + tuple(output[1:])
    return patched_hidden


def module_span_vec(model, tokenizer, layers, prompt: str, positions: list[int], layer_idx: int, module_name: str, device: torch.device) -> torch.Tensor:
    module = getattr(layers[layer_idx], module_name, None)
    if module is None:
        raise AttributeError(f"Layer {layer_idx} has no module {module_name}")
    captured: dict[str, torch.Tensor] = {}

    def hook(_module, _inputs, output):
        captured["hidden"] = _extract_module_output(output).detach()
        return output

    handle = module.register_forward_hook(hook)
    try:
        with torch.no_grad():
            model(**encoded_to_device(tokenizer, prompt, device), use_cache=False)
    finally:
        handle.remove()
    hidden = captured["hidden"][0]
    valid_positions = [p for p in positions if 0 <= p < hidden.shape[0]] or [hidden.shape[0] - 1]
    return hidden[valid_positions, :].mean(dim=0).detach()


def patched_margin_module(
    model,
    tokenizer,
    layers,
    prompt: str,
    target_positions: list[int],
    layer_idx: int,
    module_name: str,
    donor_vec: torch.Tensor,
    yes_id: int,
    no_id: int,
    device: torch.device,
) -> float:
    module = getattr(layers[layer_idx], module_name, None)
    if module is None:
        raise AttributeError(f"Layer {layer_idx} has no module {module_name}")

    def hook(_module, _inputs, output):
        hidden = _extract_module_output(output).clone()
        valid_positions = [p for p in target_positions if 0 <= p < hidden.shape[1]] or [hidden.shape[1] - 1]
        hidden[:, valid_positions, :] = donor_vec.to(hidden.device, dtype=hidden.dtype)
        return _replace_module_output(output, hidden)

    handle = module.register_forward_hook(hook)
    try:
        return process_margin(model, tokenizer, prompt, yes_id, no_id, device)
    finally:
        handle.remove()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/manual_e05_audit_combined_20260427.jsonl"))
    p.add_argument("--pairs-yaml", default=str(PROJECT / "configs/e17_real_semantic_drift_pairs.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E19_real_acpi_module_patch"))
    p.add_argument("--layers", default=None, help="Optional comma/space layer override.")
    p.add_argument("--spans", default="problem_span,trace_span,support_error_span")
    p.add_argument("--modules", default="self_attn,mlp")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def parse_ints(text: str | None) -> list[int] | None:
    if not text:
        return None
    return [int(x) for x in re.split(r"[, ]+", text.strip()) if x]


def parse_names(text: str, allowed: list[str]) -> list[str]:
    names = [x for x in re.split(r"[, ]+", text.strip()) if x]
    bad = [x for x in names if x not in allowed]
    if bad:
        raise ValueError(f"Unsupported names {bad}; allowed={allowed}")
    return names


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    manual = {}
    for line in Path(args.manual_jsonl).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        idx = row.get("e05_idx", row.get("audit_idx"))
        if idx is None:
            raise KeyError("manual row has neither e05_idx nor audit_idx")
        manual[idx] = row
    pairs_all = read_yaml(args.pairs_yaml)["pairs"]
    pairs = [p for p in pairs_all if p["model_key"] == args.model_key]
    if not pairs:
        raise SystemExit(f"No pairs for model {args.model_key}")
    spans = parse_names(args.spans, SPAN_NAMES)
    modules = parse_names(args.modules, MODULE_NAMES)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} on {args.device}; pairs={len(pairs)} modules={modules}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    yes_id = candidate_first_token_id(tokenizer, [" Yes", "Yes", " yes", "yes"])
    no_id = candidate_first_token_id(tokenizer, [" No", "No", " no", "no"])
    rows = []
    for pair in pairs:
        valid = manual[pair["valid_idx"]]
        bad = manual[pair["bad_idx"]]
        valid_prompt = verifier_prompt_process_only(valid)
        bad_prompt = verifier_prompt_process_only(bad)
        base_valid = process_margin(model, tokenizer, valid_prompt, yes_id, no_id, device)
        base_bad = process_margin(model, tokenizer, bad_prompt, yes_id, no_id, device)
        layer_ids = parse_ints(args.layers) or list(pair.get("module_layers", pair.get("layers", [])))
        layer_ids = [x for x in layer_ids if 0 <= x < len(layers)]
        pos_cache = {}
        for span in spans:
            pos_cache[("valid", span)] = find_positions(tokenizer, valid_prompt, span_target(pair, valid, "valid", span))
            pos_cache[("bad", span)] = find_positions(tokenizer, bad_prompt, span_target(pair, bad, "bad", span))
        print(f"pair={pair['id']} base_valid={base_valid:.3f} base_bad={base_bad:.3f} layers={layer_ids}", flush=True)
        for span in spans:
            for layer_idx in layer_ids:
                for module_name in modules:
                    try:
                        valid_vec = module_span_vec(model, tokenizer, layers, valid_prompt, pos_cache[("valid", span)], layer_idx, module_name, device)
                        bad_vec = module_span_vec(model, tokenizer, layers, bad_prompt, pos_cache[("bad", span)], layer_idx, module_name, device)
                        v_to_b = patched_margin_module(model, tokenizer, layers, bad_prompt, pos_cache[("bad", span)], layer_idx, module_name, valid_vec, yes_id, no_id, device)
                        b_to_v = patched_margin_module(model, tokenizer, layers, valid_prompt, pos_cache[("valid", span)], layer_idx, module_name, bad_vec, yes_id, no_id, device)
                        error = None
                    except Exception as exc:  # noqa: BLE001
                        v_to_b = base_bad
                        b_to_v = base_valid
                        error = repr(exc)
                    rows.append(
                        {
                            "pair_id": pair["id"],
                            "valid_idx": pair["valid_idx"],
                            "bad_idx": pair["bad_idx"],
                            "span": span,
                            "layer": int(layer_idx),
                            "module": module_name,
                            "base_valid_margin": base_valid,
                            "base_bad_margin": base_bad,
                            "valid_to_bad_margin": v_to_b,
                            "valid_to_bad_effect": v_to_b - base_bad,
                            "bad_to_valid_margin": b_to_v,
                            "bad_to_valid_effect": b_to_v - base_valid,
                            "error": error,
                        }
                    )
    summary = []
    for pair_id in sorted({r["pair_id"] for r in rows}):
        for span in spans:
            for module_name in modules:
                sub = [r for r in rows if r["pair_id"] == pair_id and r["span"] == span and r["module"] == module_name and r["error"] is None]
                if not sub:
                    continue
                clean = [r for r in sub if r["valid_to_bad_effect"] > 0 and r["bad_to_valid_effect"] < 0]
                best_pool = clean or sub
                best = max(best_pool, key=lambda r: (r["valid_to_bad_effect"] - r["bad_to_valid_effect"], abs(r["valid_to_bad_effect"]) + abs(r["bad_to_valid_effect"])))
                summary.append(
                    {
                        "pair_id": pair_id,
                        "span": span,
                        "module": module_name,
                        "n": len(sub),
                        "clean_direction_n": len(clean),
                        "best_layer": best["layer"],
                        "best_valid_to_bad_effect": best["valid_to_bad_effect"],
                        "best_bad_to_valid_effect": best["bad_to_valid_effect"],
                    }
                )
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "pairs": pairs,
        "rows": rows,
        "summary": summary,
    }
    out = Path(args.out_dir) / f"{args.model_key}_real_acpi_module_patch.json"
    write_json(out, result)
    clean_rows = [r for r in rows if r["error"] is None and r["valid_to_bad_effect"] > 0 and r["bad_to_valid_effect"] < 0]
    best = max(clean_rows or [r for r in rows if r["error"] is None], key=lambda r: (r["valid_to_bad_effect"] - r["bad_to_valid_effect"], abs(r["valid_to_bad_effect"]) + abs(r["bad_to_valid_effect"])))
    print(
        f"wrote {out}; rows={len(rows)} best_pair={best['pair_id']} module={best['module']} "
        f"span={best['span']} L{best['layer']} v2b={best['valid_to_bad_effect']:.3f} b2v={best['bad_to_valid_effect']:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
