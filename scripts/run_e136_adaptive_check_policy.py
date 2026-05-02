#!/usr/bin/env python3
"""E136 stage-1 post-hoc adaptive checking policy."""
from __future__ import annotations

import argparse
import json
import math
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
SCRIPTS = PROJECT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PROJECT / "src"))

import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E132_DATA = PROJECT / "data/processed/e132_suspicious_valid_controls_20260430.jsonl"
E132_DIR = PROJECT / "results/E132_E134_nonthinking_probe"
OUT_DIR = PROJECT / "results/E136_adaptive_check_policy"


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
        "pred_process_valid": yes > no,
        "yes_option": yes_opt,
        "no_option": no_opt,
    }


def global_check_prompt(problem: str, trace: str) -> str:
    return (
        "You are a low-cost process checker for a non-thinking solution. "
        "Check whether the visible reasoning process contains a key mathematical, logical, semantic, unit-conversion, counting, table, code-trace, or algebraic error. "
        "Do not judge by final answer alone. If every visible reasoning step is valid, answer Yes. "
        "If any visible step is invalid, answer No. Answer only Yes or No.\n"
        f"Problem: {problem}\n"
        f"Visible solution: {trace}\n"
        "Are all visible reasoning steps valid? Answer:"
    )


def local_check_prompt(problem: str, trace: str, excerpt: str) -> str:
    return (
        "You are a low-cost local process checker for a non-thinking solution. "
        "A hidden process-risk monitor selected the excerpt below for review. "
        "The monitor may be wrong; do not assume the excerpt is erroneous. "
        "Check the local step and its effect on the rest of the visible solution. "
        "If all visible reasoning steps are valid, answer Yes. If any visible step is invalid, answer No. Answer only Yes or No.\n"
        f"Problem: {problem}\n"
        f"Visible solution: {trace}\n"
        f"Selected excerpt: {excerpt}\n"
        "Are all visible reasoning steps valid? Answer:"
    )


