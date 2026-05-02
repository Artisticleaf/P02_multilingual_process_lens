#!/usr/bin/env python3
"""Evaluate verifier reliability on manually audited real generated traces."""
from __future__ import annotations

import argparse
import json
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
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def prompt_for(row: dict[str, Any], prompt_lang: str, mode: str) -> str:
    trace = row["completion"]
    problem = row["problem"]
    if mode == "process_only":
        if prompt_lang == "zh":
            return (
                "你是数学推理过程审计员。只判断推理过程中的数学步骤是否有效；"
                "不要因为最终答案格式缺失、截断或额外文本而判错。"
                "如果存在任何数学步骤错误，回答 否；如果可见推理步骤都数学有效，回答 是。只回答 是 或 否。\n"
                f"题目：{problem}\n"
                f"推理过程：{trace}\n"
                "可见推理步骤是否数学有效？答案："
            )
        return (
            "You are auditing a mathematical reasoning trace. Judge only whether the mathematical "
            "reasoning steps are valid; do not penalize missing final-answer formatting, truncation, "
            "or extra text after the answer. If any mathematical step is wrong, answer No. If the "
            "visible reasoning steps are mathematically valid, answer Yes. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {trace}\n"
            "Are the visible reasoning steps mathematically valid? Answer:"
        )
    if mode == "training_candidate":
        if prompt_lang == "zh":
            return (
                "你是训练数据清洗员。只有当最终答案正确、每个数学推理步骤都有效、且输出没有明显截断或答案后跑题时，才回答 是。"
                "如果答案错误、过程有错、缺少最终答案、明显截断、或答案后继续生成无关内容，回答 否。只回答 是 或 否。\n"
                f"题目：{problem}\n"
                f"推理过程：{trace}\n"
                "这条样本可以作为高质量训练轨迹保留吗？答案："
            )
        return (
            "You are cleaning training data. Answer Yes only if the final answer is correct, every "
            "mathematical reasoning step is valid, and the output is not visibly truncated or off-task "
            "after the answer. If the answer is wrong, the process is wrong, the final answer is missing, "
            "the trace is truncated, or it continues off-task after the answer, answer No. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Reasoning trace: {trace}\n"
            "Should this sample be kept as a high-quality training trajectory? Answer:"
        )
    raise KeyError(mode)


def target_for(row: dict[str, Any], mode: str) -> bool | None:
    if mode == "process_only":
        return row["manual_process_valid"]
    if mode == "training_candidate":
        return bool(
            row["manual_process_valid"] is True
            and row["manual_final_correct"] is True
            and row["manual_format_valid"] is True
        )
    raise KeyError(mode)


