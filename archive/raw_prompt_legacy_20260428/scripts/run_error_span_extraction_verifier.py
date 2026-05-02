#!/usr/bin/env python3
"""Ask a verifier to localize process errors before making a Yes/No decision."""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def build_prompt(row: dict[str, Any], prompt_lang: str, mode: str) -> str:
    problem = row["problem"]
    trace = row["completion"]
    if prompt_lang == "zh":
        header = (
            "你是数学推理过程审计员。只审计可见推理过程里的数学错误或语言语义错误；"
            "不要因为最终答案格式、输出风格或啰嗦程度判错。"
        )
        if mode == "locate_only":
            return (
                f"{header}\n"
                "请找出第一处错误。如果没有错误，只输出 `NONE`。"
                "如果有错误，先精确引用最短的错误短语，再用一句话解释。\n"
                f"题目：{problem}\n"
                f"推理过程：{trace}\n"
                "第一处错误："
            )
        if mode == "locate_then_judge":
            return (
                f"{header}\n"
                "先写 `Span:` 并引用第一处错误短语；如果没有错误写 `Span: NONE`。"
                "再写 `Process-valid:`，只回答 Yes 或 No。\n"
                f"题目：{problem}\n"
                f"推理过程：{trace}\n"
                "Span:"
            )
    else:
        header = (
            "You are auditing a mathematical reasoning trace. Judge only visible mathematical "
            "or language-semantic process errors; do not penalize final-answer formatting, style, or verbosity."
        )
        if mode == "locate_only":
            return (
                f"{header}\n"
                "Find the first error. If there is no error, output exactly `NONE`. "
                "If there is an error, quote the shortest offending phrase first, then give one short reason.\n"
                f"Problem: {problem}\n"
                f"Reasoning trace: {trace}\n"
                "First error:"
            )
        if mode == "locate_then_judge":
            return (
                f"{header}\n"
                "First write `Span:` and quote the first offending phrase; if there is no error write `Span: NONE`. "
                "Then write `Process-valid:` with only Yes or No.\n"
                f"Problem: {problem}\n"
                f"Reasoning trace: {trace}\n"
                "Span:"
            )
    raise KeyError((prompt_lang, mode))


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("％", "%")
    text = re.sub(r"[`'\"“”‘’（）()\[\]{}.,;:：，。；、\s$\\]+", "", text)
    return text


def known_spans(row: dict[str, Any]) -> list[str]:
    spans: list[str] = []
    value = row.get("known_error_spans")
    if isinstance(value, list):
        spans.extend(str(x) for x in value if x)
    err = row.get("earliest_error")
    if err:
        spans.append(str(err))
    # Add conservative fragments that make automatic matching less brittle.
    joined = " ".join(spans).lower()
    if "80% discount" in joined:
        spans.extend(["80% discount", "multiply by 0.8"])
    if "75% discount" in joined:
        spans.extend(["75% discount", "discount percentage"])
    if "打八折" in joined or "75%" in joined and "打" in joined:
        spans.extend(["打八折", "支付75%"])
    out = []
    seen = set()
    for s in spans:
        ns = normalize(s)
        if ns and ns not in seen:
            out.append(s)
            seen.add(ns)
    return out


def predicts_none(text: str) -> bool:
    head = normalize(text[:160])
    none_markers = ["none", "noerror", "noerrors", "没有错误", "无错误", "没有发现错误", "不存在错误", "无"]
    return any(m in head for m in none_markers)


def span_hit(text: str, spans: list[str]) -> bool:
    if not spans:
        return predicts_none(text)
    nt = normalize(text)
    if predicts_none(text):
        return False
    for span in spans:
        ns = normalize(span)
        if len(ns) >= 3 and ns in nt:
            return True
        # Some generations quote only the key lexical fragment.
        if len(ns) >= 8 and any(part and part in nt for part in re.split(r"[%/]+", ns)):
            return True
    return False


def parse_judgement(text: str, mode: str) -> bool | None:
    if mode != "locate_then_judge":
        return None
    low = text.lower()
    # Prefer the explicit Process-valid field if present.
    m = re.search(r"process[- ]?valid\s*[:：]?\s*(yes|no|是|否)", low, re.I)
    if m:
        return m.group(1).lower() in {"yes", "是"}
    if re.search(r"\bno\b", low) or "否" in text or "无效" in text:
        return False
    if re.search(r"\byes\b", low) or "是" in text or "有效" in text:
        return True
    return None


