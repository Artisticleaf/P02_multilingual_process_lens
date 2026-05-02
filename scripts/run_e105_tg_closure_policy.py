#!/usr/bin/env python3
"""E105 Qwen thinking closure-policy probe.

E103 showed that Qwen thinking traces can contain the right number without
submitting an explicit final answer.  E105 tests whether that is mostly a
token-budget issue or a prompt/closure-policy issue.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


@dataclass(frozen=True)
class PolicySpec:
    policy_id: str
    max_new_tokens: int
    temperature: float
    top_p: float
    top_k: int
    prompt_template: str
    note_zh: str


POLICIES = {
    "free_think_8192": PolicySpec(
        policy_id="free_think_8192",
        max_new_tokens=8192,
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        prompt_template=(
            "Solve the following AIME-style problem carefully. Show the reasoning needed to justify the result. "
            "End with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
        ),
        note_zh="只把 TG token 上限从 4096 提到 8192，测试是不是单纯 token 不够。",
    ),
    "final_contract_8192": PolicySpec(
        policy_id="final_contract_8192",
        max_new_tokens=8192,
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        prompt_template=(
            "Solve the following AIME-style problem carefully. You must finish the response with a committed final answer. "
            "A response without an explicit final-answer line is invalid. When you are done checking, write exactly one final line "
            "`Final answer: <integer>` and stop; do not write anything after that line.\n\nProblem: {problem}"
        ),
        note_zh="8k token 加强最终提交契约，测试模型是否能主动收口。",
    ),
    "budgeted_final_4096": PolicySpec(
        policy_id="budgeted_final_4096",
        max_new_tokens=4096,
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        prompt_template=(
            "Solve the following AIME-style problem. Use at most 12 concise reasoning steps; avoid repeated re-checking. "
            "After those steps, commit to one answer. End with exactly one line `Final answer: <integer>` and stop.\n\n"
            "Problem: {problem}"
        ),
        note_zh="限制推理步数并要求提交，测试收口策略是否比单纯加 token 更有效。",
    ),
    "free_think_16384": PolicySpec(
        policy_id="free_think_16384",
        max_new_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        prompt_template=(
            "Solve the following AIME-style problem carefully. Show the reasoning needed to justify the result. "
            "End with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
        ),
        note_zh="无 wall-time cap，16k token，只测试单纯提高 token 上限是否让 TG 自然收口。",
    ),
    "final_contract_16384": PolicySpec(
        policy_id="final_contract_16384",
        max_new_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        prompt_template=(
            "Solve the following AIME-style problem carefully. You must finish the response with a committed final answer. "
            "A response without an explicit final-answer line is invalid. When you are done checking, write exactly one final line "
            "`Final answer: <integer>` and stop; do not write anything after that line.\n\nProblem: {problem}"
        ),
        note_zh="无 wall-time cap，16k token，加最终提交契约，测试 prompt 收口是否有效。",
    ),
    "budgeted_final_16384": PolicySpec(
        policy_id="budgeted_final_16384",
        max_new_tokens=16384,
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        prompt_template=(
            "Solve the following AIME-style problem. Use at most 12 concise reasoning steps; avoid repeated re-checking. "
            "After those steps, commit to one answer. End with exactly one line `Final answer: <integer>` and stop.\n\n"
            "Problem: {problem}"
        ),
        note_zh="无 wall-time cap，16k token，限制推理步数并要求提交。",
    ),
    "free_think_32768": PolicySpec(
        policy_id="free_think_32768",
        max_new_tokens=32768,
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        prompt_template=(
            "Solve the following AIME-style problem carefully. Show the reasoning needed to justify the result. "
            "End with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
        ),
        note_zh="无 wall-time cap，32k token 压力测试；可能受本机显存限制。",
    ),
    "final_contract_32768": PolicySpec(
        policy_id="final_contract_32768",
        max_new_tokens=32768,
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        prompt_template=(
            "Solve the following AIME-style problem carefully. You must finish the response with a committed final answer. "
            "A response without an explicit final-answer line is invalid. When you are done checking, write exactly one final line "
            "`Final answer: <integer>` and stop; do not write anything after that line.\n\nProblem: {problem}"
        ),
        note_zh="无 wall-time cap，32k token 加最终提交契约压力测试；可能受本机显存限制。",
    ),
}


def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    text = text.rstrip(".。,:;，；")
    if re.fullmatch(r"-?\d+\.0+", text):
        return str(int(float(text)))
    return text


def extract_final_answer(text: str, *, allow_fallback: bool) -> tuple[str, bool, str]:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip(), True, "final_answer_line"
    boxed = list(re.finditer(r"\\boxed\s*\{\s*(-?\d+(?:\.\d+)?)\s*\}", text, flags=re.IGNORECASE))
    if boxed:
        return boxed[-1].group(1).strip(), True, "boxed_final_answer"
    if not allow_fallback:
        return "", False, "no_explicit_final"
    phrase_lines = [
        line
        for line in text.splitlines()
        if re.search(
            r"\bfinal\s+answer\b|\b(?:the\s+)?(?:sum|answer|result)\s*(?:is|=|:)|\bsum\s+of[^\n=]{0,80}=",
            line,
            flags=re.IGNORECASE,
        )
    ]
    for line in reversed(phrase_lines):
        nums = re.findall(r"-?\d+(?:\.\d+)?", line)
        if nums:
            return nums[-1].strip(), False, "answer_phrase_line_last_number"
    fallback_patterns = [
        (r"(?:final\s+answer|answer|sum|result)\s*(?:is|=|:)\s*\$?\s*\\boxed\s*\{?\s*(-?\d+(?:\.\d+)?)", "boxed_answer_phrase"),
        (r"(?:therefore|thus|so)[^\n]{0,120}?(?:answer|sum|result)[^\n]{0,40}?(-?\d+(?:\.\d+)?)", "therefore_answer_phrase"),
    ]
    for pattern, method in fallback_patterns:
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if matches:
            return matches[-1].group(1).strip(), False, method
    tail = text[-320:]
    nums = re.findall(r"-?\d+(?:\.\d+)?", tail)
    return (nums[-1].strip() if nums else ""), False, "tail_last_number"


def repair_marker_count(text: str) -> int:
    return len(
        re.findall(
            r"\b(wait|however|but|mistake|check|recheck|re-check|instead|actually|on second thought|correction)\b|不过|但是|检查|错误|重新|修正",
            text,
            flags=re.IGNORECASE,
        )
    )


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def render_prompt(tokenizer, spec: dict[str, Any], task: dict[str, Any], policy: PolicySpec) -> tuple[str, bool, bool]:
    content = policy.prompt_template.format(problem=task["en"])
    use_chat = should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=True)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_27b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--tasks-yaml", default=str(PROJECT / "configs/e26_aime_hard_tasks.yaml"))
    p.add_argument(
        "--task-ids",
        nargs="+",
        default=["aime25_base_divisor_p1", "aime25_integer_pairs_quad_p4", "aime25_trapezoid_incircle_p6"],
    )
    p.add_argument("--policies", nargs="+", default=["free_think_8192", "final_contract_8192", "budgeted_final_4096"])
    p.add_argument("--k", type=int, default=1)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--max-time", type=float, default=900.0, help="Optional Transformers generate max_time in seconds per batch")
    p.add_argument("--out-dir", default=str(PROJECT / "results/E105_tg_closure_policy"))
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260429)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    unknown = sorted(set(args.policies) - set(POLICIES))
    if unknown:
        raise SystemExit(f"Unknown policies: {unknown}; available={sorted(POLICIES)}")
    torch.manual_seed(args.seed)

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    all_tasks = read_yaml(args.tasks_yaml)["tasks"]
    task_map = {t["id"]: t for t in all_tasks}
    missing_tasks = [tid for tid in args.task_ids if tid not in task_map]
    if missing_tasks:
        raise SystemExit(f"Unknown task ids: {missing_tasks}")
    tasks = [task_map[tid] for tid in args.task_ids]
    policies = [POLICIES[p] for p in args.policies]

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E105 TG closure-policy probe", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    jobs: list[dict[str, Any]] = []
    for policy in policies:
        for task in tasks:
            prompt, used_chat, add_special = render_prompt(tok, spec, task, policy)
            for sample_idx in range(args.k):
                jobs.append(
                    {
                        "policy": policy,
                        "task": task,
                        "sample_idx": sample_idx,
                        "prompt": prompt,
                        "used_chat": used_chat,
                        "add_special": add_special,
                    }
                )

    checkpoint_path = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    if checkpoint_path:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text("", encoding="utf-8")

    rows: list[dict[str, Any]] = []
    start = 0
    while start < len(jobs):
        batch = jobs[start : start + args.batch_size]
        # Keep generate kwargs homogeneous inside each batch.
        add_special_values = {j["add_special"] for j in batch}
        policy_values = {j["policy"].policy_id for j in batch}
        if len(add_special_values) != 1 or len(policy_values) != 1:
            batch = batch[:1]
        policy = batch[0]["policy"]
        enc = tok([j["prompt"] for j in batch], return_tensors="pt", padding=True, add_special_tokens=batch[0]["add_special"]).to(device)
        generate_kwargs = dict(
            **enc,
            do_sample=True,
            temperature=policy.temperature,
            top_p=policy.top_p,
            top_k=policy.top_k,
            max_new_tokens=policy.max_new_tokens,
            pad_token_id=pad_token_id,
        )
        if args.max_time and args.max_time > 0:
            generate_kwargs["max_time"] = args.max_time
        batch_t0 = time.monotonic()
        with torch.no_grad():
            out = model.generate(**generate_kwargs)
        batch_elapsed = time.monotonic() - batch_t0
        prompt_len = enc["input_ids"].shape[1]
        for j, seq in zip(batch, out):
            gen_ids = seq[prompt_len:]
            completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
            strict_final, explicit_final, strict_method = extract_final_answer(completion, allow_fallback=False)
            fallback_final, _, fallback_method = extract_final_answer(completion, allow_fallback=True)
            gold = j["task"]["answer"]
            strict_correct = explicit_final and normalize_answer(strict_final) == normalize_answer(gold)
            fallback_correct = bool(fallback_final) and normalize_answer(fallback_final) == normalize_answer(gold)
            row = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "experiment": "E105_tg_closure_policy",
                "model_key": args.model_key,
                "policy_id": j["policy"].policy_id,
                "policy_note_zh": j["policy"].note_zh,
                "thinking": True,
                "temperature": j["policy"].temperature,
                "top_p": j["policy"].top_p,
                "top_k": j["policy"].top_k,
                "max_new_tokens": j["policy"].max_new_tokens,
                "task_id": j["task"]["id"],
                "problem": j["task"]["en"],
                "gold_answer": gold,
                "trap_note_not_in_prompt": j["task"].get("trap", ""),
                "sample_idx": j["sample_idx"],
                "used_chat_template": j["used_chat"],
                "add_special_tokens": j["add_special"],
                "gold_answer_in_prompt": False,
                "known_trap_note_in_prompt": False,
                "completion": completion,
                "strict_extracted_final": strict_final,
                "strict_extraction_method": strict_method,
                "explicit_final_marker_found": explicit_final,
                "strict_final_correct": bool(strict_correct),
                "fallback_extracted_final": fallback_final,
                "fallback_extraction_method": fallback_method,
                "fallback_final_correct": bool(fallback_correct),
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= j["policy"].max_new_tokens),
                "batch_elapsed_seconds": round(batch_elapsed, 3),
                "max_time_seconds": args.max_time,
                "stop_reason_heuristic": (
                    "max_new_tokens"
                    if gen_ids.numel() >= j["policy"].max_new_tokens
                    else ("maybe_max_time" if args.max_time and batch_elapsed >= args.max_time * 0.95 else "model_stop_or_eos")
                ),
                "completion_chars": len(completion),
                "repair_marker_count": repair_marker_count(completion),
                "manual_audit_status": "needs_audit" if (strict_correct or fallback_correct) else "not_final_correct",
            }
            rows.append(row)
            if checkpoint_path:
                with checkpoint_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)
        start += len(batch)

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "policy_specs": {p.policy_id: p.__dict__ for p in policies},
        "summary": summarize_rows(rows),
        "rows": rows,
        "scope_note_zh": "E105 是 Qwen TG 收口策略小样本诊断；strict final 与 fallback 必须分开报告。",
        "scope_note_en": "E105 is a Qwen TG closure-policy diagnostic; strict and fallback correctness must be reported separately.",
    }
    out = Path(args.out_dir) / f"{args.model_key}_e105_tg_closure_policy.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True), flush=True)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy: dict[str, Counter[str]] = defaultdict(Counter)
    by_policy_task: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        for key, bucket in [
            (r["policy_id"], by_policy[r["policy_id"]]),
            (f"{r['policy_id']}|{r['task_id']}", by_policy_task[f"{r['policy_id']}|{r['task_id']}"]),
        ]:
            bucket["n"] += 1
            bucket["strict_final_correct"] += int(bool(r["strict_final_correct"]))
            bucket["fallback_final_correct"] += int(bool(r["fallback_final_correct"]))
            bucket["explicit_final_marker_found"] += int(bool(r["explicit_final_marker_found"]))
            bucket["hit_max_new_tokens"] += int(bool(r["hit_max_new_tokens"]))
            bucket["needs_audit"] += int(r["manual_audit_status"] == "needs_audit")
            bucket["generated_tokens_sum"] += int(r["generated_tokens"])
            bucket["repair_marker_sum"] += int(r["repair_marker_count"])
    def format_bucket(c: Counter[str]) -> dict[str, Any]:
        n = int(c["n"])
        return {
            "n": n,
            "strict_final_correct": int(c["strict_final_correct"]),
            "fallback_final_correct": int(c["fallback_final_correct"]),
            "explicit_final_marker_rate": (c["explicit_final_marker_found"] / n) if n else None,
            "hit_max_rate": (c["hit_max_new_tokens"] / n) if n else None,
            "needs_audit": int(c["needs_audit"]),
            "mean_generated_tokens": (c["generated_tokens_sum"] / n) if n else None,
            "mean_repair_markers": (c["repair_marker_sum"] / n) if n else None,
        }
    return {
        "n": len(rows),
        "by_policy": {k: format_bucket(v) for k, v in sorted(by_policy.items())},
        "by_policy_task": {k: format_bucket(v) for k, v in sorted(by_policy_task.items())},
        "leakage_audit": {
            "gold_answer_in_prompt_rows": sum(int(bool(r["gold_answer_in_prompt"])) for r in rows),
            "known_trap_note_in_prompt_rows": sum(int(bool(r["known_trap_note_in_prompt"])) for r in rows),
            "passed": all(not r["gold_answer_in_prompt"] and not r["known_trap_note_in_prompt"] for r in rows),
        },
    }


if __name__ == "__main__":
    main()
