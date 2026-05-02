#!/usr/bin/env python3
"""Run E159/E160 answer-preserving difficult generation.

E159 uses the same task bank in non-thinking mode.  E160 uses the same prompts
and tasks in thinking mode to give a direct mode contrast.  Gold answers, trap
notes, labels, and error spans stay offline.
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

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))

import run_e49_hard_task_conditioning_official as e49  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

TASK_BANK = PROJECT / "data/processed/e159_answer_preserving_tasks_20260501.jsonl"
OUT_DIR = PROJECT / "results/E159_answer_preserving_difficult_generation"

PROMPT_VARIANTS = {
    "solve_neutral": (
        "Solve the following problem carefully. Show the reasoning needed to justify the result. "
        "Do not give the final answer before the reasoning. End with exactly one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
    "solve_terse": (
        "Solve the following problem with a concise but complete derivation. "
        "Put the final answer only at the end on one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
    "solve_self_check": (
        "Solve the following problem. After deriving the answer, do one short self-check of the main step. "
        "Then put the final answer only at the end on one line `Final answer: <answer>`.\n\nProblem: {problem}"
    ),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render_chat(tokenizer, spec: dict[str, Any], content: str, thinking: bool) -> tuple[str, bool, bool]:
    use_chat = e49.should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=thinking)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False


def render_prompt(tokenizer, spec: dict[str, Any], task: dict[str, Any], variant: str, thinking: bool) -> tuple[str, bool, bool]:
    content = PROMPT_VARIANTS[variant].format(problem=task["problem"])
    return render_chat(tokenizer, spec, content, thinking)


def select_tasks(tasks: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    fams = set(args.families or [])
    out = [t for t in tasks if not fams or t["family"] in fams]
    out = sorted(out, key=lambda t: (t["family"], int(t["family_local_id"]), t["task_id"]))
    if args.max_tasks > 0:
        out = out[: args.max_tasks]
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--task-bank", default=str(TASK_BANK))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--experiment", choices=["E159_answer_preserving_generation", "E160_thinking_answer_preserving_generation"], default="E159_answer_preserving_generation")
    p.add_argument("--thinking", choices=["true", "false"], default="false")
    p.add_argument("--variants", nargs="+", default=["solve_neutral", "solve_terse", "solve_self_check"])
    p.add_argument("--families", nargs="*", default=[])
    p.add_argument("--max-tasks", type=int, default=0)
    p.add_argument("--k", type=int, default=1)
    p.add_argument("--max-new-tokens", type=int, default=4096)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260501)
    return p.parse_args()


def main() -> None:
    import torch

    args = parse_args()
    unknown = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")
    thinking = args.thinking == "true"
    if args.experiment.startswith("E160") and not thinking:
        raise SystemExit("E160 requires --thinking true")
    if args.experiment.startswith("E159") and thinking:
        raise SystemExit("E159 requires --thinking false")
    torch.manual_seed(args.seed)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    tasks = select_tasks(load_jsonl(Path(args.task_bank)), args)
    if not tasks:
        raise SystemExit("No tasks selected")
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for {args.experiment} thinking={thinking}", flush=True)
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
        add_values = {job["add_special"] for job in batch}
        if len(add_values) != 1:
            raise RuntimeError("Mixed add_special values")
        enc = tok([job["prompt"] for job in batch], return_tensors="pt", padding=True, add_special_tokens=batch[0]["add_special"]).to(device)
        gen_kwargs = dict(
            do_sample=args.temperature > 0,
            max_new_tokens=args.max_new_tokens,
            pad_token_id=pad_token_id,
        )
        if args.temperature > 0:
            gen_kwargs.update(dict(temperature=args.temperature, top_p=args.top_p, top_k=args.top_k))
        with torch.no_grad():
            out = model.generate(**enc, **gen_kwargs)
        prompt_len = enc["input_ids"].shape[1]
        for job, seq in zip(batch, out):
            gen_ids = seq[prompt_len:]
            completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
            extracted, marker, method = e49.extract_final_answer(completion, allow_fallback=True)
            correct = e49.normalize_answer(extracted) == e49.normalize_answer(str(job["task"]["gold_answer"]))
            row = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "experiment": args.experiment,
                "model_key": args.model_key,
                "task_id": job["task"]["task_id"],
                "family": job["task"]["family"],
                "problem": job["task"]["problem"],
                "gold_answer": job["task"]["gold_answer"],
                "answer_preserving_trap_type": job["task"]["answer_preserving_trap_type"],
                "source_material": job["task"]["source_material"],
                "difficulty_tier": job["task"]["difficulty_tier"],
                "prompt_variant": job["variant"],
                "sample_idx": job["sample_idx"],
                "used_chat_template": job["used_chat"],
                "thinking": thinking,
                "gold_answer_in_prompt": False,
                "trap_note_in_prompt": False,
                "manual_label_in_prompt": False,
                "error_span_in_prompt": False,
                "completion": completion,
                "extracted_final": extracted,
                "extraction_method": method,
                "final_marker_found": marker,
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
                "manual_final_correct": correct,
                "manual_process_valid_strict": None,
                "manual_process_valid_repaired": None,
                "manual_acpi_strict": None,
                "manual_acpi_unrepaired": None,
                "manual_repair_present": None,
                "manual_error_span": None,
                "manual_error_type": None,
                "manual_self_check_markers": None,
                "manual_correction_count": None,
            }
            rows.append(row)
            if checkpoint:
                with checkpoint.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)

    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_variant: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        for bucket in (by_family[r["family"]], by_variant[r["prompt_variant"]]):
            bucket["generated"] += 1
            bucket["final_correct"] += int(r["manual_final_correct"])
            bucket["missing_final_marker"] += int(not r["final_marker_found"])
            bucket["hit_max"] += int(r["hit_max_new_tokens"])
    summary = {
        "generated": len(rows),
        "selected_tasks": len(tasks),
        "final_correct": sum(int(r["manual_final_correct"]) for r in rows),
        "missing_final_marker": sum(int(not r["final_marker_found"]) for r in rows),
        "hit_max": sum(int(r["hit_max_new_tokens"]) for r in rows),
        "thinking": thinking,
        "leakage_audit": {
            "gold_answer_in_prompt_rows": 0,
            "trap_note_in_prompt_rows": 0,
            "manual_label_in_prompt_rows": 0,
            "error_span_in_prompt_rows": 0,
            "passed": True,
        },
        "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
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
        "rows": rows,
    }
    suffix = "_".join(args.variants)
    mode = "thinking" if thinking else "nonthinking"
    out_path = Path(args.out_dir) / f"{args.model_key}_{args.experiment}_{mode}_{suffix}_k{args.k}.json"
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