def generate_one(model, tokenizer, prompt: str, device: torch.device, max_new_tokens: int) -> str:
    ids = tokenizer.encode(prompt, add_special_tokens=True)
    max_input = 6144 - max_new_tokens
    ids = ids[-max_input:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        out = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_ids = out[0, input_ids.shape[1] :]
    return tokenizer.decode(new_ids, skip_special_tokens=True).strip()


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for key in [
            (r["mode"], r["prompt_lang"], "all"),
            (r["mode"], r["prompt_lang"], f"variant={r.get('e28_variant','NA')}"),
            (r["mode"], r["prompt_lang"], f"task={r['task_id']}"),
            (r["mode"], r["prompt_lang"], f"risk={r['manual_risk']}"),
        ]:
            groups[key].append(r)
    out = []
    for (mode, prompt_lang, slice_name), g in sorted(groups.items()):
        invalid = [r for r in g if r["manual_process_valid"] is False]
        valid = [r for r in g if r["manual_process_valid"] is True]
        judged = [r for r in g if r["judge_pred_process_valid"] is not None]
        invalid_judged = [r for r in invalid if r["judge_pred_process_valid"] is not None]
        out.append(
            {
                "mode": mode,
                "prompt_lang": prompt_lang,
                "slice": slice_name,
                "n": len(g),
                "invalid_n": len(invalid),
                "valid_n": len(valid),
                "span_accuracy": sum(r["span_correct"] for r in g) / len(g) if g else None,
                "invalid_span_hit_rate": sum(r["span_correct"] for r in invalid) / len(invalid) if invalid else None,
                "valid_none_rate": sum(r["span_correct"] for r in valid) / len(valid) if valid else None,
                "judge_accuracy": (
                    sum(r["judge_pred_process_valid"] == r["manual_process_valid"] for r in judged) / len(judged)
                    if judged
                    else None
                ),
                "invalid_reject_rate": (
                    sum(r["judge_pred_process_valid"] is False for r in invalid_judged) / len(invalid_judged)
                    if invalid_judged
                    else None
                ),
                "located_but_accepted_n": sum(
                    1
                    for r in invalid_judged
                    if r["span_correct"] and r["judge_pred_process_valid"] is True
                ),
                "located_but_accepted_rate_invalid": (
                    sum(1 for r in invalid_judged if r["span_correct"] and r["judge_pred_process_valid"] is True) / len(invalid_judged)
                    if invalid_judged
                    else None
                ),
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", required=True)
    p.add_argument("--out-dir", default=str(PROJECT / "results/E29_error_span_extraction_verifier"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--prompt-langs", default="en,zh")
    p.add_argument("--modes", default="locate_only,locate_then_judge")
    p.add_argument("--max-new-tokens", type=int, default=96)
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = [json.loads(line) for line in Path(args.manual_jsonl).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.max_rows > 0:
        rows = rows[: args.max_rows]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading model={args.model_key} device={args.device} rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    prompt_langs = [x.strip() for x in args.prompt_langs.split(",") if x.strip()]
    modes = [x.strip() for x in args.modes.split(",") if x.strip()]
    eval_rows: list[dict[str, Any]] = []
    for row in rows:
        spans = known_spans(row)
        for mode in modes:
            for prompt_lang in prompt_langs:
                prompt = build_prompt(row, prompt_lang, mode)
                output = generate_one(model, tokenizer, prompt, device, args.max_new_tokens)
                none_pred = predicts_none(output)
                hit = span_hit(output, spans)
                judge = parse_judgement(output, mode)
                eval_row = {
                    "audit_idx": row["audit_idx"],
                    "trace_model_key": row.get("model_key"),
                    "task_id": row["task_id"],
                    "input_lang": row.get("input_lang"),
                    "reason_lang": row.get("reason_lang"),
                    "manual_risk": row.get("manual_risk"),
                    "manual_process_valid": row.get("manual_process_valid"),
                    "manual_final_correct": row.get("manual_final_correct"),
                    "manual_format_valid": row.get("manual_format_valid"),
                    "is_acpi": row.get("is_acpi", False),
                    "e28_variant": row.get("e28_variant"),
                    "mode": mode,
                    "prompt_lang": prompt_lang,
                    "known_error_spans": spans,
                    "raw_output": output,
                    "predicts_none": none_pred,
                    "span_correct": hit,
                    "judge_pred_process_valid": judge,
                    "judge_correct": None if judge is None else judge == row.get("manual_process_valid"),
                }
                eval_rows.append(eval_row)
                print(
                    f"idx={row['audit_idx']} mode={mode} prompt={prompt_lang} proc={row.get('manual_process_valid')} "
                    f"span_ok={hit} judge={judge} out={output[:90].replace(chr(10), ' ')}",
                    flush=True,
                )
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "verifier_model_key": args.model_key,
        "model_spec": spec,
        "manual_jsonl": args.manual_jsonl,
        "num_manual_rows": len(rows),
        "num_eval_rows": len(eval_rows),
        "args": vars(args),
        "rows": eval_rows,
        "summary": summarize(eval_rows),
    }
    out = Path(args.out_dir) / f"{args.model_key}_error_span_extraction_verifier.json"
    write_json(out, result)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] wrote {out}; eval_rows={len(eval_rows)}", flush=True)
    for s in result["summary"]:
        if s["slice"] == "all":
            print(
                f"SUMMARY mode={s['mode']} prompt={s['prompt_lang']} span_acc={s['span_accuracy']} "
                f"invalid_hit={s['invalid_span_hit_rate']} judge_acc={s['judge_accuracy']} "
                f"loc_but_accept={s['located_but_accepted_rate_invalid']}",
                flush=True,
            )


if __name__ == "__main__":
    main()