def option_logprob(
    model,
    tokenizer,
    prompt: str,
    option: str,
    device: torch.device,
    max_model_len: int,
) -> float:
    """Teacher-force a whole option string and sum token log-probabilities."""
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    if not option_ids:
        return float("-inf")
    # Keep room for at least the option tokens if the trace is long.
    keep_prompt = max(1, max_model_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
    score = 0.0
    start = len(prompt_ids)
    for j, tok_id in enumerate(option_ids):
        pos = start + j - 1
        logp = F.log_softmax(logits[pos], dim=-1)
        score += float(logp[tok_id].item())
    return score


def margin_for(
    model,
    tokenizer,
    prompt: str,
    yes_options: list[str],
    no_options: list[str],
    device: torch.device,
    max_model_len: int,
) -> tuple[float, float, float, str, str]:
    yes_scored = [(option_logprob(model, tokenizer, prompt, opt, device, max_model_len), opt) for opt in yes_options]
    no_scored = [(option_logprob(model, tokenizer, prompt, opt, device, max_model_len), opt) for opt in no_options]
    yes_score, yes_opt = max(yes_scored, key=lambda x: x[0])
    no_score, no_opt = max(no_scored, key=lambda x: x[0])
    return yes_score - no_score, yes_score, no_score, yes_opt, no_opt


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for key in [
            (r["mode"], r["prompt_lang"], "all"),
            (r["mode"], r["prompt_lang"], f"reason={r['reason_lang']}"),
            (r["mode"], r["prompt_lang"], f"risk={r['manual_risk']}"),
        ]:
            groups[key].append(r)
    out = []
    for (mode, prompt_lang, slice_name), g in sorted(groups.items()):
        valid = [r for r in g if r["target"] is not None]
        if not valid:
            continue
        target_false = [r for r in valid if r["target"] is False]
        process_invalid = [r for r in valid if r["manual_process_valid"] is False]
        acpi = [r for r in valid if r["is_acpi"]]
        out.append(
            {
                "mode": mode,
                "prompt_lang": prompt_lang,
                "slice": slice_name,
                "n": len(valid),
                "accuracy": sum(r["pred"] == r["target"] for r in valid) / len(valid),
                "yes_rate": sum(r["pred"] for r in valid) / len(valid),
                "false_accept_rate_target_false": (
                    sum(r["pred"] for r in target_false) / len(target_false) if target_false else None
                ),
                "process_invalid_false_accept_rate": (
                    sum(r["pred"] for r in process_invalid) / len(process_invalid) if process_invalid else None
                ),
                "acpi_false_accept_rate": sum(r["pred"] for r in acpi) / len(acpi) if acpi else None,
                "mean_margin": sum(r["yes_minus_no_logprob"] for r in valid) / len(valid),
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/manual_trace_audit_seed_20260427.jsonl"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E04_manual_trace_verifier"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--max-rows", type=int, default=0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = [json.loads(line) for line in Path(args.manual_jsonl).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.max_rows > 0:
        rows = rows[: args.max_rows]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading tokenizer: {args.model_key} -> {spec['path']}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] loading model dtype={args.dtype} device={args.device}", flush=True)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    options = {
        "en": ([" Yes", "Yes", " yes", "yes"], [" No", "No", " no", "no"]),
        "zh": ([" 是", "是"], [" 否", "否", " 不", "不"]),
    }
    eval_rows = []
    for row in rows:
        for mode in ("process_only", "training_candidate"):
            target = target_for(row, mode)
            if target is None:
                continue
            for prompt_lang in ("en", "zh"):
                yes_options, no_options = options[prompt_lang]
                prompt = prompt_for(row, prompt_lang, mode)
                margin, yes_score, no_score, yes_option, no_option = margin_for(
                    model, tokenizer, prompt, yes_options, no_options, device, args.max_model_len
                )
                pred = margin > 0
                eval_rows.append(
                    {
                        "audit_idx": row["audit_idx"],
                        "trace_model_key": row["model_key"],
                        "task_id": row["task_id"],
                        "input_lang": row["input_lang"],
                        "reason_lang": row["reason_lang"],
                        "manual_risk": row["manual_risk"],
                        "manual_process_valid": row["manual_process_valid"],
                        "manual_final_correct": row["manual_final_correct"],
                        "manual_format_valid": row["manual_format_valid"],
                        "is_acpi": row["is_acpi"],
                        "mode": mode,
                        "prompt_lang": prompt_lang,
                        "target": target,
                        "pred": pred,
                        "correct": pred == target,
                        "yes_minus_no_logprob": margin,
                        "yes_score": yes_score,
                        "no_score": no_score,
                        "yes_option": yes_option,
                        "no_option": no_option,
                    }
                )
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "verifier_model_key": args.model_key,
        "backend": "hf",
        "model_spec": spec,
        "manual_jsonl": args.manual_jsonl,
        "num_manual_rows": len(rows),
        "num_eval_rows": len(eval_rows),
        "args": vars(args),
        "rows": eval_rows,
        "summary": summarize(eval_rows),
    }
    out = Path(args.out_dir) / f"{args.model_key}_manual_trace_verifier.json"
    write_json(out, result)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] wrote {out}; eval_rows={len(eval_rows)}", flush=True)
    for s in result["summary"]:
        if s["slice"] == "all":
            print(
                "SUMMARY "
                f"model={args.model_key} mode={s['mode']} prompt={s['prompt_lang']} "
                f"acc={s['accuracy']:.3f} false_accept={s['false_accept_rate_target_false']} "
                f"proc_inv_false_accept={s['process_invalid_false_accept_rate']}",
                flush=True,
            )


if __name__ == "__main__":
    main()
