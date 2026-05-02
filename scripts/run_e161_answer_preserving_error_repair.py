#!/usr/bin/env python3
"""Run E161 answer-preserving error finding and repair probes.

Inputs are candidate traces from E159.  Prompts never expose the gold answer.
The oracle-span condition intentionally exposes an offline error span for
invalid traces only; it is an upper-bound intervention, not a blind detector.
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

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))

import run_e49_hard_task_conditioning_official as e49  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

SOL_BANK = PROJECT / "data/processed/e159_answer_preserving_candidate_solutions_20260501.jsonl"
OUT_DIR = PROJECT / "results/E161_answer_preserving_error_repair"

PROMPT_VARIANTS = {
    "blind_global": (
        "You are checking a proposed solution. Do not solve from scratch unless needed. "
        "State whether the proposed solution contains any wrong reasoning step. "
        "Use this exact final block:\nERROR: Yes or No\nLOCATION: <short quote or NONE>\nREASON: <one sentence>\n\n"
        "Problem: {problem}\nProposed solution:\n{solution}"
    ),
    "blind_localize_only": (
        "Look only for the first questionable reasoning step in the proposed solution. Do not repair the solution. "
        "Use this exact final block:\nERROR: Yes or No\nLOCATION: <short quote or NONE>\n\n"
        "Problem: {problem}\nProposed solution:\n{solution}"
    ),
    "oracle_span_repair": (
        "A separate hidden monitor flagged this visible span as potentially abnormal: `{span}`. "
        "Check whether that span is actually a wrong reasoning step. If it is wrong, give a minimal corrected step, "
        "but do not solve the entire problem from scratch. Use this exact final block:\n"
        "ERROR: Yes or No\nLOCATION: <short quote or NONE>\nCORRECTION: <minimal correction or NONE>\n\n"
        "Problem: {problem}\nProposed solution:\n{solution}"
    ),
}

ERROR_RE = re.compile(r"ERROR\s*[:：]\s*(Yes|No)", re.IGNORECASE)
LOCATION_RE = re.compile(r"LOCATION\s*[:：]\s*(.+)", re.IGNORECASE)
CORRECTION_RE = re.compile(r"CORRECTION\s*[:：]\s*(.+)", re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_span(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip("\"'`")).lower()


def location_matches(location: str, span: str | None) -> bool:
    if not span:
        return False
    loc = normalize_span(location)
    target = normalize_span(span)
    if not loc or loc == "none" or not target:
        return False
    return target in loc or loc in target


def parse_block(text: str) -> dict[str, Any]:
    errors = [m.group(1).lower() == "yes" for m in ERROR_RE.finditer(text)]
    locs = [m.group(1).strip() for m in LOCATION_RE.finditer(text)]
    corrs = [m.group(1).strip() for m in CORRECTION_RE.finditer(text)]
    return {
        "parse_ok": bool(errors),
        "first_pred_error": errors[0] if errors else None,
        "last_pred_error": errors[-1] if errors else None,
        "first_location": locs[0] if locs else "",
        "last_location": locs[-1] if locs else "",
        "correction": corrs[-1] if corrs else "",
        "error_line_count": len(errors),
        "error_judgment_flip": bool(len(errors) >= 2 and errors[0] != errors[-1]),
    }


def render_chat(tokenizer, spec: dict[str, Any], content: str) -> tuple[str, bool, bool]:
    use_chat = e49.should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nAnswer:", False, True
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False


def select_rows(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    fams = set(args.families or [])
    variants = set(args.candidate_variants or [])
    out = [
        r
        for r in rows
        if (not fams or r["family"] in fams)
        and (not variants or r["candidate_variant"] in variants)
    ]
    out = sorted(out, key=lambda r: (r["family"], r["task_id"], r["candidate_variant"]))
    if args.max_rows > 0:
        out = out[: args.max_rows]
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--solution-bank", default=str(SOL_BANK))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--variants", nargs="+", default=["blind_global", "blind_localize_only", "oracle_span_repair"])
    p.add_argument("--families", nargs="*", default=[])
    p.add_argument("--candidate-variants", nargs="*", default=[])
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--max-new-tokens", type=int, default=768)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--top-k", type=int, default=0)
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    import torch

    args = parse_args()
    unknown = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = select_rows(load_jsonl(Path(args.solution_bank)), args)
    if not rows:
        raise SystemExit("No candidate rows selected")
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E161 rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    jobs = []
    for row in rows:
        for variant in args.variants:
            span = row.get("manual_error_span") or "NONE"
            content = PROMPT_VARIANTS[variant].format(problem=row["problem"], solution=row["candidate_solution"], span=span)
            prompt, used_chat, add_special = render_chat(tok, spec, content)
            oracle_span = variant == "oracle_span_repair" and bool(row.get("manual_error_span"))
            jobs.append({"row": row, "variant": variant, "prompt": prompt, "used_chat": used_chat, "add_special": add_special, "oracle_span": oracle_span})

    checkpoint = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    if checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text("", encoding="utf-8")

    out_rows = []
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
            parsed = parse_block(completion)
            manual_has_error = not bool(job["row"]["manual_process_valid_strict"])
            rec = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "experiment": "E161_answer_preserving_error_repair",
                "model_key": args.model_key,
                "task_id": job["row"]["task_id"],
                "family": job["row"]["family"],
                "solution_id": job["row"]["solution_id"],
                "candidate_variant": job["row"]["candidate_variant"],
                "prompt_variant": job["variant"],
                "thinking": False,
                "gold_answer_in_prompt": False,
                "manual_label_in_prompt": False,
                "error_span_in_prompt": bool(job["oracle_span"]),
                "oracle_span_condition": bool(job["oracle_span"]),
                "problem": job["row"]["problem"],
                "candidate_solution": job["row"]["candidate_solution"],
                "manual_has_error": manual_has_error,
                "manual_error_span_offline": job["row"].get("manual_error_span") or "",
                "manual_error_type": job["row"].get("manual_error_type") or "",
                "completion": completion,
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
                **parsed,
            }
            rec["last_pred_correct"] = parsed["last_pred_error"] is not None and bool(parsed["last_pred_error"]) == manual_has_error
            rec["last_location_matches_error_span"] = location_matches(parsed["last_location"], job["row"].get("manual_error_span"))
            rec["correction_nonempty"] = bool(parsed["correction"] and normalize_span(parsed["correction"]) != "none")
            out_rows.append(rec)
            if checkpoint:
                with checkpoint.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)

    by_slice: dict[str, Counter[str]] = defaultdict(Counter)
    for r in out_rows:
        for key in [
            "all::all",
            f"candidate::{r['candidate_variant']}",
            f"prompt::{r['prompt_variant']}",
            f"family::{r['family']}",
        ]:
            by_slice[key]["n"] += 1
            by_slice[key]["parse_ok"] += int(r["parse_ok"])
            by_slice[key]["last_pred_correct"] += int(r["last_pred_correct"])
            by_slice[key]["last_location_matches_error_span"] += int(r["last_location_matches_error_span"])
            by_slice[key]["correction_nonempty"] += int(r["correction_nonempty"])
            by_slice[key]["hit_max"] += int(r["hit_max_new_tokens"])
    summary = {
        "jobs": len(out_rows),
        "candidate_rows": len(rows),
        "parse_ok": sum(int(r["parse_ok"]) for r in out_rows),
        "last_pred_correct": sum(int(r["last_pred_correct"]) for r in out_rows),
        "last_location_matches_error_span": sum(int(r["last_location_matches_error_span"]) for r in out_rows),
        "correction_nonempty": sum(int(r["correction_nonempty"]) for r in out_rows),
        "hit_max": sum(int(r["hit_max_new_tokens"]) for r in out_rows),
        "leakage_audit": {
            "gold_answer_in_prompt_rows": 0,
            "manual_label_in_prompt_rows": 0,
            "error_span_in_prompt_rows": sum(int(r["error_span_in_prompt"]) for r in out_rows),
            "note": "error spans appear only in the explicit oracle_span_repair intervention condition.",
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
    out_path = Path(args.out_dir) / f"{args.model_key}_e161_{suffix}_error_repair.json"
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
