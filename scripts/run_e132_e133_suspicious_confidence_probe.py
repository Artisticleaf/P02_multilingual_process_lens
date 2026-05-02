#!/usr/bin/env python3
"""Run E132 suspicious-valid and E133 confidence-matched process probe.

This script reuses E90 component directions trained on E61.  Manual labels and
error spans are used only offline for grouping/prefix selection; verifier
prompts contain only the problem and a visible trace prefix.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PROJECT / "src"))

import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

DATA = PROJECT / "data/processed/e132_suspicious_valid_controls_20260430.jsonl"
OUT_DIR = PROJECT / "results/E132_E133_suspicious_confidence_probe"

MARKER_RE = re.compile(
    r"\b(wait|double[- ]?check|verify|mistaken|carefully|alternative|second valid check)\b|"
    r"等一下|核对|不太确定|换一个角度|Deng yixia|hedui|keneng|Ling yige",
    re.IGNORECASE,
)
REPAIR_OR_CONTRAST_RE = re.compile(
    r"\b(but|however|actually|instead|correct|using the actual|using the correct)\b|但是|实际|正确|应当|才是|Danshi",
    re.IGNORECASE,
)
FINAL_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*[^\n]+", re.IGNORECASE | re.MULTILINE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def plain_prompt(problem: str, trace: str) -> str:
    return (
        "You are auditing a reasoning trace. Judge whether the visible reasoning steps are valid. "
        "If any mathematical, logical, code-trace, table-interpretation, unit-conversion, or language-semantics step is wrong, answer No. "
        "If the visible reasoning steps are valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Are the visible reasoning steps valid? Answer:"
    )


def yes_no_metrics_from_logits(logits: torch.Tensor, tok) -> dict[str, Any]:
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


def forward_yes_no(model, tok, prompt: str, add: bool, device: torch.device, max_len: int) -> dict[str, Any]:
    ids = tok.encode(prompt, add_special_tokens=add)
    truncated_left = max(0, len(ids) - max_len)
    ids = ids[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)
    with torch.no_grad():
        try:
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False, logits_to_keep=1)
        except TypeError:
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
    metrics = yes_no_metrics_from_logits(out.logits[0, -1], tok)
    metrics["input_tokens"] = len(ids)
    metrics["truncated_left_tokens"] = truncated_left
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return metrics


def first_sentence_end(text: str) -> int | None:
    for sep in [".", "。", "\n"]:
        pos = text.find(sep)
        if pos >= 0:
            return pos + len(sep)
    return None


def prefix_points(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row["completion"]
    points: list[dict[str, Any]] = []
    m = MARKER_RE.search(comp)
    if m:
        points.append({"stage": "suspicion_marker_end", "char_end": m.end(), "span_text": m.group(0), "detector": "suspicion_marker_regex"})
        points.append({"stage": "post_suspicion_240chars", "char_end": min(len(comp), m.end() + 240), "span_text": comp[m.start() : min(len(comp), m.end() + 240)], "detector": "post_suspicion_window"})
    err = row.get("manual_error_span") or ""
    if err and err in comp:
        s = comp.find(err)
        points.append({"stage": "error_span_end", "char_end": s + len(err), "span_text": err, "detector": "literal_error_span"})
        points.append({"stage": "post_error_240chars", "char_end": min(len(comp), s + len(err) + 240), "span_text": comp[s : min(len(comp), s + len(err) + 240)], "detector": "post_error_window"})
    elif row.get("manual_acpi_strict"):
        first_end = first_sentence_end(comp)
        if first_end:
            points.append({"stage": "first_claim_end", "char_end": first_end, "span_text": comp[:first_end], "detector": "first_sentence_fallback"})
    if row.get("manual_acpi_strict"):
        r = REPAIR_OR_CONTRAST_RE.search(comp)
        if r:
            points.append({"stage": "repair_or_contrast_marker_end", "char_end": r.end(), "span_text": r.group(0), "detector": "repair_or_contrast_regex"})
    f = FINAL_RE.search(comp)
    if f:
        points.append({"stage": "first_final_answer_end", "char_end": f.end(), "span_text": f.group(0), "detector": "final_regex"})
    points.append({"stage": "completion_end", "char_end": len(comp), "span_text": comp[-160:], "detector": "completion_end"})
    out: list[dict[str, Any]] = []
    seen = set()
    for p in sorted(points, key=lambda x: (int(x["char_end"]), x["stage"])):
        key = (p["stage"], int(p["char_end"]))
        if key not in seen:
            out.append(p)
            seen.add(key)
    return out


def select_rows(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    variants = set(args.variants or [])
    routes = set(args.routes or [])
    selected = []
    for row in rows:
        if variants and row.get("variant") not in variants:
            continue
        if routes and row.get("route_id") not in routes:
            continue
        selected.append(row)
    selected = sorted(selected, key=lambda r: int(r["audit_idx"]))
    if args.rows_per_variant:
        by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in selected:
            by_variant[str(row["variant"])].append(row)
        limited: list[dict[str, Any]] = []
        for variant in sorted(by_variant):
            limited.extend(by_variant[variant][: args.rows_per_variant])
        selected = sorted(limited, key=lambda r: int(r["audit_idx"]))
    if args.max_rows:
        selected = selected[: args.max_rows]
    return selected


def selected_component_key(best: int, component_keys: list[str]) -> str:
    preferred = f"{best}:residual_hidden_state"
    if preferred in component_keys:
        return preferred
    return component_keys[0]


def component_scores(
    feats: dict[tuple[int, str], torch.Tensor],
    directions: dict[tuple[int, str], torch.Tensor],
    centers: dict[tuple[int, str], torch.Tensor],
) -> dict[str, float]:
    out = {}
    for key, direction in directions.items():
        if key not in feats:
            continue
        out[f"{key[0]}:{key[1]}"] = float(((feats[key] - centers[key]) * direction).sum().item())
    return out


def auc_score(values: list[float], labels: list[bool]) -> float | None:
    pairs = [(v, y) for v, y in zip(values, labels) if not math.isnan(v)]
    pos = [v for v, y in pairs if y]
    neg = [v for v, y in pairs if not y]
    if not pos or not neg:
        return None
    wins = 0.0
    total = len(pos) * len(neg)
    for p in pos:
        for n in neg:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / total


def summarize_group(rows: list[dict[str, Any]], best_key: str) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    return {
        "n": len(rows),
        "hidden_trigger_rate_score_lt_0": sum(r["best_component_score"] < 0 for r in rows) / len(rows),
        "strict_accept_rate": sum(r["strict_pred_process_valid"] for r in rows) / len(rows),
        "plain_accept_rate": sum(r["plain_pred_process_valid"] for r in rows) / len(rows),
        "mean_best_component_score": mean(r["best_component_score"] for r in rows),
        "mean_strict_yes_minus_no": mean(r["strict_yes_minus_no"] for r in rows),
        "mean_plain_yes_minus_no": mean(r["plain_yes_minus_no"] for r in rows),
        "best_component_key": best_key,
    }


def matched_analysis(trace_rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in trace_rows if r["manual_process_valid_strict"]]
    invalid = [r for r in trace_rows if not r["manual_process_valid_strict"]]
    if not valid or not invalid:
        return {"n_pairs": 0, "note": "missing valid or invalid rows"}
    all_rows = valid + invalid
    def zvals(key: str) -> dict[int, float]:
        vals = np.array([float(r[key]) for r in all_rows], dtype=float)
        sd = float(vals.std()) or 1.0
        mu = float(vals.mean())
        return {id(r): (float(r[key]) - mu) / sd for r in all_rows}
    z_conf = zvals("strict_readout_confidence")
    z_len = zvals("strict_input_tokens")
    z_mark = zvals("suspicion_marker_count")
    pairs = []
    for inv in invalid:
        candidates = [r for r in valid if r["source_task_name"] == inv["source_task_name"] and r["route_id"] == inv["route_id"]]
        if not candidates:
            candidates = [r for r in valid if r["source_task_name"] == inv["source_task_name"]]
        if not candidates:
            candidates = valid
        def dist(v):
            return (
                abs(z_conf[id(v)] - z_conf[id(inv)])
                + 0.5 * abs(z_len[id(v)] - z_len[id(inv)])
                + 0.5 * abs(z_mark[id(v)] - z_mark[id(inv)])
            )
        best = min(candidates, key=dist)
        pairs.append(
            {
                "invalid_audit_idx": inv["audit_idx"],
                "valid_audit_idx": best["audit_idx"],
                "invalid_variant": inv["variant"],
                "valid_variant": best["variant"],
                "source_task_name": inv["source_task_name"],
                "route_id": inv["route_id"],
                "distance": dist(best),
                "invalid_hidden_score": inv["best_component_score"],
                "valid_hidden_score": best["best_component_score"],
                "invalid_confidence": inv["strict_readout_confidence"],
                "valid_confidence": best["strict_readout_confidence"],
                "hidden_prefers_valid": best["best_component_score"] > inv["best_component_score"],
            }
        )
    return {
        "n_pairs": len(pairs),
        "hidden_pair_accuracy_valid_gt_invalid": sum(p["hidden_prefers_valid"] for p in pairs) / len(pairs),
        "mean_match_distance": mean(p["distance"] for p in pairs),
        "pairs": pairs,
    }


def analyze(scored: list[dict[str, Any]], best_key: str) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        for typ, key in [
            ("stage", row["stage"]),
            ("variant", row["variant"]),
            ("route_id", row["route_id"]),
            ("family", row["family"]),
            ("variant_stage", f"{row['variant']}::{row['stage']}"),
        ]:
            groups[(typ, key)].append(row)
    summary = [
        {"slice_type": typ, "slice": key, **summarize_group(vals, best_key)}
        for (typ, key), vals in sorted(groups.items())
    ]
    trace_rows = [r for r in scored if r["stage"] == "completion_end"]
    labels = [bool(r["manual_process_valid_strict"]) for r in trace_rows]
    hidden = [float(r["best_component_score"]) for r in trace_rows]
    confidence = [float(r["strict_readout_confidence"]) for r in trace_rows]
    analysis = {
        "trace_level_rows": len(trace_rows),
        "hidden_auc_valid_vs_invalid_completion": auc_score(hidden, labels),
        "strict_confidence_auc_valid_vs_invalid_completion": auc_score(confidence, labels),
        "plain_accept_auc_valid_vs_invalid_completion": auc_score([float(r["plain_yes_minus_no"]) for r in trace_rows], labels),
        "summary": summary,
        "matched_analysis_completion": matched_analysis(trace_rows),
        "variant_completion": {
            key: summarize_group([r for r in trace_rows if r["variant"] == key], best_key)
            for key in sorted({r["variant"] for r in trace_rows})
        },
    }
    return analysis


def write_dry_run(args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    recs = []
    for row in rows:
        recs.append(
            {
                "audit_idx": row["audit_idx"],
                "variant": row["variant"],
                "route_id": row["route_id"],
                "source_task_name": row["source_task_name"],
                "manual_process_valid_strict": row["manual_process_valid_strict"],
                "points": prefix_points(row),
            }
        )
    out = out_dir / f"{args.model_key}_e132_e133_selection_dry_run.json"
    write_json(out, {
        "experiment": "E132_E133_dry_run",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "args": vars(args),
        "rows": len(rows),
        "by_variant": dict(Counter(r["variant"] for r in rows)),
        "prefix_rows": sum(len(r["points"]) for r in recs),
        "selection": recs,
    })
    print(json.dumps({"dry_run": True, "rows": len(rows), "out": rel(out)}, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--data-jsonl", default=str(DATA))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--layer-window", type=int, default=1)
    p.add_argument("--hidden-layers", nargs="+", type=int, default=None)
    p.add_argument("--all-layers", action="store_true")
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--rows-per-variant", type=int, default=0)
    p.add_argument("--variants", nargs="+", default=None)
    p.add_argument("--routes", nargs="+", default=None)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = select_rows(load_jsonl(Path(args.data_jsonl)), args)
    if args.dry_run:
        write_dry_run(args, rows)
        return
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E132/E133 rows={len(rows)}", flush=True)
    tok = load_tokenizer(spec["path"], local_files_only=args.local_files_only or is_local_model(spec))
    use_chat = e90.should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=args.local_files_only or is_local_model(spec))
    device = model_device(model)
    layers = get_transformer_layers(model)
    best = e90.best_hidden_layer(args.model_key, args.best_layer)
    hidden_layers = e90.selected_hidden_layers(best, len(layers), args.all_layers, args.layer_window, args.hidden_layers)
    component_plan = e90.build_component_plan(layers, hidden_layers)
    print(f"hidden_layers={hidden_layers}", flush=True)
    print(f"component hooks={len(component_plan)}", flush=True)
    directions, centers, component_keys = e90.train_component_directions(
        model,
        tok,
        use_chat,
        device,
        args.max_model_len,
        hidden_layers,
        component_plan,
    )
    best_key = selected_component_key(best, component_keys)
    best_tuple = (int(best_key.split(":", 1)[0]), best_key.split(":", 1)[1])
    scored: list[dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        for point in prefix_points(row):
            trace = row["completion"][: int(point["char_end"])]
            strict_rendered, strict_add = e90.render_prompt(tok, e90.strict_prompt(row["problem"], trace), use_chat)
            feats, strict_meta = e90.collect_activation(
                model,
                tok,
                strict_rendered,
                strict_add,
                device,
                args.max_model_len,
                hidden_layers,
                component_plan,
            )
            scores = component_scores(feats, directions, centers)
            plain_rendered, plain_add = e90.render_prompt(tok, plain_prompt(row["problem"], trace), use_chat)
            plain_meta = forward_yes_no(model, tok, plain_rendered, plain_add, device, args.max_model_len)
            strict_conf = abs(float(strict_meta["yes_minus_no"]))
            vals = torch.tensor([strict_meta["yes_score"], strict_meta["no_score"]], dtype=torch.float64)
            probs = torch.softmax(vals, dim=0)
            strict_entropy = float(-(probs * torch.log(probs + 1e-12)).sum().item())
            rec = {
                "audit_idx": row["audit_idx"],
                "model_key": args.model_key,
                "source_task_name": row["source_task_name"],
                "task_id": row["task_id"],
                "family": row["family"],
                "route_id": row["route_id"],
                "variant": row["variant"],
                "manual_process_valid_strict": row["manual_process_valid_strict"],
                "manual_acpi_strict": row["manual_acpi_strict"],
                "manual_acpi_unrepaired": row["manual_acpi_unrepaired"],
                "manual_repair_present": row["manual_repair_present"],
                "manual_error_span": row.get("manual_error_span"),
                "suspicion_marker_count": row.get("suspicion_marker_count", 0),
                "stage": point["stage"],
                "char_end": int(point["char_end"]),
                "span_text": point.get("span_text", ""),
                "detector": point.get("detector", ""),
                "strict_input_tokens": strict_meta["input_tokens"],
                "strict_truncated_left_tokens": strict_meta["truncated_left_tokens"],
                "strict_yes_minus_no": strict_meta["yes_minus_no"],
                "strict_readout_confidence": strict_conf,
                "strict_label_entropy": strict_entropy,
                "strict_pred_process_valid": strict_meta["pred_process_valid"],
                "plain_input_tokens": plain_meta["input_tokens"],
                "plain_truncated_left_tokens": plain_meta["truncated_left_tokens"],
                "plain_yes_minus_no": plain_meta["yes_minus_no"],
                "plain_readout_confidence": plain_meta["readout_confidence"],
                "plain_label_entropy": plain_meta["label_entropy"],
                "plain_pred_process_valid": plain_meta["pred_process_valid"],
                "component_validity_scores": scores,
                "best_component_key": best_key,
                "best_component_score": float(scores.get(best_key, scores.get(f"{best_tuple[0]}:{best_tuple[1]}", float("nan")))),
            }
            scored.append(rec)
        if i % 12 == 0 or i == len(rows):
            print(f"E132/E133 scored source rows {i}/{len(rows)} prefix_rows={len(scored)}", flush=True)
    result = {
        "experiment": "E132_E133_suspicious_confidence_probe",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "best_hidden_layer": best,
        "selected_hidden_layers": hidden_layers,
        "component_keys": component_keys,
        "best_component_key": best_key,
        "args": vars(args),
        "source_rows": len(rows),
        "prefix_rows": len(scored),
        "rows": scored,
        "analysis": analyze(scored, best_key),
        "leakage_audit": {
            "labels_in_prompt_rows": 0,
            "error_spans_in_prompt_rows": 0,
            "gold_answer_in_prompt_rows": 0,
            "note_zh": "manual labels/error spans/gold answers are offline metadata only. Verifier prompts contain problem plus visible trace prefix.",
        },
        "scope_note_zh": "E132/E133 是小探针：检查可疑但正确 trace 的 hidden false trigger，以及 confidence-matched valid/invalid 区分。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    if args.max_rows:
        row_tag = f"max{args.max_rows}"
    elif args.rows_per_variant:
        row_tag = f"rowspervariant{args.rows_per_variant}"
    else:
        row_tag = "all"
    out = out_dir / f"{args.model_key}_e132_e133_{row_tag}_{suffix}.json"
    write_json(out, result)
    print(json.dumps({"out": rel(out), "source_rows": len(rows), "prefix_rows": len(scored), "best_key": best_key}, ensure_ascii=False, indent=2), flush=True)
    for key, stats in result["analysis"]["variant_completion"].items():
        print("VARIANT", key, stats, flush=True)


if __name__ == "__main__":
    main()
