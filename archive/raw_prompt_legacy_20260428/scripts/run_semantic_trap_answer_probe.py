#!/usr/bin/env python3
"""Answer-option logprob probe for multilingual semantic traps.

This is a cheap probe: no generation, just teacher-forced option scores after an
answer-only prompt. It tests whether the model's local answer preference already
leans toward the correct value or toward a trap value under each input/reasoning
language route.
"""
from __future__ import annotations

import argparse
import json
import math
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402
from run_trace_pool_generate import build_prompt as build_trace_prompt  # noqa: E402

ROUTES = [("en", "en"), ("zh", "zh"), ("zh", "en"), ("en", "zh")]

TRAP_OPTIONS: dict[str, list[str]] = {
    "disc_zh_75_price": ["60", "20", "80"],
    "disc_en_25_off": ["60", "20", "80"],
    "disc_en_75_off": ["20", "60", "80"],
    "ratio_boys_girls": ["40", "24", "64", "15"],
    "ratio_boys_total": ["40", "24", "64", "15"],
    "ratio_girls_boys": ["40", "24", "64", "15"],
    "avg_simple": ["11", "5", "27"],
    "avg_weighted": ["85", "80", "90", "255"],
    "deriv_sum": ["2x + 3", "2x", "3", "x + 3"],
    "deriv_product_equiv": ["2x + 3", "x^2 + 3x", "2x", "3x^2 + 6x"],
    "deriv_coeff": ["6x + 1", "7x", "6x", "6x + x"],
    "rem_137_9": ["2", "1", "5", "8"],
    "frac_simplify": ["3/4", "4/6", "6/8", "0.75"],
    "percent_then_discount": ["80", "60", "100", "75"],
}


def answer_instruction(reason_lang: str) -> str:
    if reason_lang == "zh":
        return "请只输出最终答案，不要解释。"
    return "Answer with only the final answer. Do not explain."


def build_answer_prompt(tokenizer, spec: dict[str, Any], problem: str, reason_lang: str, chat_template: str) -> tuple[str, bool]:
    if chat_template == "always" or (
        chat_template == "auto" and bool(getattr(tokenizer, "chat_template", None)) and not str(spec.get("class", "")).startswith("base")
    ):
        messages = [
            {"role": "system", "content": answer_instruction(reason_lang)},
            {"role": "user", "content": problem},
        ]
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), True
        except Exception:  # noqa: BLE001
            pass
    if reason_lang == "zh":
        return f"{answer_instruction(reason_lang)}\n题目：{problem}\n答案：", False
    return f"{answer_instruction(reason_lang)}\nProblem: {problem}\nAnswer:", False


def option_forms(option: str, reason_lang: str) -> list[str]:
    raw = option.strip()
    forms = [raw, " " + raw]
    compact = raw.replace(" ", "")
    if compact != raw:
        forms += [compact, " " + compact]
    if any(ch.isdigit() for ch in raw):
        forms += [f"${raw}", f" ${raw}", f"{raw} dollars", f" {raw} dollars", f"{raw}美元", f" {raw}美元"]
    if "/" in raw:
        forms += [f"{raw}.", f" {raw}."]
    # Preserve order while removing duplicates.
    out = []
    seen = set()
    for f in forms:
        if f not in seen:
            seen.add(f); out.append(f)
    return out


