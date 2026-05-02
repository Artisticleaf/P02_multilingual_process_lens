#!/usr/bin/env python3
"""Span-specific residual patching for process-verifier anchors.

This is a tighter causal smoke than final-token patching: it asks whether
problem, trace, error/support, or final-clause spans can move the Yes-vs-No
process-validity margin when transplanted between valid and answer-correct
process-invalid traces.
"""
from __future__ import annotations

import argparse
import re
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.anchor_eval import _extract_layer_output, _replace_layer_output, auto_patch_layers, process_margin  # noqa: E402
from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import (  # noqa: E402
    candidate_first_token_id,
    get_transformer_layers,
    is_local_model,
    load_causal_lm,
    load_tokenizer,
    model_device,
    visible_device_label,
)
from mplens.text_cases import group_process_pairs, verifier_prompt  # noqa: E402


SPAN_NAMES = ("verdict_pos", "problem_span", "trace_span", "support_error_span", "final_clause_span")


def parse_layers(text: str | None) -> list[int] | None:
    if not text:
        return None
    out = []
    for part in re.split(r"[, ]+", text.strip()):
        if part:
            out.append(int(part))
    return sorted(set(out))


def first_clause(text: str) -> str:
    parts = re.split(r"(?:, then|, so|\\.\\s+|;)", text, maxsplit=1, flags=re.IGNORECASE)
    return parts[0].strip()


def final_clause(text: str) -> str:
    parts = re.split(r"(?:, then|, so|\\.\\s+|;)", text, flags=re.IGNORECASE)
    return next((p.strip() for p in reversed(parts) if p.strip()), text.strip())


def span_text(case: dict[str, Any], span_name: str) -> str | None:
    if span_name == "problem_span":
        return case["problem"]
    if span_name == "trace_span":
        return case["trace"]
    if span_name == "support_error_span":
        if case.get("process_valid"):
            return case.get("support_span") or first_clause(case["trace"])
        return case.get("error_span") or first_clause(case["trace"])
    if span_name == "final_clause_span":
        return final_clause(case["trace"])
    if span_name == "verdict_pos":
        return None
    raise KeyError(span_name)


def find_positions(tokenizer, prompt: str, target_text: str | None) -> list[int]:
    if target_text is None:
        enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        return [int(enc["attention_mask"].sum().item()) - 1]

    start = prompt.find(target_text)
    if start < 0:
        # Be conservative: if the exact clause was not found, fall back to the
        # final verifier token rather than silently patching a wrong span.
        return find_positions(tokenizer, prompt, None)
    end = start + len(target_text)
    try:
        enc = tokenizer(prompt, return_tensors="pt", return_offsets_mapping=True, add_special_tokens=True)
        offsets = enc["offset_mapping"][0].tolist()
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

    # Slow-tokenizer fallback: search the token-id subsequence.
    target_ids = tokenizer.encode(target_text, add_special_tokens=False)
    input_ids = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)["input_ids"][0].tolist()
    for idx in range(max(0, len(input_ids) - len(target_ids) + 1)):
        if input_ids[idx : idx + len(target_ids)] == target_ids:
            return list(range(idx, idx + len(target_ids)))
    return find_positions(tokenizer, prompt, None)


def encoded_to_device(tokenizer, prompt: str, device: torch.device) -> dict[str, torch.Tensor]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
    return {k: v.to(device) for k, v in enc.items()}


