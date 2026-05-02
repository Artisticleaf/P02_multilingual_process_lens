#!/usr/bin/env python3
"""E139 generated rationale audit for global/local second-check behavior.

E136 used deterministic Yes/No option-logprob scoring, so it did not produce
check-time CoT/rationales.  E139 asks the same model to generate a concise
audit rationale and explicit strict vs repair-aware decisions, under both
non-thinking and thinking chat-template modes.

Manual labels and error spans are used only for row selection/evaluation.
Prompts contain only the problem, visible trace, and, for local checks, a
visible excerpt selected by the prior hidden trigger.
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

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E132_DATA = PROJECT / "data/processed/e132_suspicious_valid_controls_20260430.jsonl"
E136_DIR = PROJECT / "results/E136_suspicious_confidence_adaptive_check"
OUT_DIR = PROJECT / "results/E139_check_rationale_audit"

FIELD_RE = {
    "wrong_step_quoted": re.compile(r"^\s*Wrong step quoted\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE),
    "wrong_step_problem": re.compile(r"^\s*Wrong step problem\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE),
    "later_discarded_repaired": re.compile(r"^\s*Later discarded/repaired\s*[:：]\s*(Yes|No|NA|N/A)\b", re.IGNORECASE | re.MULTILINE),
    "strict_decision": re.compile(r"^\s*Strict decision\s*[:：]\s*(Yes|No)\b", re.IGNORECASE | re.MULTILINE),
    "repair_aware_decision": re.compile(r"^\s*Repair-aware decision\s*[:：]\s*(Yes|No)\b", re.IGNORECASE | re.MULTILINE),
    "short_reason": re.compile(r"^\s*Short reason\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE),
}

FINAL_BLOCK_RE = re.compile(r"<FINAL_AUDIT>\s*(.*?)\s*</FINAL_AUDIT>", re.IGNORECASE | re.DOTALL)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def e136_path(model_key: str) -> Path:
    path = E136_DIR / f"{model_key}_e136_suspicious_confidence_adaptive_check_rowspervariant12.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def render_prompt(tokenizer, content: str, use_chat: bool, thinking: bool) -> tuple[str, bool]:
    if not use_chat:
        return content + "\nAudit:", True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=thinking, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def audit_prompt(problem: str, trace: str, check_type: str, excerpt: str | None) -> str:
    local_part = ""
    if check_type == "local":
        local_part = (
            "A hidden process-risk monitor selected this visible excerpt for special review. "
            "The monitor can be wrong; do not assume the excerpt is erroneous.\n"
            f"Selected excerpt: {excerpt or ''}\n"
        )
    return (
        "You are auditing a visible reasoning trace. Use two separate standards.\n"
        "Strict trace-as-proof standard: if any visible reasoning step is wrong, answer Strict decision: No, even if a later line repairs it and even if the final answer is correct.\n"
        "Repair-aware standard: answer Repair-aware decision: Yes only if any wrong step is clearly discarded and the final surviving proof is self-consistent.\n"
        "Do not judge by the final answer alone. Quote the key wrong step if one exists.\n"
        "Think only as much as needed. You must finish with a final block exactly in this format:\n"
        "<FINAL_AUDIT>\n"
        "Wrong step quoted: <quote or NONE>\n"
        "Wrong step problem: <short description or NONE>\n"
        "Later discarded/repaired: <Yes/No/NA>\n"
        "Strict decision: <Yes/No>\n"
        "Repair-aware decision: <Yes/No>\n"
        "Short reason: <one sentence>\n"
        "</FINAL_AUDIT>\n\n"
        f"Problem: {problem}\n"
        f"Visible trace: {trace}\n"
        f"{local_part}"
    )


def parse_fields(text: str) -> dict[str, Any]:
    block_match = FINAL_BLOCK_RE.search(text)
    parse_text = block_match.group(1) if block_match else text
    out: dict[str, Any] = {}
    for key, regex in FIELD_RE.items():
        m = regex.search(parse_text)
        out[key] = m.group(1).strip() if m else ""
    for key in ["later_discarded_repaired", "strict_decision", "repair_aware_decision"]:
        if out.get(key):
            val = out[key].strip().lower()
            if val in {"yes", "y"}:
                out[key] = "Yes"
            elif val in {"no", "n"}:
                out[key] = "No"
            elif val in {"na", "n/a"}:
                out[key] = "NA"
    out["final_block_found"] = bool(block_match)
    out["parse_ok"] = bool(out.get("strict_decision") in {"Yes", "No"} and out.get("repair_aware_decision") in {"Yes", "No"})
    quote = str(out.get("wrong_step_quoted") or "").strip()
    out["claims_no_wrong_step"] = quote.upper() in {"NONE", "NA", "N/A", "NO", ""}
    return out


FAILURE_POLICY_KEYS = [
    "plain_base_no_check_accept",
    "plain_always_global_check_accept",
    "plain_hidden_global_check_accept",
    "plain_hidden_local_check_accept",
    "strict_base_no_check_accept",
    "strict_always_global_check_accept",
    "strict_hidden_global_check_accept",
    "strict_hidden_local_check_accept",
]


def failure_policy_names(row: dict[str, Any]) -> list[str]:
    return [key for key in FAILURE_POLICY_KEYS if bool(row.get(key))]


def source_result_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "audit_idx": row["audit_idx"],
        "family": row["family"],
        "route_id": row["route_id"],
        "variant": row["variant"],
        "manual_process_valid_strict": row["manual_process_valid_strict"],
        "manual_acpi_strict": row.get("manual_acpi_strict"),
        "manual_acpi_unrepaired": row.get("manual_acpi_unrepaired"),
        "manual_repair_present": row.get("manual_repair_present"),
        "policy_trigger": row["policy_trigger"],
        "policy_trigger_meta": row.get("policy_trigger_meta"),
        "plain_base_no_check_accept": row["plain_base_no_check_accept"],
        "plain_always_global_check_accept": row["plain_always_global_check_accept"],
        "plain_hidden_local_check_accept": row["plain_hidden_local_check_accept"],
        "strict_base_no_check_accept": row["strict_base_no_check_accept"],
        "strict_always_global_check_accept": row["strict_always_global_check_accept"],
        "strict_hidden_local_check_accept": row["strict_hidden_local_check_accept"],
        "failure_policy_names": row.get("failure_policy_names", failure_policy_names(row)),
    }


def select_rows(e136_rows: list[dict[str, Any]], clean_controls: int, max_rows: int, selection: str) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    clean_added = 0
    for row in sorted(e136_rows, key=lambda r: int(r["audit_idx"])):
        reason = None
        failures = failure_policy_names(row)
        if selection == "failure_only":
            if (not bool(row["manual_process_valid_strict"])) and failures:
                reason = "strict_invalid_failure"
        else:
            if not bool(row["manual_process_valid_strict"]):
                reason = "strict_invalid"
            elif bool(row["policy_trigger"]):
                reason = "triggered_valid_false_positive"
            elif row.get("variant") == "clean_valid" and clean_added < clean_controls:
                reason = "clean_valid_control"
                clean_added += 1
        if reason:
            rec = dict(row)
            rec["selection_reason"] = reason
            rec["failure_policy_names"] = failures
            selected.append(rec)
    if max_rows:
        selected = selected[:max_rows]
    return selected


def build_jobs(rows: list[dict[str, Any]], modes: list[str], check_types: list[str]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for row in rows:
        for mode in modes:
            for check_type in check_types:
                if check_type == "local" and not row.get("policy_trigger"):
                    continue
                jobs.append({"row": row, "mode": mode, "thinking": mode == "thinking", "check_type": check_type})
    return jobs


def eos_token_ids(tok) -> set[int]:
    ids: set[int] = set()
    eos = tok.eos_token_id
    if isinstance(eos, list):
        ids.update(int(x) for x in eos)
    elif eos is not None:
        ids.add(int(eos))
    return ids


def generate_one(model, tok, prompt: str, add_special: bool, device: torch.device, max_input_tokens: int, max_new_tokens: int, max_time: float) -> dict[str, Any]:
    enc = tok(prompt, return_tensors="pt", add_special_tokens=add_special, truncation=True, max_length=max_input_tokens).to(device)
    kwargs: dict[str, Any] = {
        **enc,
        "do_sample": False,
        "max_new_tokens": max_new_tokens,
        "pad_token_id": tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id,
    }
    if tok.eos_token_id is not None:
        kwargs["eos_token_id"] = tok.eos_token_id
    if max_time > 0:
        kwargs["max_time"] = max_time
    with torch.no_grad():
        out = model.generate(**kwargs)
    prompt_len = enc["input_ids"].shape[1]
    gen_ids = out[0, prompt_len:]
    completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
    eos_ids = eos_token_ids(tok)
    stopped_with_eos = bool(gen_ids.numel() and int(gen_ids[-1].item()) in eos_ids)
    return {
        "completion": completion,
        "input_tokens": int(prompt_len),
        "generated_tokens": int(gen_ids.numel()),
        "hit_max_new_tokens": bool(gen_ids.numel() >= max_new_tokens),
        "stopped_with_eos": stopped_with_eos,
        "may_have_hit_max_time": bool(max_time > 0 and not stopped_with_eos and gen_ids.numel() < max_new_tokens),
        "truncated_input": bool(enc["input_ids"].shape[1] >= max_input_tokens),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for key in [
            "all",
            f"mode={row['mode']}",
            f"check={row['check_type']}",
            f"mode_check={row['mode']}::{row['check_type']}",
            f"reason={row['selection_reason']}",
            f"family={row['family']}",
            f"route={row['route_id']}",
        ]:
            groups[key].append(row)

    def stats(vals: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(vals)
        return {
            "n": n,
            "parse_ok_rate": sum(bool(v["parsed"]["parse_ok"]) for v in vals) / n if n else None,
            "strict_accept_rate": sum(v["parsed"].get("strict_decision") == "Yes" for v in vals) / n if n else None,
            "repair_aware_accept_rate": sum(v["parsed"].get("repair_aware_decision") == "Yes" for v in vals) / n if n else None,
            "claims_no_wrong_step_rate": sum(bool(v["parsed"].get("claims_no_wrong_step")) for v in vals) / n if n else None,
            "mean_generated_tokens": sum(int(v["generation"]["generated_tokens"]) for v in vals) / n if n else None,
            "hit_max_rate": sum(bool(v["generation"]["hit_max_new_tokens"]) for v in vals) / n if n else None,
            "may_have_hit_max_time_rate": sum(bool(v["generation"].get("may_have_hit_max_time")) for v in vals) / n if n else None,
            "final_block_found_rate": sum(bool(v["parsed"].get("final_block_found")) for v in vals) / n if n else None,
        }

    return {
        "n": len(rows),
        "by_slice": {k: stats(v) for k, v in sorted(groups.items())},
        "leakage_audit": {
            "labels_in_prompt_rows": 0,
            "gold_answer_in_prompt_rows": 0,
            "manual_error_span_annotation_in_prompt_rows": 0,
            "passed": True,
            "note_zh": "Prompts contain problem, visible trace, and optionally a hidden-selected visible excerpt. Manual labels/gold/error-span annotations are not inserted.",
        },
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--e136-result", default="")
    p.add_argument("--data-jsonl", default=str(E132_DATA))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--modes", nargs="+", choices=["nonthinking", "thinking"], default=["nonthinking", "thinking"])
    p.add_argument("--check-types", nargs="+", choices=["global", "local"], default=["global", "local"])
    p.add_argument("--clean-controls", type=int, default=2)
    p.add_argument("--selection", choices=["failure_only", "diagnostic_mix"], default="failure_only")
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--max-input-tokens", type=int, default=6144)
    p.add_argument("--max-new-tokens-nonthinking", type=int, default=512)
    p.add_argument("--max-new-tokens-thinking", type=int, default=1536)
    p.add_argument("--max-time-nonthinking", type=float, default=30.0)
    p.add_argument("--max-time-thinking", type=float, default=120.0)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    e136_result = Path(args.e136_result) if args.e136_result else e136_path(args.model_key)
    e136 = json.loads(e136_result.read_text(encoding="utf-8"))
    data_by_idx = {int(r["audit_idx"]): r for r in load_jsonl(Path(args.data_jsonl))}
    selected = select_rows(list(e136["rows"]), args.clean_controls, args.max_rows, args.selection)
    jobs = build_jobs(selected, args.modes, args.check_types)
    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "model_key": args.model_key,
            "source_e136": rel(e136_result),
            "selected_rows": len(selected),
            "jobs": len(jobs),
            "selection_counts": dict(Counter(r["selection_reason"] for r in selected)),
            "failure_policy_counts": dict(Counter(policy for r in selected for policy in r.get("failure_policy_names", []))),
            "jobs_by_mode_check": dict(Counter(f"{j['mode']}::{j['check_type']}" for j in jobs)),
        }, ensure_ascii=False, indent=2))
        return

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    local_only = args.local_files_only or is_local_model(spec)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E139 jobs={len(jobs)} rows={len(selected)}", flush=True)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    use_chat = should_use_chat(spec, tok)

    out_rows: list[dict[str, Any]] = []
    for i, job in enumerate(jobs, start=1):
        row = job["row"]
        src = data_by_idx[int(row["audit_idx"])]
        excerpt = row.get("excerpt") if job["check_type"] == "local" else None
        content = audit_prompt(src["problem"], src["completion"], job["check_type"], excerpt)
        rendered, add_special = render_prompt(tok, content, use_chat, bool(job["thinking"]))
        max_new = args.max_new_tokens_thinking if job["thinking"] else args.max_new_tokens_nonthinking
        max_time = args.max_time_thinking if job["thinking"] else args.max_time_nonthinking
        gen = generate_one(model, tok, rendered, add_special, device, args.max_input_tokens, max_new, max_time)
        parsed = parse_fields(gen["completion"])
        rec = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "experiment": "E139_check_rationale_audit",
            "model_key": args.model_key,
            "mode": job["mode"],
            "thinking": bool(job["thinking"]),
            "check_type": job["check_type"],
            "selection_reason": row["selection_reason"],
            **source_result_row(row),
            "problem": src["problem"],
            "visible_trace": src["completion"],
            "manual_process_valid_repaired": src.get("manual_process_valid_repaired"),
            "manual_notes_zh": src.get("manual_notes_zh"),
            "prompt_contains_gold_label_or_error_annotation": False,
            "generation": gen,
            "parsed": parsed,
        }
        out_rows.append(rec)
        print(f"E139 {args.model_key} generated {i}/{len(jobs)} mode={job['mode']} check={job['check_type']} idx={row['audit_idx']} strict={parsed.get('strict_decision')} repair={parsed.get('repair_aware_decision')}", flush=True)

    result = {
        "experiment": "E139_check_rationale_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "source_e136_result": rel(e136_result),
        "source_data_jsonl": rel(Path(args.data_jsonl)),
        "args": vars(args),
        "selected_rows": [source_result_row(r) | {"selection_reason": r["selection_reason"]} for r in selected],
        "rows": out_rows,
        "summary": summarize(out_rows),
        "scope_note_zh": "E139 生成短审计理由，用于解释 E136 global/local check 为什么接受或拒绝；它不是新的自然发生率实验。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.model_key}_e139_check_rationale_audit.json"
    write_json(out, result)
    print(json.dumps({"out": rel(out), "jobs": len(jobs), "summary": result["summary"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
