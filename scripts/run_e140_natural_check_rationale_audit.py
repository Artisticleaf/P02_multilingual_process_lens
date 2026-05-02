#!/usr/bin/env python3
"""E140 generated rationale audit for E138 natural-check failures.

E138 scores global/local second checks with deterministic Yes/No logits. E140
asks the same model to explain selected E138 natural rows, especially cases
where base/default/strict local checks still accept a strict-invalid trace.

Manual labels are used only for row selection and offline evaluation. Prompts
contain the problem, visible trace, and optionally a hidden-trigger-selected
visible excerpt.  E138/E131 trigger points are diagnostic and partly
label-informed offline; do not present E140 as a deployment-style online policy.
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

import torch
from transformers import StoppingCriteria, StoppingCriteriaList

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

AUDIT_JSONL = PROJECT / "data/processed/e119_e146_process_audit_official_20260430.jsonl"
E138_DIR = PROJECT / "results/E138_natural_hidden_trigger_check"
OUT_DIR = PROJECT / "results/E140_natural_check_rationale_audit"

FIELD_RE = {
    "wrong_step_quoted": re.compile(r"^\s*Wrong step quoted\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE),
    "wrong_step_problem": re.compile(r"^\s*Wrong step problem\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE),
    "error_recognized": re.compile(r"^\s*Error recognized\s*[:：]\s*(Yes|No)\b", re.IGNORECASE | re.MULTILINE),
    "later_discarded_repaired": re.compile(r"^\s*Later discarded/repaired\s*[:：]\s*(Yes|No|NA|N/A)\b", re.IGNORECASE | re.MULTILINE),
    "strict_decision": re.compile(r"^\s*Strict decision\s*[:：]\s*(Yes|No)\b", re.IGNORECASE | re.MULTILINE),
    "repair_aware_decision": re.compile(r"^\s*Repair-aware decision\s*[:：]\s*(Yes|No)\b", re.IGNORECASE | re.MULTILINE),
    "failure_mode": re.compile(r"^\s*Failure mode\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE),
    "short_reason": re.compile(r"^\s*Short reason\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE),
}
FINAL_BLOCK_RE = re.compile(r"<FINAL_AUDIT>\s*(.*?)\s*</FINAL_AUDIT>", re.IGNORECASE | re.DOTALL)


class StopOnDecodedString(StoppingCriteria):
    def __init__(self, tokenizer, prompt_len: int, stop_string: str):
        self.tokenizer = tokenizer
        self.prompt_len = prompt_len
        self.stop_string = stop_string

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        tail = input_ids[0, self.prompt_len :]
        if tail.numel() == 0:
            return False
        text = self.tokenizer.decode(tail.detach().cpu(), skip_special_tokens=True)
        return self.stop_string in text


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def e138_path(model_key: str, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    path = E138_DIR / f"{model_key}_e138_natural_hidden_trigger_check_all.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content + "\nAudit:", True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def audit_prompt(problem: str, trace: str, scope: str, excerpt: str | None) -> str:
    local = ""
    if scope == "local":
        local = (
            "A hidden process-risk monitor selected this visible excerpt for special review. "
            "The monitor can be wrong; do not assume the excerpt is erroneous. Use it as a focus, but judge the whole visible trace under both standards.\n"
            f"Selected excerpt: {excerpt or ''}\n"
        )
    return (
        "You are auditing a visible candidate solution written by another system. It is not your own chain-of-thought.\n"
        "Use two separate standards:\n"
        "1. Strict trace-as-proof: if any visible local claim, equation, transformation, counting step, semantic interpretation, or intermediate final answer is wrong, Strict decision must be No, even if a later line repairs it and even if the final answer is correct.\n"
        "2. Repair-aware final proof: Repair-aware decision is Yes only if any wrong step is clearly discarded and the final surviving proof is self-consistent.\n"
        "Do not judge by final answer alone. Quote the key wrong step if one exists. Do not write explanation outside the final block.\n"
        "Finish exactly with one block:\n"
        "<FINAL_AUDIT>\n"
        "Wrong step quoted: <quote or NONE>\n"
        "Wrong step problem: <short description or NONE>\n"
        "Error recognized: <Yes/No>\n"
        "Later discarded/repaired: <Yes/No/NA>\n"
        "Strict decision: <Yes/No>\n"
        "Repair-aware decision: <Yes/No>\n"
        "Failure mode: <no_error_seen / repair_aware_accept / final_answer_anchor / local_excerpt_missed / strict_reject / unclear>\n"
        "Short reason: <one sentence>\n"
        "</FINAL_AUDIT>\n\n"
        f"Problem: {problem}\n"
        f"Visible trace: {trace}\n"
        f"{local}"
    )


def parse_fields(text: str) -> dict[str, Any]:
    block_match = FINAL_BLOCK_RE.search(text)
    parse_text = block_match.group(1) if block_match else text
    out: dict[str, Any] = {"final_block_found": bool(block_match)}
    for key, regex in FIELD_RE.items():
        m = regex.search(parse_text)
        out[key] = m.group(1).strip() if m else ""
    for key in ["error_recognized", "later_discarded_repaired", "strict_decision", "repair_aware_decision"]:
        val = str(out.get(key, "")).strip().lower()
        if val in {"yes", "y"}:
            out[key] = "Yes"
        elif val in {"no", "n"}:
            out[key] = "No"
        elif val in {"na", "n/a"}:
            out[key] = "NA"
    quote = str(out.get("wrong_step_quoted") or "").strip()
    out["claims_no_wrong_step"] = quote.upper() in {"NONE", "NA", "N/A", "NO", ""}
    out["parse_ok"] = out.get("strict_decision") in {"Yes", "No"} and out.get("repair_aware_decision") in {"Yes", "No"}
    return out


def eos_token_ids(tok) -> set[int]:
    ids: set[int] = set()
    eos = tok.eos_token_id
    if isinstance(eos, list):
        ids.update(int(x) for x in eos)
    elif eos is not None:
        ids.add(int(eos))
    return ids


def trim_after_stop(text: str, stop: str) -> tuple[str, bool]:
    idx = text.find(stop)
    if idx < 0:
        return text.strip(), False
    return text[: idx + len(stop)].strip(), True


def generate_one(model, tok, prompt: str, add_special: bool, device: torch.device, max_input_tokens: int, max_new_tokens: int, max_time: float) -> dict[str, Any]:
    enc = tok(prompt, return_tensors="pt", add_special_tokens=add_special, truncation=True, max_length=max_input_tokens).to(device)
    kwargs: dict[str, Any] = {
        **enc,
        "do_sample": False,
        "max_new_tokens": max_new_tokens,
        "pad_token_id": tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id,
        "stopping_criteria": StoppingCriteriaList([StopOnDecodedString(tok, enc["input_ids"].shape[1], "</FINAL_AUDIT>")]),
    }
    if tok.eos_token_id is not None:
        kwargs["eos_token_id"] = tok.eos_token_id
    if max_time > 0:
        kwargs["max_time"] = max_time
    with torch.no_grad():
        out = model.generate(**kwargs)
    prompt_len = enc["input_ids"].shape[1]
    gen_ids = out[0, prompt_len:]
    raw = tok.decode(gen_ids, skip_special_tokens=True).strip()
    completion, stopped_with_block = trim_after_stop(raw, "</FINAL_AUDIT>")
    eos_ids = eos_token_ids(tok)
    stopped_with_eos = bool(gen_ids.numel() and int(gen_ids[-1].item()) in eos_ids)
    return {
        "completion": completion,
        "raw_completion": raw,
        "input_tokens": int(prompt_len),
        "generated_tokens": int(gen_ids.numel()),
        "hit_max_new_tokens": bool(gen_ids.numel() >= max_new_tokens and not stopped_with_block),
        "stopped_with_eos": stopped_with_eos,
        "stopped_with_final_block": stopped_with_block,
        "may_have_hit_max_time": bool(max_time > 0 and not stopped_with_eos and not stopped_with_block and gen_ids.numel() < max_new_tokens),
        "truncated_input": bool(enc["input_ids"].shape[1] >= max_input_tokens),
    }


def row_needs_audit(row: dict[str, Any], include_success_contrast: bool) -> bool:
    if row["trace_class"] == "unrepaired_acpi":
        return True
    if row["trace_class"] != "strict_valid":
        if bool(row["base_completion_accept"]):
            return True
        for key, val in row.get("policy_decisions", {}).items():
            if key.startswith("zero_") and bool(val.get("accept")):
                return True
        if include_success_contrast and bool(row["threshold_policies"]["zero"]["trigger"]):
            return True
    if include_success_contrast and row["trace_class"] == "strict_valid" and bool(row["threshold_policies"]["zero"]["trigger"]):
        return True
    return False


def select_rows(e138_rows: list[dict[str, Any]], max_rows: int, include_success_contrast: bool) -> list[dict[str, Any]]:
    rows = [r for r in e138_rows if row_needs_audit(r, include_success_contrast)]
    rows.sort(key=lambda r: (r["trace_class"] == "strict_valid", int(r["audit_idx"])))
    if max_rows:
        rows = rows[:max_rows]
    return rows


def build_jobs(rows: list[dict[str, Any]], scopes: list[str]) -> list[dict[str, Any]]:
    jobs = []
    for row in rows:
        for scope in scopes:
            if scope == "local" and not bool(row["threshold_policies"]["zero"]["trigger"]):
                continue
            jobs.append({"row": row, "scope": scope})
    return jobs


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups["all"].append(row)
        groups[f"scope={row['scope']}"].append(row)
        groups[f"trace_class={row['trace_class']}"].append(row)
        groups[f"scope_class={row['scope']}::{row['trace_class']}"].append(row)
        groups[f"error_type={row.get('manual_error_type')}"].append(row)

    def stats(vals: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(vals)
        return {
            "n": n,
            "parse_ok_rate": sum(bool(v["parsed"]["parse_ok"]) for v in vals) / n if n else None,
            "final_block_found_rate": sum(bool(v["parsed"]["final_block_found"]) for v in vals) / n if n else None,
            "hit_max_rate": sum(bool(v["generation"]["hit_max_new_tokens"]) for v in vals) / n if n else None,
            "error_recognized_rate": sum(v["parsed"].get("error_recognized") == "Yes" for v in vals) / n if n else None,
            "strict_accept_rate": sum(v["parsed"].get("strict_decision") == "Yes" for v in vals) / n if n else None,
            "repair_aware_accept_rate": sum(v["parsed"].get("repair_aware_decision") == "Yes" for v in vals) / n if n else None,
            "claims_no_wrong_step_rate": sum(bool(v["parsed"].get("claims_no_wrong_step")) for v in vals) / n if n else None,
        }

    return {
        "n": len(rows),
        "by_slice": {key: stats(vals) for key, vals in sorted(groups.items())},
        "failure_modes": dict(Counter(str(r["parsed"].get("failure_mode") or "") for r in rows)),
        "leakage_audit": {
            "labels_in_prompt_rows": 0,
            "gold_answer_in_prompt_rows": 0,
            "manual_error_span_annotation_in_prompt_rows": 0,
            "passed": True,
            "note_zh": "Prompts contain only problem, visible trace, and optionally a hidden-trigger-selected visible excerpt. Manual labels/gold/error-span annotations are offline only.",
        },
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--e138-result", default="")
    p.add_argument("--audit-jsonl", default=str(AUDIT_JSONL))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--scopes", nargs="+", choices=["global", "local"], default=["global", "local"])
    p.add_argument("--include-success-contrast", action="store_true")
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--max-input-tokens", type=int, default=8192)
    p.add_argument("--max-new-tokens", type=int, default=384)
    p.add_argument("--max-time", type=float, default=45.0)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    e138_file = e138_path(args.model_key, args.e138_result)
    e138 = json.loads(e138_file.read_text(encoding="utf-8"))
    audit_by_idx = {int(r["audit_idx"]): r for r in load_jsonl(Path(args.audit_jsonl)) if r.get("model_key") == args.model_key}
    selected = select_rows(list(e138["rows"]), args.max_rows, args.include_success_contrast)
    jobs = build_jobs(selected, args.scopes)
    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "model_key": args.model_key,
            "source_e138": rel(e138_file),
            "selected_rows": len(selected),
            "jobs": len(jobs),
            "selected_by_class": dict(Counter(r["trace_class"] for r in selected)),
            "jobs_by_scope_class": dict(Counter(f"{j['scope']}::{j['row']['trace_class']}" for j in jobs)),
        }, ensure_ascii=False, indent=2))
        return

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    local_only = args.local_files_only or is_local_model(spec)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E140 jobs={len(jobs)} rows={len(selected)}", flush=True)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    use_chat = should_use_chat(spec, tok)

    out_rows: list[dict[str, Any]] = []
    for i, job in enumerate(jobs, start=1):
        row = job["row"]
        audit = audit_by_idx[int(row["audit_idx"])]
        excerpt = row["threshold_policies"]["zero"].get("excerpt") if job["scope"] == "local" else None
        content = audit_prompt(audit["problem"], audit["completion"], job["scope"], excerpt)
        rendered, add_special = render_prompt(tok, content, use_chat)
        gen = generate_one(model, tok, rendered, add_special, device, args.max_input_tokens, args.max_new_tokens, args.max_time)
        parsed = parse_fields(gen["completion"])
        rec = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "experiment": "E140_natural_check_rationale_audit",
            "model_key": args.model_key,
            "scope": job["scope"],
            "thinking": False,
            "audit_idx": row["audit_idx"],
            "task_id": row.get("task_id"),
            "run_id": row.get("run_id"),
            "sampling_profile": row.get("sampling_profile"),
            "prompt_variant": row.get("prompt_variant"),
            "trace_class": row["trace_class"],
            "manual_process_valid_strict": row["manual_process_valid_strict"],
            "manual_process_valid_repaired": row["manual_process_valid_repaired"],
            "manual_acpi_strict": row["manual_acpi_strict"],
            "manual_acpi_unrepaired": row["manual_acpi_unrepaired"],
            "manual_repair_present": row["manual_repair_present"],
            "manual_error_type": row.get("manual_error_type"),
            "base_completion_accept": row["base_completion_accept"],
            "zero_trigger": row["threshold_policies"]["zero"]["trigger"],
            "zero_min_score": row["threshold_policies"]["zero"]["min_score"],
            "zero_earliest_trigger": row["threshold_policies"]["zero"].get("earliest_trigger"),
            "e138_policy_accepts": {k: v["accept"] for k, v in row["policy_decisions"].items()},
            "selected_excerpt": excerpt,
            "problem": audit["problem"],
            "visible_trace": audit["completion"],
            "prompt_contains_gold_label_or_error_annotation": False,
            "offline_prefix_selection_label_informed": True,
            "generation": gen,
            "parsed": parsed,
        }
        out_rows.append(rec)
        print(
            f"E140 {args.model_key} {i}/{len(jobs)} scope={job['scope']} idx={row['audit_idx']} "
            f"class={row['trace_class']} strict={parsed.get('strict_decision')} repair={parsed.get('repair_aware_decision')}",
            flush=True,
        )

    result = {
        "experiment": "E140_natural_check_rationale_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "source_e138_result": rel(e138_file),
        "source_audit_jsonl": rel(Path(args.audit_jsonl)),
        "args": vars(args),
        "selected_rows": [
            {
                "audit_idx": r["audit_idx"],
                "trace_class": r["trace_class"],
                "base_completion_accept": r["base_completion_accept"],
                "zero_trigger": r["threshold_policies"]["zero"]["trigger"],
                "manual_error_type": r.get("manual_error_type"),
            }
            for r in selected
        ],
        "rows": out_rows,
        "summary": summarize(out_rows),
        "scope_note_zh": "E140 解释 E138 自然样本二次检查成败；它使用 E138 的可见 excerpt，不是新的自然发生率估计，也不是在线部署策略。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.model_key}_e140_natural_check_rationale_audit.json"
    write_json(out, result)
    print(json.dumps({"out": rel(out), "jobs": len(jobs), "summary": result["summary"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