def option_score(model, tokenizer, prompt_ids: list[int], option_ids: list[int], device: torch.device) -> tuple[float, float, int]:
    if not option_ids:
        return float("-inf"), float("-inf"), 0
    max_len = 6144
    keep_prompt = max(1, max_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
    total = 0.0
    start = len(prompt_ids)
    for j, tok_id in enumerate(option_ids):
        pos = start + j - 1
        total += float(F.log_softmax(logits[pos], dim=-1)[tok_id].item())
    return total, total / len(option_ids), len(option_ids)


def best_option_score(model, tokenizer, prompt: str, option: str, reason_lang: str, device: torch.device) -> dict[str, Any]:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
    scored = []
    for form in option_forms(option, reason_lang):
        ids = tokenizer.encode(form, add_special_tokens=False)
        total, avg, n = option_score(model, tokenizer, prompt_ids, ids, device)
        scored.append({"form": form, "sum_logprob": total, "avg_logprob": avg, "num_tokens": n})
    best_sum = max(scored, key=lambda x: x["sum_logprob"])
    best_avg = max(scored, key=lambda x: x["avg_logprob"])
    return {"option": option, "best_sum": best_sum, "best_avg": best_avg, "all_forms": scored}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--tasks-yaml", default=str(PROJECT / "configs/e05_acpi_tasks.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E07_semantic_trap_answer_probe"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--chat-template", choices=["auto", "always", "never"], default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--max-tasks", type=int, default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    task_list = read_yaml(args.tasks_yaml)["tasks"]
    if args.max_tasks:
        task_list = task_list[: args.max_tasks]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} on {args.device}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    rows = []
    for task in task_list:
        options = TRAP_OPTIONS.get(task["id"], [str(task["answer"])])
        gold = str(task["answer"])
        if gold not in options:
            options = [gold] + options
        for input_lang, reason_lang in ROUTES:
            problem = task[input_lang]
            prompt, used_chat = build_answer_prompt(tokenizer, spec, problem, reason_lang, args.chat_template)
            scored = [best_option_score(model, tokenizer, prompt, opt, reason_lang, device) for opt in options]
            pred_sum = max(scored, key=lambda x: x["best_sum"]["sum_logprob"])
            pred_avg = max(scored, key=lambda x: x["best_avg"]["avg_logprob"])
            gold_score = next(x for x in scored if x["option"] == gold)
            best_wrong_avg = max((x for x in scored if x["option"] != gold), key=lambda x: x["best_avg"]["avg_logprob"], default=None)
            best_wrong_sum = max((x for x in scored if x["option"] != gold), key=lambda x: x["best_sum"]["sum_logprob"], default=None)
            rows.append(
                {
                    "model_key": args.model_key,
                    "task_id": task["id"],
                    "trap": task.get("trap"),
                    "input_lang": input_lang,
                    "reason_lang": reason_lang,
                    "problem": problem,
                    "gold_answer": gold,
                    "used_chat_template": used_chat,
                    "prompt": prompt,
                    "options": scored,
                    "pred_sum": pred_sum["option"],
                    "pred_avg": pred_avg["option"],
                    "correct_sum": pred_sum["option"] == gold,
                    "correct_avg": pred_avg["option"] == gold,
                    "gold_avg_logprob": gold_score["best_avg"]["avg_logprob"],
                    "best_wrong_avg_logprob": best_wrong_avg["best_avg"]["avg_logprob"] if best_wrong_avg else None,
                    "gold_minus_best_wrong_avg": (
                        gold_score["best_avg"]["avg_logprob"] - best_wrong_avg["best_avg"]["avg_logprob"] if best_wrong_avg else None
                    ),
                    "gold_sum_logprob": gold_score["best_sum"]["sum_logprob"],
                    "best_wrong_sum_logprob": best_wrong_sum["best_sum"]["sum_logprob"] if best_wrong_sum else None,
                    "gold_minus_best_wrong_sum": (
                        gold_score["best_sum"]["sum_logprob"] - best_wrong_sum["best_sum"]["sum_logprob"] if best_wrong_sum else None
                    ),
                }
            )
            print(
                f"row task={task['id']} route={input_lang}->{reason_lang} gold={gold} pred_avg={pred_avg['option']} "
                f"margin_avg={rows[-1]['gold_minus_best_wrong_avg']:.3f}",
                flush=True,
            )
    by = {}
    for key_name in ["all"]:
        pass
    summary = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        for key in [("all", "all"), ("reason_lang", r["reason_lang"]), ("input_lang", r["input_lang"]), ("task", r["task_id"]), ("route", f"{r['input_lang']}->{r['reason_lang']}")]:
            groups.setdefault(key, []).append(r)
    for (slice_type, slice_name), g in sorted(groups.items()):
        summary.append(
            {
                "slice_type": slice_type,
                "slice": slice_name,
                "n": len(g),
                "acc_avg": sum(x["correct_avg"] for x in g) / len(g),
                "acc_sum": sum(x["correct_sum"] for x in g) / len(g),
                "mean_gold_minus_best_wrong_avg": sum(x["gold_minus_best_wrong_avg"] for x in g if x["gold_minus_best_wrong_avg"] is not None) / len(g),
                "mean_gold_minus_best_wrong_sum": sum(x["gold_minus_best_wrong_sum"] for x in g if x["gold_minus_best_wrong_sum"] is not None) / len(g),
            }
        )
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "rows": rows,
        "summary": summary,
    }
    out = Path(args.out_dir) / f"{args.model_key}_semantic_trap_answer_probe.json"
    write_json(out, result)
    all_summary = next(s for s in summary if s["slice_type"] == "all")
    print(f"wrote {out}; rows={len(rows)} acc_avg={all_summary['acc_avg']:.3f} mean_margin={all_summary['mean_gold_minus_best_wrong_avg']:.3f}", flush=True)


if __name__ == "__main__":
    main()
