#!/usr/bin/env python3
"""E55 residual-to-logit mediation diagnostic.

At selected residual layers, learn leave-one-task-out directions from final-token
verifier hidden states and test whether adding the direction changes Yes/No
(pointwise) and A/B (sibling comparison) logits.
"""
from __future__ import annotations

import argparse
import json
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

from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    if mode == "raw":
        return False
    if mode == "chat":
        return True
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


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


def contrastive_prompt(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "You are comparing two reasoning traces for the same math problem. "
        "Exactly one trace has a local mathematical or language-semantic process error, although both may end with the same final answer. "
        "Ignore style and verbosity. Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
        f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
    )


def option_logprob(model, tokenizer, prompt: str, option: str, device: torch.device, max_model_len: int, add_special_tokens: bool) -> float:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    if not option_ids:
        return float("-inf")
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


def margin_yes_no(model, tokenizer, prompt: str, add_special: bool, device: torch.device, max_model_len: int) -> float:
    yes, _ = best_score(model, tokenizer, prompt, [" Yes", "Yes", " yes", "yes"], device, max_model_len, add_special)
    no, _ = best_score(model, tokenizer, prompt, [" No", "No", " no", "no"], device, max_model_len, add_special)
    return yes - no


def margin_ab(model, tokenizer, prompt: str, add_special: bool, device: torch.device, max_model_len: int) -> float:
    a, _ = best_score(model, tokenizer, prompt, ["A", " A", "A.", " A."], device, max_model_len, add_special)
    b, _ = best_score(model, tokenizer, prompt, ["B", " B", "B.", " B."], device, max_model_len, add_special)
    return a - b


def extract_layer_output(output):
    return output[0] if isinstance(output, tuple) else output


def replace_layer_output(output, hidden):
    if isinstance(output, tuple):
        return (hidden,) + tuple(output[1:])
    return hidden


def collect_features(model, tokenizer, items: list[dict[str, Any]], layers: list[int], device: torch.device, max_model_len: int) -> dict[int, torch.Tensor]:
    out = {layer: [] for layer in layers}
    for i, item in enumerate(items, start=1):
        ids = tokenizer.encode(item["prompt"], add_special_tokens=item["add_special_tokens"])[-max_model_len:]
        enc = {
            "input_ids": torch.tensor([ids], dtype=torch.long, device=device),
            "attention_mask": torch.ones((1, len(ids)), dtype=torch.long, device=device),
        }
        with torch.no_grad():
            y = model(**enc, output_hidden_states=True, use_cache=False)
        for layer in layers:
            out[layer].append(y.hidden_states[layer + 1][0, -1, :].detach().float().cpu())
        if i % 12 == 0:
            print(f"features {i}/{len(items)}", flush=True)
    return {layer: torch.stack(vecs) for layer, vecs in out.items()}


def patched_option_logprob(model, tokenizer, modules, prompt: str, option: str, add_special: bool, device: torch.device, max_model_len: int, layer: int, delta: torch.Tensor) -> float:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special)
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    keep_prompt = max(1, max_model_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    patch_pos = len(prompt_ids) - 1
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)

    def hook(_module, _inputs, output):
        hidden = extract_layer_output(output).clone()
        hidden[:, patch_pos, :] = hidden[:, patch_pos, :] + delta.to(device=hidden.device, dtype=hidden.dtype)
        return replace_layer_output(output, hidden)

    handle = modules[layer].register_forward_hook(hook)
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


def patched_margin_yes_no(model, tokenizer, modules, item: dict[str, Any], device: torch.device, max_model_len: int, layer: int, delta: torch.Tensor) -> float:
    prompt = item["prompt"]
    add_special = item["add_special_tokens"]
    yes = max(patched_option_logprob(model, tokenizer, modules, prompt, opt, add_special, device, max_model_len, layer, delta) for opt in [" Yes", "Yes", " yes", "yes"])
    no = max(patched_option_logprob(model, tokenizer, modules, prompt, opt, add_special, device, max_model_len, layer, delta) for opt in [" No", "No", " no", "no"])
    return yes - no


