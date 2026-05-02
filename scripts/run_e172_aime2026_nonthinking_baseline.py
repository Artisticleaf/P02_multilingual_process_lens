#!/usr/bin/env python3
"""Run E172 AIME 2026 non-thinking baseline generations."""
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
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))

import run_e49_hard_task_conditioning_official as e49  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

TASK_BANK = PROJECT / "data/processed/e172_aime2026_matharena_task_bank_20260502.jsonl"
OUT_DIR = PROJECT / "results/E172_aime2026_hidden_gate"

PROMPT_TEMPLATE = (
    "Solve the following AIME 2026 problem carefully in non-thinking mode. "
    "Show only the reasoning needed to justify the answer; do not give the final answer before the reasoning. "
    "End with exactly one line `Final answer: <integer>`.\n\n"
    "Problem: {problem}"
)

BOXED_RE = re.compile(r"\\boxed\s*\{\s*(-?\d+(?:\.\d+)?)\s*\}", re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    return load_jsonl(path) if path.exists() else []


def canonical_extracted_answer(text: str) -> str:
    boxed = list(BOXED_RE.finditer(text))
    if boxed:
        return boxed[-1].group(1).strip()
    simple_box = re.fullmatch(r"\s*\\boxed\s*\{\s*([^}]+?)\s*\}\s*\.?\s*", text, flags=re.IGNORECASE)
    if simple_box:
        return simple_box.group(1).strip()
    return text.strip()


def is_complete_checkpoint_row(row: dict[str, Any]) -> bool:
    return bool(row.get("final_marker_found")) and not bool(row.get("hit_max_new_tokens"))


def load_complete_resume_rows(path_text: str) -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    stats: Counter[str] = Counter()
    complete: dict[str, dict[str, Any]] = {}
    if not path_text:
        return complete, stats
    path = Path(path_text)
    rows = load_jsonl_if_exists(path)
    stats["rows_seen"] = len(rows)
    for row in rows:
        if is_complete_checkpoint_row(row):
            retained = dict(row)
            retained["retained_from_resume_checkpoint"] = True
            retained["resume_source_checkpoint"] = str(path)
            retained["resume_policy"] = "kept_complete_final_marker_and_not_hit_max"
            complete[row["task_id"]] = retained
            stats["complete_rows"] += 1
        else:
            stats["incomplete_rows_to_rerun"] += 1
    stats["unique_complete_jobs"] = len(complete)
    return complete, stats


def render_chat(tokenizer, spec: dict[str, Any], content: str) -> tuple[str, bool, bool]:
    use_chat = e49.should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False


def select_tasks(tasks: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    task_ids = set(args.task_ids or [])
    out = [t for t in tasks if not task_ids or t["task_id"] in task_ids or str(t["problem_idx"]) in task_ids]
    out = sorted(out, key=lambda t: int(t["problem_idx"]))
    if args.max_tasks > 0:
        out = out[: args.max_tasks]
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--task-bank", default=str(TASK_BANK))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--task-ids", nargs="*", default=[])
    p.add_argument("--max-tasks", type=int, default=0)
    p.add_argument("--max-new-tokens", type=int, default=16384)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--top-k", type=int, default=0)
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--resume-from-checkpoint", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--tag", default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    tasks = select_tasks(load_jsonl(Path(args.task_bank)), args)
    if not tasks:
        raise SystemExit("No E172 AIME2026 tasks selected")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E172 AIME2026 baseline tasks={len(tasks)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    jobs = []
    for task in tasks:
        content = PROMPT_TEMPLATE.format(problem=task["problem"])
        prompt, used_chat, add_special = render_chat(tok, spec, content)
        jobs.append({"task": task, "content": content, "prompt": prompt, "used_chat": used_chat, "add_special": add_special})

    resume_complete, resume_stats = load_complete_resume_rows(args.resume_from_checkpoint)
    out_rows: list[dict[str, Any]] = []
    pending = []
    for job in jobs:
        task_id = job["task"]["task_id"]
        if task_id in resume_complete:
            out_rows.append(resume_complete[task_id])
        else:
            pending.append(job)

    checkpoint = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    if checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text("", encoding="utf-8")
        for row in out_rows:
            with checkpoint.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    for start in range(0, len(pending), args.batch_size):
        batch = pending[start : start + args.batch_size]
        add_values = {job["add_special"] for job in batch}
        if len(add_values) != 1:
            raise RuntimeError("Mixed add_special values")
        enc = tok([job["prompt"] for job in batch], return_tensors="pt", padding=True, add_special_tokens=batch[0]["add_special"]).to(device)
        gen_kwargs = dict(max_new_tokens=args.max_new_tokens, pad_token_id=pad_token_id)
        if args.temperature > 0:
            gen_kwargs.update(dict(do_sample=True, temperature=args.temperature, top_p=args.top_p, top_k=args.top_k))
        else:
            gen_kwargs.update(dict(do_sample=False))
        with torch.no_grad():
            seqs = model.generate(**enc, **gen_kwargs)
        prompt_len = enc["input_ids"].shape[1]
        for job, seq in zip(batch, seqs):
            task = job["task"]
            gen_ids = seq[prompt_len:]
            completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
            extracted_raw, marker, method = e49.extract_final_answer(completion, allow_fallback=True)
            extracted = canonical_extracted_answer(extracted_raw)
            final_correct = e49.normalize_answer(extracted) == e49.normalize_answer(str(task["gold_answer"]))
            rec = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "experiment": "E172_aime2026_nonthinking_baseline",
                "model_key": args.model_key,
                "task_id": task["task_id"],
                "source_task_id": task.get("source_task_id", ""),
                "problem_idx": int(task["problem_idx"]),
                "task_source": task["task_source"],
                "family": task["family"],
                "problem": task["problem"],
                "gold_answer": task["gold_answer"],
                "dataset_repo": task.get("dataset_repo", ""),
                "dataset_sha": task.get("dataset_sha", ""),
                "thinking": False,
                "prompt_variant": "baseline_nonthinking_aime2026",
                "used_chat_template": job["used_chat"],
                "chat_template_enable_thinking_false_requested": bool(job["used_chat"]),
                "gold_answer_in_prompt": False,
                "dataset_metadata_in_prompt": False,
                "hidden_signal_in_prompt": False,
                "prompt_content": job["content"],
                "prompt_tokens": int(enc["input_ids"].shape[1]),
                "completion": completion,
                "extracted_final": extracted,
                "extracted_final_raw": extracted_raw,
                "extraction_method": method,
                "final_marker_found": marker,
                "manual_final_correct": final_correct,
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
                "retained_from_resume_checkpoint": False,
                "resume_source_checkpoint": args.resume_from_checkpoint or "",
                "resume_policy": "generated_this_run",
            }
            out_rows.append(rec)
            if checkpoint:
                with checkpoint.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated/resumed {len(out_rows)}/{len(jobs)}", flush=True)

    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    for row in out_rows:
        bucket = by_task[row["task_id"]]
        bucket["n"] += 1
        bucket["manual_final_correct"] += int(row["manual_final_correct"])
        bucket["final_marker_found"] += int(row["final_marker_found"])
        bucket["hit_max"] += int(row["hit_max_new_tokens"])
        bucket["completion_tokens"] += int(row["generated_tokens"])
    summary = {
        "jobs": len(out_rows),
        "tasks": len(tasks),
        "manual_final_correct": sum(int(r["manual_final_correct"]) for r in out_rows),
        "accuracy": sum(int(r["manual_final_correct"]) for r in out_rows) / len(out_rows) if out_rows else None,
        "final_marker_found": sum(int(r["final_marker_found"]) for r in out_rows),
        "hit_max": sum(int(r["hit_max_new_tokens"]) for r in out_rows),
        "completion_tokens": sum(int(r["generated_tokens"]) for r in out_rows),
        "leakage_audit": {
            "gold_answer_in_prompt_rows": sum(int(r["gold_answer_in_prompt"]) for r in out_rows),
            "dataset_metadata_in_prompt_rows": sum(int(r["dataset_metadata_in_prompt"]) for r in out_rows),
            "hidden_signal_in_prompt_rows": sum(int(r["hidden_signal_in_prompt"]) for r in out_rows),
        },
        "resume": {
            "resume_from_checkpoint": args.resume_from_checkpoint,
            "resume_stats": dict(resume_stats),
            "retained_complete_jobs": sum(int(bool(r.get("retained_from_resume_checkpoint"))) for r in out_rows),
            "generated_this_run_jobs": sum(int(not bool(r.get("retained_from_resume_checkpoint"))) for r in out_rows),
        },
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
    }
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "args": vars(args),
        "prompt_template": PROMPT_TEMPLATE,
        "summary": summary,
        "rows": out_rows,
    }
    tag = f"_{args.tag}" if args.tag else ""
    out_path = Path(args.out_dir) / f"{args.model_key}_e172_aime2026_baseline{tag}.json"
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
