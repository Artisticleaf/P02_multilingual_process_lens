#!/usr/bin/env python3
"""E44 leave-one-family-out MLP direction steering.

For a held-out family, build a mean MLP direction from all other families:
mean(valid support-span MLP output) - mean(invalid error-span MLP output).
Then add the direction to held-out invalid traces and subtract it from held-out
valid traces.  Random same-norm controls are included.
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
    try:
        return tokenizer.apply_chat_template([{"role": "user", "content": text}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tokenizer.apply_chat_template([{"role": "user", "content": text}], tokenize=False, add_generation_prompt=True)


def encode(tokenizer, prompt: str, device: torch.device, *, add_special_tokens: bool) -> dict[str, torch.Tensor]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=add_special_tokens)
    return {k: v.to(device) for k, v in enc.items()}


def find_positions(tokenizer, prompt: str, target: str, *, add_special_tokens: bool) -> list[int]:
    enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=add_special_tokens)
    start = prompt.find(target)
    if start >= 0:
        end = start + len(target)
        try:
            enc2 = tokenizer(prompt, return_tensors="pt", add_special_tokens=add_special_tokens, return_offsets_mapping=True)
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


def extract_module_output(output):
    return output[0] if isinstance(output, tuple) else output


def replace_module_output(output, patched):
    if isinstance(output, tuple):
        return (patched,) + tuple(output[1:])
    return patched


def mlp_vec(model, tokenizer, layers, prompt: str, positions: list[int], layer_idx: int, device: torch.device, *, add_special_tokens: bool) -> torch.Tensor:
    module = getattr(layers[layer_idx], "mlp", None)
    if module is None:
        raise AttributeError(f"Layer {layer_idx} has no mlp module")
    captured: dict[str, torch.Tensor] = {}

    def hook(_module, _inputs, output):
        captured["hidden"] = extract_module_output(output).detach()
        return output

    handle = module.register_forward_hook(hook)
    try:
        with torch.no_grad():
            model(**encode(tokenizer, prompt, device, add_special_tokens=add_special_tokens), use_cache=False)
    finally:
        handle.remove()
    hidden = captured["hidden"][0]
    pos = [p for p in positions if 0 <= p < hidden.shape[0]] or [hidden.shape[0] - 1]
    return hidden[pos, :].mean(dim=0).detach()


def steered_margin(
    model,
    tokenizer,
    layers,
    prompt: str,
    positions: list[int],
    layer_idx: int,
    direction: torch.Tensor,
    alpha: float,
    yes_id: int,
    no_id: int,
    device: torch.device,
    *,
    add_special_tokens: bool,
) -> float:
    module = getattr(layers[layer_idx], "mlp", None)
    if module is None:
        raise AttributeError(f"Layer {layer_idx} has no mlp module")

    def hook(_module, _inputs, output):
        hidden = extract_module_output(output).clone()
        pos = [p for p in positions if 0 <= p < hidden.shape[1]] or [hidden.shape[1] - 1]
        hidden[:, pos, :] = hidden[:, pos, :] + alpha * direction.to(hidden.device, dtype=hidden.dtype)
        return replace_module_output(output, hidden)

    handle = module.register_forward_hook(hook)
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
    p.add_argument("--out-dir", default=str(PROJECT / "results/E44_mlp_direction_steering"))
    p.add_argument("--layers", default=None)
    p.add_argument("--alphas", default="0.5,1.0")
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260428)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows_by_id = {r["audit_idx"]: r for r in load_jsonl(Path(args.manual_jsonl))}
    pairs = read_yaml(args.pairs_yaml)["pairs"]
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
    default_layers = [4, 8, 12, 16, 20, 24, min(28, len(layers) - 1)]
    layer_ids = sorted({x for x in parse_layers(args.layers, default_layers) if 0 <= x < len(layers)})
    alphas = [float(x) for x in re.split(r"[, ]+", args.alphas.strip()) if x]
    yes_id = candidate_first_token_id(tokenizer, [" Yes", "Yes", " yes", "yes"])
    no_id = candidate_first_token_id(tokenizer, [" No", "No", " no", "no"])

    items: list[dict[str, Any]] = []
    for p in pairs:
        for side, idx_key, span_key in [("valid", "valid_idx", "support_span"), ("bad", "bad_idx", "error_span")]:
            row = rows_by_id[p[idx_key]]
            prompt = maybe_chat(tokenizer, verifier_prompt(row), use_chat)
            positions = find_positions(tokenizer, prompt, p[span_key], add_special_tokens=add_special_tokens)
            base_margin = process_margin(model, tokenizer, prompt, yes_id, no_id, device, add_special_tokens=add_special_tokens)
            items.append(
                {
                    "task_id": p["task_id"],
                    "pair_id": p["id"],
                    "paraphrase_tag": p["paraphrase_tag"],
                    "side": side,
                    "prompt": prompt,
                    "positions": positions,
                    "base_margin": base_margin,
                }
            )

    vecs: dict[tuple[str, str, str, int], torch.Tensor] = {}
    for item in items:
        for layer_idx in layer_ids:
            vecs[(item["task_id"], item["paraphrase_tag"], item["side"], layer_idx)] = mlp_vec(
                model,
                tokenizer,
                layers,
                item["prompt"],
                item["positions"],
                layer_idx,
                device,
                add_special_tokens=add_special_tokens,
            )

    eval_rows = []
    for heldout in families:
        train = [i for i in items if i["task_id"] != heldout]
        held = [i for i in items if i["task_id"] == heldout]
        for layer_idx in layer_ids:
            valid_vecs = [vecs[(i["task_id"], i["paraphrase_tag"], "valid", layer_idx)] for i in train if i["side"] == "valid"]
            bad_vecs = [vecs[(i["task_id"], i["paraphrase_tag"], "bad", layer_idx)] for i in train if i["side"] == "bad"]
            direction = torch.stack(valid_vecs).mean(dim=0) - torch.stack(bad_vecs).mean(dim=0)
            rand = torch.randn_like(direction)
            rand = rand / (rand.norm() + 1e-6) * (direction.norm() + 1e-6)
            controls = {
                "process_direction": direction,
                "random_same_norm": rand,
                "opposite_direction": -direction,
            }
            for item in held:
                desired_sign = 1.0 if item["side"] == "bad" else -1.0
                for control, vec in controls.items():
                    for alpha in alphas:
                        margin = steered_margin(
                            model,
                            tokenizer,
                            layers,
                            item["prompt"],
                            item["positions"],
                            layer_idx,
                            vec,
                            desired_sign * alpha,
                            yes_id,
                            no_id,
                            device,
                            add_special_tokens=add_special_tokens,
                        )
                        effect = margin - item["base_margin"]
                        desired_effect = effect if item["side"] == "bad" else -effect
                        eval_rows.append(
                            {
                                "heldout_task": heldout,
                                "pair_id": item["pair_id"],
                                "paraphrase_tag": item["paraphrase_tag"],
                                "side": item["side"],
                                "layer": layer_idx,
                                "control": control,
                                "alpha": alpha,
                                "base_margin": item["base_margin"],
                                "steered_margin": margin,
                                "effect": effect,
                                "desired_effect": desired_effect,
                                "flipped": (item["base_margin"] <= 0 < margin) if item["side"] == "bad" else (item["base_margin"] > 0 >= margin),
                            }
                        )
        print(f"finished heldout={heldout}", flush=True)

    summary = []
    for control in ["process_direction", "random_same_norm", "opposite_direction"]:
        for alpha in alphas:
            sub = [r for r in eval_rows if r["control"] == control and r["alpha"] == alpha]
            # Best layer per heldout/side/tag, to ask whether any audited layer carries a reusable direction.
            best = []
            for key in sorted({(r["heldout_task"], r["pair_id"], r["side"]) for r in sub}):
                g = [r for r in sub if (r["heldout_task"], r["pair_id"], r["side"]) == key]
                best.append(max(g, key=lambda r: r["desired_effect"]))
            summary.append(
                {
                    "control": control,
                    "alpha": alpha,
                    "n_best_items": len(best),
                    "mean_best_desired_effect": sum(r["desired_effect"] for r in best) / len(best),
                    "positive_best_rate": sum(r["desired_effect"] > 0 for r in best) / len(best),
                    "flip_count": sum(bool(r["flipped"]) for r in best),
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
    out = Path(args.out_dir) / f"{args.model_key}_e44_mlp_direction_steering_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}; rows={len(eval_rows)}", flush=True)
    for s in summary:
        print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
