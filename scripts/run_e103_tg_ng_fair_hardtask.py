#!/usr/bin/env python3
"""E103 TG/NG hard-task fairness probe.

This is a deliberately small generation experiment.  It keeps thinking-mode
and non-thinking-mode rows in one file, but reports strict final answers,
fallback extractions, and hit-max separately so we do not turn an unfinished
thinking trace into a clean final decision.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
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


PROMPT_VARIANTS = {
    "neutral": (
        "Solve the following AIME-style problem carefully. Show the reasoning needed to justify the result. "
        "End with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
    ),
    "self_check": (
        "Solve the following AIME-style problem. After deriving an answer, do one brief self-check for the main trap, "
        "then end with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
    ),
    "answer_first_no_gold": (
        "Solve the following AIME-style problem yourself. First write one line `Final answer: <integer>`, "
        "then give a concise justification. No final answer is provided in the prompt.\n\nProblem: {problem}"
    ),
}


@dataclass(frozen=True)
class ModeSpec:
    mode_label: str
    thinking: bool
    temperature: float
    top_p: float
    top_k: int
    sampling_note: str


def default_mode_specs(model_key: str) -> list[ModeSpec]:
    """Return the default E103 mode list.

    `TG_official` uses the local E91 thinking-parameter audit. `NG_baseline`
    preserves the earlier E49 direct-generation settings.  `NG_matched_sampling`
    is included to separate thinking-template effects from sampling-temperature
    effects without changing the scientific headline.
    """
    if "qwen35" in model_key:
        return [
            ModeSpec("NG_baseline", False, 0.7, 0.95, 50, "E49 non-thinking baseline"),
            ModeSpec("NG_matched_sampling", False, 1.0, 0.95, 20, "same sampling as Qwen thinking recommendation"),
            ModeSpec("TG_official", True, 1.0, 0.95, 20, "E91 Qwen thinking recommendation without unsupported presence_penalty"),
        ]
    if "gemma" in model_key:
        return [
            ModeSpec("NG_baseline", False, 0.7, 0.95, 50, "E49 non-thinking baseline"),
            ModeSpec("TG_official", True, 1.0, 0.95, 64, "E91 Gemma thinking recommendation"),
        ]
    return [
        ModeSpec("NG_baseline", False, 0.7, 0.95, 50, "E49 non-thinking baseline"),
        ModeSpec("TG_official", True, 1.0, 0.95, 50, "generic thinking mode; model-card sampling not specialized"),
    ]


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


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def render_prompt(tokenizer, spec: dict[str, Any], task: dict[str, Any], variant: str, thinking: bool) -> tuple[str, bool, bool]:
    content = PROMPT_VARIANTS[variant].format(problem=task["en"])
    use_chat = should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=thinking)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False


def repair_marker_count(text: str) -> int:
    return len(
        re.findall(
            r"\b(wait|however|but|mistake|check|recheck|re-check|instead|actually|on second thought|correction)\b|不过|但是|检查|错误|重新|修正",
            text,
            flags=re.IGNORECASE,
        )
    )


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
    p.add_argument("--variants", nargs="+", default=["neutral", "self_check", "answer_first_no_gold"])
    p.add_argument("--modes", nargs="+", default=["NG_baseline", "NG_matched_sampling", "TG_official"])
    p.add_argument("--k", type=int, default=1)
    p.add_argument("--max-new-tokens", type=int, default=4096)
    p.add_argument("--max-time", type=float, default=0.0, help="Optional Transformers generate max_time in seconds per batch")
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--out-dir", default=str(PROJECT / "results/E103_tg_ng_fair_hardtask"))
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260429)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    unknown_variants = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown_variants:
        raise SystemExit(f"Unknown variants: {unknown_variants}")
    torch.manual_seed(args.seed)

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    all_tasks = read_yaml(args.tasks_yaml)["tasks"]
    task_map = {t["id"]: t for t in all_tasks}
    missing_tasks = [tid for tid in args.task_ids if tid not in task_map]
    if missing_tasks:
        raise SystemExit(f"Unknown task ids: {missing_tasks}")
    tasks = [task_map[tid] for tid in args.task_ids]

    mode_map = {m.mode_label: m for m in default_mode_specs(args.model_key)}
    missing_modes = [m for m in args.modes if m not in mode_map]
    if missing_modes:
        raise SystemExit(f"Unknown modes for {args.model_key}: {missing_modes}; available={sorted(mode_map)}")
    modes = [mode_map[m] for m in args.modes]

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E103 TG/NG fairness probe", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    jobs: list[dict[str, Any]] = []
    for mode in modes:
        for task in tasks:
            for variant in args.variants:
                prompt, used_chat, add_special = render_prompt(tok, spec, task, variant, mode.thinking)
                for sample_idx in range(args.k):
                    jobs.append(
                        {
                            "mode": mode,
                            "task": task,
                            "variant": variant,
                            "sample_idx": sample_idx,
                            "prompt": prompt,
                            "used_chat": used_chat,
                            "add_special": add_special,
                        }
                    )

    rows: list[dict[str, Any]] = []
    checkpoint_path = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    if checkpoint_path:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text("", encoding="utf-8")

    start = 0
    while start < len(jobs):
        batch = jobs[start : start + args.batch_size]
        add_special_values = {j["add_special"] for j in batch}
        mode_values = {j["mode"].mode_label for j in batch}
        # Keep generate kwargs homogeneous inside each batch.
        if len(add_special_values) != 1 or len(mode_values) != 1:
            batch = batch[:1]
        mode = batch[0]["mode"]
        enc = tok([j["prompt"] for j in batch], return_tensors="pt", padding=True, add_special_tokens=batch[0]["add_special"]).to(device)
        generate_kwargs = dict(
            **enc,
            do_sample=True,
            temperature=mode.temperature,
            top_p=mode.top_p,
            top_k=mode.top_k,
            max_new_tokens=args.max_new_tokens,
            pad_token_id=pad_token_id,
        )
        if args.max_time and args.max_time > 0:
            generate_kwargs["max_time"] = args.max_time
        with torch.no_grad():
            out = model.generate(**generate_kwargs)
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
                "experiment": "E103_tg_ng_fair_hardtask",
                "model_key": args.model_key,
                "mode_label": j["mode"].mode_label,
                "thinking": j["mode"].thinking,
                "temperature": j["mode"].temperature,
                "top_p": j["mode"].top_p,
                "top_k": j["mode"].top_k,
                "sampling_note": j["mode"].sampling_note,
                "task_id": j["task"]["id"],
                "problem": j["task"]["en"],
                "gold_answer": gold,
                "trap_note_not_in_prompt": j["task"].get("trap", ""),
                "prompt_variant": j["variant"],
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
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
                "completion_chars": len(completion),
                "repair_marker_count": repair_marker_count(completion),
                "manual_process_valid_strict": None,
                "manual_process_valid_repaired": None,
                "manual_acpi_strict": None,
                "manual_repair_present": None,
                "manual_acpi_unrepaired": None,
                "manual_audit_status": "needs_audit" if (strict_correct or fallback_correct) else "not_final_correct",
            }
            rows.append(row)
            if checkpoint_path:
                with checkpoint_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)
        start += len(batch)

    summary = summarize_rows(rows)
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "prompt_variants": {k: PROMPT_VARIANTS[k] for k in args.variants},
        "mode_specs": [m.__dict__ for m in modes],
        "summary": summary,
        "rows": rows,
        "scope_note_zh": "E103 是小样本 TG/NG 公平对照；strict_final_correct 与 fallback_final_correct 必须分开报告。",
        "scope_note_en": "E103 is a small TG/NG fairness probe; strict and fallback correctness must be reported separately.",
    }
    out = Path(args.out_dir) / f"{args.model_key}_e103_tg_ng_fair_hardtask.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    by_mode_variant: dict[str, Counter[str]] = defaultdict(Counter)
    by_mode_task: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        keys = [
            r["mode_label"],
            f"{r['mode_label']}|{r['prompt_variant']}",
            f"{r['mode_label']}|{r['task_id']}",
        ]
        buckets = [by_mode[keys[0]], by_mode_variant[keys[1]], by_mode_task[keys[2]]]
        for bucket in buckets:
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
        "by_mode": {k: format_bucket(v) for k, v in sorted(by_mode.items())},
        "by_mode_variant": {k: format_bucket(v) for k, v in sorted(by_mode_variant.items())},
        "by_mode_task": {k: format_bucket(v) for k, v in sorted(by_mode_task.items())},
        "leakage_audit": {
            "gold_answer_in_prompt_rows": sum(int(bool(r["gold_answer_in_prompt"])) for r in rows),
            "known_trap_note_in_prompt_rows": sum(int(bool(r["known_trap_note_in_prompt"])) for r in rows),
            "passed": all(not r["gold_answer_in_prompt"] and not r["known_trap_note_in_prompt"] for r in rows),
        },
    }


if __name__ == "__main__":
    main()