def patched_margin_ab(model, tokenizer, modules, item: dict[str, Any], device: torch.device, max_model_len: int, layer: int, delta: torch.Tensor) -> float:
    prompt = item["prompt"]
    add_special = item["add_special_tokens"]
    a = max(patched_option_logprob(model, tokenizer, modules, prompt, opt, add_special, device, max_model_len, layer, delta) for opt in ["A", " A", "A.", " A."])
    b = max(patched_option_logprob(model, tokenizer, modules, prompt, opt, add_special, device, max_model_len, layer, delta) for opt in ["B", " B", "B.", " B."])
    return a - b


def loto_direction(X: torch.Tensor, labels: list[bool], tasks: list[str], heldout_task: str) -> tuple[torch.Tensor, torch.Tensor]:
    train = [i for i, t in enumerate(tasks) if t != heldout_task]
    y = torch.tensor([labels[i] for i in train], dtype=torch.bool)
    x = X[train]
    pos = x[y].mean(dim=0)
    neg = x[~y].mean(dim=0)
    return pos - neg, 0.5 * (pos + neg)


def probe_rows(X: torch.Tensor, labels: list[bool], tasks: list[str], layer: int, positive_name: str) -> list[dict[str, Any]]:
    rows = []
    for heldout in sorted(set(tasks)):
        direction, center = loto_direction(X, labels, tasks, heldout)
        for i, task in enumerate(tasks):
            if task != heldout:
                continue
            score = float((X[i] - center) @ direction)
            pred = score > 0
            rows.append({"layer": layer, "heldout_task": heldout, "item_index": i, "positive_label": positive_name, "score": score, "pred": bool(pred), "target": bool(labels[i]), "correct": bool(pred) == bool(labels[i])})
    return rows


def summarize_probe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for r in rows:
        groups[(r["objective"], r["layer"])].append(r)
    return [{"objective": obj, "layer": layer, "n": len(g), "accuracy": sum(r["correct"] for r in g) / len(g)} for (obj, layer), g in sorted(groups.items())]


