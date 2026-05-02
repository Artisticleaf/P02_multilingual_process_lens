#!/usr/bin/env python3
"""E49 official AIME/hard-task final-correct conditioning.

The no-gold variants estimate how often a model produces strict final-correct
hard-task traces under a fixed sampling budget.  The answer-anchor variant is
kept as an explicitly marked diagnostic and must not be used for prevalence.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from collections import Counter, defaultdict
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
    "answer_first_no_gold": (
        "Solve the following AIME-style problem yourself. First write one line `Final answer: <integer>`, "
        "then give a concise justification. No final answer is provided in the prompt.\n\nProblem: {problem}"
    ),
    "self_check": (
        "Solve the following AIME-style problem. After deriving an answer, do one brief self-check for the main trap, "
        "then end with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
    ),
    "answer_anchor": (
        "This is not a benchmark-performance run. A public final answer is provided only to condition a rationale. "
        "Write a concise mathematical solution that genuinely justifies the given answer. "
        "If a step is uncertain, say so rather than inventing it. End with exactly one line `Final answer: <integer>`.\n\n"
        "Problem: {problem}\nGiven final answer: {answer}"
    ),
    "thinking_boxed_neutral": (
        "Solve the following AIME-style problem carefully. Think through the reasoning, then give the final answer. "
        "Put the final integer answer inside exactly one LaTeX box at the end, like `\\boxed{{123}}`.\n\nProblem: {problem}"
    ),
    "thinking_boxed_answer_after": (
        "Solve the following AIME-style problem yourself. Think first. In the final visible response, put the final integer answer "
        "inside exactly one LaTeX box on the last line, like `\\boxed{{123}}`. If you include visible justification after thinking, keep it concise. "
        "No final answer is provided in the prompt.\n\nProblem: {problem}"
    ),
    "thinking_boxed_self_check": (
        "Solve the following AIME-style problem. Think through the solution, check the main trap once, then give the final answer. "
        "Put the final integer answer inside exactly one LaTeX box at the end, like `\\boxed{{123}}`.\n\nProblem: {problem}"
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


def extract_final_answer(text: str, *, allow_fallback: bool = False) -> tuple[str, bool, str]:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip(), True, "final_answer_line"
    boxed = list(re.finditer(r"\\boxed\s*\{\s*(-?\d+(?:\.\d+)?)\s*\}", text, flags=re.IGNORECASE))
    if boxed:
        return boxed[-1].group(1).strip(), True, "boxed_final_answer"
    if not allow_fallback:
        return "", False, "no_final_answer_line"
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


def render_prompt(tokenizer, spec: dict[str, Any], task: dict[str, Any], variant: str, thinking: bool) -> tuple[str, bool, bool, bool]:
    gold_in_prompt = variant == "answer_anchor"
    content = PROMPT_VARIANTS[variant].format(problem=task["en"], answer=task["answer"])
    use_chat = should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True, gold_in_prompt
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=thinking)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False, gold_in_prompt


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--tasks-yaml", default=str(PROJECT / "configs/e26_aime_hard_tasks.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E49_hard_task_conditioning_official"))
    p.add_argument("--variants", nargs="+", default=["neutral", "answer_first_no_gold", "self_check"])
    p.add_argument("--k", type=int, default=1)
    p.add_argument("--max-tasks", type=int, default=6)
    p.add_argument("--max-new-tokens", type=int, default=2048)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--thinking", choices=["auto", "true", "false"], default="auto")
    p.add_argument("--allow-final-fallback", action="store_true")
    p.add_argument("--checkpoint-jsonl", default="", help="Optional JSONL path for per-row checkpointing during generation")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260428)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    unknown = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")
    torch.manual_seed(args.seed)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    tasks = read_yaml(args.tasks_yaml)["tasks"][: args.max_tasks]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E49 hard-task conditioning", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    thinking = True if args.thinking == "auto" else (args.thinking == "true")

    jobs = []
    for task in tasks:
        for variant in args.variants:
            prompt, used_chat, add_special, gold_in_prompt = render_prompt(tok, spec, task, variant, thinking)
            for sample_idx in range(args.k):
                jobs.append({"task": task, "variant": variant, "sample_idx": sample_idx, "prompt": prompt, "used_chat": used_chat, "add_special": add_special, "gold_in_prompt": gold_in_prompt})

    rows = []
    checkpoint_path = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    if checkpoint_path:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text("", encoding="utf-8")
    for start in range(0, len(jobs), args.batch_size):
        batch = jobs[start : start + args.batch_size]
        add_special_values = {j["add_special"] for j in batch}
        if len(add_special_values) != 1:
            raise RuntimeError("Mixed add_special values in one batch")
        enc = tok([j["prompt"] for j in batch], return_tensors="pt", padding=True, add_special_tokens=batch[0]["add_special"]).to(device)
        with torch.no_grad():
            out = model.generate(
                **enc,
                do_sample=True,
                temperature=args.temperature,
                top_p=args.top_p,
                top_k=args.top_k,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=pad_token_id,
            )
        prompt_len = enc["input_ids"].shape[1]
        for j, seq in zip(batch, out):
            gen_ids = seq[prompt_len:]
            completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
            extracted, final_marker, extraction_method = extract_final_answer(completion, allow_fallback=args.allow_final_fallback)
            final_correct = normalize_answer(extracted) == normalize_answer(j["task"]["answer"])
            row = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "model_key": args.model_key,
                "task_id": j["task"]["id"],
                "problem": j["task"]["en"],
                "gold_answer": j["task"]["answer"],
                "trap_note_not_in_prompt": j["task"].get("trap", ""),
                "prompt_variant": j["variant"],
                "sample_idx": j["sample_idx"],
                "used_chat_template": j["used_chat"],
                "add_special_tokens": j["add_special"],
                "thinking": thinking,
                "gold_answer_in_prompt": j["gold_in_prompt"],
                "known_trap_note_in_prompt": False,
                "completion": completion,
                "extracted_final": extracted,
                "extraction_method": extraction_method,
                "final_marker_found": final_marker,
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
                "manual_final_correct": final_correct,
                "manual_process_valid": None,
                "manual_risk": "final_correct_needs_manual_process_audit" if final_correct else "not_final_correct",
                "is_acpi": False,
            }
            rows.append(row)
            if checkpoint_path:
                with checkpoint_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)

    by_variant = defaultdict(Counter)
    by_task = defaultdict(Counter)
    for r in rows:
        for bucket in (by_variant[r["prompt_variant"]], by_task[r["task_id"]]):
            bucket["n"] += 1
            bucket["final_correct"] += int(r["manual_final_correct"])
            bucket["gold_answer_in_prompt"] += int(r["gold_answer_in_prompt"])
            bucket["needs_manual_process_audit"] += int(r["manual_risk"] == "final_correct_needs_manual_process_audit")
    summary = {
        "n": len(rows),
        "final_correct": sum(r["manual_final_correct"] for r in rows),
        "not_final_correct": sum(not r["manual_final_correct"] for r in rows),
        "strict_final_marker_missing": sum(not r["final_marker_found"] for r in rows),
        "gold_answer_in_prompt_rows": sum(r["gold_answer_in_prompt"] for r in rows),
        "known_trap_note_in_prompt_rows": sum(r["known_trap_note_in_prompt"] for r in rows),
        "needs_manual_process_audit": sum(r["manual_risk"] == "final_correct_needs_manual_process_audit" for r in rows),
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
    }
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "prompt_variants": PROMPT_VARIANTS,
        "summary": summary,
        "rows": rows,
        "scope_note_en": "Rows with gold_answer_in_prompt=True are answer-anchor diagnostics, not natural prevalence.",
        "scope_note_zh": "gold_answer_in_prompt=True 的行是 answer-anchor 诊断，不是自然发生率。",
    }
    suffix = "_".join(args.variants)
    out = Path(args.out_dir) / f"{args.model_key}_e49_{suffix}_hard_task_conditioning.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", summary, flush=True)


if __name__ == "__main__":
    main()
