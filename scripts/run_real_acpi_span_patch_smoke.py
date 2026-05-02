#!/usr/bin/env python3
"""Residual span patching on manually confirmed real ACPI pairs."""
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

from mplens.anchor_eval import _extract_layer_output, _replace_layer_output  # noqa: E402
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

SPAN_NAMES = ["verdict_pos", "problem_span", "trace_span", "support_error_span", "final_answer_span"]


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


def should_use_chat_template(model_spec: dict[str, Any], mode: str, tokenizer) -> bool:
    if mode == "raw":
        return False
    if mode == "chat":
        return bool(getattr(tokenizer, "chat_template", None))
    cls = str(model_spec.get("class", "")).lower()
    fam = str(model_spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (
        fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls
    )


def maybe_chat_prompt(tokenizer, prompt: str, use_chat_template: bool) -> str:
    if not use_chat_template:
        return prompt
    messages = [{"role": "user", "content": prompt}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def find_positions(tokenizer, prompt: str, target: str | None, *, add_special_tokens: bool) -> list[int]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=add_special_tokens)
    if target is None:
        return [int(enc["attention_mask"].sum().item()) - 1]
    start = prompt.find(target)
    if start >= 0:
        end = start + len(target)
        try:
            enc2 = tokenizer(
                prompt,
                return_tensors="pt",
                add_special_tokens=add_special_tokens,
                return_offsets_mapping=True,
            )
            offsets = enc2["offset_mapping"][0].tolist()
            positions = []
            for idx, (a, b) in enumerate(offsets):
                if a == b == 0:
                    continue
                if max(a, start) < min(b, end):
                    positions.append(idx)
            if positions:
                return positions
        except Exception:  # noqa: BLE001
            pass
    # Loose fallback for target snippets with whitespace/latex differences.
    compact_prompt = re.sub(r"\s+", "", prompt)
    compact_target = re.sub(r"\s+", "", target)
    start_compact = compact_prompt.find(compact_target)
    if start_compact >= 0:
        # If compact matching works but offsets are hard, use the target token-id subsequence.
        target_ids = tokenizer.encode(target, add_special_tokens=False)
        ids = enc["input_ids"][0].tolist()
        for idx in range(max(0, len(ids) - len(target_ids) + 1)):
            if ids[idx : idx + len(target_ids)] == target_ids:
                return list(range(idx, idx + len(target_ids)))
    return [int(enc["attention_mask"].sum().item()) - 1]


def span_target(pair: dict[str, Any], row: dict[str, Any], side: str, span: str) -> str | None:
    if span == "verdict_pos":
        return None
    if span == "problem_span":
        return row["problem"]
    if span == "trace_span":
        return row["completion"]
    if span == "support_error_span":
        return pair["support_span"] if side == "valid" else pair["error_span"]
    if span == "final_answer_span":
        return pair.get("final_span_valid") if side == "valid" else pair.get("final_span_bad")
    raise KeyError(span)


def encoded_to_device(tokenizer, prompt: str, device: torch.device, *, add_special_tokens: bool) -> dict[str, torch.Tensor]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=add_special_tokens)
    return {k: v.to(device) for k, v in enc.items()}


def layer_span_vec(
    model,
    tokenizer,
    prompt: str,
    positions: list[int],
    layer_idx: int,
    device: torch.device,
    *,
    add_special_tokens: bool,
) -> torch.Tensor:
    enc = encoded_to_device(tokenizer, prompt, device, add_special_tokens=add_special_tokens)
    with torch.no_grad():
        out = model(**enc, output_hidden_states=True, use_cache=False)
    hidden = out.hidden_states[layer_idx + 1][0]
    valid_positions = [p for p in positions if 0 <= p < hidden.shape[0]] or [hidden.shape[0] - 1]
    return hidden[valid_positions, :].mean(dim=0).detach()


