#!/usr/bin/env python3
"""E101 small generation sensitivity audit for batch size and mode.

This is deliberately capped to avoid long thinking loops.  It tests whether
changing batch size changes generated text under the same seed/prompt family.
It is a sensitivity diagnostic, not a natural-prevalence estimate.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402
from run_e49_hard_task_conditioning_official import extract_final_answer, normalize_answer, render_prompt  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_27b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--tasks-yaml", default=str(PROJECT / "configs/e26_aime_hard_tasks.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E101_batch_generation_sensitivity"))
    p.add_argument("--batch-sizes", nargs="+", type=int, default=[1, 2, 4])
    p.add_argument("--max-tasks", type=int, default=2)
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=20)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260429)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    started = datetime.now().isoformat(timespec="seconds")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    tasks = read_yaml(args.tasks_yaml)["tasks"][: args.max_tasks]
    print(f"[{started}] E101 loading {args.model_key}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    variants = [
        ("NG_neutral", "neutral", False),
        ("TG_boxed_neutral", "thinking_boxed_neutral", True),
    ]
    rows = []
    for bs in args.batch_sizes:
        jobs = []
        for task in tasks:
            for mode_label, variant, thinking in variants:
                prompt, used_chat, add_special, gold_in_prompt = render_prompt(tok, spec, {"en": task["en"], "answer": task["answer"]}, variant, thinking)
                jobs.append(
                    {
                        "task": task,
                        "mode_label": mode_label,
                        "variant": variant,
                        "thinking": thinking,
                        "prompt": prompt,
                        "used_chat": used_chat,
                        "add_special": add_special,
                        "gold_in_prompt": gold_in_prompt,
                    }
                )
        torch.manual_seed(args.seed)
        for start in range(0, len(jobs), bs):
            batch = jobs[start : start + bs]
            add_values = {j["add_special"] for j in batch}
            if len(add_values) != 1:
                raise RuntimeError("Mixed add_special values in E101 batch")
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
                extracted, marker, method = extract_final_answer(completion, allow_fallback=True)
                rows.append(
                    {
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "model_key": args.model_key,
                        "batch_size": bs,
                        "mode_label": j["mode_label"],
                        "thinking": j["thinking"],
                        "task_id": j["task"]["id"],
                        "problem": j["task"]["en"],
                        "gold_answer": j["task"]["answer"],
                        "prompt_variant": j["variant"],
                        "used_chat_template": j["used_chat"],
                        "gold_answer_in_prompt": j["gold_in_prompt"],
                        "completion": completion,
                        "completion_chars": len(completion),
                        "generated_tokens": int(gen_ids.numel()),
                        "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
                        "extracted_final": extracted,
                        "extraction_method": method,
                        "final_marker_found": marker,
                        "manual_final_correct": normalize_answer(extracted) == normalize_answer(j["task"]["answer"]),
                    }
                )
            print(f"E101 batch_size={bs} generated {min(start + len(batch), len(jobs))}/{len(jobs)}", flush=True)
    groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["batch_size"], row["mode_label"])].append(row)
    summary = []
    for (bs, mode), vals in sorted(groups.items()):
        summary.append(
            {
                "batch_size": bs,
                "mode_label": mode,
                "n": len(vals),
                "mean_generated_tokens": mean(v["generated_tokens"] for v in vals),
                "hit_max_rate": sum(v["hit_max_new_tokens"] for v in vals) / len(vals),
                "final_correct": sum(v["manual_final_correct"] for v in vals),
                "final_marker_rate": sum(v["final_marker_found"] for v in vals) / len(vals),
                "extraction_methods": dict(Counter(v["extraction_method"] for v in vals)),
            }
        )
    result = {
        "experiment": "E101_batch_generation_sensitivity",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "args": vars(args),
        "rows": rows,
        "summary": summary,
        "audit": {
            "natural_prevalence_estimate": False,
            "note_zh": "E101 是小样本 batch size 生成敏感性诊断；max_new_tokens 被故意压低，不能作为 TG 自然发生率。",
        },
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.model_key}_e101_batch_generation_sensitivity.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    for rec in summary:
        print("SUMMARY", rec, flush=True)


if __name__ == "__main__":
    main()
