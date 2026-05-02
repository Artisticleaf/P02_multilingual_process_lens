#!/usr/bin/env python3
"""E71 strict vs repair-aware verifier objective.

Scores pointwise Yes/No process-verifier prompts under three explicit target
objectives: strict trace-selection, repair-aware reading, and final-surviving
proof reading. Prompts contain only the problem and visible trace; manual labels,
error spans, and repair annotations are used only offline for grouping/metrics.
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
from statistics import mean
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E57_AUDIT = PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl"
E61_DATA = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"

REPAIR_RE = re.compile(
    r"\b(wait|re-?read|double[- ]?check|check|but|however|actually|correct(?:ed|ly)?|using the actual|using the correct)\b|可是|但是|实际|正确|应当|应为|才是",
    re.IGNORECASE,
)

OBJECTIVES = ["strict_process", "repair_aware", "final_surviving_proof"]


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


def repair_marker_after_error(row: dict[str, Any]) -> bool:
    completion = row.get("completion", "") or ""
    error_span = row.get("error_span") or row.get("manual_error_span") or ""
    error_pos = completion.find(error_span) if error_span else -1
    first_repair = min((m.start() for m in REPAIR_RE.finditer(completion)), default=-1)
    return first_repair >= 0 and (error_pos < 0 or first_repair > error_pos)


def build_rows(include_e61: bool = True, include_e57: bool = True) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if include_e57:
        for r in load_jsonl(E57_AUDIT):
            strict_valid = bool(r["manual_process_valid_strict"])
            repaired_valid = bool(r["manual_process_valid_repaired"])
            unrepaired_acpi = bool(r.get("manual_acpi_unrepaired", False))
            repaired_acpi = bool(r.get("manual_acpi_strict", False)) and repaired_valid and not unrepaired_acpi
            out.append(
                {
                    "dataset": "E57_hard_task",
                    "source_model": r["model_key"],
                    "item_id": f"E57:{r['model_key']}:{r['manual_audit_idx']}",
                    "audit_idx": r["manual_audit_idx"],
                    "task_id": r["task_id"],
                    "family": "hard_task",
                    "prompt_variant": r.get("prompt_variant"),
                    "problem": r["problem"],
                    "completion": r["completion"],
                    "strict_process_valid": strict_valid,
                    "repair_aware_valid": repaired_valid,
                    "final_surviving_valid": repaired_valid,
                    "trace_class": "valid" if strict_valid else ("repaired_acpi" if repaired_acpi else "unrepaired_acpi"),
                    "manual_label_source": "human_e57_manual_audit",
                    "manual_final_correct": bool(r.get("manual_final_correct", True)),
                    "gold_answer_in_prompt": bool(r.get("gold_answer_in_prompt", False)),
                    "known_trap_note_in_prompt": bool(r.get("known_trap_note_in_prompt", False)),
                }
            )
    if include_e61:
        for r in load_jsonl(E61_DATA):
            strict_valid = bool(r["manual_process_valid"])
            repaired = (not strict_valid) and repair_marker_after_error(r)
            out.append(
                {
                    "dataset": "E61_language_grid",
                    "source_model": "human_controlled",
                    "item_id": f"E61:{r['audit_idx']}",
                    "audit_idx": r["audit_idx"],
                    "task_id": r["task_id"],
                    "family": r.get("family"),
                    "route_id": r.get("route_id"),
                    "problem": r["problem"],
                    "completion": r["completion"],
                    "strict_process_valid": strict_valid,
                    # For E61 this is a conservative regex-derived label, not a human relabel.
                    "repair_aware_valid": strict_valid or repaired,
                    "final_surviving_valid": strict_valid or repaired,
                    "trace_class": "valid" if strict_valid else ("repair_marker_invalid" if repaired else "no_clear_repair_invalid"),
                    "manual_label_source": "e61_manual_strict_plus_e69_regex_repair_marker",
                    "manual_final_correct": bool(r.get("manual_final_correct", True)),
                    "gold_answer_in_prompt": bool(r.get("gold_label_in_prompt", False)),
                    "known_trap_note_in_prompt": bool(r.get("known_error_span_annotation_in_prompt", False)),
                }
            )
    return out


def prompt_for(row: dict[str, Any], objective: str) -> str:
    problem = row["problem"]
    trace = row["completion"]
    if objective == "strict_process":
        head = (
            "You are a strict trace-selection auditor. Judge the visible reasoning trace step by step. "
            "If any visible local step, definition, arithmetic operation, counting rule, unit conversion, semantic interpretation, or proof implication is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
            "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No."
        )
        q = "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    elif objective == "repair_aware":
        head = (
            "You are a repair-aware reasoning auditor. A trace may contain scratch work or an early mistake. "
            "If an early mistake is explicitly noticed, abandoned, or corrected later, judge the repaired reasoning as acceptable. "
            "Answer No only if an uncorrected local error remains in the reasoning that supports the final answer. Answer only Yes or No."
        )
        q = "Using this repair-aware rule, is the reasoning acceptable after any explicit corrections? Answer:"
    elif objective == "final_surviving_proof":
        head = (
            "You are auditing the final surviving proof, not abandoned scratch work. Ignore earlier guesses or lines that are later clearly superseded. "
            "Judge whether the final chain of reasoning that remains after revisions correctly supports the final answer. "
            "Answer only Yes or No."
        )
        q = "Does the final surviving proof correctly support the final answer? Answer:"
    else:
        raise ValueError(objective)
    return f"{head}\nProblem: {problem}\nReasoning trace: {trace}\n{q}"


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


def first_token_score(model, tokenizer, prompt: str, options: list[str], device: torch.device, max_model_len: int, add_special_tokens: bool) -> tuple[float, str]:
    """Score short labels from the next-token distribution in one forward pass."""
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)[-max_model_len:]
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0, -1].float()
    logp = F.log_softmax(logits, dim=-1)
    scored = []
    for opt in options:
        ids = tokenizer.encode(opt, add_special_tokens=False)
        if ids:
            scored.append((float(logp[ids[0]].item()), opt))
    del input_ids, attention_mask
    return max(scored, key=lambda x: x[0])


def batch_first_token_scores(
    model,
    tokenizer,
    prompts: list[str],
    options: list[str],
    device: torch.device,
    max_model_len: int,
    add_special_tokens: bool,
) -> list[tuple[float, str]]:
    """Batched next-token label scoring for short labels."""
    old_padding = getattr(tokenizer, "padding_side", "right")
    tokenizer.padding_side = "left"
    enc = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_model_len,
        add_special_tokens=add_special_tokens,
    ).to(device)
    with torch.no_grad():
        logits = model(**enc, use_cache=False).logits[:, -1, :].float()
    logp = F.log_softmax(logits, dim=-1)
    option_ids = []
    for opt in options:
        ids = tokenizer.encode(opt, add_special_tokens=False)
        if ids:
            option_ids.append((opt, int(ids[0])))
    out = []
    for i in range(logp.shape[0]):
        scored = [(float(logp[i, tok_id].item()), opt) for opt, tok_id in option_ids]
        out.append(max(scored, key=lambda x: x[0]))
    tokenizer.padding_side = old_padding
    del enc, logits, logp
    return out


def target_for(row: dict[str, Any], objective: str) -> bool:
    if objective == "strict_process":
        return bool(row["strict_process_valid"])
    if objective == "repair_aware":
        return bool(row["repair_aware_valid"])
    if objective == "final_surviving_proof":
        return bool(row["final_surviving_valid"])
    raise ValueError(objective)


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for key in ["all", "dataset", "trace_class", "source_model", "prompt_variant", "family"]:
            val = "all" if key == "all" else r.get(key)
            if val is not None:
                groups[(r["objective"], key, str(val))].append(r)
    out = []
    for (obj, st, sv), g in sorted(groups.items()):
        invalid_strict = [r for r in g if not r["strict_process_valid"]]
        unrepaired = [r for r in g if r.get("trace_class") == "unrepaired_acpi"]
        repaired = [r for r in g if r.get("trace_class") in {"repaired_acpi", "repair_marker_invalid"}]
        out.append(
            {
                "objective": obj,
                "slice_type": st,
                "slice": sv,
                "n": len(g),
                "accuracy_to_objective_target": sum(r["pred_process_valid"] == r["objective_target_valid"] for r in g) / len(g),
                "yes_rate": sum(r["pred_process_valid"] for r in g) / len(g),
                "strict_invalid_accept_rate": sum(r["pred_process_valid"] for r in invalid_strict) / len(invalid_strict) if invalid_strict else None,
                "repaired_accept_rate": sum(r["pred_process_valid"] for r in repaired) / len(repaired) if repaired else None,
                "unrepaired_accept_rate": sum(r["pred_process_valid"] for r in unrepaired) / len(unrepaired) if unrepaired else None,
                "mean_yes_minus_no_margin": mean(r["margin_yes_minus_no"] for r in g),
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E71_repair_objective"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--datasets", default="E57,E61", help="Comma-separated: E57,E61")
    p.add_argument("--score-mode", choices=["first_token", "full_option"], default="first_token")
    p.add_argument("--batch-size", type=int, default=4)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    selected = {x.strip() for x in args.datasets.split(",") if x.strip()}
    items = build_rows(include_e57="E57" in selected, include_e61="E61" in selected)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E71 n_items={len(items)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    yes_opts = [" Yes", "Yes", " yes", "yes"]
    no_opts = [" No", "No", " no", "no"]
    rows = []
    total = len(items) * len(OBJECTIVES)
    done = 0
    for obj in OBJECTIVES:
        for start in range(0, len(items), args.batch_size):
            batch = items[start : start + args.batch_size]
            rendered = [render_prompt(tok, prompt_for(item, obj), use_chat) for item in batch]
            prompts = [x[0] for x in rendered]
            add_values = {x[1] for x in rendered}
            if len(add_values) != 1:
                raise RuntimeError("mixed add_special_tokens in E71 batch")
            add_special = next(iter(add_values))
            if args.score_mode == "first_token":
                yes_scores = batch_first_token_scores(model, tok, prompts, yes_opts, device, args.max_model_len, add_special)
                no_scores = batch_first_token_scores(model, tok, prompts, no_opts, device, args.max_model_len, add_special)
            else:
                yes_scores = [best_score(model, tok, p, yes_opts, device, args.max_model_len, add_special) for p in prompts]
                no_scores = [best_score(model, tok, p, no_opts, device, args.max_model_len, add_special) for p in prompts]
            for item, (yes_score, yes_opt), (no_score, no_opt) in zip(batch, yes_scores, no_scores):
                margin = yes_score - no_score
                target = target_for(item, obj)
                rows.append({
                    **{k: v for k, v in item.items() if k not in {"problem", "completion"}},
                    "objective": obj,
                    "objective_target_valid": target,
                    "pred_process_valid": margin > 0,
                    "margin_yes_minus_no": margin,
                    "yes_score": yes_score,
                    "no_score": no_score,
                    "yes_option": yes_opt,
                    "no_option": no_opt,
                    "used_chat_template": use_chat,
                })
                done += 1
            if done % 50 < args.batch_size or done == total:
                print(f"scored {done}/{total}", flush=True)
    result = {
        "experiment": "E71_repair_objective",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "datasets": sorted(selected),
        "used_chat_template": use_chat,
        "args": vars(args),
        "rows": rows,
        "summary": summarize(rows),
        "leakage_audit": {
            "gold_answer_in_prompt_rows": sum(1 for x in items if x.get("gold_answer_in_prompt")),
            "known_trap_note_in_prompt_rows": sum(1 for x in items if x.get("known_trap_note_in_prompt")),
            "manual_labels_in_prompt_rows": 0,
            "error_spans_in_prompt_as_annotation_rows": 0,
            "note_zh": "Prompt 只含 problem 与 visible trace；人工 strict/repaired/unrepaired 标签、error span 和 repair marker 只用于离线分组。",
        },
        "scope_note_zh": "E71 测试 explicit strict/repair-aware/final-proof 口径是否改变 verifier 决策；E61 repair-aware target 含 regex 修复标记，须作为启发式标签报告。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e71_repair_objective_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] == "all":
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