def process_margin_local(
    model,
    tokenizer,
    prompt: str,
    yes_id: int,
    no_id: int,
    device: torch.device,
    *,
    add_special_tokens: bool,
) -> float:
    enc = encoded_to_device(tokenizer, prompt, device, add_special_tokens=add_special_tokens)
    with torch.no_grad():
        logits = model(**enc, use_cache=False).logits[0, -1, :].float()
    log_probs = torch.nn.functional.log_softmax(logits, dim=-1)
    return float((log_probs[yes_id] - log_probs[no_id]).item())


def patched_margin(
    model,
    tokenizer,
    layers,
    prompt: str,
    target_positions: list[int],
    layer_idx: int,
    donor_vec: torch.Tensor,
    yes_id: int,
    no_id: int,
    device: torch.device,
    *,
    add_special_tokens: bool,
) -> float:
    def hook(_module, _inputs, output):
        hidden = _extract_layer_output(output).clone()
        valid_positions = [p for p in target_positions if 0 <= p < hidden.shape[1]] or [hidden.shape[1] - 1]
        hidden[:, valid_positions, :] = donor_vec.to(hidden.device, dtype=hidden.dtype)
        return _replace_layer_output(output, hidden)

    handle = layers[layer_idx].register_forward_hook(hook)
    try:
        return process_margin_local(
            model,
            tokenizer,
            prompt,
            yes_id,
            no_id,
            device,
            add_special_tokens=add_special_tokens,
        )
    finally:
        handle.remove()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/manual_e05_audit_seed_20260427.jsonl"))
    p.add_argument("--pairs-yaml", default=str(PROJECT / "configs/e09_real_acpi_pairs.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E09_real_acpi_span_patch"))
    p.add_argument("--layers", default=None, help="Optional comma/space layer override")
    p.add_argument("--spans", default=",".join(SPAN_NAMES))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="raw")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def parse_layer_override(text: str | None) -> list[int] | None:
    if not text:
        return None
    return [int(x) for x in re.split(r"[, ]+", text.strip()) if x]


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    manual = {json.loads(line)["audit_idx"]: json.loads(line) for line in Path(args.manual_jsonl).read_text(encoding="utf-8").splitlines() if line.strip()}
    pairs_all = read_yaml(args.pairs_yaml)["pairs"]
    pairs = [p for p in pairs_all if p["model_key"] == args.model_key]
    if not pairs:
        raise SystemExit(f"No pairs for model {args.model_key}")
    spans = [s for s in re.split(r"[, ]+", args.spans.strip()) if s]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} on {args.device}; pairs={len(pairs)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat_template = should_use_chat_template(spec, args.prompt_format, tokenizer)
    add_special_tokens = not use_chat_template
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    yes_id = candidate_first_token_id(tokenizer, [" Yes", "Yes", " yes", "yes"])
    no_id = candidate_first_token_id(tokenizer, [" No", "No", " no", "no"])
    rows = []
    for pair in pairs:
        valid = manual[pair["valid_idx"]]
        bad = manual[pair["bad_idx"]]
        valid_prompt = maybe_chat_prompt(tokenizer, verifier_prompt_process_only(valid), use_chat_template)
        bad_prompt = maybe_chat_prompt(tokenizer, verifier_prompt_process_only(bad), use_chat_template)
        base_valid = process_margin_local(
            model,
            tokenizer,
            valid_prompt,
            yes_id,
            no_id,
            device,
            add_special_tokens=add_special_tokens,
        )
        base_bad = process_margin_local(
            model,
            tokenizer,
            bad_prompt,
            yes_id,
            no_id,
            device,
            add_special_tokens=add_special_tokens,
        )
        layer_ids = parse_layer_override(args.layers) or list(pair.get("layers", []))
        layer_ids = [x for x in layer_ids if 0 <= x < len(layers)]
        pos_cache = {}
        for span in spans:
            pos_cache[("valid", span)] = find_positions(
                tokenizer,
                valid_prompt,
                span_target(pair, valid, "valid", span),
                add_special_tokens=add_special_tokens,
            )
            pos_cache[("bad", span)] = find_positions(
                tokenizer,
                bad_prompt,
                span_target(pair, bad, "bad", span),
                add_special_tokens=add_special_tokens,
            )
        print(f"pair={pair['id']} base_valid={base_valid:.3f} base_bad={base_bad:.3f} layers={layer_ids}", flush=True)
        for span in spans:
            for layer_idx in layer_ids:
                valid_vec = layer_span_vec(
                    model,
                    tokenizer,
                    valid_prompt,
                    pos_cache[("valid", span)],
                    layer_idx,
                    device,
                    add_special_tokens=add_special_tokens,
                )
                bad_vec = layer_span_vec(
                    model,
                    tokenizer,
                    bad_prompt,
                    pos_cache[("bad", span)],
                    layer_idx,
                    device,
                    add_special_tokens=add_special_tokens,
                )
                v_to_b = patched_margin(
                    model,
                    tokenizer,
                    layers,
                    bad_prompt,
                    pos_cache[("bad", span)],
                    layer_idx,
                    valid_vec,
                    yes_id,
                    no_id,
                    device,
                    add_special_tokens=add_special_tokens,
                )
                b_to_v = patched_margin(
                    model,
                    tokenizer,
                    layers,
                    valid_prompt,
                    pos_cache[("valid", span)],
                    layer_idx,
                    bad_vec,
                    yes_id,
                    no_id,
                    device,
                    add_special_tokens=add_special_tokens,
                )
                rows.append(
                    {
                        "pair_id": pair["id"],
                        "valid_idx": pair["valid_idx"],
                        "bad_idx": pair["bad_idx"],
                        "span": span,
                        "layer": int(layer_idx),
                        "base_valid_margin": base_valid,
                        "base_bad_margin": base_bad,
                        "valid_to_bad_margin": v_to_b,
                        "valid_to_bad_effect": v_to_b - base_bad,
                        "bad_to_valid_margin": b_to_v,
                        "bad_to_valid_effect": b_to_v - base_valid,
                        "valid_positions": pos_cache[("valid", span)],
                        "bad_positions": pos_cache[("bad", span)],
                        "valid_span_text": span_target(pair, valid, "valid", span) or "<verdict_pos>",
                        "bad_span_text": span_target(pair, bad, "bad", span) or "<verdict_pos>",
                    }
                )
    by_span_layer_pair = []
    for pair in pairs:
        for span in spans:
            for layer_idx in sorted({r["layer"] for r in rows if r["pair_id"] == pair["id"] and r["span"] == span}):
                sub = [r for r in rows if r["pair_id"] == pair["id"] and r["span"] == span and r["layer"] == layer_idx]
                by_span_layer_pair.append(
                    {
                        "pair_id": pair["id"],
                        "span": span,
                        "layer": layer_idx,
                        "n": len(sub),
                        "mean_valid_to_bad_effect": sum(r["valid_to_bad_effect"] for r in sub) / len(sub),
                        "mean_bad_to_valid_effect": sum(r["bad_to_valid_effect"] for r in sub) / len(sub),
                        "mean_abs_effect": sum(abs(r["valid_to_bad_effect"]) + abs(r["bad_to_valid_effect"]) for r in sub) / (2 * len(sub)),
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
        "used_chat_template": use_chat_template,
        "add_special_tokens": add_special_tokens,
        "pairs": pairs,
        "rows": rows,
        "by_span_layer_pair": by_span_layer_pair,
    }
    out = Path(args.out_dir) / f"{args.model_key}_real_acpi_span_patch.json"
    write_json(out, result)
    clean = [r for r in by_span_layer_pair if r["mean_valid_to_bad_effect"] > 0 and r["mean_bad_to_valid_effect"] < 0]
    best = max(clean or by_span_layer_pair, key=lambda r: (r["mean_valid_to_bad_effect"] - r["mean_bad_to_valid_effect"], r["mean_abs_effect"]))
    print(
        f"wrote {out}; rows={len(rows)} best_pair={best['pair_id']} span={best['span']} L{best['layer']} "
        f"v2b={best['mean_valid_to_bad_effect']:.3f} b2v={best['mean_bad_to_valid_effect']:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
