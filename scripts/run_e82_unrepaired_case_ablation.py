#!/usr/bin/env python3
"""E82 ablations for the two Gemma26 unrepaired hard-task ACPI cases.

The goal is diagnostic: test whether strict verifiers accept the cases because
of final-answer anchoring, because the wrong factorization is locally subtle, or
because the trace remains answer-coherent after the erroneous step. Prompts never
include labels or error-span annotations; variants are visible text ablations.
"""
from __future__ import annotations

import argparse
import json
import re
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

E57_AUDIT = PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl"
FINAL_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", re.IGNORECASE | re.MULTILINE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    if mode == "raw":
        return False
    if mode == "chat":
        return True
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm", "exaone", "nemotron"} or "instruct" in cls or "post" in cls


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


def strict_prompt(problem: str, trace: str) -> str:
    return (
        "You are a strict trace-selection auditor. Judge the visible reasoning trace step by step. "
        "If any visible local step, definition, arithmetic operation, counting rule, algebraic transformation, semantic interpretation, or proof implication is wrong, answer No, even if the final answer is correct. "
        "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    )


def replace_final(trace: str, replacement: str | None) -> str:
    matches = list(FINAL_RE.finditer(trace))
    if not matches:
        return trace
    m = matches[-1]
    if replacement is None:
        return trace[: m.start()] + trace[m.end():]
    return trace[: m.start()] + replacement + trace[m.end():]


def first_final_prefix(trace: str) -> str:
    m = next(FINAL_RE.finditer(trace), None)
    return trace[: m.end()] if m else trace[: min(len(trace), 800)]


def error_prefix(trace: str, err: str) -> str:
    if err and err in trace:
        return trace[: trace.find(err) + len(err)]
    return trace[: min(len(trace), 500)]


def ablation_variants(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row["completion"]
    err = row.get("manual_error_span") or ""
    final = str(row.get("extracted_final") or row.get("gold_answer") or "117")
    wrong_final = "118" if final != "118" else "116"
    variants = [
        ("original", comp, "Original unrepaired ACPI trace with correct final answer."),
        ("final_removed", replace_final(comp, None), "Remove the final-answer line; process error remains."),
        ("final_masked", replace_final(comp, "Final answer: [MASKED]"), "Mask the final answer; process error remains."),
        ("final_wrong", replace_final(comp, f"Final answer: {wrong_final}"), "Replace the final answer with a wrong visible answer; process error remains."),
        ("error_prefix_only", error_prefix(comp, err), "Show only the trace up to the erroneous factorization span."),
        ("first_final_prefix", first_final_prefix(comp), "Show only through the first final-answer line."),
    ]
    out = []
    for name, trace, note in variants:
        out.append({
            "case_id": f"audit{row['manual_audit_idx']}:{name}",
            "variant": name,
            "variant_note": note,
            "problem": row["problem"],
            "trace": trace.strip(),
            "source_model": row["model_key"],
            "manual_audit_idx": row["manual_audit_idx"],
            "task_id": row["task_id"],
            "gold_answer": row.get("gold_answer"),
            "original_extracted_final": row.get("extracted_final"),
            "manual_error_type": row.get("manual_error_type"),
            "manual_error_span": row.get("manual_error_span"),
            "target_strict_valid": False,
        })
    return out


def build_items() -> list[dict[str, Any]]:
    rows = [r for r in load_jsonl(E57_AUDIT) if r.get("manual_acpi_unrepaired")]
    items = []
    for r in rows:
        items.extend(ablation_variants(r))
    return items


def label_logprob(logits: torch.Tensor, tok, options: list[str]) -> tuple[float, str]:
    logp = F.log_softmax(logits.float(), dim=-1)
    scored = []
    for opt in options:
        ids = tok.encode(opt, add_special_tokens=False)
        if ids:
            scored.append((float(logp[int(ids[0])].item()), opt))
    return max(scored, key=lambda x: x[0])


def score_prompt(model, tok, prompt: str, device: torch.device, max_model_len: int, add_special_tokens: bool) -> dict[str, Any]:
    ids = tok.encode(prompt, add_special_tokens=add_special_tokens)[-max_model_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attn, use_cache=False).logits[0, -1]
    yes_score, yes_opt = label_logprob(logits, tok, [" Yes", "Yes", " yes", "yes"])
    no_score, no_opt = label_logprob(logits, tok, [" No", "No", " no", "no"])
    del input_ids, attn, logits
    return {
        "yes_score": yes_score,
        "no_score": no_score,
        "yes_minus_no": yes_score - no_score,
        "pred_process_valid": yes_score > no_score,
        "yes_option": yes_opt,
        "no_option": no_opt,
        "input_tokens": len(ids),
    }


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[("all", "all")].append(r)
        groups[("variant", r["variant"])].append(r)
        groups[("audit_idx", str(r["manual_audit_idx"]))].append(r)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        out.append({
            "slice_type": typ,
            "slice": key,
            "n": len(vals),
            "strict_invalid_accept_rate": sum(v["pred_process_valid"] for v in vals) / len(vals),
            "mean_yes_minus_no": mean(v["yes_minus_no"] for v in vals),
        })
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E82_unrepaired_case_ablation"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    items = build_items()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E82 n_items={len(items)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    rows = []
    for i, item in enumerate(items, start=1):
        prompt, add = render_prompt(tok, strict_prompt(item["problem"], item["trace"]), use_chat)
        scored = score_prompt(model, tok, prompt, device, args.max_model_len, add)
        rows.append({**{k: v for k, v in item.items() if k not in {"problem", "trace"}}, **scored, "used_chat_template": use_chat})
        print(f"scored {i}/{len(items)}", flush=True)
    result = {
        "experiment": "E82_unrepaired_case_ablation",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "args": vars(args),
        "rows": rows,
        "summary": summarize(rows),
        "leakage_audit": {"labels_in_prompt_rows": 0, "error_span_annotation_in_prompt_rows": 0, "gold_answer_in_prompt_rows": 0, "note_zh": "prompt 只含题目和可见 ablated trace；manual_error_span 只用于离线构造 error_prefix，不作为标注展示。"},
        "scope_note_zh": "E82 是 case diagnostic，不估计自然发生率；所有 variant 的 strict target 都是 invalid。",
    }
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e82_unrepaired_case_ablation_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] in {"all", "variant"}:
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