def score_prompt(model, tok, prompt_text: str, use_chat: bool, device: torch.device, max_len: int) -> dict[str, Any]:
    prompt, add = render_prompt(tok, prompt_text, use_chat)
    ids = tok.encode(prompt, add_special_tokens=add)[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
    metrics = yes_no_metrics(out.logits[0, -1], tok)
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {"input_tokens": len(ids), **metrics}


def get_excerpt(row: dict[str, Any], prefix_rows: list[dict[str, Any]], data_by_idx: dict[int, dict[str, Any]], radius: int) -> str:
    trig = [p for p in prefix_rows if int(p["audit_idx"]) == int(row["audit_idx"]) and p.get("hidden_trigger")]
    src = data_by_idx[int(row["audit_idx"])]
    comp = src["completion"]
    if not trig:
        return comp[: min(len(comp), 2 * radius)]
    first = sorted(trig, key=lambda p: (int(p.get("char_end", 0)), str(p.get("stage"))))[0]
    center = int(first.get("char_end") or len(comp))
    start = max(0, center - radius)
    end = min(len(comp), center + radius)
    return comp[start:end]


def policy_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all")].append(row)
        groups[("validity_class", row["validity_class"])].append(row)
        groups[("synthetic_variant", row["synthetic_variant"])].append(row)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        rec: dict[str, Any] = {"slice_type": typ, "slice": key, "n": len(vals)}
        for policy in ["base_no_check", "always_global_check", "hidden_global_check", "hidden_local_check"]:
            accepted = sum(bool(v[f"{policy}_accept"]) for v in vals)
            rec[f"{policy}_accept_rate"] = accepted / len(vals)
        rec["hidden_trigger_rate"] = sum(bool(v["hidden_trigger"]) for v in vals) / len(vals)
        out.append(rec)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--e132-result", default=None)
    p.add_argument("--data", default=str(E132_DATA))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=4096)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--excerpt-radius", type=int, default=220)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    result_path = Path(args.e132_result) if args.e132_result else E132_DIR / f"{args.model_key}_e132_e134_nonthinking_probe_chat.json"
    e132 = json.loads(result_path.read_text(encoding="utf-8"))
    data_by_idx = {int(r["audit_idx"]): r for r in load_jsonl(Path(args.data))}
    rows = list(e132["rows"])
    rows = sorted(rows, key=lambda r: int(r["audit_idx"]))
    if args.max_rows:
        rows = rows[: args.max_rows]
    prefix_rows = e132.get("prefix_rows", [])
    if args.dry_run:
        print(json.dumps({"dry_run": True, "model_key": args.model_key, "rows": len(rows), "source": rel(result_path)}, ensure_ascii=False, indent=2))
        return

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    local_only = args.local_files_only or is_local_model(spec)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E136 rows={len(rows)}", flush=True)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    out_rows = []
    leakage_flags = Counter()
    for i, row in enumerate(rows, start=1):
        src = data_by_idx[int(row["audit_idx"])]
        problem = src["problem"]
        trace = src["completion"]
        excerpt = get_excerpt(row, prefix_rows, data_by_idx, args.excerpt_radius)
        global_metrics = score_prompt(model, tok, global_check_prompt(problem, trace), use_chat, device, args.max_model_len)
        if row.get("hidden_trigger"):
            local_metrics = score_prompt(model, tok, local_check_prompt(problem, trace, excerpt), use_chat, device, args.max_model_len)
        else:
            local_metrics = None
        base_accept = bool(row["pred_process_valid"])
        always_global_accept = bool(global_metrics["pred_process_valid"])
        hidden_global_accept = always_global_accept if row.get("hidden_trigger") else base_accept
        hidden_local_accept = bool(local_metrics["pred_process_valid"]) if local_metrics is not None else base_accept
        rec = {
            "audit_idx": row["audit_idx"],
            "task_id": row["task_id"],
            "family": row.get("family"),
            "route_id": row.get("route_id"),
            "synthetic_variant": row["synthetic_variant"],
            "validity_class": row["validity_class"],
            "process_valid": bool(row["process_valid"]),
            "hidden_trigger": bool(row["hidden_trigger"]),
            "base_no_check_accept": base_accept,
            "always_global_check_accept": always_global_accept,
            "hidden_global_check_accept": hidden_global_accept,
            "hidden_local_check_accept": hidden_local_accept,
            "base_yes_minus_no": row["yes_minus_no"],
            "hidden_score": row["best_component_score"],
            "global_check": global_metrics,
            "local_check": local_metrics,
            "excerpt": excerpt,
        }
        out_rows.append(rec)
        if any(term in global_check_prompt(problem, trace).lower() for term in ["process_valid", "synthetic_variant", "error_span", "manual_"]):
            leakage_flags["metadata_label_terms"] += 1
        if i % 32 == 0 or i == len(rows):
            print(f"E136 checked {i}/{len(rows)}", flush=True)

    result = {
        "experiment": "E136_adaptive_check_policy_stage1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "source_e132_result": rel(result_path),
        "args": vars(args),
        "rows": out_rows,
        "summary": policy_summary(out_rows),
        "leakage_audit": {
            **dict(leakage_flags),
            "passed": all(v == 0 for v in leakage_flags.values()),
            "note_zh": "check prompts contain only problem, visible trace, and hidden-selected visible excerpt; no gold answer or manual label is inserted outside the visible trace.",
        },
        "scope_note_zh": "E136 stage-1 是低成本二次检查/筛选策略，不是 long-CoT 重新解题，也不是最终自适应生成策略。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.model_key}_e136_adaptive_check_policy_stage1.json"
    write_json(out, result)
    print(json.dumps({"out": rel(out), "rows": len(out_rows), "summary": result["summary"][:6], "leakage_audit": result["leakage_audit"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