def layer_span_vec(
    model,
    tokenizer,
    prompt: str,
    positions: list[int],
    layer_idx: int,
    device: torch.device,
) -> torch.Tensor:
    enc = encoded_to_device(tokenizer, prompt, device)
    with torch.no_grad():
        out = model(**enc, output_hidden_states=True, use_cache=False)
    hidden = out.hidden_states[layer_idx + 1][0]
    valid_positions = [p for p in positions if 0 <= p < hidden.shape[0]]
    if not valid_positions:
        valid_positions = [hidden.shape[0] - 1]
    return hidden[valid_positions, :].mean(dim=0).detach()


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
) -> float:
    def hook(_module, _inputs, output):
        hidden = _extract_layer_output(output).clone()
        valid_positions = [p for p in target_positions if 0 <= p < hidden.shape[1]]
        if not valid_positions:
            valid_positions = [hidden.shape[1] - 1]
        hidden[:, valid_positions, :] = donor_vec.to(hidden.device, dtype=hidden.dtype)
        return _replace_layer_output(output, hidden)

    handle = layers[layer_idx].register_forward_hook(hook)
    try:
        return process_margin(model, tokenizer, prompt, yes_id, no_id, device)
    finally:
        handle.remove()


def layers_from_anchor(model_key: str, result_dir: Path, num_layers: int) -> list[int]:
    layers = set(auto_patch_layers(num_layers))
    path = result_dir / f"{model_key}_anchor_smoke.json"
    if not path.exists():
        return sorted(layers)
    data = read_json(path)
    bridge = data.get("contextual_bridge", {})
    for key in ("best_layer", "early_bridge_layer"):
        row = bridge.get(key)
        if isinstance(row, dict) and row.get("layer") is not None:
            layers.add(int(row["layer"]))
    for row in data.get("residual_patching", {}).get("by_layer", []):
        if row.get("mean_valid_to_bad_effect", 0) > 0 and row.get("mean_bad_to_valid_effect", 0) < 0:
            layers.add(int(row["layer"]))
    return sorted(x for x in layers if 0 <= x < num_layers)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--config", default=str(PROJECT / "configs/anchor_hard_smoke.yaml"))
    p.add_argument("--anchor-result-dir", default=str(PROJECT / "results/E01_anchor_matrix_hard"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E03_span_patch_hard"))
    p.add_argument("--layers", default=None, help="Comma/space separated layer list. Defaults to anchor-informed layers.")
    p.add_argument("--spans", default=",".join(SPAN_NAMES))
    p.add_argument("--max-pairs", type=int, default=None)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    config = read_yaml(args.config)
    spec = registry[args.model_key]
    spans = [s for s in re.split(r"[, ]+", args.spans.strip()) if s]
    unknown = sorted(set(spans) - set(SPAN_NAMES))
    if unknown:
        raise ValueError(f"Unknown spans: {unknown}; choices={SPAN_NAMES}")

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading tokenizer: {args.model_key} -> {spec['path']}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] loading model dtype={args.dtype} device={args.device}", flush=True)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    layer_ids = parse_layers(args.layers) or layers_from_anchor(args.model_key, Path(args.anchor_result_dir), len(layers))
    layer_ids = [x for x in layer_ids if 0 <= x < len(layers)]

    yes_id = candidate_first_token_id(tokenizer, [" Yes", "Yes", " yes", "yes"])
    no_id = candidate_first_token_id(tokenizer, [" No", "No", " no", "no"])
    cases = config["process_cases"][: config.get("run", {}).get("max_process_cases", len(config["process_cases"]))]
    pairs = group_process_pairs(cases)
    if args.max_pairs:
        pairs = pairs[: args.max_pairs]
    print(f"[{datetime.now().isoformat(timespec='seconds')}] pairs={len(pairs)} layers={layer_ids} spans={spans}", flush=True)

    rows = []
    for valid, bad in pairs:
        valid_prompt = verifier_prompt(valid["problem"], valid["trace"], lang="en")
        bad_prompt = verifier_prompt(bad["problem"], bad["trace"], lang="en")
        base_valid = process_margin(model, tokenizer, valid_prompt, yes_id, no_id, device)
        base_bad = process_margin(model, tokenizer, bad_prompt, yes_id, no_id, device)
        pos_cache: dict[tuple[str, str], list[int]] = {}
        prompt_cache = {"valid": valid_prompt, "bad": bad_prompt}
        case_cache = {"valid": valid, "bad": bad}

        for span_name in spans:
            for side in ("valid", "bad"):
                pos_cache[(side, span_name)] = find_positions(
                    tokenizer,
                    prompt_cache[side],
                    span_text(case_cache[side], span_name),
                )
            for layer_idx in layer_ids:
                valid_vec = layer_span_vec(
                    model,
                    tokenizer,
                    valid_prompt,
                    pos_cache[("valid", span_name)],
                    layer_idx,
                    device,
                )
                bad_vec = layer_span_vec(
                    model,
                    tokenizer,
                    bad_prompt,
                    pos_cache[("bad", span_name)],
                    layer_idx,
                    device,
                )
                v_to_b = patched_margin(
                    model,
                    tokenizer,
                    layers,
                    bad_prompt,
                    pos_cache[("bad", span_name)],
                    layer_idx,
                    valid_vec,
                    yes_id,
                    no_id,
                    device,
                )
                b_to_v = patched_margin(
                    model,
                    tokenizer,
                    layers,
                    valid_prompt,
                    pos_cache[("valid", span_name)],
                    layer_idx,
                    bad_vec,
                    yes_id,
                    no_id,
                    device,
                )
                rows.append(
                    {
                        "valid_case_id": valid["id"],
                        "bad_case_id": bad["id"],
                        "span": span_name,
                        "layer": int(layer_idx),
                        "valid_positions": pos_cache[("valid", span_name)],
                        "bad_positions": pos_cache[("bad", span_name)],
                        "valid_span_text": span_text(valid, span_name) or "<verdict_pos>",
                        "bad_span_text": span_text(bad, span_name) or "<verdict_pos>",
                        "base_valid_margin": base_valid,
                        "base_bad_margin": base_bad,
                        "valid_to_bad_margin": v_to_b,
                        "valid_to_bad_effect": v_to_b - base_bad,
                        "bad_to_valid_margin": b_to_v,
                        "bad_to_valid_effect": b_to_v - base_valid,
                    }
                )

    by_span_layer = []
    for span_name in spans:
        for layer_idx in layer_ids:
            sub = [r for r in rows if r["span"] == span_name and r["layer"] == layer_idx]
            if not sub:
                continue
            by_span_layer.append(
                {
                    "span": span_name,
                    "layer": int(layer_idx),
                    "n": len(sub),
                    "mean_valid_to_bad_effect": float(sum(r["valid_to_bad_effect"] for r in sub) / len(sub)),
                    "mean_bad_to_valid_effect": float(sum(r["bad_to_valid_effect"] for r in sub) / len(sub)),
                    "mean_abs_effect": float(
                        sum(abs(r["valid_to_bad_effect"]) + abs(r["bad_to_valid_effect"]) for r in sub) / (2 * len(sub))
                    ),
                }
            )

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "dtype": args.dtype,
        "device": str(device),
        "num_layers": len(layers),
        "layers": layer_ids,
        "spans": spans,
        "yes_id": int(yes_id),
        "no_id": int(no_id),
        "rows": rows,
        "by_span_layer": by_span_layer,
    }
    out = Path(args.out_dir) / f"{args.model_key}_span_patch_hard.json"
    write_json(out, result)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] wrote {out}; rows={len(rows)}", flush=True)
    clean = [
        r
        for r in by_span_layer
        if r["mean_valid_to_bad_effect"] > 0 and r["mean_bad_to_valid_effect"] < 0
    ]
    best = max(clean or by_span_layer, key=lambda r: (r["mean_valid_to_bad_effect"] - r["mean_bad_to_valid_effect"], r["mean_abs_effect"]))
    print(
        "SUMMARY "
        f"model={args.model_key} best_span={best['span']} layer={best['layer']} "
        f"v2b={best['mean_valid_to_bad_effect']:.3f} b2v={best['mean_bad_to_valid_effect']:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
