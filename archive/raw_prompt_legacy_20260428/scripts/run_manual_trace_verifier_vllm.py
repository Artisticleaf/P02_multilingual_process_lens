#!/usr/bin/env python3
"""High-throughput vLLM version of the manual trace verifier.

This is for black-box verifier experiments (Yes/No scoring). Hidden-state
mechanism probes must keep using the HuggingFace scripts because vLLM does not
expose the intermediate activations we patch.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from vllm import LLM, SamplingParams
from vllm.inputs import TokensPrompt

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import visible_device_label  # noqa: E402


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


def option_token_ids(tokenizer, option: str) -> list[int]:
    ids = tokenizer.encode(option, add_special_tokens=False)
    if not ids:
        raise ValueError(f"Empty tokenization for option {option!r}")
    return [int(x) for x in ids]


def make_scoring_prompt(tokenizer, prompt: str, option: str, max_model_len: int) -> tuple[TokensPrompt, int, list[int]]:
    prompt_ids = [int(x) for x in tokenizer.encode(prompt, add_special_tokens=True)]
    opt_ids = option_token_ids(tokenizer, option)
    keep_prompt = max(1, max_model_len - len(opt_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    full_ids = prompt_ids + opt_ids
    return {"prompt_token_ids": full_ids}, len(prompt_ids), opt_ids


def extract_option_score(output, start: int, opt_ids: list[int]) -> float:
    score = 0.0
    if output.prompt_logprobs is None:
        raise RuntimeError("vLLM did not return prompt_logprobs")
    for offset, tok_id in enumerate(opt_ids):
        pos = start + offset
        token_logprobs = output.prompt_logprobs[pos]
        if token_logprobs is None or tok_id not in token_logprobs:
            got = None if token_logprobs is None else list(token_logprobs)[:8]
            raise KeyError(f"Missing logprob for token {tok_id} at position {pos}; got={got}")
        score += float(token_logprobs[tok_id].logprob)
    return score


def score_options_batched(
    llm: LLM,
    tokenizer,
    items: list[tuple[int, str, str]],
    *,
    max_model_len: int,
    batch_size: int,
    prompt_logprobs: int,
) -> dict[tuple[int, str], float]:
    """Score (eval_idx, option_label, prompt+option) triples."""
    scores: dict[tuple[int, str], float] = {}
    params = SamplingParams(max_tokens=1, temperature=0.0, prompt_logprobs=prompt_logprobs)
    for batch_start in range(0, len(items), batch_size):
        batch = items[batch_start : batch_start + batch_size]
        prompts = []
        starts: list[int] = []
        opt_ids_list: list[list[int]] = []
        for eval_idx, option, prompt in batch:
            token_prompt, start, opt_ids = make_scoring_prompt(tokenizer, prompt, option, max_model_len)
            prompts.append(token_prompt)
            starts.append(start)
            opt_ids_list.append(opt_ids)
        outputs = llm.generate(prompts, params, use_tqdm=False)
        for (eval_idx, option, _prompt), output, start, opt_ids in zip(batch, outputs, starts, opt_ids_list, strict=True):
            scores[(eval_idx, option)] = extract_option_score(output, start, opt_ids)
    return scores


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/manual_trace_audit_seed_20260427.jsonl"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E04_manual_trace_verifier"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--tensor-parallel-size", type=int, default=4)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.88)
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--prompt-logprobs", type=int, default=5)
    p.add_argument("--enforce-eager", action="store_true")
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
    print(
        f"[{started}] loading vLLM model={args.model_key} tp={args.tensor_parallel_size} "
        f"max_len={args.max_model_len} rows={len(rows)}",
        flush=True,
    )
    llm = LLM(
        model=str(spec["path"]),
        tokenizer=str(spec["path"]),
        trust_remote_code=True,
        tensor_parallel_size=args.tensor_parallel_size,
        dtype=args.dtype,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        enforce_eager=args.enforce_eager,
    )
    tokenizer = llm.get_tokenizer()
    options = {
        "en": ([" Yes", "Yes", " yes", "yes"], [" No", "No", " no", "no"]),
        "zh": ([" 是", "是"], [" 否", "否", " 不", "不"]),
    }
    eval_plan: list[dict[str, Any]] = []
    scoring_items: list[tuple[int, str, str]] = []
    for row in rows:
        for mode in ("process_only", "training_candidate"):
            target = target_for(row, mode)
            if target is None:
                continue
            for prompt_lang in ("en", "zh"):
                prompt = prompt_for(row, prompt_lang, mode)
                eval_idx = len(eval_plan)
                yes_options, no_options = options[prompt_lang]
                eval_plan.append(
                    {
                        "row": row,
                        "mode": mode,
                        "prompt_lang": prompt_lang,
                        "target": target,
                        "yes_options": yes_options,
                        "no_options": no_options,
                    }
                )
                for option in yes_options + no_options:
                    scoring_items.append((eval_idx, option, prompt))
    scores = score_options_batched(
        llm,
        tokenizer,
        scoring_items,
        max_model_len=args.max_model_len,
        batch_size=args.batch_size,
        prompt_logprobs=args.prompt_logprobs,
    )
    eval_rows = []
    for eval_idx, plan in enumerate(eval_plan):
        row = plan["row"]
        yes_scored = [(scores[(eval_idx, option)], option) for option in plan["yes_options"]]
        no_scored = [(scores[(eval_idx, option)], option) for option in plan["no_options"]]
        yes_score, yes_option = max(yes_scored, key=lambda x: x[0])
        no_score, no_option = max(no_scored, key=lambda x: x[0])
        margin = yes_score - no_score
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
                "mode": plan["mode"],
                "prompt_lang": plan["prompt_lang"],
                "target": plan["target"],
                "pred": pred,
                "correct": pred == plan["target"],
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
        "backend": "vllm",
        "verifier_model_key": args.model_key,
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
