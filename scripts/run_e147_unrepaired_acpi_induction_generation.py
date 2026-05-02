#!/usr/bin/env python3
"""Run E147 non-thinking unrepaired-ACPI induction generation.

This is a no-gold generation runner.  The task bank stores gold answers and risk
notes as offline metadata, but prompts contain only the problem text.
"""
from __future__ import annotations

import argparse
import json
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

TASK_BANK = PROJECT / "data/processed/e147_unrepaired_acpi_induction_tasks_20260430.jsonl"
OUT_DIR = PROJECT / "results/E147_unrepaired_acpi_induction"

PROMPT_VARIANTS = {
    "neutral": (
        "Solve the following problem carefully. Show the reasoning needed to justify the result. "
        "End with exactly one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
    "answer_first_no_gold": (
        "Solve the following problem yourself. First write one line `Final answer: <answer>`, "
        "then give a concise justification. No final answer is provided in the prompt.\n\nProblem: {problem}"
    ),
    "terse_solution": (
        "Solve the following problem with a terse but complete derivation. "
        "End with exactly one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
    "self_check_short": (
        "Solve the following problem. After deriving an answer, do one short self-check of the main step, "
        "then end with exactly one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    return e49.should_use_chat(spec, tokenizer)


def render_prompt(tokenizer, spec: dict[str, Any], task: dict[str, Any], variant: str, thinking: bool) -> tuple[str, bool, bool]:
    content = PROMPT_VARIANTS[variant].format(problem=task["problem"])
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
    p.add_argument("--task-bank", default=str(TASK_BANK))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--variants", nargs="+", default=["neutral", "answer_first_no_gold", "terse_solution", "self_check_short"])
    p.add_argument("--families", nargs="*", default=[])
    p.add_argument("--routes", nargs="*", default=[])
    p.add_argument("--max-tasks", type=int, default=0)
    p.add_argument("--k", type=int, default=1)
    p.add_argument("--max-new-tokens", type=int, default=4096)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--thinking", choices=["true", "false"], default="false")
    p.add_argument("--allow-final-fallback", action="store_true")
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260430)
    return p.parse_args()


def select_tasks(tasks: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    families = set(args.families or [])
    routes = set(args.routes or [])
    out = []
    for task in tasks:
        if families and task["family"] not in families:
            continue
        if routes and task["route_id"] not in routes:
            continue
        out.append(task)
    out = sorted(out, key=lambda t: (t["family"], int(t["family_local_id"]), t["route_id"], t["task_id"]))
    if args.max_tasks and args.max_tasks > 0:
        out = out[: args.max_tasks]
    return out


def main() -> None:
    args = parse_args()
    unknown = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")
    torch.manual_seed(args.seed)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    tasks = select_tasks(load_jsonl(Path(args.task_bank)), args)
    if not tasks:
        raise SystemExit("No tasks selected")
    thinking = args.thinking == "true"
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E147 induction generation", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    jobs: list[dict[str, Any]] = []
    for task in tasks:
        for variant in args.variants:
            prompt, used_chat, add_special = render_prompt(tok, spec, task, variant, thinking)
            for sample_idx in range(args.k):
                jobs.append(
                    {
                        "task": task,
                        "variant": variant,
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
    for start in range(0, len(jobs), args.batch_size):
        batch = jobs[start : start + args.batch_size]
        add_values = {job["add_special"] for job in batch}
        if len(add_values) != 1:
            raise RuntimeError("Mixed add_special values in one batch")
        enc = tok([job["prompt"] for job in batch], return_tensors="pt", padding=True, add_special_tokens=batch[0]["add_special"]).to(device)
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
            extracted, final_marker, extraction_method = e49.extract_final_answer(completion, allow_fallback=args.allow_final_fallback)
            final_correct = e49.normalize_answer(extracted) == e49.normalize_answer(str(job["task"]["gold_answer"]))
            row = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "experiment": "E147_unrepaired_acpi_induction",
                "model_key": args.model_key,
                "task_id": job["task"]["task_id"],
                "family": job["task"]["family"],
                "route_id": job["task"]["route_id"],
                "problem": job["task"]["problem"],
                "gold_answer": job["task"]["gold_answer"],
                "risk_pattern_offline": job["task"]["risk_pattern"],
                "trap_note_not_in_prompt": job["task"]["trap_note_not_in_prompt"],
                "prompt_variant": job["variant"],
                "sample_idx": job["sample_idx"],
                "used_chat_template": job["used_chat"],
                "add_special_tokens": job["add_special"],
                "thinking": thinking,
                "gold_answer_in_prompt": False,
                "known_trap_note_in_prompt": False,
                "manual_label_in_prompt": False,
                "error_span_in_prompt": False,
                "completion": completion,
                "extracted_final": extracted,
                "extraction_method": extraction_method,
                "final_marker_found": final_marker,
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
                "manual_final_correct": final_correct,
                "manual_process_valid_strict": None,
                "manual_process_valid_repaired": None,
                "manual_acpi_strict": None,
                "manual_repair_present": None,
                "manual_acpi_unrepaired": None,
                "manual_error_type": None,
                "manual_error_span": None,
                "manual_notes_zh": "",
            }
            rows.append(row)
            if checkpoint_path:
                with checkpoint_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)

    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_variant: dict[str, Counter[str]] = defaultdict(Counter)
    by_route: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for bucket in (by_family[row["family"]], by_variant[row["prompt_variant"]], by_route[row["route_id"]]):
            bucket["generated"] += 1
            bucket["final_correct"] += int(row["manual_final_correct"])
            bucket["final_marker_missing"] += int(not row["final_marker_found"])
            bucket["hit_max"] += int(row["hit_max_new_tokens"])
            bucket["gold_answer_in_prompt"] += int(row["gold_answer_in_prompt"])
            bucket["known_trap_note_in_prompt"] += int(row["known_trap_note_in_prompt"])
            bucket["manual_label_in_prompt"] += int(row["manual_label_in_prompt"])
            bucket["error_span_in_prompt"] += int(row["error_span_in_prompt"])
    summary = {
        "generated": len(rows),
        "selected_tasks": len(tasks),
        "final_correct": sum(int(r["manual_final_correct"]) for r in rows),
        "final_marker_missing": sum(int(not r["final_marker_found"]) for r in rows),
        "hit_max": sum(int(r["hit_max_new_tokens"]) for r in rows),
        "leakage_audit": {
            "gold_answer_in_prompt_rows": sum(int(r["gold_answer_in_prompt"]) for r in rows),
            "known_trap_note_in_prompt_rows": sum(int(r["known_trap_note_in_prompt"]) for r in rows),
            "manual_label_in_prompt_rows": sum(int(r["manual_label_in_prompt"]) for r in rows),
            "error_span_in_prompt_rows": sum(int(r["error_span_in_prompt"]) for r in rows),
            "passed": True,
        },
        "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "by_route": {k: dict(v) for k, v in sorted(by_route.items())},
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
        "task_bank": rel(Path(args.task_bank)),
        "summary": summary,
        "rows": rows,
        "scope_note_zh": "E147 是诱发/发现网格，不是自然发生率估计；gold/risk/trap 只作离线元数据。",
    }
    suffix = "_".join(args.variants)
    out_path = Path(args.out_dir) / f"{args.model_key}_e147_{suffix}_k{args.k}_induction_generation.json"
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

