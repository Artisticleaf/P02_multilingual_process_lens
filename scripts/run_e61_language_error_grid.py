#!/usr/bin/env python3
"""E61 language-route x error-taxonomy controlled verifier grid.

The experiment tests whether ACPI over-acceptance generalizes across language
routes and error families. It uses deterministic option-logprob scoring only.
Prompts contain only the problem and trace(s), never manual labels, error spans,
support spans, or corrections.
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

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

DATA_PATH = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
PAIRS_PATH = PROJECT / "configs/e61_language_error_grid_pairs.yaml"

POINTWISE_OBJECTIVES = [
    "plain_yes_no",
    "careful_yes_no",
    "answer_blind_yes_no",
    "locate_then_judge_yes_no",
]
CONTRASTIVE_OBJECTIVES = ["sibling_comparison", "careful_sibling_comparison"]


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


def pointwise_prompt(row: dict[str, Any], objective: str) -> str:
    problem = row["problem"]
    completion = row["completion"]
    if objective == "plain_yes_no":
        return (
            "You are auditing a reasoning trace. Judge only whether the visible reasoning steps are valid; "
            "do not penalize missing final-answer formatting, truncation, or extra text after the answer. "
            "If any mathematical, logical, code-trace, table-interpretation, unit-conversion, or language-semantics step is wrong, answer No. "
            "If the visible reasoning steps are valid, answer Yes. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {completion}\n"
            "Are the visible reasoning steps valid? Answer:"
        )
    if objective == "careful_yes_no":
        return (
            "You are a strict process auditor. Read the trace line by line. A correct final answer is not enough: "
            "the reasoning is invalid if any local definition, arithmetic operation, unit conversion, counting rule, inequality boundary, "
            "table interpretation, code execution step, proof implication, geometry notation, or language-semantics interpretation is wrong. "
            "Ignore style and formatting. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {completion}\n"
            "After careful line-by-line checking, are all visible reasoning steps valid? Answer:"
        )
    if objective == "answer_blind_yes_no":
        return (
            "You are checking process validity, not answer correctness. Mentally cover the final-answer line before judging. "
            "A trace that ends with the correct answer must still be rejected if the visible derivation contains a wrong local step, "
            "wrong definition, wrong semantic interpretation, or wrong execution rule. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {completion}\n"
            "Ignoring the final answer as an anchor, is the visible reasoning process valid? Answer:"
        )
    if objective == "locate_then_judge_yes_no":
        return (
            "You are doing error localization followed by a binary judgment. First internally look for the earliest unsupported or wrong step "
            "in the reasoning trace, including arithmetic, units, counting, inequality boundaries, code execution, proof implications, "
            "table reading, and language semantics. If such a step exists, the process is invalid even if the final answer is correct. "
            "Do not output the location; answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {completion}\n"
            "After internally locating any error, is the visible reasoning process valid? Answer:"
        )
    raise ValueError(f"unknown pointwise objective {objective}")


def contrastive_prompt(problem: str, trace_a: str, trace_b: str, objective: str) -> str:
    if objective == "sibling_comparison":
        return (
            "You are comparing two reasoning traces for the same problem. Exactly one trace has a local process error, "
            "although both may end with the same final answer. Ignore style and verbosity. Choose the trace whose reasoning process is invalid. "
            "Answer only A or B.\n"
            f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
        )
    if objective == "careful_sibling_comparison":
        return (
            "You are a strict process auditor comparing two traces for the same problem. Both traces may look fluent and may end with the same final answer. "
            "Exactly one trace contains a local process error. Check definitions, arithmetic, units, counting, inequalities, code execution, table reading, "
            "proof implications, geometry notation, and language semantics line by line. Choose the trace whose reasoning process is invalid. "
            "Answer only A or B.\n"
            f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
        )
    raise ValueError(f"unknown contrastive objective {objective}")


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


def load_e61(limit_traces: int | None = None, limit_pairs: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = load_jsonl(DATA_PATH)
    by_idx = {int(r["audit_idx"]): r for r in rows}
    traces: list[dict[str, Any]] = []
    for row in rows:
        traces.append(
            {
                "pool_exp": "E61",
                "pool": "language_error_grid",
                "audit_idx": int(row["audit_idx"]),
                "task_id": row["task_id"],
                "source_family": row.get("source_family"),
                "family": row.get("family"),
                "route_id": row.get("route_id"),
                "route": row.get("route"),
                "input_lang": row.get("input_lang"),
                "reason_lang": row.get("reason_lang"),
                "problem": row["problem"],
                "completion": row["completion"],
                "e61_variant": row.get("e61_variant"),
                "manual_process_valid": bool(row["manual_process_valid"]),
                "manual_final_correct": bool(row.get("manual_final_correct", False)),
                "is_acpi": bool(row.get("is_acpi", False)),
                "gold_label_in_prompt": bool(row.get("gold_label_in_prompt", False)),
                "known_error_span_in_prompt": bool(row.get("known_error_span_in_prompt", False)),
                "known_error_span_annotation_in_prompt": bool(row.get("known_error_span_annotation_in_prompt", False)),
                "manual_correction_in_prompt": bool(row.get("manual_correction_in_prompt", False)),
            }
        )
    pairs: list[dict[str, Any]] = []
    for pair in read_yaml(PAIRS_PATH)["pairs"]:
        valid = by_idx[int(pair["valid_idx"])]
        bad = by_idx[int(pair["bad_idx"])]
        pairs.append(
            {
                "pool_exp": "E61",
                "pool": "language_error_grid",
                "pair_id": pair["id"],
                "task_id": pair["task_id"],
                "source_family": bad.get("source_family"),
                "family": pair.get("family") or bad.get("family"),
                "route_id": pair.get("route_id") or bad.get("route_id"),
                "route": bad.get("route"),
                "input_lang": bad.get("input_lang"),
                "reason_lang": bad.get("reason_lang"),
                "problem": bad["problem"],
                "valid_trace": valid["completion"],
                "bad_trace": bad["completion"],
            }
        )
    if limit_traces is not None:
        traces = traces[:limit_traces]
    if limit_pairs is not None:
        pairs = pairs[:limit_pairs]
    return traces, pairs


def group_keys(row: dict[str, Any]) -> list[tuple[str, str]]:
    keys = [("all", "all")]
    for key in ["route_id", "family", "source_family", "input_lang", "reason_lang"]:
        if row.get(key):
            keys.append((key, str(row[key])))
    if row.get("route_id") and row.get("family"):
        keys.append(("route_family", f"{row['route_id']}::{row['family']}"))
    return keys


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for slice_type, slice_name in group_keys(r):
            groups[(r["objective"], slice_type, slice_name)].append(r)
    out: list[dict[str, Any]] = []
    for (objective, slice_type, slice_name), g in sorted(groups.items()):
        if g[0]["objective_type"] == "pointwise":
            invalid = [r for r in g if not r["target_process_valid"]]
            valid = [r for r in g if r["target_process_valid"]]
            out.append(
                {
                    "objective": objective,
                    "objective_type": "pointwise",
                    "slice_type": slice_type,
                    "slice": slice_name,
                    "n": len(g),
                    "accuracy": sum(r["pred_process_valid"] == r["target_process_valid"] for r in g) / len(g),
                    "yes_rate": sum(r["pred_process_valid"] for r in g) / len(g),
                    "acpi_accept_rate": sum(r["pred_process_valid"] for r in invalid) / len(invalid) if invalid else None,
                    "valid_accept_rate": sum(r["pred_process_valid"] for r in valid) / len(valid) if valid else None,
                    "mean_margin": mean(r["margin_valid_minus_invalid"] for r in g),
                }
            )
        else:
            out.append(
                {
                    "objective": objective,
                    "objective_type": "contrastive",
                    "slice_type": slice_type,
                    "slice": slice_name,
                    "n": len(g),
                    "accuracy": sum(r["correct"] for r in g) / len(g),
                    "pred_A_rate": sum(r["pred"] == "A" for r in g) / len(g),
                    "mean_target_margin": mean(r["margin_target_minus_other"] for r in g),
                    "accepted_acpi_rate_proxy": 1.0 - (sum(r["correct"] for r in g) / len(g)),
                }
            )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E61_language_error_grid"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--pointwise-objectives", default=",".join(POINTWISE_OBJECTIVES))
    p.add_argument("--contrastive-objectives", default=",".join(CONTRASTIVE_OBJECTIVES))
    p.add_argument("--limit-traces", type=int, default=None, help="Debug only: score only first N traces.")
    p.add_argument("--limit-pairs", type=int, default=None, help="Debug only: score only first N pairs.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    traces, pairs = load_e61(args.limit_traces, args.limit_pairs)
    pointwise_objectives = [x.strip() for x in args.pointwise_objectives.split(",") if x.strip()]
    contrastive_objectives = [x.strip() for x in args.contrastive_objectives.split(",") if x.strip()]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E61 traces={len(traces)} pairs={len(pairs)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tokenizer, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    yes_opts = [" Yes", "Yes", " yes", "yes"]
    no_opts = [" No", "No", " no", "no"]
    a_opts = ["A", " A", "A.", " A."]
    b_opts = ["B", " B", "B.", " B."]
    rows: list[dict[str, Any]] = []

    total_point = len(traces) * len(pointwise_objectives)
    done = 0
    for objective in pointwise_objectives:
        for row in traces:
            prompt_text, add_special = render_prompt(tokenizer, pointwise_prompt(row, objective), use_chat)
            yes_score, yes_opt = best_score(model, tokenizer, prompt_text, yes_opts, device, args.max_model_len, add_special)
            no_score, no_opt = best_score(model, tokenizer, prompt_text, no_opts, device, args.max_model_len, add_special)
            margin = yes_score - no_score
            rows.append(
                {
                    "objective_type": "pointwise",
                    "objective": objective,
                    "pool_exp": row["pool_exp"],
                    "pool": row["pool"],
                    "audit_idx": row["audit_idx"],
                    "task_id": row["task_id"],
                    "source_family": row.get("source_family"),
                    "family": row.get("family"),
                    "route_id": row.get("route_id"),
                    "route": row.get("route"),
                    "input_lang": row.get("input_lang"),
                    "reason_lang": row.get("reason_lang"),
                    "e61_variant": row.get("e61_variant"),
                    "target_process_valid": bool(row["manual_process_valid"]),
                    "manual_final_correct": row.get("manual_final_correct"),
                    "is_acpi": bool(row.get("is_acpi", False)),
                    "pred_process_valid": margin > 0,
                    "margin_valid_minus_invalid": margin,
                    "yes_score": yes_score,
                    "no_score": no_score,
                    "yes_option": yes_opt,
                    "no_option": no_opt,
                    "used_chat_template": use_chat,
                }
            )
            done += 1
            if done % 48 == 0 or done == total_point:
                print(f"pointwise scored {done}/{total_point}", flush=True)

    total_con = len(pairs) * len(contrastive_objectives) * 2
    done = 0
    for objective in contrastive_objectives:
        for pair in pairs:
            for order in ["bad_A", "bad_B"]:
                if order == "bad_A":
                    trace_a, trace_b, target = pair["bad_trace"], pair["valid_trace"], "A"
                else:
                    trace_a, trace_b, target = pair["valid_trace"], pair["bad_trace"], "B"
                prompt_text, add_special = render_prompt(
                    tokenizer,
                    contrastive_prompt(pair["problem"], trace_a, trace_b, objective),
                    use_chat,
                )
                a_score, a_opt = best_score(model, tokenizer, prompt_text, a_opts, device, args.max_model_len, add_special)
                b_score, b_opt = best_score(model, tokenizer, prompt_text, b_opts, device, args.max_model_len, add_special)
                pred = "A" if a_score >= b_score else "B"
                margin = (a_score - b_score) if target == "A" else (b_score - a_score)
                rows.append(
                    {
                        "objective_type": "contrastive",
                        "objective": objective,
                        "pool_exp": pair["pool_exp"],
                        "pool": pair["pool"],
                        "pair_id": pair["pair_id"],
                        "task_id": pair["task_id"],
                        "source_family": pair.get("source_family"),
                        "family": pair.get("family"),
                        "route_id": pair.get("route_id"),
                        "route": pair.get("route"),
                        "input_lang": pair.get("input_lang"),
                        "reason_lang": pair.get("reason_lang"),
                        "order": order,
                        "target": target,
                        "pred": pred,
                        "correct": pred == target,
                        "margin_target_minus_other": margin,
                        "a_score": a_score,
                        "b_score": b_score,
                        "a_option": a_opt,
                        "b_option": b_opt,
                        "used_chat_template": use_chat,
                    }
                )
                done += 1
                if done % 48 == 0 or done == total_con:
                    print(f"contrastive scored {done}/{total_con}", flush=True)

    result = {
        "experiment": "E61_language_error_grid",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "prompt_format": args.prompt_format,
        "used_chat_template": use_chat,
        "args": vars(args),
        "data_path": str(DATA_PATH.relative_to(PROJECT)),
        "pairs_path": str(PAIRS_PATH.relative_to(PROJECT)),
        "scope_note_en": "E61 crosses language routes and error families. Prompts contain only problem and trace(s), never manual labels, support spans, error spans, or corrections.",
        "scope_note_zh": "E61 交叉语言路径与错误类型。prompt 只包含题目和 trace，不包含人工标签、support span、error span 或人工修正。",
        "leakage_audit": {
            "gold_label_in_prompt_rows": sum(int(r.get("gold_label_in_prompt", False)) for r in traces),
            "known_error_span_in_prompt_rows": sum(int(r.get("known_error_span_in_prompt", False)) for r in traces),
            "known_error_span_annotation_in_prompt_rows": sum(int(r.get("known_error_span_annotation_in_prompt", False)) for r in traces),
            "manual_correction_in_prompt_rows": sum(int(r.get("manual_correction_in_prompt", False)) for r in traces),
            "note_zh": "错误句子本身作为 trace 内容出现，这是被审计对象；error_span/support_span/manual_correction 不进入 prompt。",
        },
        "rows": rows,
        "summary": summarize(rows),
    }
    suffix = "chat" if use_chat else "raw"
    debug_suffix = ""
    if args.limit_traces is not None or args.limit_pairs is not None:
        debug_suffix = f"_debug_t{args.limit_traces or 'all'}_p{args.limit_pairs or 'all'}"
    out = Path(args.out_dir) / f"{args.model_key}_e61_language_error_grid_{suffix}{debug_suffix}.json"
    write_json(out, result)
    print(f"wrote {out}; rows={len(rows)}; used_chat_template={use_chat}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] == "all":
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
