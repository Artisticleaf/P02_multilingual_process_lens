#!/usr/bin/env python3
"""E136b adaptive checking on E132/E133 suspicious-confidence probe rows.

This runner uses the newer E132/E133 schema where every scored row is a prefix
point.  Manual labels are used only for offline evaluation.  Check prompts only
contain the problem, the visible trace, and, for local checking, a visible text
excerpt selected by the hidden process-risk trigger.
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
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PROJECT / "src"))

import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

DATA = PROJECT / "data/processed/e132_suspicious_valid_controls_20260430.jsonl"
E132_DIR = PROJECT / "results/E132_E133_suspicious_confidence_probe"
OUT_DIR = PROJECT / "results/E136_suspicious_confidence_adaptive_check"

POLICIES = [
    "plain_base_no_check",
    "plain_always_global_check",
    "plain_hidden_global_check",
    "plain_hidden_local_check",
    "strict_base_no_check",
    "strict_always_global_check",
    "strict_hidden_global_check",
    "strict_hidden_local_check",
]

STAGES_EXCLUDED_FROM_POLICY_TRIGGER = {"suspicion_marker_end"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    return e90.render_prompt(tokenizer, content, use_chat)


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    return e90.should_use_chat_template(spec, mode)


def yes_no_metrics(logits: torch.Tensor, tok) -> dict[str, Any]:
    yes, yes_opt = e90.label_logprob(logits, tok, [" Yes", "Yes", " yes", "yes"])
    no, no_opt = e90.label_logprob(logits, tok, [" No", "No", " no", "no"])
    vals = torch.tensor([yes, no], dtype=torch.float64)
    probs = torch.softmax(vals, dim=0)
    entropy = float(-(probs * torch.log(probs + 1e-12)).sum().item())
    return {
        "yes_score": yes,
        "no_score": no,
        "yes_minus_no": yes - no,
        "readout_confidence": abs(yes - no),
        "label_entropy": entropy,
        "p_yes_binary": float(probs[0].item()),
        "p_no_binary": float(probs[1].item()),
        "pred_process_valid": yes > no,
        "yes_option": yes_opt,
        "no_option": no_opt,
    }


def global_check_prompt(problem: str, trace: str) -> str:
    return (
        "You are a low-cost process checker for a visible solution. "
        "Check whether the visible reasoning process contains a key mathematical, logical, semantic, unit-conversion, counting, table-reading, code-trace, proof, or algebraic error. "
        "Do not judge by final answer alone. If every visible reasoning step is valid, answer Yes. "
        "If any visible step is invalid, answer No. Answer only Yes or No.\n"
        f"Problem: {problem}\n"
        f"Visible solution: {trace}\n"
        "Are all visible reasoning steps valid? Answer:"
    )


def local_check_prompt(problem: str, trace: str, excerpt: str) -> str:
    return (
        "You are a low-cost local process checker for a visible solution. "
        "A process-risk monitor selected the excerpt below for review. "
        "The monitor can be wrong; do not assume the excerpt is erroneous. "
        "Check the local step and its effect on the rest of the visible solution. "
        "If all visible reasoning steps are valid, answer Yes. If any visible step is invalid, answer No. Answer only Yes or No.\n"
        f"Problem: {problem}\n"
        f"Visible solution: {trace}\n"
        f"Selected excerpt: {excerpt}\n"
        "Are all visible reasoning steps valid? Answer:"
    )


def score_prompt(model, tok, prompt_text: str, use_chat: bool, device: torch.device, max_len: int) -> dict[str, Any]:
    rendered, add = render_prompt(tok, prompt_text, use_chat)
    ids_all = tok.encode(rendered, add_special_tokens=add)
    truncated_left = max(0, len(ids_all) - max_len)
    ids = ids_all[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)
    with torch.no_grad():
        try:
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False, logits_to_keep=1)
        except TypeError:
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
    metrics = yes_no_metrics(out.logits[0, -1], tok)
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {"input_tokens": len(ids), "truncated_left_tokens": truncated_left, **metrics}


def source_result_path(model_key: str, e132_result: str | None) -> Path:
    if e132_result:
        return Path(e132_result)
    candidates = [
        E132_DIR / f"{model_key}_e132_e133_rowspervariant12_chat.json",
        E132_DIR / f"{model_key}_e132_e133_all_chat.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"No E132/E133 suspicious-confidence result found for {model_key}: {candidates}")


def trace_key(row: dict[str, Any]) -> int:
    return int(row["audit_idx"])


def completion_rows(scored_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [r for r in scored_rows if r.get("stage") == "completion_end"]
    return sorted(rows, key=trace_key)


def policy_trigger_prefixes(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    by_idx: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        stage = str(row.get("stage", ""))
        if stage == "completion_end" or stage in STAGES_EXCLUDED_FROM_POLICY_TRIGGER:
            continue
        if float(row.get("best_component_score", 0.0)) < 0.0:
            by_idx[trace_key(row)].append(row)
    for idx in by_idx:
        by_idx[idx] = sorted(by_idx[idx], key=lambda r: (int(r.get("char_end", 0)), str(r.get("stage", ""))))
    return by_idx


def local_excerpt(src: dict[str, Any], trigger_rows: list[dict[str, Any]], radius: int) -> tuple[str, dict[str, Any] | None]:
    comp = src["completion"]
    if trigger_rows:
        trig = trigger_rows[0]
        center = int(trig.get("char_end") or len(comp))
        start = max(0, center - radius)
        end = min(len(comp), center + radius)
        return comp[start:end], {
            "stage": trig.get("stage"),
            "detector": trig.get("detector"),
            "char_end": int(trig.get("char_end") or 0),
            "span_text": trig.get("span_text", ""),
            "best_component_score": trig.get("best_component_score"),
            "strict_yes_minus_no": trig.get("strict_yes_minus_no"),
            "plain_yes_minus_no": trig.get("plain_yes_minus_no"),
        }
    return comp[: min(len(comp), 2 * radius)], None


def row_variant(row: dict[str, Any]) -> str:
    return str(row.get("variant") or row.get("synthetic_variant") or "")


def row_validity_class(row: dict[str, Any]) -> str:
    if bool(row.get("manual_process_valid_strict")):
        return "strict_valid"
    if bool(row.get("manual_acpi_unrepaired")):
        return "unrepaired_acpi"
    if bool(row.get("manual_repair_present")):
        return "repaired_strict_acpi"
    return "strict_invalid"


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all")].append(row)
        groups[("validity_class", row["validity_class"])].append(row)
        groups[("variant", row["variant"])].append(row)
        groups[("family", row.get("family", ""))].append(row)
        groups[("route_id", row.get("route_id", ""))].append(row)
    out: list[dict[str, Any]] = []
    for (typ, key), vals in sorted(groups.items()):
        rec: dict[str, Any] = {
            "slice_type": typ,
            "slice": key,
            "n": len(vals),
            "manual_strict_valid_rate": sum(bool(v["manual_process_valid_strict"]) for v in vals) / len(vals),
            "policy_trigger_rate": sum(bool(v["policy_trigger"]) for v in vals) / len(vals),
            "completion_hidden_trigger_rate": sum(bool(v["completion_hidden_trigger"]) for v in vals) / len(vals),
            "mean_completion_hidden_score": mean(float(v["completion_hidden_score"]) for v in vals),
        }
        for policy in POLICIES:
            accepted = sum(bool(v[f"{policy}_accept"]) for v in vals)
            rec[f"{policy}_accept_rate"] = accepted / len(vals)
        rec["always_global_check_call_rate"] = 1.0
        rec["hidden_global_check_call_rate"] = sum(bool(v["policy_trigger"]) for v in vals) / len(vals)
        rec["hidden_local_check_call_rate"] = sum(bool(v["policy_trigger"]) for v in vals) / len(vals)
        rec["implementation_note_zh"] = "脚本为公平比较预计算了每条样本的 global check；策略成本应看 *_check_call_rate。"
        out.append(rec)
    return out


def leakage_check_prompt_texts(problem: str, trace: str, excerpt: str | None = None) -> dict[str, bool]:
    text = global_check_prompt(problem, trace)
    if excerpt is not None:
        text += "\n" + local_check_prompt(problem, trace, excerpt)
    lower = text.lower()
    return {
        "manual_label_terms": any(x in lower for x in ["manual_acpi", "manual_process", "validity_class", "synthetic_variant", "gold_answer", "error_span"]),
        "gold_outside_visible_trace_unchecked": False,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--e132-result", default=None)
    p.add_argument("--data-jsonl", default=str(DATA))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--excerpt-radius", type=int, default=220)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    result_path = source_result_path(args.model_key, args.e132_result)
    e132 = json.loads(result_path.read_text(encoding="utf-8"))
    data_by_idx = {int(r["audit_idx"]): r for r in load_jsonl(Path(args.data_jsonl))}
    trace_rows = completion_rows(list(e132["rows"]))
    if args.max_rows:
        trace_rows = trace_rows[: args.max_rows]
    trigger_by_idx = policy_trigger_prefixes(list(e132["rows"]))
    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "model_key": args.model_key,
            "source": rel(result_path),
            "trace_rows": len(trace_rows),
            "policy_trigger_trace_rows": sum(1 for r in trace_rows if trace_key(r) in trigger_by_idx),
            "variants": dict(Counter(row_variant(r) for r in trace_rows)),
            "note_zh": "dry-run only checks row selection and policy-trigger availability; no model load.",
        }, ensure_ascii=False, indent=2))
        return

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    local_only = args.local_files_only or is_local_model(spec)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E136b rows={len(trace_rows)} source={rel(result_path)}", flush=True)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    out_rows: list[dict[str, Any]] = []
    leakage_flags = Counter()
    for i, row in enumerate(trace_rows, start=1):
        idx = trace_key(row)
        src = data_by_idx[idx]
        problem = src["problem"]
        trace = src["completion"]
        triggers = trigger_by_idx.get(idx, [])
        excerpt, trigger_meta = local_excerpt(src, triggers, args.excerpt_radius)
        flags = leakage_check_prompt_texts(problem, trace, excerpt if triggers else None)
        leakage_flags.update({k: int(v) for k, v in flags.items() if v})

        global_metrics = score_prompt(model, tok, global_check_prompt(problem, trace), use_chat, device, args.max_model_len)
        local_metrics = None
        if triggers:
            local_metrics = score_prompt(model, tok, local_check_prompt(problem, trace, excerpt), use_chat, device, args.max_model_len)

        plain_base = bool(row["plain_pred_process_valid"])
        strict_base = bool(row["strict_pred_process_valid"])
        global_accept = bool(global_metrics["pred_process_valid"])
        local_accept = bool(local_metrics["pred_process_valid"]) if local_metrics is not None else None
        policy_trigger = bool(triggers)

        rec = {
            "audit_idx": idx,
            "task_id": row.get("task_id"),
            "source_task_name": row.get("source_task_name"),
            "family": row.get("family"),
            "route_id": row.get("route_id"),
            "variant": row_variant(row),
            "validity_class": row_validity_class(row),
            "manual_process_valid_strict": bool(row["manual_process_valid_strict"]),
            "manual_acpi_strict": bool(row.get("manual_acpi_strict")),
            "manual_acpi_unrepaired": bool(row.get("manual_acpi_unrepaired")),
            "manual_repair_present": bool(row.get("manual_repair_present")),
            "completion_hidden_score": float(row["best_component_score"]),
            "completion_hidden_trigger": float(row["best_component_score"]) < 0.0,
            "completion_best_component_key": row.get("best_component_key"),
            "policy_trigger": policy_trigger,
            "policy_trigger_meta": trigger_meta,
            "plain_base_yes_minus_no": row["plain_yes_minus_no"],
            "plain_base_readout_confidence": row["plain_readout_confidence"],
            "strict_base_yes_minus_no": row["strict_yes_minus_no"],
            "strict_base_readout_confidence": row["strict_readout_confidence"],
            "plain_base_no_check_accept": plain_base,
            "plain_always_global_check_accept": global_accept,
            "plain_hidden_global_check_accept": global_accept if policy_trigger else plain_base,
            "plain_hidden_local_check_accept": local_accept if policy_trigger else plain_base,
            "strict_base_no_check_accept": strict_base,
            "strict_always_global_check_accept": global_accept,
            "strict_hidden_global_check_accept": global_accept if policy_trigger else strict_base,
            "strict_hidden_local_check_accept": local_accept if policy_trigger else strict_base,
            "global_check": global_metrics,
            "local_check": local_metrics,
            "excerpt": excerpt if policy_trigger else None,
        }
        out_rows.append(rec)
        if i % 16 == 0 or i == len(trace_rows):
            print(f"E136b checked {i}/{len(trace_rows)}", flush=True)

    result = {
        "experiment": "E136_suspicious_confidence_adaptive_check_stage1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "source_e132_result": rel(result_path),
        "source_data_jsonl": rel(Path(args.data_jsonl)),
        "args": vars(args),
        "rows": out_rows,
        "summary": summarize(out_rows),
        "leakage_audit": {
            **dict(leakage_flags),
            "passed": all(v == 0 for v in leakage_flags.values()),
            "note_zh": "Prompts contain only the problem, visible solution, and hidden-trigger-selected visible excerpt. Manual labels/error spans/gold are used only offline for grouping/evaluation.",
        },
        "scope_note_zh": "E136b 是 stage-1 后验筛选实验：用 hidden process-risk 触发低成本局部/全局二次检查；它不是 long-CoT 重新解题，也不是在线生成时的激活干预。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"max{args.max_rows}" if args.max_rows else "rowspervariant12"
    out = out_dir / f"{args.model_key}_e136_suspicious_confidence_adaptive_check_{tag}.json"
    write_json(out, result)
    print(json.dumps({
        "out": rel(out),
        "rows": len(out_rows),
        "summary": result["summary"][:8],
        "leakage_audit": result["leakage_audit"],
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
