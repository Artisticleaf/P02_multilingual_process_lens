#!/usr/bin/env python3
"""E122 component steering audit on E119/E146 official hard-task labels.

This is a small causal diagnostic, not a prevalence estimate. It trains a
process-validity direction on E61 controlled rows under the same strict verifier
prompt, then patches selected layer outputs on E119/E146 valid/repaired/
unrepaired rows and records whether Yes/No logits move.
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

E61_DATA = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
E65_DIR = PROJECT / "results/E65_mechanistic_layer_sweep"
E119_E146_AUDIT = PROJECT / "data/processed/e119_e146_process_audit_official_20260430.jsonl"


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
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm", "exaone", "nemotron"} or "instruct" in cls or "post" in cls


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


def strict_prompt(problem: str, trace: str) -> str:
    return (
        "You are a strict trace-selection auditor. Judge the visible reasoning trace step by step. "
        "If any visible local step, definition, arithmetic operation, counting rule, unit conversion, semantic interpretation, algebraic transformation, or proof implication is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
        "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    )


def yes_no_metrics(logits: torch.Tensor, tok) -> dict[str, Any]:
    logp = F.log_softmax(logits.float(), dim=-1)
    def best(options: list[str]) -> tuple[float, str]:
        vals = []
        for opt in options:
            ids = tok.encode(opt, add_special_tokens=False)
            if ids:
                vals.append((float(logp[int(ids[0])].item()), opt))
        return max(vals, key=lambda x: x[0])

    yes, yes_opt = best([" Yes", "Yes", " yes", "yes"])
    no, no_opt = best([" No", "No", " no", "no"])
    vals = torch.tensor([yes, no], dtype=torch.float64)
    probs = torch.softmax(vals, dim=0)
    return {
        "yes_score": yes,
        "no_score": no,
        "yes_minus_no": yes - no,
        "pred_process_valid": yes > no,
        "readout_confidence": abs(yes - no),
        "p_yes_binary": float(probs[0].item()),
        "yes_option": yes_opt,
        "no_option": no_opt,
    }


def best_layer_for(model_key: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    path = E65_DIR / f"{model_key}_e65_e61_layer_sweep.json"
    if path.exists():
        return int(read_json(path)["best_all_layer"]["layer"])
    defaults = {"qwen35_27b": 34, "gemma4_31b_it": 34, "gemma4_26b_a4b_it": 17, "glm47_flash_candidate": 27}
    return defaults.get(model_key, 16)


def module_for_component(layer_module, component: str):
    if component == "residual":
        return layer_module
    if component == "mlp":
        for name in ["mlp", "feed_forward", "ffn"]:
            if hasattr(layer_module, name):
                return getattr(layer_module, name)
    if component == "token_mixer":
        for name in ["self_attn", "linear_attn", "attention", "attn", "token_mixer"]:
            if hasattr(layer_module, name):
                return getattr(layer_module, name)
    raise AttributeError(f"Cannot locate component={component} on {type(layer_module)}")


def extract_output(output):
    return output[0] if isinstance(output, tuple) else output


def replace_output(output, hidden):
    if isinstance(output, tuple):
        return (hidden,) + tuple(output[1:])
    return hidden


def train_residual_direction(model, tok, use_chat: bool, device: torch.device, best_layer: int, max_len: int, max_train: int) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    rows = load_jsonl(E61_DATA)
    if max_train:
        rows = sorted(rows, key=lambda r: (r["task_id"], bool(r["manual_process_valid"]), r["audit_idx"]))[:max_train]
    feats = []
    labels = []
    for i, row in enumerate(rows, start=1):
        prompt, add = render_prompt(tok, strict_prompt(row["problem"], row["completion"]), use_chat)
        ids = tok.encode(prompt, add_special_tokens=add)[-max_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids)
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
        feats.append(out.hidden_states[best_layer][0, -1, :].detach().float().cpu())
        labels.append(bool(row["manual_process_valid"]))
        del out, input_ids, attn
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if i % 24 == 0 or i == len(rows):
            print(f"E122 train direction {i}/{len(rows)}", flush=True)
    X = torch.stack(feats)
    y = torch.tensor(labels, dtype=torch.bool)
    direction = X[y].mean(0) - X[~y].mean(0)
    direction = direction / (direction.norm() + 1e-8)
    center = X.mean(0)
    meta = {"train_rows": len(rows), "train_valid": int(y.sum()), "train_invalid": int((~y).sum())}
    return direction, center, meta


def target_rows(model_key: str, max_rows: int) -> list[dict[str, Any]]:
    rows = [r for r in load_jsonl(E119_E146_AUDIT) if r["model_key"] == model_key and r.get("strict_final_decision")]
    priority = []
    priority.extend([r for r in rows if r.get("manual_acpi_unrepaired")])
    priority.extend([r for r in rows if r.get("manual_acpi_strict") and r.get("manual_repair_present")])
    priority.extend([r for r in rows if r.get("manual_process_valid_strict") is True])
    seen = set()
    out = []
    for row in priority:
        if row["audit_idx"] in seen:
            continue
        seen.add(row["audit_idx"])
        out.append(row)
        if max_rows and len(out) >= max_rows:
            break
    return out


def classify(row: dict[str, Any]) -> str:
    if row.get("manual_acpi_unrepaired"):
        return "unrepaired_acpi"
    if row.get("manual_acpi_strict") and row.get("manual_repair_present"):
        return "repaired_acpi"
    if row.get("manual_process_valid_strict") is True:
        return "strict_valid"
    return "other"


def patched_metrics(model, tok, prompt: str, add: bool, device: torch.device, max_len: int, module, delta: torch.Tensor) -> dict[str, Any]:
    ids = tok.encode(prompt, add_special_tokens=add)[-max_len:]
    pos = len(ids) - 1
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)

    def hook(_module, _inputs, output):
        hidden = extract_output(output).clone()
        hidden[:, pos, :] = hidden[:, pos, :] + delta.to(device=hidden.device, dtype=hidden.dtype)
        return replace_output(output, hidden)

    handle = module.register_forward_hook(hook)
    try:
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
        metrics = yes_no_metrics(out.logits[0, -1], tok)
        del out
    finally:
        handle.remove()
    del input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return metrics


def base_metrics(model, tok, prompt: str, add: bool, device: torch.device, max_len: int, best_layer: int, direction: torch.Tensor, center: torch.Tensor) -> dict[str, Any]:
    ids = tok.encode(prompt, add_special_tokens=add)[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
    metrics = yes_no_metrics(out.logits[0, -1], tok)
    vec = out.hidden_states[best_layer][0, -1, :].detach().float().cpu()
    metrics["hidden_process_score"] = float(((vec - center) @ direction).item())
    metrics["input_tokens"] = len(ids)
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return metrics


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all", row["patch"])].append(row)
        groups[("trace_class", row["trace_class"], row["patch"])].append(row)
        groups[("component", row["component"], row["patch"])].append(row)
    out = []
    for (typ, key, patch), vals in sorted(groups.items()):
        out.append(
            {
                "slice_type": typ,
                "slice": key,
                "patch": patch,
                "n": len(vals),
                "base_accept_rate": sum(v["base_pred_process_valid"] for v in vals) / len(vals),
                "patched_accept_rate": sum(v["patched_pred_process_valid"] for v in vals) / len(vals),
                "flip_count": sum(v["patched_pred_process_valid"] != v["base_pred_process_valid"] for v in vals),
                "mean_yes_minus_no_effect": mean(v["patched_yes_minus_no"] - v["base_yes_minus_no"] for v in vals),
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E122_component_steering_audit"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--max-train-items", type=int, default=0)
    p.add_argument("--max-target-rows", type=int, default=10)
    p.add_argument("--components", nargs="+", default=["residual", "mlp", "token_mixer"])
    p.add_argument("--alphas", nargs="+", type=float, default=[-2.0, 2.0])
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E122", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    best = best_layer_for(args.model_key, args.best_layer)
    module_idx = max(0, min(best - 1, len(layers) - 1))
    direction, center, train_meta = train_residual_direction(model, tok, use_chat, device, best, args.max_model_len, args.max_train_items)

    rows_out = []
    targets = target_rows(args.model_key, args.max_target_rows)
    for row in targets:
        prompt, add = render_prompt(tok, strict_prompt(row["problem"], row["completion"]), use_chat)
        base = base_metrics(model, tok, prompt, add, device, args.max_model_len, best, direction, center)
        for comp in args.components:
            try:
                module = module_for_component(layers[module_idx], comp)
            except AttributeError as exc:
                rows_out.append(
                    {
                        "audit_idx": row["audit_idx"],
                        "trace_class": classify(row),
                        "component": comp,
                        "patch": "component_missing",
                        "error": str(exc),
                    }
                )
                continue
            for alpha in args.alphas:
                patch_name = f"alpha_{alpha:+.2f}"
                patched = patched_metrics(model, tok, prompt, add, device, args.max_model_len, module, alpha * direction)
                rows_out.append(
                    {
                        "audit_idx": row["audit_idx"],
                        "task_id": row["task_id"],
                        "prompt_variant": row["prompt_variant"],
                        "trace_class": classify(row),
                        "component": comp,
                        "patch": patch_name,
                        "alpha": alpha,
                        "base_yes_minus_no": base["yes_minus_no"],
                        "base_pred_process_valid": bool(base["pred_process_valid"]),
                        "base_hidden_process_score": base["hidden_process_score"],
                        "patched_yes_minus_no": patched["yes_minus_no"],
                        "patched_pred_process_valid": bool(patched["pred_process_valid"]),
                        "patched_readout_confidence": patched["readout_confidence"],
                    }
                )
        print(f"E122 patched audit_idx={row['audit_idx']}", flush=True)

    result = {
        "experiment": "E122_component_steering_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "best_hidden_layer": best,
        "patched_module_index": module_idx,
        "args": vars(args),
        "train_direction_meta": train_meta,
        "rows": rows_out,
        "summary": summarize([r for r in rows_out if "base_yes_minus_no" in r]),
        "leakage_audit": {
            "gold_answer_in_prompt_rows": 0,
            "manual_labels_in_prompt_rows": 0,
            "error_span_annotation_in_prompt_rows": 0,
            "note_zh": "E61/E119/E146 标签只用于离线训练方向、选择行和评分；prompt 只含 problem 与 visible trace。",
        },
        "scope_note_zh": "E122 是小规模组件 steering 诊断，不估计自然发生率，也不是完整 circuit 证明。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e122_component_steering_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print(json.dumps({"summary": result["summary"][:12]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
