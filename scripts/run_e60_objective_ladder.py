#!/usr/bin/env python3
"""E60 process-inspection objective ladder.

The goal is to test whether "asking the verifier to check more carefully" is
enough to remove answer-correct/process-invalid over-acceptance.

This script runs deterministic option-logprob scoring only.  It does not put
manual labels, support spans, error spans, or corrections into prompts.
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

P0_POOLS = [
    (
        "E42",
        "controlled_12_family",
        PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl",
        PROJECT / "configs/e42_e39_objective_pairs.yaml",
    ),
    (
        "E54",
        "parameterized_18_family",
        PROJECT / "data/processed/e54_parameterized_no_leak_generalization_20260428.jsonl",
        PROJECT / "configs/e54_parameterized_no_leak_pairs.yaml",
    ),
]


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
            "You are auditing a mathematical reasoning trace. Judge only whether the mathematical "
            "reasoning steps are valid; do not penalize missing final-answer formatting, truncation, "
            "or extra text after the answer. If any mathematical step is wrong, answer No. If the "
            "visible reasoning steps are mathematically valid, answer Yes. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {completion}\n"
            "Are the visible reasoning steps mathematically valid? Answer:"
        )
    if objective == "careful_yes_no":
        return (
            "You are a strict process auditor. Read the trace line by line. A correct final answer "
            "is not enough: the reasoning is invalid if any local definition, arithmetic operation, "
            "unit conversion, counting rule, inequality boundary, or language-semantics interpretation "
            "is wrong. Ignore style and formatting. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {completion}\n"
            "After careful line-by-line checking, are all visible mathematical reasoning steps valid? Answer:"
        )
    if objective == "answer_blind_yes_no":
        return (
            "You are checking process validity, not answer correctness. Mentally cover the final-answer "
            "line before judging. A trace that ends with the correct answer must still be rejected if "
            "the visible derivation contains a wrong mathematical or semantic step. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {completion}\n"
            "Ignoring the final answer as an anchor, is the visible reasoning process valid? Answer:"
        )
    if objective == "locate_then_judge_yes_no":
        return (
            "You are doing error localization followed by a binary judgment. First internally look for "
            "the earliest unsupported or wrong step in the reasoning trace. If such a step exists, the "
            "process is invalid even if the final answer is correct. If no such step exists, the process "
            "is valid. Do not output the location; answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {completion}\n"
            "After internally locating any error, is the visible reasoning process valid? Answer:"
        )
    raise ValueError(f"unknown pointwise objective {objective}")


def contrastive_prompt(problem: str, trace_a: str, trace_b: str, objective: str) -> str:
    if objective == "sibling_comparison":
        return (
            "You are comparing two reasoning traces for the same math problem. "
            "Exactly one trace has a local mathematical or language-semantic process error, although both may end with the same final answer. "
            "Ignore style and verbosity. Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
            f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
        )
    if objective == "careful_sibling_comparison":
        return (
            "You are a strict process auditor comparing two traces for the same math problem. "
            "Both traces may look fluent and may end with the same final answer. Exactly one trace contains a local process error. "
            "Check definitions, arithmetic, units, counting, inequalities, and language semantics line by line. "
            "Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
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


def load_pools(selected: set[str] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    traces: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for exp, pool, jsonl_path, pairs_path in P0_POOLS:
        if selected and exp not in selected and pool not in selected:
            continue
        rows = load_jsonl(jsonl_path)
        by_idx = {int(r["audit_idx"]): r for r in rows}
        for row in rows:
            traces.append(
                {
                    "pool_exp": exp,
                    "pool": pool,
                    "audit_idx": int(row["audit_idx"]),
                    "task_id": row["task_id"],
                    "family": row.get("family"),
                    "problem": row["problem"],
                    "completion": row["completion"],
                    "e39_variant": row.get("e39_variant") or row.get("e54_variant"),
                    "manual_process_valid": bool(row["manual_process_valid"]),
                    "manual_final_correct": row.get("manual_final_correct"),
                    "is_acpi": bool(row.get("is_acpi", False)),
                }
            )
        for pair in read_yaml(pairs_path)["pairs"]:
            valid = by_idx[int(pair["valid_idx"])]
            bad = by_idx[int(pair["bad_idx"])]
            pairs.append(
                {
                    "pool_exp": exp,
                    "pool": pool,
                    "pair_id": pair["id"],
                    "task_id": pair["task_id"],
                    "family": bad.get("family"),
                    "problem": bad["problem"],
                    "valid_trace": valid["completion"],
                    "bad_trace": bad["completion"],
                }
            )
    return traces, pairs


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["objective"], "all", "all")].append(r)
        groups[(r["objective"], "pool", r["pool"])].append(r)
        groups[(r["objective"], "task", r["task_id"])].append(r)
        if r.get("family"):
            groups[(r["objective"], "family", r["family"])].append(r)
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
                }
            )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E60_objective_ladder"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--pools", default="E42,E54", help="Comma-separated subset: E42,E54 or pool names.")
    p.add_argument(
        "--pointwise-objectives",
        default="plain_yes_no,careful_yes_no,answer_blind_yes_no,locate_then_judge_yes_no",
    )
    p.add_argument("--contrastive-objectives", default="sibling_comparison,careful_sibling_comparison")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    selected = {x.strip() for x in args.pools.split(",") if x.strip()} if args.pools else None
    traces, pairs = load_pools(selected)
    pointwise_objectives = [x.strip() for x in args.pointwise_objectives.split(",") if x.strip()]
    contrastive_objectives = [x.strip() for x in args.contrastive_objectives.split(",") if x.strip()]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E60 pools={args.pools}", flush=True)
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
                    "family": row.get("family"),
                    "e39_variant": row["e39_variant"],
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
            if done % 30 == 0:
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
                        "family": pair.get("family"),
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
                if done % 30 == 0:
                    print(f"contrastive scored {done}/{total_con}", flush=True)

    result = {
        "experiment": "E60_objective_ladder",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "prompt_format": args.prompt_format,
        "used_chat_template": use_chat,
        "args": vars(args),
        "scope_note_en": "E60 compares pointwise process-verifier prompts from plain to stricter inspection prompts, plus sibling comparison. Prompts contain only problem and trace(s), never manual labels or error spans.",
        "scope_note_zh": "E60 比较从普通到更严格检查的单点过程 verifier prompt，并加入 sibling comparison。prompt 只包含题目和 trace，不包含人工标签或错误 span。",
        "leakage_audit": {
            "gold_label_in_prompt_rows": 0,
            "known_error_span_annotation_in_prompt_rows": 0,
            "manual_correction_in_prompt_rows": 0,
            "note_zh": "错误句子本身作为 trace 内容出现，这是被审计对象；error_span/support_span/manual_correction 不进入 prompt。",
        },
        "rows": rows,
        "summary": summarize(rows),
    }
    suffix = "chat" if use_chat else "raw"
    out = Path(args.out_dir) / f"{args.model_key}_e60_objective_ladder_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}; rows={len(rows)}; used_chat_template={use_chat}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] == "all":
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
