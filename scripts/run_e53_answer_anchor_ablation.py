#!/usr/bin/env python3
"""E53 answer-anchor ablation.

For each controlled E39/E42 valid/invalid process trace, keep the process text
fixed and vary only the final-answer line: shown/correct, removed, masked, or
wrong.  Score the same process-only Yes/No verifier prompt used by E42.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def split_final_answer(completion: str) -> tuple[str, str | None]:
    marker = "\nFinal answer:"
    if marker in completion:
        body, ans = completion.rsplit(marker, 1)
        return body.rstrip(), ans.strip()
    return completion.rstrip(), None


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    if mode == "raw":
        return False
    if mode == "chat":
        return True
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


def process_prompt(row: dict[str, Any]) -> str:
    return (
        "You are auditing a mathematical reasoning trace. Judge only whether the mathematical "
        "reasoning steps are valid; do not penalize missing final-answer formatting, truncation, "
        "or extra text after the answer. If any mathematical step is wrong, answer No. If the "
        "visible reasoning steps are mathematically valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {row['problem']}\n"
        f"Reasoning trace: {row['completion']}\n"
        "Are the visible reasoning steps mathematically valid? Answer:"
    )


def option_logprob(model, tokenizer, prompt: str, option: str, device: torch.device, max_model_len: int, add_special_tokens: bool) -> float:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    if not option_ids:
        return float("-inf")
    keep_prompt = max(1, max_model_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
    total = 0.0
    start = len(prompt_ids)
    for j, tok_id in enumerate(option_ids):
        total += float(F.log_softmax(logits[start + j - 1], dim=-1)[tok_id].item())
    return total


def best_score(model, tokenizer, prompt: str, options: list[str], device: torch.device, max_model_len: int, add_special_tokens: bool) -> tuple[float, str]:
    scored = [(option_logprob(model, tokenizer, prompt, opt, device, max_model_len, add_special_tokens), opt) for opt in options]
    return max(scored, key=lambda x: x[0])


def build_e53_rows(e39_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_task: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in e39_rows:
        by_task[row["task_id"]][row["e39_variant"]] = row
    out: list[dict[str, Any]] = []
    base = 530000
    for task_i, task_id in enumerate(sorted(by_task)):
        variants = by_task[task_id]
        for process_variant in ["valid_correct", "invalid_correct"]:
            src = variants[process_variant]
            wrong_src = variants["valid_wrong" if process_variant == "valid_correct" else "invalid_wrong"]
            body, gold_from_trace = split_final_answer(src["completion"])
            _, wrong_from_trace = split_final_answer(wrong_src["completion"])
            if gold_from_trace is None or wrong_from_trace is None:
                raise SystemExit(f"Missing final answer line for {task_id}/{process_variant}")
            answer_variants = [
                ("shown", f"{body}\nFinal answer: {gold_from_trace}", True, True),
                # Removed/masked conditions test answer anchoring; final correctness is not visible/applicable.
                ("removed", body, None, False),
                ("masked", f"{body}\nFinal answer: [MASKED]", None, True),
                ("wrong", f"{body}\nFinal answer: {wrong_from_trace}", False, True),
            ]
            for ans_i, (answer_condition, completion, final_correct, has_final_line) in enumerate(answer_variants):
                idx = base + task_i * 100 + (0 if process_variant == "valid_correct" else 10) + ans_i
                out.append(
                    {
                        "audit_idx": idx,
                        "source_audit_idx": src["audit_idx"],
                        "task_id": task_id,
                        "problem": src["problem"],
                        "completion": completion,
                        "gold_answer": src["gold_answer"],
                        "e53_process_variant": process_variant,
                        "e53_answer_condition": answer_condition,
                        "manual_process_valid": bool(src["manual_process_valid"]),
                        "manual_final_correct": final_correct,
                        "manual_has_final_answer_line": has_final_line,
                        "manual_format_valid": has_final_line and answer_condition != "masked",
                        "is_acpi": (not bool(src["manual_process_valid"])) and (final_correct is True),
                        "input_lang": src.get("input_lang"),
                        "reason_lang": src.get("reason_lang"),
                        "support_span": src.get("support_span"),
                        "error_span": src.get("error_span"),
                        "known_error_span_in_prompt": False,
                        "gold_label_in_prompt": False,
                    }
                )
    expected = len(by_task) * 2 * 4
    if len(out) != expected:
        raise SystemExit(f"Unexpected E53 size {len(out)} != {expected}")
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def add(group_key: str, group_rows: list[dict[str, Any]]) -> dict[str, Any]:
        invalid = [r for r in group_rows if not r["target_process_valid"]]
        valid = [r for r in group_rows if r["target_process_valid"]]
        return {
            "slice": group_key,
            "n": len(group_rows),
            "accuracy": sum(r["pred_process_valid"] == r["target_process_valid"] for r in group_rows) / len(group_rows),
            "yes_rate": sum(r["pred_process_valid"] for r in group_rows) / len(group_rows),
            "invalid_accept_rate": sum(r["pred_process_valid"] for r in invalid) / len(invalid) if invalid else None,
            "valid_accept_rate": sum(r["pred_process_valid"] for r in valid) / len(valid) if valid else None,
            "mean_margin": mean([r["margin"] for r in group_rows]),
        }
    out: dict[str, Any] = {"overall": add("overall", rows), "by_answer_condition": [], "by_process_and_answer": []}
    for cond in sorted({r["e53_answer_condition"] for r in rows}):
        out["by_answer_condition"].append(add(f"answer={cond}", [r for r in rows if r["e53_answer_condition"] == cond]))
    for proc in sorted({r["e53_process_variant"] for r in rows}):
        for cond in sorted({r["e53_answer_condition"] for r in rows}):
            g = [r for r in rows if r["e53_process_variant"] == proc and r["e53_answer_condition"] == cond]
            out["by_process_and_answer"].append(add(f"process={proc}|answer={cond}", g))
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--e39-jsonl", default=str(PROJECT / "data/processed/e39_surface_semantic_generalization_20260428.jsonl"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E53_answer_anchor_ablation"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    e53_rows = build_e53_rows(load_jsonl(Path(args.e39_jsonl)))
    data_out = PROJECT / "data/processed/e53_answer_anchor_ablation_20260428.jsonl"
    write_jsonl(data_out, e53_rows)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E53", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tokenizer, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    yes_opts = [" Yes", "Yes", " yes", "yes"]
    no_opts = [" No", "No", " no", "no"]
    scored = []
    for i, row in enumerate(e53_rows, start=1):
        prompt_text, add_special = render_prompt(tokenizer, process_prompt(row), use_chat)
        yes_score, yes_opt = best_score(model, tokenizer, prompt_text, yes_opts, device, args.max_model_len, add_special)
        no_score, no_opt = best_score(model, tokenizer, prompt_text, no_opts, device, args.max_model_len, add_special)
        margin = yes_score - no_score
        scored.append(
            {
                "objective": "absolute_process_e53_answer_anchor",
                "audit_idx": row["audit_idx"],
                "source_audit_idx": row["source_audit_idx"],
                "task_id": row["task_id"],
                "e53_process_variant": row["e53_process_variant"],
                "e53_answer_condition": row["e53_answer_condition"],
                "target_process_valid": bool(row["manual_process_valid"]),
                "manual_final_correct": row["manual_final_correct"],
                "pred_process_valid": margin > 0,
                "margin": margin,
                "yes_score": yes_score,
                "no_score": no_score,
                "yes_option": yes_opt,
                "no_option": no_opt,
                "used_chat_template": use_chat,
            }
        )
        if i % 12 == 0:
            print(f"scored {i}/{len(e53_rows)}", flush=True)
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "args": vars(args),
        "data_path": str(data_out),
        "rows": scored,
        "summary": summarize(scored),
        "leakage_audit": {
            "gold_label_in_prompt_rows": 0,
            "known_error_span_annotation_in_prompt_rows": 0,
            "note_en": "Prompts contain problem and trace only; process labels/span annotations are post-hoc fields. The erroneous mathematical sentence itself remains part of the trace by design.",
            "note_zh": "prompt 只包含题目和 trace；过程标签/span 标注仅用于事后分析。错误数学句子本身当然仍作为 trace 内容出现。",
        },
    }
    out = Path(args.out_dir) / f"{args.model_key}_e53_answer_anchor_ablation.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", json.dumps(result["summary"]["by_answer_condition"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
