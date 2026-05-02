#!/usr/bin/env python3
"""E124 broad no-gold hard-task harvesting for unrepaired ACPI candidates."""
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
    "answer_first_no_gold": (
        "Solve the following math problem yourself. First write one line `Final answer: <integer>`, "
        "then give a concise justification. No final answer is provided in the prompt.\n\nProblem: {problem}"
    ),
    "neutral": (
        "Solve the following math problem carefully. Show the reasoning needed to justify the result. "
        "End with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
    ),
    "self_check": (
        "Solve the following math problem. After deriving an answer, do one brief self-check for the main trap, "
        "then end with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
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


def extract_final_answer(text: str, *, allow_fallback: bool = True) -> tuple[str, bool, str]:
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
        if re.search(r"\bfinal\s+answer\b|\b(?:the\s+)?(?:sum|answer|result|count)\s*(?:is|=|:)", line, flags=re.IGNORECASE)
    ]
    for line in reversed(phrase_lines):
        nums = re.findall(r"-?\d+(?:\.\d+)?", line)
        if nums:
            return nums[-1].strip(), False, "answer_phrase_line_last_number"
    nums = re.findall(r"-?\d+(?:\.\d+)?", text[-320:])
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--tasks-yaml", default=str(PROJECT / "configs/e124_broad_unrepaired_harvest_tasks.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E124_broad_unrepaired_harvest"))
    p.add_argument("--variants", nargs="+", default=["answer_first_no_gold"])
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--max-tasks", type=int, default=0)
    p.add_argument("--max-new-tokens", type=int, default=4096)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--thinking", choices=["true", "false"], default="false")
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260430)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    unknown = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")
    torch.manual_seed(args.seed)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    tasks = read_yaml(args.tasks_yaml)["tasks"]
    if args.max_tasks:
        tasks = tasks[: args.max_tasks]
    thinking = args.thinking == "true"
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E124 broad harvest", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    jobs = []
    for task in tasks:
        for variant in args.variants:
            prompt, used_chat, add_special = render_prompt(tok, spec, task, variant, thinking)
            for sample_idx in range(args.k):
                jobs.append({"task": task, "variant": variant, "sample_idx": sample_idx, "prompt": prompt, "used_chat": used_chat, "add_special": add_special})

    checkpoint = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    if checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text("", encoding="utf-8")
    rows = []
    for start in range(0, len(jobs), args.batch_size):
        batch = jobs[start : start + args.batch_size]
        add_values = {j["add_special"] for j in batch}
        if len(add_values) != 1:
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
        for job, seq in zip(batch, out):
            gen_ids = seq[prompt_len:]
            completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
            strict, strict_marker, strict_method = extract_final_answer(completion, allow_fallback=False)
            fallback, _fallback_marker, fallback_method = extract_final_answer(completion, allow_fallback=True)
            task = job["task"]
            row = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "model_key": args.model_key,
                "task_id": task["id"],
                "task_family": task.get("family"),
                "problem": task["en"],
                "gold_answer": task["answer"],
                "trap_note_not_in_prompt": task.get("trap", ""),
                "prompt_variant": job["variant"],
                "sample_idx": job["sample_idx"],
                "used_chat_template": job["used_chat"],
                "add_special_tokens": job["add_special"],
                "thinking": thinking,
                "gold_answer_in_prompt": False,
                "known_trap_note_in_prompt": False,
                "completion": completion,
                "strict_extracted_final": strict,
                "strict_extraction_method": strict_method,
                "strict_final_marker_found": strict_marker,
                "strict_final_correct": bool(strict_marker and normalize_answer(strict) == normalize_answer(task["answer"])),
                "fallback_extracted_final": fallback,
                "fallback_extraction_method": fallback_method,
                "fallback_final_correct": bool(fallback and normalize_answer(fallback) == normalize_answer(task["answer"])),
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
                "manual_audit_status": "needs_audit" if (strict_marker and normalize_answer(strict) == normalize_answer(task["answer"])) or (fallback and normalize_answer(fallback) == normalize_answer(task["answer"])) else "not_final_correct",
                "manual_process_valid_strict": None,
                "manual_process_valid_repaired": None,
                "manual_acpi_strict": None,
                "manual_repair_present": None,
                "manual_acpi_unrepaired": None,
            }
            rows.append(row)
            if checkpoint:
                with checkpoint.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"E124 generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)

    by_model = Counter()
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_model["generated"] += 1
        by_model["strict_final_correct"] += int(row["strict_final_correct"])
        by_model["fallback_final_correct"] += int(row["fallback_final_correct"])
        by_model["hit_max"] += int(row["hit_max_new_tokens"])
        for bucket in (by_family[row["task_family"]], by_task[row["task_id"]]):
            bucket["generated"] += 1
            bucket["strict_final_correct"] += int(row["strict_final_correct"])
            bucket["fallback_final_correct"] += int(row["fallback_final_correct"])
            bucket["hit_max"] += int(row["hit_max_new_tokens"])
    result = {
        "experiment": "E124_broad_unrepaired_harvest",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "prompt_variants": PROMPT_VARIANTS,
        "summary": {
            "model": dict(by_model),
            "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
            "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
            "gold_answer_in_prompt_rows": 0,
            "known_trap_note_in_prompt_rows": 0,
        },
        "rows": rows,
        "scope_note_zh": "E124 是 no-gold broad-task 自然采样；gold/trap 只在元数据中供离线过滤和人审使用，不进入 prompt。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_".join(args.variants)
    out_path = out_dir / f"{args.model_key}_e124_{suffix}_broad_unrepaired_harvest.json"
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print("SUMMARY", json.dumps(result["summary"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
