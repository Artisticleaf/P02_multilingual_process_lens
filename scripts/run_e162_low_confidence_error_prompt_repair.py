#!/usr/bin/env python3
"""Run E162 low-confidence truncation plus error-prompt repair probes."""
from __future__ import annotations

import argparse
import json
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))

import run_e49_hard_task_conditioning_official as e49  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

CASE_BANK = PROJECT / "data/processed/e162_low_confidence_error_prompt_cases_20260501.jsonl"
OUT_DIR = PROJECT / "results/E162_low_confidence_error_prompt_repair"

PROMPT_VARIANTS = {
    "baseline_regenerate": (
        "Solve the following problem carefully. Do not give the final answer before the reasoning. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}"
    ),
    "prefix_continue": (
        "Continue the partial solution below. Do not restart unless the partial solution itself requires revision. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "generic_error_prompt": (
        "A hidden monitor raised a low-confidence warning somewhere in the partial solution below. "
        "Recheck the partial solution from the original problem, correct it if needed, and continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "localized_error_prompt": (
        "A hidden monitor flagged this visible span as potentially abnormal: `{localized_span}`. "
        "{localized_hint} Correct the local step if needed, then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "oracle_error_prompt": (
        "A hidden monitor flagged this visible span as abnormal: `{localized_span}`. "
        "Audit note: {oracle_hint} Correct the local step if needed, then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "random_location_prompt": (
        "A hidden monitor flagged this visible span as potentially abnormal: `{random_span}`. "
        "Recheck only that location first; avoid changing unrelated correct steps. Then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return load_jsonl(path)


def job_key(case_id: str, variant: str) -> tuple[str, str]:
    return (case_id, variant)


def is_complete_checkpoint_row(row: dict[str, Any]) -> bool:
    return bool(row.get("final_marker_found")) and not bool(row.get("hit_max_new_tokens"))


def load_complete_resume_rows(path_text: str) -> tuple[dict[tuple[str, str], dict[str, Any]], Counter[str]]:
    stats: Counter[str] = Counter()
    complete: dict[tuple[str, str], dict[str, Any]] = {}
    if not path_text:
        return complete, stats
    path = Path(path_text)
    rows = load_jsonl_if_exists(path)
    stats["rows_seen"] = len(rows)
    for row in rows:
        key = job_key(row["case_id"], row["prompt_variant"])
        if is_complete_checkpoint_row(row):
            retained = dict(row)
            retained["retained_from_resume_checkpoint"] = True
            retained["resume_source_checkpoint"] = str(path)
            retained["resume_policy"] = "kept_complete_final_marker_and_not_hit_max"
            complete[key] = retained
            stats["complete_rows"] += 1
        else:
            stats["incomplete_rows_to_rerun"] += 1
    stats["unique_complete_jobs"] = len(complete)
    return complete, stats


def render_content(row: dict[str, Any], variant: str) -> str:
    return PROMPT_VARIANTS[variant].format(
        problem=row["problem"],
        prefix=row["prefix_text"],
        localized_span=row.get("localized_span") or row.get("manual_error_span") or "NONE",
        localized_hint=row.get("localized_hint") or "",
        oracle_hint=row.get("oracle_hint") or "",
        random_span=row.get("random_location_span") or "NONE",
    )


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


def select_cases(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    case_ids = set(args.case_ids or [])
    case_types = set(args.case_types or [])
    families = set(args.families or [])
    out = [
        r
        for r in rows
        if (not case_ids or r["case_id"] in case_ids)
        and (not case_types or r["case_type"] in case_types)
        and (not families or r["family"] in families)
    ]
    out = sorted(out, key=lambda r: (r["case_type"], r["family"], r["case_id"]))
    if args.max_cases > 0:
        out = out[: args.max_cases]
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--case-bank", default=str(CASE_BANK))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--variants", nargs="+", default=list(PROMPT_VARIANTS))
    p.add_argument("--case-ids", nargs="*", default=[])
    p.add_argument("--case-types", nargs="*", default=[])
    p.add_argument("--families", nargs="*", default=[])
    p.add_argument("--max-cases", type=int, default=0)
    p.add_argument("--max-new-tokens", type=int, default=1024)
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
    import torch

    args = parse_args()
    unknown = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")
    rows = select_cases(load_jsonl(Path(args.case_bank)), args)
    if not rows:
        raise SystemExit("No E162 cases selected")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E162 cases={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    all_jobs = []
    for row in rows:
        for variant in args.variants:
            content = render_content(row, variant)
            prompt, used_chat, add_special = render_chat(tok, spec, content)
            all_jobs.append({"row": row, "variant": variant, "content": content, "prompt": prompt, "used_chat": used_chat, "add_special": add_special})

    resume_complete, resume_stats = load_complete_resume_rows(args.resume_from_checkpoint)
    jobs = []
    out_rows = []
    for job in all_jobs:
        key = job_key(job["row"]["case_id"], job["variant"])
        if key in resume_complete:
            out_rows.append(resume_complete[key])
        else:
            jobs.append(job)

    checkpoint = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    if checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text("", encoding="utf-8")
        if out_rows:
            with checkpoint.open("a", encoding="utf-8") as f:
                for row in out_rows:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    if args.resume_from_checkpoint:
        print(
            "RESUME "
            + json.dumps(
                {
                    "resume_from_checkpoint": args.resume_from_checkpoint,
                    "total_jobs": len(all_jobs),
                    "retained_complete_jobs": len(out_rows),
                    "jobs_to_run": len(jobs),
                    "resume_stats": dict(resume_stats),
                    "policy": "rerun missing rows and rows without final marker or rows that hit max_new_tokens",
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            flush=True,
        )

    for start in range(0, len(jobs), args.batch_size):
        batch = jobs[start : start + args.batch_size]
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
            gen_ids = seq[prompt_len:]
            completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
            extracted, marker, method = e49.extract_final_answer(completion, allow_fallback=True)
            final_correct = e49.normalize_answer(extracted) == e49.normalize_answer(str(job["row"]["gold_answer"]))
            source_answer_repeated = e49.normalize_answer(extracted) == e49.normalize_answer(str(job["row"].get("source_extracted_final") or ""))
            rec = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "experiment": "E162_low_confidence_error_prompt_repair",
                "model_key": args.model_key,
                "case_id": job["row"]["case_id"],
                "case_type": job["row"]["case_type"],
                "task_id": job["row"]["task_id"],
                "family": job["row"]["family"],
                "prompt_variant": job["variant"],
                "thinking": False,
                "problem": job["row"]["problem"],
                "gold_answer": job["row"]["gold_answer"],
                "source_model_key": job["row"]["source_model_key"],
                "source_extracted_final": job["row"].get("source_extracted_final") or "",
                "source_final_correct": bool(job["row"]["source_final_correct"]),
                "source_process_valid_strict": bool(job["row"]["source_process_valid_strict"]),
                "manual_error_span_offline": job["row"].get("manual_error_span") or "",
                "localized_span_in_prompt": job["row"].get("localized_span") if job["variant"] in {"localized_error_prompt", "oracle_error_prompt"} else "",
                "random_span_in_prompt": job["row"].get("random_location_span") if job["variant"] == "random_location_prompt" else "",
                "oracle_hint_in_prompt": job["row"].get("oracle_hint") if job["variant"] == "oracle_error_prompt" else "",
                "gold_answer_in_prompt": False,
                "manual_label_in_prompt": False,
                "used_chat_template": job["used_chat"],
                "chat_template_enable_thinking_false_requested": bool(job["used_chat"]),
                "retained_from_resume_checkpoint": False,
                "resume_source_checkpoint": args.resume_from_checkpoint or "",
                "resume_policy": "generated_this_run",
                "prompt_content": job["content"],
                "completion": completion,
                "extracted_final": extracted,
                "extraction_method": method,
                "final_marker_found": marker,
                "manual_final_correct": final_correct,
                "source_answer_repeated": source_answer_repeated,
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
            }
            out_rows.append(rec)
            if checkpoint:
                with checkpoint.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated/resumed {len(out_rows)}/{len(all_jobs)}", flush=True)

    by_slice: dict[str, Counter[str]] = defaultdict(Counter)
    for r in out_rows:
        for key in [
            "all::all",
            f"prompt::{r['prompt_variant']}",
            f"case_type::{r['case_type']}",
            f"family::{r['family']}",
        ]:
            by_slice[key]["n"] += 1
            by_slice[key]["manual_final_correct"] += int(r["manual_final_correct"])
            by_slice[key]["source_answer_repeated"] += int(r["source_answer_repeated"])
            by_slice[key]["final_marker_found"] += int(r["final_marker_found"])
            by_slice[key]["hit_max"] += int(r["hit_max_new_tokens"])
    summary = {
        "jobs": len(out_rows),
        "cases": len(rows),
        "manual_final_correct": sum(int(r["manual_final_correct"]) for r in out_rows),
        "source_answer_repeated": sum(int(r["source_answer_repeated"]) for r in out_rows),
        "final_marker_found": sum(int(r["final_marker_found"]) for r in out_rows),
        "hit_max": sum(int(r["hit_max_new_tokens"]) for r in out_rows),
        "resume": {
            "resume_from_checkpoint": args.resume_from_checkpoint,
            "resume_stats": dict(resume_stats),
            "total_jobs": len(all_jobs),
            "retained_complete_jobs": sum(int(bool(r.get("retained_from_resume_checkpoint"))) for r in out_rows),
            "generated_this_run_jobs": sum(int(not bool(r.get("retained_from_resume_checkpoint"))) for r in out_rows),
            "policy": "Rows with final_marker_found=true and hit_max_new_tokens=false are retained; missing, no-final, or hit-max rows are rerun.",
        },
        "leakage_audit": {
            "gold_answer_in_prompt_rows": sum(int(r["gold_answer_in_prompt"]) for r in out_rows),
            "manual_label_in_prompt_rows": sum(int(r["manual_label_in_prompt"]) for r in out_rows),
            "oracle_hint_rows": sum(int(bool(r["oracle_hint_in_prompt"])) for r in out_rows),
            "note": "Oracle condition may expose the audited local correction cue, but never the final answer.",
        },
        "by_slice": {k: dict(v) for k, v in sorted(by_slice.items())},
    }
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "args": vars(args),
        "prompt_variants": PROMPT_VARIANTS,
        "summary": summary,
        "rows": out_rows,
    }
    suffix = "_".join(args.variants)
    tag = f"_{args.tag}" if args.tag else ""
    out_path = Path(args.out_dir) / f"{args.model_key}_e162_{suffix}{tag}.json"
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