def summarize_patch(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for r in rows:
        groups[(r["objective"], r["layer"], r["gold_label"] if "gold_label" in r else "all")].append(r)
    out = []
    for (obj, layer, label), g in sorted(groups.items()):
        out.append({
            "objective": obj,
            "layer": layer,
            "gold_label": label,
            "n": len(g),
            "mean_target_effect": mean([r["target_direction_effect"] for r in g]),
            "target_effect_positive_rate": sum(r["target_direction_effect"] > 0 for r in g) / len(g),
            "target_flip_count": sum(r.get("target_flip", False) for r in g),
        })
    return out


def infer_layers(args: argparse.Namespace) -> list[int]:
    if args.layers:
        return args.layers
    e50_path = PROJECT / "results/E50_residual_probe_steering" / f"{args.model_key}_e50_residual_probe_steering.json"
    if e50_path.exists():
        best = int(read_json(e50_path)["summary"]["best_probe_layer"]["layer"])
        return [best]
    return [16]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl"))
    p.add_argument("--pairs-yaml", default=str(PROJECT / "configs/e42_e39_objective_pairs.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E55_residual_to_logit_mediation"))
    p.add_argument("--layers", nargs="+", type=int, default=None)
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--max-patch-items", type=int, default=0, help="0 means all items")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    layers = infer_layers(args)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = [r for r in load_jsonl(Path(args.manual_jsonl)) if r["e39_variant"] in {"valid_correct", "invalid_correct"}]
    rows = sorted(rows, key=lambda r: (r["task_id"], r["e39_variant"]))
    manual = {r["audit_idx"]: r for r in rows}
    pairs = read_yaml(args.pairs_yaml)["pairs"]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E55 layers={layers}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    modules = get_transformer_layers(model)

    abs_items = []
    for row in rows:
        prompt, add_special = render_prompt(tok, process_prompt(row), use_chat)
        abs_items.append({"task_id": row["task_id"], "audit_idx": row["audit_idx"], "prompt": prompt, "add_special_tokens": add_special, "label_valid": bool(row["manual_process_valid"]), "e39_variant": row["e39_variant"]})
    con_items = []
    for pair in pairs:
        valid = manual[int(pair["valid_idx"])]
        bad = manual[int(pair["bad_idx"])]
        for order in ["bad_A", "bad_B"]:
            if order == "bad_A":
                trace_a, trace_b, target_a = bad["completion"], valid["completion"], True
            else:
                trace_a, trace_b, target_a = valid["completion"], bad["completion"], False
            prompt, add_special = render_prompt(tok, contrastive_prompt(bad["problem"], trace_a, trace_b), use_chat)
            con_items.append({"task_id": pair["task_id"], "pair_id": pair["id"], "order": order, "prompt": prompt, "add_special_tokens": add_special, "target_A": target_a})

    print("collecting absolute features", flush=True)
    X_abs = collect_features(model, tok, abs_items, layers, device, args.max_model_len)
    print("collecting contrastive features", flush=True)
    X_con = collect_features(model, tok, con_items, layers, device, args.max_model_len)

    probe = []
    patch = []
    abs_labels = [it["label_valid"] for it in abs_items]
    abs_tasks = [it["task_id"] for it in abs_items]
    con_labels = [it["target_A"] for it in con_items]
    con_tasks = [it["task_id"] for it in con_items]
    for layer in layers:
        for r in probe_rows(X_abs[layer], abs_labels, abs_tasks, layer, "valid"):
            r["objective"] = "absolute_yes_no"
            probe.append(r)
        for r in probe_rows(X_con[layer], con_labels, con_tasks, layer, "target_A"):
            r["objective"] = "contrastive_ab"
            probe.append(r)

        abs_patch_items = abs_items if args.max_patch_items <= 0 else abs_items[: args.max_patch_items]
        for item in abs_patch_items:
            direction, _center = loto_direction(X_abs[layer], abs_labels, abs_tasks, item["task_id"])
            base = margin_yes_no(model, tok, item["prompt"], item["add_special_tokens"], device, args.max_model_len)
            # Target direction means "toward the gold class": toward valid for valid rows, toward invalid for invalid rows.
            delta_target = direction if item["label_valid"] else -direction
            target_margin = patched_margin_yes_no(model, tok, modules, item, device, args.max_model_len, layer, delta_target)
            patch.append({
                "objective": "absolute_yes_no",
                "layer": layer,
                "task_id": item["task_id"],
                "audit_idx": item["audit_idx"],
                "gold_label": "valid" if item["label_valid"] else "invalid",
                "base_margin_yes_minus_no": base,
                "target_patched_margin": target_margin,
                "target_direction_effect": (target_margin - base) if item["label_valid"] else (base - target_margin),
                "target_flip": (base > 0) != (target_margin > 0),
            })
        con_patch_items = con_items if args.max_patch_items <= 0 else con_items[: args.max_patch_items]
        for item in con_patch_items:
            direction, _center = loto_direction(X_con[layer], con_labels, con_tasks, item["task_id"])
            base_ab = margin_ab(model, tok, item["prompt"], item["add_special_tokens"], device, args.max_model_len)
            base_target = base_ab if item["target_A"] else -base_ab
            delta_target = direction if item["target_A"] else -direction
            patched_ab = patched_margin_ab(model, tok, modules, item, device, args.max_model_len, layer, delta_target)
            patched_target = patched_ab if item["target_A"] else -patched_ab
            patch.append({
                "objective": "contrastive_ab",
                "layer": layer,
                "task_id": item["task_id"],
                "pair_id": item["pair_id"],
                "order": item["order"],
                "gold_label": "target_A" if item["target_A"] else "target_B",
                "base_margin_target_minus_other": base_target,
                "target_patched_margin": patched_target,
                "target_direction_effect": patched_target - base_target,
                "target_flip": (base_target > 0) != (patched_target > 0),
            })
        print(f"patched layer {layer}", flush=True)

    summary = {"probe": summarize_probe(probe), "patch": summarize_patch(patch)}
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "layers": layers,
        "args": vars(args),
        "probe_rows": probe,
        "patch_rows": patch,
        "summary": summary,
        "scope_note_en": "E55 is a causal diagnostic over controlled E42 rows. Directions are built leave-one-task-out and labels/spans are not inserted in prompts.",
        "scope_note_zh": "E55 是受控 E42 行上的因果诊断。方向采用 leave-one-task-out 构造，标签和 span 不进入 prompt。",
    }
    out = Path(args.out_dir) / f"{args.model_key}_e55_residual_to_logit_mediation.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
