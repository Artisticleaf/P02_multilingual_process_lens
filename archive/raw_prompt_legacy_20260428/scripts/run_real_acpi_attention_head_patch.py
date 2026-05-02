#!/usr/bin/env python3
"""Pre-o_proj attention-head patching on real ACPI sibling pairs.

This is a narrower mechanism probe than residual/module patching. It replaces
one attention head's pre-output-projection vector at the audited span, then
measures the verifier Yes-minus-No margin change.
"""
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


def parse_ints(text: str | None) -> list[int] | None:
    if not text:
        return None
    return [int(x) for x in re.split(r"[, ]+", text.strip()) if x]


def parse_spans(text: str) -> list[str]:
    spans = [x for x in re.split(r"[, ]+", text.strip()) if x]
    bad = [x for x in spans if x not in SPAN_NAMES]
    if bad:
        raise ValueError(f"Unsupported spans {bad}; allowed={SPAN_NAMES}")
    return spans


def load_manual(path: str) -> dict[int, dict[str, Any]]:
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        idx = row.get("e05_idx", row.get("audit_idx"))
        if idx is None:
            raise KeyError("manual row has neither e05_idx nor audit_idx")
        out[idx] = row
    return out


def get_o_proj(layers, layer_idx: int):
    attn = getattr(layers[layer_idx], "self_attn", None)
    if attn is None or not hasattr(attn, "o_proj"):
        raise AttributeError(f"Layer {layer_idx} has no self_attn.o_proj")
    return attn.o_proj


def capture_o_proj_input(
    model,
    tokenizer,
    layers,
    prompt: str,
    positions: list[int],
    layer_idx: int,
    head_idx: int,
    head_dim: int,
    device: torch.device,
) -> torch.Tensor:
    o_proj = get_o_proj(layers, layer_idx)
    captured: dict[str, torch.Tensor] = {}

    def pre_hook(_module, inputs):
        captured["x"] = inputs[0].detach()
        return None

    handle = o_proj.register_forward_pre_hook(pre_hook)
    try:
        with torch.no_grad():
            model(**encoded_to_device(tokenizer, prompt, device), use_cache=False)
    finally:
        handle.remove()
    x = captured["x"][0]
    valid_positions = [p for p in positions if 0 <= p < x.shape[0]] or [x.shape[0] - 1]
    start = head_idx * head_dim
    end = start + head_dim
    return x[valid_positions, start:end].mean(dim=0).detach()


def patched_margin_head(
    model,
    tokenizer,
    layers,
    prompt: str,
    target_positions: list[int],
    layer_idx: int,
    head_idx: int,
    head_dim: int,
    donor_vec: torch.Tensor,
    yes_id: int,
    no_id: int,
    device: torch.device,
) -> float:
    o_proj = get_o_proj(layers, layer_idx)
    start = head_idx * head_dim
    end = start + head_dim

    def pre_hook(_module, inputs):
        x = inputs[0].clone()
        valid_positions = [p for p in target_positions if 0 <= p < x.shape[1]] or [x.shape[1] - 1]
        x[:, valid_positions, start:end] = donor_vec.to(x.device, dtype=x.dtype)
        return (x,) + tuple(inputs[1:])

    handle = o_proj.register_forward_pre_hook(pre_hook)
    try:
        return process_margin(model, tokenizer, prompt, yes_id, no_id, device)
    finally:
        handle.remove()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/s6_lexical_grid_verifier_subset_20260427.jsonl"))
    p.add_argument("--pairs-yaml", default=str(PROJECT / "configs/s6_lexical_grid_span_patch_pairs.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/S6_lexical_grid_attention_head_patch"))
    p.add_argument("--layers", default=None)
    p.add_argument("--spans", default="support_error_span")
    p.add_argument("--heads", default=None, help="Optional comma/space head override; default scans all heads.")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    manual = load_manual(args.manual_jsonl)
    pairs_all = read_yaml(args.pairs_yaml)["pairs"]
    pairs = [p for p in pairs_all if p["model_key"] == args.model_key]
    if not pairs:
        raise SystemExit(f"No pairs for model {args.model_key}")
    spans = parse_spans(args.spans)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} on {args.device}; pairs={len(pairs)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    n_heads = int(getattr(model.config, "num_attention_heads"))
    head_dim = int(getattr(model.config, "head_dim", getattr(model.config, "hidden_size") // n_heads))
    heads = parse_ints(args.heads) or list(range(n_heads))
    heads = [h for h in heads if 0 <= h < n_heads]
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
        layer_ids = parse_ints(args.layers) or list(pair.get("head_layers", pair.get("module_layers", pair.get("layers", []))))
        layer_ids = [x for x in layer_ids if 0 <= x < len(layers)]
        pos_cache = {}
        for span in spans:
            pos_cache[("valid", span)] = find_positions(tokenizer, valid_prompt, span_target(pair, valid, "valid", span))
            pos_cache[("bad", span)] = find_positions(tokenizer, bad_prompt, span_target(pair, bad, "bad", span))
        print(
            f"pair={pair['id']} base_valid={base_valid:.3f} base_bad={base_bad:.3f} "
            f"layers={layer_ids} heads={len(heads)}",
            flush=True,
        )
        for span in spans:
            for layer_idx in layer_ids:
                for head_idx in heads:
                    try:
                        valid_vec = capture_o_proj_input(
                            model, tokenizer, layers, valid_prompt, pos_cache[("valid", span)], layer_idx, head_idx, head_dim, device
                        )
                        bad_vec = capture_o_proj_input(
                            model, tokenizer, layers, bad_prompt, pos_cache[("bad", span)], layer_idx, head_idx, head_dim, device
                        )
                        v_to_b = patched_margin_head(
                            model, tokenizer, layers, bad_prompt, pos_cache[("bad", span)], layer_idx, head_idx, head_dim, valid_vec, yes_id, no_id, device
                        )
                        b_to_v = patched_margin_head(
                            model, tokenizer, layers, valid_prompt, pos_cache[("valid", span)], layer_idx, head_idx, head_dim, bad_vec, yes_id, no_id, device
                        )
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
                            "head": int(head_idx),
                            "base_valid_margin": base_valid,
                            "base_bad_margin": base_bad,
                            "valid_to_bad_margin": v_to_b,
                            "valid_to_bad_effect": v_to_b - base_bad,
                            "bad_to_valid_margin": b_to_v,
                            "bad_to_valid_effect": b_to_v - base_valid,
                            "error": error,
                        }
                    )
    valid_rows = [r for r in rows if r["error"] is None]
    clean = [r for r in valid_rows if r["valid_to_bad_effect"] > 0 and r["bad_to_valid_effect"] < 0]
    best = max(clean or valid_rows, key=lambda r: (r["valid_to_bad_effect"] - r["bad_to_valid_effect"], abs(r["valid_to_bad_effect"]) + abs(r["bad_to_valid_effect"])))
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "num_attention_heads": n_heads,
        "head_dim": head_dim,
        "pairs": pairs,
        "rows": rows,
        "best_clean_or_effect": best,
        "clean_direction_n": len(clean),
        "valid_row_n": len(valid_rows),
    }
    out = Path(args.out_dir) / f"{args.model_key}_real_acpi_attention_head_patch.json"
    write_json(out, result)
    print(
        f"wrote {out}; rows={len(rows)} clean={len(clean)}/{len(valid_rows)} "
        f"best_pair={best['pair_id']} span={best['span']} L{best['layer']} H{best['head']} "
        f"v2b={best['valid_to_bad_effect']:.3f} b2v={best['bad_to_valid_effect']:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
