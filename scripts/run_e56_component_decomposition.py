#!/usr/bin/env python3
"""E56 component decomposition for process-validity evidence.

For the E42 controlled rows at a selected residual layer, compare how much
process-validity information is linearly recoverable from the layer residual
output, self-attention output, and MLP output.  Then patch component outputs at
the final verifier-prompt token to test whether those directions affect Yes/No
margins.
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


def extract_output(output):
    return output[0] if isinstance(output, tuple) else output


def replace_output(output, hidden):
    if isinstance(output, tuple):
        return (hidden,) + tuple(output[1:])
    return hidden


def component_modules(layer_module) -> dict[str, Any]:
    mods = {"residual_layer_output": layer_module}
    for name in ["self_attn", "linear_attn", "attention", "attn", "token_mixer"]:
        if hasattr(layer_module, name):
            mods["token_mixer_output"] = getattr(layer_module, name)
            break
    for name in ["mlp", "feed_forward", "ffn"]:
        if hasattr(layer_module, name):
            mods["mlp_output"] = getattr(layer_module, name)
            break
    return mods


def collect_component_features(model, tokenizer, items: list[dict[str, Any]], modules: dict[str, Any], device: torch.device, max_model_len: int) -> dict[str, torch.Tensor]:
    feats = {name: [] for name in modules}
    for i, item in enumerate(items, start=1):
        captured: dict[str, torch.Tensor] = {}
        handles = []
        for name, module in modules.items():
            def make_hook(component_name):
                def hook(_module, _inputs, output):
                    hidden = extract_output(output)
                    captured[component_name] = hidden[0, -1, :].detach().float().cpu()
                    return output
                return hook
            handles.append(module.register_forward_hook(make_hook(name)))
        try:
            ids = tokenizer.encode(item["prompt"], add_special_tokens=item["add_special_tokens"])[-max_model_len:]
            enc = {"input_ids": torch.tensor([ids], dtype=torch.long, device=device), "attention_mask": torch.ones((1, len(ids)), dtype=torch.long, device=device)}
            with torch.no_grad():
                model(**enc, use_cache=False)
        finally:
            for h in handles:
                h.remove()
        missing = sorted(set(modules) - set(captured))
        if missing:
            raise RuntimeError(f"Missing captured components: {missing}")
        for name in modules:
            feats[name].append(captured[name])
        if i % 12 == 0:
            print(f"component features {i}/{len(items)}", flush=True)
    return {name: torch.stack(vals) for name, vals in feats.items()}


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


def best_score(model, tokenizer, prompt: str, options: list[str], device: torch.device, max_model_len: int, add_special_tokens: bool) -> float:
    return max(option_logprob(model, tokenizer, prompt, opt, device, max_model_len, add_special_tokens) for opt in options)


def margin_yes_no(model, tokenizer, item: dict[str, Any], device: torch.device, max_model_len: int) -> float:
    yes = best_score(model, tokenizer, item["prompt"], [" Yes", "Yes", " yes", "yes"], device, max_model_len, item["add_special_tokens"])
    no = best_score(model, tokenizer, item["prompt"], [" No", "No", " no", "no"], device, max_model_len, item["add_special_tokens"])
    return yes - no


def patched_option_logprob(model, tokenizer, module, item: dict[str, Any], option: str, device: torch.device, max_model_len: int, delta: torch.Tensor) -> float:
    prompt_ids = tokenizer.encode(item["prompt"], add_special_tokens=item["add_special_tokens"])
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    keep_prompt = max(1, max_model_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    patch_pos = len(prompt_ids) - 1
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)

    def hook(_module, _inputs, output):
        hidden = extract_output(output).clone()
        hidden[:, patch_pos, :] = hidden[:, patch_pos, :] + delta.to(device=hidden.device, dtype=hidden.dtype)
        return replace_output(output, hidden)

    handle = module.register_forward_hook(hook)
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


def patched_margin_yes_no(model, tokenizer, module, item: dict[str, Any], device: torch.device, max_model_len: int, delta: torch.Tensor) -> float:
    yes = max(patched_option_logprob(model, tokenizer, module, item, opt, device, max_model_len, delta) for opt in [" Yes", "Yes", " yes", "yes"])
    no = max(patched_option_logprob(model, tokenizer, module, item, opt, device, max_model_len, delta) for opt in [" No", "No", " no", "no"])
    return yes - no


def loto_direction(X: torch.Tensor, labels: list[bool], tasks: list[str], heldout_task: str) -> tuple[torch.Tensor, torch.Tensor]:
    train = [i for i, t in enumerate(tasks) if t != heldout_task]
    y = torch.tensor([labels[i] for i in train], dtype=torch.bool)
    x = X[train]
    valid = x[y].mean(dim=0)
    invalid = x[~y].mean(dim=0)
    return valid - invalid, 0.5 * (valid + invalid)


def component_probe_rows(X_by_component: dict[str, torch.Tensor], labels: list[bool], tasks: list[str]) -> list[dict[str, Any]]:
    out = []
    for comp, X in X_by_component.items():
        for heldout in sorted(set(tasks)):
            direction, center = loto_direction(X, labels, tasks, heldout)
            for i, task in enumerate(tasks):
                if task != heldout:
                    continue
                score = float((X[i] - center) @ direction)
                pred = score > 0
                out.append({"component": comp, "heldout_task": heldout, "item_index": i, "score": score, "pred_process_valid": bool(pred), "gold_process_valid": bool(labels[i]), "correct": bool(pred) == bool(labels[i])})
    return out


def summarize_probe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for r in rows:
        groups[r["component"]].append(r)
    return [{"component": comp, "n": len(g), "accuracy": sum(r["correct"] for r in g) / len(g)} for comp, g in sorted(groups.items())]


def summarize_patch(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for r in rows:
        groups[(r["component"], r["gold_process_valid"])].append(r)
    out = []
    for (comp, gold), g in sorted(groups.items()):
        out.append({
            "component": comp,
            "gold_process_valid": gold,
            "n": len(g),
            "mean_target_effect": mean([r["target_direction_effect"] for r in g]),
            "target_effect_positive_rate": sum(r["target_direction_effect"] > 0 for r in g) / len(g),
            "flip_count": sum(r["target_flip"] for r in g),
        })
    return out


def infer_layer(args: argparse.Namespace) -> int:
    if args.layer is not None:
        return args.layer
    e50_path = PROJECT / "results/E50_residual_probe_steering" / f"{args.model_key}_e50_residual_probe_steering.json"
    if e50_path.exists():
        return int(read_json(e50_path)["summary"]["best_probe_layer"]["layer"])
    return 16


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E56_component_decomposition"))
    p.add_argument("--layer", type=int, default=None)
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    layer_idx = infer_layer(args)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = [r for r in load_jsonl(Path(args.manual_jsonl)) if r["e39_variant"] in {"valid_correct", "invalid_correct"}]
    rows = sorted(rows, key=lambda r: (r["task_id"], r["e39_variant"]))
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E56 layer={layer_idx}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    layer_module = layers[layer_idx]
    mods = component_modules(layer_module)
    print(f"components={sorted(mods)}", flush=True)

    items = []
    for row in rows:
        prompt, add_special = render_prompt(tok, process_prompt(row), use_chat)
        items.append({"task_id": row["task_id"], "audit_idx": row["audit_idx"], "prompt": prompt, "add_special_tokens": add_special, "gold_process_valid": bool(row["manual_process_valid"]), "e39_variant": row["e39_variant"]})
    X = collect_component_features(model, tok, items, mods, device, args.max_model_len)
    labels = [it["gold_process_valid"] for it in items]
    tasks = [it["task_id"] for it in items]
    probe = component_probe_rows(X, labels, tasks)

    base_margins = {}
    for i, item in enumerate(items, start=1):
        base_margins[item["audit_idx"]] = margin_yes_no(model, tok, item, device, args.max_model_len)
        if i % 12 == 0:
            print(f"base margins {i}/{len(items)}", flush=True)

    patch_rows = []
    for comp, comp_X in X.items():
        module = mods[comp]
        for idx, item in enumerate(items):
            direction, _center = loto_direction(comp_X, labels, tasks, item["task_id"])
            delta_target = direction if item["gold_process_valid"] else -direction
            base = base_margins[item["audit_idx"]]
            patched = patched_margin_yes_no(model, tok, module, item, device, args.max_model_len, delta_target)
            target_effect = (patched - base) if item["gold_process_valid"] else (base - patched)
            patch_rows.append({
                "component": comp,
                "layer": layer_idx,
                "task_id": item["task_id"],
                "audit_idx": item["audit_idx"],
                "gold_process_valid": item["gold_process_valid"],
                "base_margin": base,
                "target_patched_margin": patched,
                "target_direction_effect": target_effect,
                "target_flip": (base > 0) != (patched > 0),
            })
        print(f"patched component {comp}", flush=True)

    summary = {"probe": summarize_probe(probe), "patch": summarize_patch(patch_rows)}
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "layer": layer_idx,
        "components": sorted(mods),
        "args": vars(args),
        "probe_rows": probe,
        "patch_rows": patch_rows,
        "summary": summary,
        "scope_note_en": "Component directions are leave-one-task-out diagnostics on E42 controlled rows; this is not a full circuit proof.",
        "scope_note_zh": "组件方向是在 E42 受控行上做的 leave-one-task-out 诊断；这不是完整 circuit 证明。",
    }
    out = Path(args.out_dir) / f"{args.model_key}_e56_component_decomposition.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
