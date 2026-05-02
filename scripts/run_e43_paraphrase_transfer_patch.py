#!/usr/bin/env python3
"""E43 cross-paraphrase residual span transfer.

For each family, vectors are taken from one paraphrase and patched into the
other paraphrase.  A mismatched-family donor is included as a negative control.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verifier_prompt(row: dict[str, Any]) -> str:
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


def maybe_chat(tokenizer, text: str, use_chat: bool) -> str:
    if not use_chat:
        return text
    messages = [{"role": "user", "content": text}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def encode(tokenizer, prompt: str, device: torch.device, *, add_special_tokens: bool) -> dict[str, torch.Tensor]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=add_special_tokens)
    return {k: v.to(device) for k, v in enc.items()}


def find_positions(tokenizer, prompt: str, target: str, *, add_special_tokens: bool) -> list[int]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=add_special_tokens)
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
            pos = []
            for idx, (a, b) in enumerate(enc2["offset_mapping"][0].tolist()):
                if a == b == 0:
                    continue
                if max(a, start) < min(b, end):
                    pos.append(idx)
            if pos:
                return pos
        except Exception:  # noqa: BLE001
            pass
    target_ids = tokenizer.encode(target, add_special_tokens=False)
    ids = enc["input_ids"][0].tolist()
    for i in range(max(0, len(ids) - len(target_ids) + 1)):
        if ids[i : i + len(target_ids)] == target_ids:
            return list(range(i, i + len(target_ids)))
    return [int(enc["attention_mask"].sum().item()) - 1]


def process_margin(model, tokenizer, prompt: str, yes_id: int, no_id: int, device: torch.device, *, add_special_tokens: bool) -> float:
    with torch.no_grad():
        logits = model(**encode(tokenizer, prompt, device, add_special_tokens=add_special_tokens), use_cache=False).logits[0, -1, :].float()
    logp = F.log_softmax(logits, dim=-1)
    return float((logp[yes_id] - logp[no_id]).item())


def residual_vec(model, tokenizer, prompt: str, positions: list[int], layer_idx: int, device: torch.device, *, add_special_tokens: bool) -> torch.Tensor:
    with torch.no_grad():
        out = model(**encode(tokenizer, prompt, device, add_special_tokens=add_special_tokens), output_hidden_states=True, use_cache=False)
    hidden = out.hidden_states[layer_idx + 1][0]
    pos = [p for p in positions if 0 <= p < hidden.shape[0]] or [hidden.shape[0] - 1]
    return hidden[pos, :].mean(dim=0).detach()


def patched_margin(
    model,
    tokenizer,
    layers,
    prompt: str,
    positions: list[int],
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
        pos = [p for p in positions if 0 <= p < hidden.shape[1]] or [hidden.shape[1] - 1]
        hidden[:, pos, :] = donor_vec.to(hidden.device, dtype=hidden.dtype)
        return _replace_layer_output(output, hidden)

    handle = layers[layer_idx].register_forward_hook(hook)
    try:
        return process_margin(model, tokenizer, prompt, yes_id, no_id, device, add_special_tokens=add_special_tokens)
    finally:
        handle.remove()


def parse_layers(text: str | None, default: list[int]) -> list[int]:
    if not text:
        return default
    return [int(x) for x in re.split(r"[, ]+", text.strip()) if x]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/e43_paraphrase_transfer_20260428.jsonl"))
    p.add_argument("--pairs-yaml", default=str(PROJECT / "configs/e43_paraphrase_transfer_pairs.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E43_paraphrase_transfer_patch"))
    p.add_argument("--layers", default=None)
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows_by_id = {r["audit_idx"]: r for r in load_jsonl(Path(args.manual_jsonl))}
    pairs = read_yaml(args.pairs_yaml)["pairs"]
    pair_by_family_tag = {(p["task_id"], p["paraphrase_tag"]): p for p in pairs}
    families = sorted({p["task_id"] for p in pairs})
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} device={args.device}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format, tokenizer)
    add_special_tokens = not use_chat
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    default_layers = [0, 4, 8, 12, 16, 20, 24, 28, len(layers) - 1]
    layer_ids = sorted({x for x in parse_layers(args.layers, default_layers) if 0 <= x < len(layers)})
    yes_id = candidate_first_token_id(tokenizer, [" Yes", "Yes", " yes", "yes"])
    no_id = candidate_first_token_id(tokenizer, [" No", "No", " no", "no"])

    prepared: dict[tuple[str, str, str], dict[str, Any]] = {}
    for p in pairs:
        for side, idx_key, span_key in [("valid", "valid_idx", "support_span"), ("bad", "bad_idx", "error_span")]:
            row = rows_by_id[p[idx_key]]
            prompt = maybe_chat(tokenizer, verifier_prompt(row), use_chat)
            prepared[(p["task_id"], p["paraphrase_tag"], side)] = {
                "row": row,
                "pair": p,
                "prompt": prompt,
                "positions": find_positions(tokenizer, prompt, p[span_key], add_special_tokens=add_special_tokens),
                "span_text": p[span_key],
                "base_margin": process_margin(model, tokenizer, prompt, yes_id, no_id, device, add_special_tokens=add_special_tokens),
            }

    vec_cache: dict[tuple[str, str, str, int], torch.Tensor] = {}
    for key, item in prepared.items():
        for layer_idx in layer_ids:
            vec_cache[(*key, layer_idx)] = residual_vec(
                model,
                tokenizer,
                item["prompt"],
                item["positions"],
                layer_idx,
                device,
                add_special_tokens=add_special_tokens,
            )

    eval_rows = []
    tags = ["a", "b"]
    for fam_i, fam in enumerate(families):
        mismatch_fam = families[(fam_i + 1) % len(families)]
        for target_tag in tags:
            donor_tag = "b" if target_tag == "a" else "a"
            for control, donor_fam in [("same_family", fam), ("mismatched_family", mismatch_fam)]:
                donor_pair = pair_by_family_tag[(donor_fam, donor_tag)]
                target_pair = pair_by_family_tag[(fam, target_tag)]
                target_valid = prepared[(fam, target_tag, "valid")]
                target_bad = prepared[(fam, target_tag, "bad")]
                for layer_idx in layer_ids:
                    donor_valid_vec = vec_cache[(donor_fam, donor_tag, "valid", layer_idx)]
                    donor_bad_vec = vec_cache[(donor_fam, donor_tag, "bad", layer_idx)]
                    v_to_b = patched_margin(
                        model,
                        tokenizer,
                        layers,
                        target_bad["prompt"],
                        target_bad["positions"],
                        layer_idx,
                        donor_valid_vec,
                        yes_id,
                        no_id,
                        device,
                        add_special_tokens=add_special_tokens,
                    )
                    b_to_v = patched_margin(
                        model,
                        tokenizer,
                        layers,
                        target_valid["prompt"],
                        target_valid["positions"],
                        layer_idx,
                        donor_bad_vec,
                        yes_id,
                        no_id,
                        device,
                        add_special_tokens=add_special_tokens,
                    )
                    eval_rows.append(
                        {
                            "target_task": fam,
                            "target_pair_id": target_pair["id"],
                            "target_tag": target_tag,
                            "donor_task": donor_fam,
                            "donor_pair_id": donor_pair["id"],
                            "donor_tag": donor_tag,
                            "control": control,
                            "layer": layer_idx,
                            "base_valid_margin": target_valid["base_margin"],
                            "base_bad_margin": target_bad["base_margin"],
                            "valid_to_bad_margin": v_to_b,
                            "valid_to_bad_effect": v_to_b - target_bad["base_margin"],
                            "bad_to_valid_margin": b_to_v,
                            "bad_to_valid_effect": b_to_v - target_valid["base_margin"],
                            "clean_direction": (v_to_b - target_bad["base_margin"] > 0) and (b_to_v - target_valid["base_margin"] < 0),
                        }
                    )
        print(f"finished family={fam}", flush=True)

    summary = []
    for control in ["same_family", "mismatched_family"]:
        sub = [r for r in eval_rows if r["control"] == control]
        best_by_target = []
        for pair_id in sorted({r["target_pair_id"] for r in sub}):
            g = [r for r in sub if r["target_pair_id"] == pair_id]
            clean = [r for r in g if r["clean_direction"]]
            best = max(clean or g, key=lambda r: (r["valid_to_bad_effect"] - r["bad_to_valid_effect"], abs(r["valid_to_bad_effect"]) + abs(r["bad_to_valid_effect"])))
            best_by_target.append(best)
        summary.append(
            {
                "control": control,
                "n_targets": len(best_by_target),
                "clean_best_targets": sum(r["clean_direction"] for r in best_by_target),
                "mean_best_transfer_score": sum(r["valid_to_bad_effect"] - r["bad_to_valid_effect"] for r in best_by_target) / len(best_by_target),
                "mean_best_valid_to_bad": sum(r["valid_to_bad_effect"] for r in best_by_target) / len(best_by_target),
                "mean_best_bad_to_valid": sum(r["bad_to_valid_effect"] for r in best_by_target) / len(best_by_target),
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
        "used_chat_template": use_chat,
        "add_special_tokens": add_special_tokens,
        "layers": layer_ids,
        "rows": eval_rows,
        "summary": summary,
    }
    suffix = "chat" if use_chat else "raw"
    out = Path(args.out_dir) / f"{args.model_key}_e43_paraphrase_transfer_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}; rows={len(eval_rows)}", flush=True)
    for s in summary:
        print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
