#!/usr/bin/env python3
"""E50 residual-state process-validity probe and steering.

This is a mechanism pilot meant to improve on the weaker single-MLP direction
experiment.  It tests whether verifier hidden states contain a reusable
valid-vs-invalid process direction under official chat-template scoring.
"""
from __future__ import annotations

import argparse
import json
import math
import socket
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def should_use_chat_template(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def process_prompt(row: dict[str, Any]) -> str:
    return (
        "You are auditing a mathematical reasoning trace. Judge only whether the mathematical "
        "reasoning steps are valid; do not penalize missing final-answer formatting, truncation, "
        "or extra text after the answer. If any mathematical step is wrong, answer No. If the "
        "visible reasoning steps are mathematically valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {row['problem']}\n"
        f"Reasoning trace: {row['completion']}\n"
        "Are the visible reasoning steps mathematically valid? Answer:"
    )


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), False


def option_logprob(model, tokenizer, prompt: str, option: str, device: torch.device, max_model_len: int, add_special_tokens: bool) -> float:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    keep_prompt = max(1, max_model_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
    total = 0.0
    start = len(prompt_ids)
    for j, tok_id in enumerate(option_ids):
        total += float(F.log_softmax(logits[start + j - 1], dim=-1)[tok_id].item())
    return total


def best_score(model, tokenizer, prompt: str, options: list[str], device: torch.device, max_model_len: int, add_special_tokens: bool) -> tuple[float, str]:
    scored = [(option_logprob(model, tokenizer, prompt, opt, device, max_model_len, add_special_tokens), opt) for opt in options]
    return max(scored, key=lambda x: x[0])


def yes_no_margin(model, tokenizer, prompt: str, device: torch.device, max_model_len: int, add_special_tokens: bool) -> float:
    yes, _ = best_score(model, tokenizer, prompt, [" Yes", "Yes", " yes", "yes"], device, max_model_len, add_special_tokens)
    no, _ = best_score(model, tokenizer, prompt, [" No", "No", " no", "no"], device, max_model_len, add_special_tokens)
    return yes - no


def extract_layer_output(output):
    if isinstance(output, tuple):
        return output[0]
    return output


def replace_layer_output(output, hidden):
    if isinstance(output, tuple):
        return (hidden,) + tuple(output[1:])
    return hidden


def collect_final_token_features(
    model,
    tokenizer,
    rows: list[dict[str, Any]],
    prompts: dict[int, tuple[str, bool]],
    layers: list[int],
    device: torch.device,
    max_model_len: int,
) -> tuple[dict[int, torch.Tensor], dict[int, float]]:
    features = {layer: [] for layer in layers}
    margins = {}
    for row in rows:
        prompt, add_special = prompts[row["audit_idx"]]
        ids = tokenizer.encode(prompt, add_special_tokens=add_special)
        ids = ids[-max_model_len:]
        enc = {
            "input_ids": torch.tensor([ids], dtype=torch.long, device=device),
            "attention_mask": torch.ones((1, len(ids)), dtype=torch.long, device=device),
        }
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        for layer in layers:
            features[layer].append(out.hidden_states[layer + 1][0, -1, :].detach().float().cpu())
        margins[row["audit_idx"]] = yes_no_margin(model, tokenizer, prompt, device, max_model_len, add_special)
        print(f"features audit_idx={row['audit_idx']}", flush=True)
    return {layer: torch.stack(vecs) for layer, vecs in features.items()}, margins


def mean_direction_probe(X: torch.Tensor, y: torch.Tensor, tasks: list[str], layer: int, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    probe_rows = []
    control_rows = []
    unique_tasks = sorted(set(tasks))
    gen = torch.Generator().manual_seed(seed + layer)
    for heldout in unique_tasks:
        train_idx = [i for i, t in enumerate(tasks) if t != heldout]
        test_idx = [i for i, t in enumerate(tasks) if t == heldout]
        x_train = X[train_idx]
        y_train = y[train_idx]
        x_test = X[test_idx]
        y_test = y[test_idx]
        valid_mean = x_train[y_train].mean(dim=0)
        bad_mean = x_train[~y_train].mean(dim=0)
        direction = valid_mean - bad_mean
        center = 0.5 * (valid_mean + bad_mean)
        scores = (x_test - center) @ direction
        preds = scores > 0
        for idx, score, pred, gold in zip(test_idx, scores.tolist(), preds.tolist(), y_test.tolist()):
            probe_rows.append({"layer": layer, "heldout_task": heldout, "row_index": idx, "score": score, "pred_process_valid": bool(pred), "gold_process_valid": bool(gold), "correct": bool(pred) == bool(gold), "control": "mean_diff"})
        rand = torch.randn(direction.shape, generator=gen)
        rand = rand / (rand.norm() + 1e-8) * (direction.norm() + 1e-8)
        rand_scores = (x_test - center) @ rand
        rand_preds = rand_scores > 0
        for idx, score, pred, gold in zip(test_idx, rand_scores.tolist(), rand_preds.tolist(), y_test.tolist()):
            control_rows.append({"layer": layer, "heldout_task": heldout, "row_index": idx, "score": score, "pred_process_valid": bool(pred), "gold_process_valid": bool(gold), "correct": bool(pred) == bool(gold), "control": "random_same_norm"})
    return probe_rows, control_rows


def patched_option_logprob(
    model,
    tokenizer,
    layers_modules,
    prompt: str,
    option: str,
    add_special_tokens: bool,
    device: torch.device,
    max_model_len: int,
    layer: int,
    delta: torch.Tensor,
) -> float:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    keep_prompt = max(1, max_model_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    patch_pos = len(prompt_ids) - 1
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)

    def hook(_module, _inputs, output):
        hidden = extract_layer_output(output).clone()
        # Patch the prompt-final position, because that position predicts the
        # first Yes/No option token. Patching the appended option token would
        # not change the option log-probability.
        hidden[:, patch_pos, :] = hidden[:, patch_pos, :] + delta.to(device=hidden.device, dtype=hidden.dtype)
        return replace_layer_output(output, hidden)

    handle = layers_modules[layer].register_forward_hook(hook)
    try:
        with torch.no_grad():
            logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
        total = 0.0
        start = len(prompt_ids)
        for j, tok_id in enumerate(option_ids):
            total += float(F.log_softmax(logits[start + j - 1], dim=-1)[tok_id].item())
        return total
    finally:
        handle.remove()


def patched_margin(
    model,
    tokenizer,
    layers_modules,
    prompt: str,
    add_special_tokens: bool,
    device: torch.device,
    max_model_len: int,
    layer: int,
    delta: torch.Tensor,
) -> float:
    yes = max(
        patched_option_logprob(model, tokenizer, layers_modules, prompt, opt, add_special_tokens, device, max_model_len, layer, delta)
        for opt in [" Yes", "Yes", " yes", "yes"]
    )
    no = max(
        patched_option_logprob(model, tokenizer, layers_modules, prompt, opt, add_special_tokens, device, max_model_len, layer, delta)
        for opt in [" No", "No", " no", "no"]
    )
    return yes - no


def steering_rows(
    model,
    tokenizer,
    rows: list[dict[str, Any]],
    prompts: dict[int, tuple[str, bool]],
    X_by_layer: dict[int, torch.Tensor],
    y: torch.Tensor,
    tasks: list[str],
    layers: list[int],
    margins: dict[int, float],
    device: torch.device,
    max_model_len: int,
    alpha: float,
) -> list[dict[str, Any]]:
    modules = get_transformer_layers(model)
    out_rows = []
    unique_tasks = sorted(set(tasks))
    for layer in layers:
        X = X_by_layer[layer]
        for heldout in unique_tasks:
            train_idx = [i for i, t in enumerate(tasks) if t != heldout]
            test_idx = [i for i, t in enumerate(tasks) if t == heldout]
            x_train = X[train_idx]
            y_train = y[train_idx]
            direction = x_train[y_train].mean(dim=0) - x_train[~y_train].mean(dim=0)
            if not torch.isfinite(direction).all() or float(direction.norm()) == 0.0:
                continue
            delta_valid = alpha * direction
            delta_invalid = -alpha * direction
            for idx in test_idx:
                row = rows[idx]
                prompt, add_special = prompts[row["audit_idx"]]
                base = margins[row["audit_idx"]]
                for control, delta in [("toward_valid", delta_valid), ("toward_invalid", delta_invalid)]:
                    steered = patched_margin(model, tokenizer, modules, prompt, add_special, device, max_model_len, layer, delta)
                    expected_sign = 1 if control == "toward_valid" else -1
                    out_rows.append(
                        {
                            "layer": layer,
                            "alpha": alpha,
                            "heldout_task": heldout,
                            "audit_idx": row["audit_idx"],
                            "task_id": row["task_id"],
                            "e39_variant": row["e39_variant"],
                            "gold_process_valid": bool(row["manual_process_valid"]),
                            "control": control,
                            "base_margin": base,
                            "steered_margin": steered,
                            "effect": steered - base,
                            "effect_has_expected_sign": (steered - base) * expected_sign > 0,
                        }
                    )
    return out_rows


def summarize_probe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for row in rows:
        groups[(row["control"], row["layer"])].append(row)
    out = []
    for (control, layer), g in sorted(groups.items()):
        out.append({"control": control, "layer": layer, "n": len(g), "accuracy": sum(r["correct"] for r in g) / len(g)})
    return out


def summarize_steering(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for row in rows:
        groups[(row["control"], row["layer"], row["gold_process_valid"])].append(row)
    out = []
    for (control, layer, gold_valid), g in sorted(groups.items()):
        out.append(
            {
                "control": control,
                "layer": layer,
                "gold_process_valid": gold_valid,
                "n": len(g),
                "mean_effect": mean([r["effect"] for r in g]),
                "expected_sign_rate": sum(r["effect_has_expected_sign"] for r in g) / len(g),
                "flip_count": sum((r["base_margin"] > 0) != (r["steered_margin"] > 0) for r in g),
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_9b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E50_residual_probe_steering"))
    p.add_argument("--layers", nargs="+", type=int, default=[4, 8, 12, 16, 20, 24, 28, 31])
    p.add_argument("--steer-layers", nargs="+", type=int, default=[8, 12, 16, 20])
    p.add_argument("--alpha", type=float, default=1.0)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260428)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = [r for r in read_jsonl(Path(args.manual_jsonl)) if r["e39_variant"] in {"valid_correct", "invalid_correct"}]
    rows = sorted(rows, key=lambda r: (r["task_id"], r["e39_variant"]))
    if not rows or len({r["task_id"] for r in rows}) * 2 != len(rows):
        raise SystemExit("E50 expects one valid_correct and one invalid_correct row per task.")
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E50 residual probe", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, tokenizer)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    prompts = {}
    for row in rows:
        prompts[row["audit_idx"]] = render_prompt(tokenizer, process_prompt(row), use_chat)
    X_by_layer, margins = collect_final_token_features(model, tokenizer, rows, prompts, args.layers, device, args.max_model_len)
    y = torch.tensor([bool(r["manual_process_valid"]) for r in rows], dtype=torch.bool)
    tasks = [r["task_id"] for r in rows]

    probe_rows = []
    control_rows = []
    for layer, X in X_by_layer.items():
        p_rows, c_rows = mean_direction_probe(X, y, tasks, layer, args.seed)
        probe_rows.extend(p_rows)
        control_rows.extend(c_rows)
    all_probe_rows = probe_rows + control_rows
    steering = steering_rows(
        model,
        tokenizer,
        rows,
        prompts,
        X_by_layer,
        y,
        tasks,
        [layer for layer in args.steer_layers if layer in X_by_layer],
        margins,
        device,
        args.max_model_len,
        args.alpha,
    )
    summary = {
        "probe": summarize_probe(all_probe_rows),
        "steering": summarize_steering(steering),
        "best_probe_layer": max(summarize_probe([r for r in all_probe_rows if r["control"] == "mean_diff"]), key=lambda x: (x["accuracy"], -x["layer"])),
        "mean_random_probe_accuracy": mean([r["accuracy"] for r in summarize_probe([r for r in all_probe_rows if r["control"] == "random_same_norm"])]),
        "base_absolute_acpi_accept_rate": sum(margins[r["audit_idx"]] > 0 for r in rows if not r["manual_process_valid"]) / sum(not r["manual_process_valid"] for r in rows),
        "base_valid_accept_rate": sum(margins[r["audit_idx"]] > 0 for r in rows if r["manual_process_valid"]) / sum(r["manual_process_valid"] for r in rows),
    }
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "add_special_tokens": not use_chat,
        "args": vars(args),
        "rows": rows,
        "margins": {str(k): v for k, v in margins.items()},
        "probe_rows": all_probe_rows,
        "steering_rows": steering,
        "summary": summary,
        "scope_note_en": "The probe is leave-one-task-out over paired valid_correct/invalid_correct traces with identical final answers; it is a mechanism diagnostic, not a population prevalence estimate.",
        "scope_note_zh": "该 probe 在 final answer 相同的 valid_correct/invalid_correct 成对 trace 上做 leave-one-task-out；它是机制诊断，不是总体发生率估计。",
    }
    out = Path(args.out_dir) / f"{args.model_key}_e50_residual_probe_steering.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
