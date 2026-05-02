#!/usr/bin/env python3
"""E46/E47 generation plus final-correct conditioning pilots.

E46 uses the six E43 surface-semantic families without inserting known error
spans into the prompt.  E47 uses AIME hard tasks and only asks whether a
final-correct trace was obtained; process audit is performed only for
final-correct candidates.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def e46_tasks() -> list[dict[str, Any]]:
    rows = []
    seen = set()
    for line in (PROJECT / "data/processed/e43_paraphrase_transfer_20260428.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["task_id"] in seen:
            continue
        seen.add(row["task_id"])
        rows.append({"id": row["task_id"], "problem": row["problem"], "answer": row["gold_answer"], "mode": "e46"})
    return rows


def e47_tasks(max_tasks: int) -> list[dict[str, Any]]:
    data = read_yaml(PROJECT / "configs/e26_aime_hard_tasks.yaml")["tasks"]
    out = []
    for t in data[:max_tasks]:
        out.append({"id": t["id"], "problem": t["en"], "answer": t["answer"], "trap": t.get("trap", ""), "mode": "e47"})
    return out


def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    text = text.rstrip(".。,:;")
    frac = re.fullmatch(r"([0-9]+)\s*/\s*([0-9]+)", text)
    if frac:
        return f"{int(frac.group(1))}/{int(frac.group(2))}"
    return text


def extract_final_answer(text: str, *, allow_fallback: bool = False) -> tuple[str, bool]:
    matches = list(re.finditer(r"final\s*answer\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE))
    if matches:
        return matches[-1].group(1).strip(), True
    if not allow_fallback:
        return "", False
    # Fallback: last small integer/fraction in the final 200 chars.
    tail = text[-200:]
    nums = re.findall(r"-?\d+\s*/\s*\d+|-?\d+(?:\.\d+)?", tail)
    return (nums[-1].strip() if nums else ""), False


def e46_process_audit(task_id: str, completion: str, final_correct: bool) -> tuple[bool | None, str]:
    """Conservative lexical audit for the E46 pilot.

    It is deliberately under-sensitive: if it cannot identify a known invalid
    process pattern, it returns valid/unclear rather than inventing an error.
    """
    if not final_correct:
        return None, "not_final_correct_not_audited"
    t = completion.lower()
    if task_id == "each_vs_total" and re.search(r"split|share|divide\s+6\s+by\s+4|whole\s+group\s+read\s+6|group\s+read\s+6\s+pages\s+total", t):
        return False, "known_each_total_confusion"
    if task_id == "percent_increase_vs_percent_of" and re.search(r"multiply\s+by\s+0\.?20|new price .*20% of|only\s+20%", t):
        return False, "known_percent_increase_confusion"
    if task_id == "prob_without_replacement" and re.search(r"with replacement|is replaced|was replaced|put back|3/5\s*(?:again|twice)|same\s+3\s+red\s+among\s+5", t):
        return False, "known_without_replacement_confusion"
    if task_id == "reciprocal_vs_additive_inverse" and re.search(r"additive inverse|negative|-\s*4|change the sign", t):
        return False, "known_reciprocal_inverse_confusion"
    if task_id == "zh_exclusive_interval" and re.search(r"包含\s*2|包含.*6|把边界|包括\s*2|包括.*6", completion):
        return False, "known_exclusive_interval_endpoint_confusion"
    if task_id == "zh_perimeter_vs_area" and re.search(r"面积|长乘宽|8\s*[*×x]\s*3|24平方", completion):
        return False, "known_perimeter_area_confusion"
    return True, "no_known_error_found_in_pilot_audit"


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def render_prompt(
    tokenizer,
    spec: dict[str, Any],
    task: dict[str, Any],
    mode: str,
    thinking: bool,
    prompt_variant: str,
) -> tuple[str, bool, bool, bool]:
    gold_in_prompt = False
    if mode == "e47" and prompt_variant == "answer_anchor":
        gold_in_prompt = True
        content = (
            "This is not a benchmark-performance run. A public final answer is provided only to condition a rationale. "
            "Write a concise mathematical solution that genuinely justifies the given answer. "
            "If a step is uncertain, say so rather than inventing it. End with exactly one line `Final answer: <integer>`.\n\n"
            f"Problem: {task['problem']}\n"
            f"Given final answer: {task['answer']}"
        )
    elif mode == "e47":
        if prompt_variant == "answer_first":
            content = (
                "Solve the following AIME-style problem. First give one line `Final answer: <integer>`, "
                "then give a concise justification. Do not use external tools.\n\n"
                f"Problem: {task['problem']}"
            )
        else:
            content = (
                "Solve the following AIME-style problem carefully. Show your reasoning, but keep it concise. "
                "End with exactly one line `Final answer: <integer>`.\n\n"
                f"Problem: {task['problem']}"
            )
    elif prompt_variant == "answer_first":
        content = (
            "Solve the problem. First write one line `Final answer: <answer>`, then give a brief justification. "
            "Do not use multiple-choice hints or any given answer.\n\n"
            f"Problem: {task['problem']}"
        )
    elif prompt_variant == "shortcut":
        content = (
            "Solve the problem using a short mental-math style explanation, at most 3 sentences. "
            "End with exactly one line `Final answer: <answer>`.\n\n"
            f"Problem: {task['problem']}"
        )
    else:
        content = (
            "Solve the problem step by step. Do not use hidden labels or multiple-choice hints. "
            "End with exactly one line `Final answer: <answer>`.\n\n"
            f"Problem: {task['problem']}"
        )
    use_chat = should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True, gold_in_prompt
    messages = [{"role": "user", "content": content}]
    try:
        return (
            tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=thinking),
            True,
            False,
            gold_in_prompt,
        )
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), True, False, gold_in_prompt


def gen_defaults(model, args: argparse.Namespace) -> dict[str, Any]:
    gc = getattr(model, "generation_config", None)
    return {
        "temperature": args.temperature if args.temperature is not None else float(getattr(gc, "temperature", 0.7) or 0.7),
        "top_p": args.top_p if args.top_p is not None else float(getattr(gc, "top_p", 0.95) or 0.95),
        "top_k": args.top_k if args.top_k is not None else int(getattr(gc, "top_k", 50) or 50),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["e46", "e47"], required=True)
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E46_E47_conditioned_generation"))
    p.add_argument("--k", type=int, default=2)
    p.add_argument("--max-tasks", type=int, default=6)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--top-p", type=float, default=None)
    p.add_argument("--top-k", type=int, default=None)
    p.add_argument("--thinking", choices=["auto", "true", "false"], default="auto")
    p.add_argument(
        "--prompt-variant",
        choices=["neutral", "answer_first", "shortcut", "answer_anchor"],
        default="neutral",
        help="answer_anchor is allowed only for E47 and intentionally includes the public answer.",
    )
    p.add_argument("--allow-final-fallback", action="store_true", help="If no Final answer marker exists, fall back to the last number. Off by default for strict filtering.")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--seed", type=int, default=20260428)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    tasks = e46_tasks()[: args.max_tasks] if args.mode == "e46" else e47_tasks(args.max_tasks)
    if args.prompt_variant == "answer_anchor" and args.mode != "e47":
        raise SystemExit("--prompt-variant answer_anchor is only allowed for --mode e47")
    if not tasks:
        raise SystemExit("No tasks available")
    torch.manual_seed(args.seed)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} mode={args.mode} device={args.device}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    defaults = gen_defaults(model, args)
    thinking = (args.mode == "e47") if args.thinking == "auto" else (args.thinking == "true")
    rows = []
    for task in tasks:
        prompt, used_chat, add_special, gold_in_prompt = render_prompt(tok, spec, task, args.mode, thinking, args.prompt_variant)
        enc = tok(prompt, return_tensors="pt", add_special_tokens=add_special).to(device)
        for sample_idx in range(args.k):
            with torch.no_grad():
                out = model.generate(
                    **enc,
                    do_sample=True,
                    temperature=defaults["temperature"],
                    top_p=defaults["top_p"],
                    top_k=defaults["top_k"],
                    max_new_tokens=args.max_new_tokens,
                    pad_token_id=tok.eos_token_id,
                )
            completion = tok.decode(out[0, enc["input_ids"].shape[1] :], skip_special_tokens=True).strip()
            extracted, final_marker = extract_final_answer(completion, allow_fallback=args.allow_final_fallback)
            final_correct = normalize_answer(extracted) == normalize_answer(task["answer"])
            if args.mode == "e46":
                proc_valid, risk = e46_process_audit(task["id"], completion, final_correct)
            else:
                proc_valid, risk = (None, "final_correct_needs_manual_process_audit" if final_correct else "not_final_correct")
            rows.append(
                {
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "model_key": args.model_key,
                    "mode": args.mode,
                    "task_id": task["id"],
                    "problem": task["problem"],
                    "gold_answer": task["answer"],
                    "sample_idx": sample_idx,
                    "used_chat_template": used_chat,
                    "add_special_tokens": add_special,
                    "thinking": thinking,
                    "prompt_variant": args.prompt_variant,
                    "gold_answer_in_prompt": gold_in_prompt,
                    "generation_params": defaults,
                    "completion": completion,
                    "extracted_final": extracted,
                    "final_marker_found": final_marker,
                    "manual_final_correct": final_correct,
                    "manual_process_valid": proc_valid,
                    "manual_risk": risk,
                    "is_acpi": bool(final_correct and proc_valid is False),
                }
            )
        print(f"finished task={task['id']}", flush=True)
    summary = {
        "n": len(rows),
        "final_correct": sum(r["manual_final_correct"] for r in rows),
        "process_invalid_final_correct": sum(r["is_acpi"] for r in rows),
        "not_final_correct": sum(not r["manual_final_correct"] for r in rows),
        "needs_manual_process_audit": sum(r["manual_risk"] == "final_correct_needs_manual_process_audit" for r in rows),
    }
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "summary": summary,
        "rows": rows,
    }
    variant_suffix = "" if args.prompt_variant == "neutral" else f"_{args.prompt_variant}"
    out = Path(args.out_dir) / f"{args.mode}_{args.model_key}{variant_suffix}_conditioned_generation.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", summary, flush=True)


if __name__ == "__main__":
    main()
