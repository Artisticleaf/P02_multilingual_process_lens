#!/usr/bin/env python3
"""E132-E134 non-thinking process-risk probe suite."""
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

import torch

PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PROJECT / "src"))

import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E132_DATA = PROJECT / "data/processed/e132_suspicious_valid_controls_20260430.jsonl"
E131_DIR = PROJECT / "results/E131_e119_e146_hidden_localization"
OUT_DIR = PROJECT / "results/E132_E134_nonthinking_probe"

MARKER_RE = re.compile(
    r"\b(wait|double[- ]?check|verify|uncertain|alternative|equivalent|maybe|actually|however|but)\b|"
    r"复核|检查|不确定|等价|但是|可是|实际|fuhe|jiancha|queding|dengjia",
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


def wilson_ci(k: int, n: int, z: float = 1.96) -> list[float | None]:
    if n <= 0:
        return [None, None]
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return [max(0.0, center - half), min(1.0, center + half)]


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    return e90.should_use_chat_template(spec, mode)


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    return e90.render_prompt(tokenizer, content, use_chat)


def strict_prompt(problem: str, trace: str) -> str:
    return e90.strict_prompt(problem, trace)


def prompt_leakage_check(prompt: str, row: dict[str, Any]) -> dict[str, bool]:
    # Conservative: exact gold labels and manual labels should not appear as
    # audit metadata. The final answer may naturally be inside the visible
    # trace, so this does not count answer-in-trace as leakage.
    lower = prompt.lower()
    bad_terms = ["manual_process_valid", "synthetic_variant", "process_valid", "is_acpi", "error_span"]
    return {
        "metadata_label_terms": any(term in lower for term in bad_terms),
        "manual_error_annotation": "known_error_span" in lower or "manual correction" in lower,
    }


def best_hidden_layer(model_key: str, explicit: int | None) -> int:
    return e90.best_hidden_layer(model_key, explicit)


def selected_hidden_layers(best_layer: int, n_model_layers: int, layer_window: int, explicit: list[int] | None) -> list[int]:
    return e90.selected_hidden_layers(best_layer, n_model_layers, False, layer_window, explicit)


def collect_item(
    model,
    tok,
    use_chat: bool,
    device: torch.device,
    max_len: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
    directions: dict[tuple[int, str], torch.Tensor],
    centers: dict[tuple[int, str], torch.Tensor],
    component_keys: list[str],
    row: dict[str, Any],
    char_end: int | None = None,
) -> dict[str, Any]:
    trace = row["completion"] if char_end is None else row["completion"][:char_end]
    prompt_text = strict_prompt(row["problem"], trace)
    prompt, add = render_prompt(tok, prompt_text, use_chat)
    feats, meta = e90.collect_activation(model, tok, prompt, add, device, max_len, hidden_layers, component_plan)
    scores: dict[str, float] = {}
    for comp_text in component_keys:
        key = (int(comp_text.split(":", 1)[0]), comp_text.split(":", 1)[1])
        if key in feats and key in directions:
            scores[comp_text] = float(((feats[key] - centers[key]) * directions[key]).sum().item())
    leakage = prompt_leakage_check(prompt_text, row)
    return {
        **meta,
        "component_validity_scores": scores,
        "prompt_leakage_flags": leakage,
        "trace_chars": len(trace),
        "marker_count": len(MARKER_RE.findall(trace)),
    }


def trigger_points(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row["completion"]
    points: list[dict[str, Any]] = []
    for m in MARKER_RE.finditer(comp):
        points.append({"stage": "marker_end", "char_end": m.end(), "span_text": m.group(0), "detector": "marker_regex"})
    final = next(FINAL_RE.finditer(comp), None)
    if final:
        points.append({"stage": "first_final_answer_end", "char_end": final.end(), "span_text": final.group(0), "detector": "final_regex"})
    if comp:
        points.append({"stage": "completion_end", "char_end": len(comp), "span_text": comp[-160:], "detector": "completion_end"})
    out = []
    seen = set()
    for p in sorted(points, key=lambda x: (int(x["char_end"]), x["stage"])):
        key = (p["stage"], int(p["char_end"]))
        if key in seen:
            continue
        out.append(p)
        seen.add(key)
    return out


def window_text(text: str, char_end: int, radius: int) -> dict[str, Any]:
    start = max(0, char_end - radius)
    end = min(len(text), char_end + radius)
    return {
        "window_start": start,
        "window_end": end,
        "window_text": text[start:end],
    }


def summarize_rows(rows: list[dict[str, Any]], best_key: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all")].append(row)
        for key in ["synthetic_variant", "validity_class", "family", "route_id"]:
            groups[(key, str(row.get(key)))].append(row)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        n = len(vals)
        trigger = sum(bool(v["hidden_trigger"]) for v in vals)
        accept = sum(bool(v["pred_process_valid"]) for v in vals)
        rec = {
            "slice_type": typ,
            "slice": key,
            "n": n,
            "hidden_trigger_rate": trigger / n,
            "hidden_trigger_wilson_95": wilson_ci(trigger, n),
            "accept_rate": accept / n,
            "accept_wilson_95": wilson_ci(accept, n),
            "mean_yes_minus_no": mean(float(v["yes_minus_no"]) for v in vals),
            "mean_readout_confidence": mean(abs(float(v["yes_minus_no"])) for v in vals),
            "mean_marker_count": mean(int(v["marker_count"]) for v in vals),
        }
        best_scores = [v["component_validity_scores"].get(best_key) for v in vals if best_key in v["component_validity_scores"]]
        if best_scores:
            rec["mean_best_component_score"] = mean(float(x) for x in best_scores)
        out.append(rec)
    return out


def auc(labels: list[bool], scores: list[float]) -> float | None:
    pos = [s for y, s in zip(labels, scores) if y]
    neg = [s for y, s in zip(labels, scores) if not y]
    if not pos or not neg:
        return None
    wins = 0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p > n else 0.5 if p == n else 0.0
    return wins / (len(pos) * len(neg))


def confidence_matched(rows: list[dict[str, Any]], score_key: str) -> dict[str, Any]:
    valid = [r for r in rows if r["process_valid"]]
    invalid = [r for r in rows if not r["process_valid"]]
    pairs = []
    for bad in invalid:
        pool = [r for r in valid if r.get("family") == bad.get("family")] or valid
        good = min(pool, key=lambda r: abs(abs(float(r["yes_minus_no"])) - abs(float(bad["yes_minus_no"]))))
        pairs.append(
            {
                "invalid_audit_idx": bad["audit_idx"],
                "valid_audit_idx": good["audit_idx"],
                "family": bad.get("family"),
                "confidence_gap": abs(abs(float(good["yes_minus_no"])) - abs(float(bad["yes_minus_no"]))),
                "hidden_orders_valid_above_invalid": float(good[score_key]) > float(bad[score_key]),
                "yes_no_orders_valid_above_invalid": float(good["yes_minus_no"]) > float(bad["yes_minus_no"]),
            }
        )
    return {
        "n": len(pairs),
        "mean_confidence_gap": mean([p["confidence_gap"] for p in pairs]) if pairs else None,
        "hidden_pair_accuracy": sum(p["hidden_orders_valid_above_invalid"] for p in pairs) / len(pairs) if pairs else None,
        "yes_no_pair_accuracy": sum(p["yes_no_orders_valid_above_invalid"] for p in pairs) / len(pairs) if pairs else None,
        "pairs_brief": pairs[:32],
    }


def residualized_correlation(rows: list[dict[str, Any]], score_key: str) -> float | None:
    if len(rows) < 4:
        return None
    y = torch.tensor([1.0 if r["process_valid"] else 0.0 for r in rows], dtype=torch.float64)
    h = torch.tensor([float(r[score_key]) for r in rows], dtype=torch.float64)
    controls = torch.tensor(
        [
            [
                abs(float(r["yes_minus_no"])),
                float(r.get("label_entropy", 0.0)),
                float(r.get("input_tokens", 0)),
                float(r.get("marker_count", 0)),
            ]
            for r in rows
        ],
        dtype=torch.float64,
    )
    ones = torch.ones((controls.shape[0], 1), dtype=torch.float64)
    X = torch.cat([ones, controls], dim=1)
    h_res = h - (X @ torch.linalg.lstsq(X, h[:, None]).solution).squeeze(1)
    y_res = y - (X @ torch.linalg.lstsq(X, y[:, None]).solution).squeeze(1)
    denom = torch.sqrt((h_res * h_res).sum() * (y_res * y_res).sum())
    if float(denom.item()) == 0.0:
        return None
    return float(((h_res * y_res).sum() / denom).item())


def build_trigger_windows(rows: list[dict[str, Any]], prefix_rows: list[dict[str, Any]], radius: int, max_windows: int) -> list[dict[str, Any]]:
    by_idx = {int(r["audit_idx"]): r for r in rows}
    candidates = [r for r in prefix_rows if r["hidden_trigger"]]
    candidates = sorted(candidates, key=lambda r: (not bool(r["process_valid"]), r["synthetic_variant"], r["audit_idx"], r["char_end"]))
    out = []
    for row in candidates[:max_windows]:
        src = by_idx[int(row["audit_idx"])]
        out.append(
            {
                "audit_idx": row["audit_idx"],
                "synthetic_variant": row["synthetic_variant"],
                "validity_class": row["validity_class"],
                "process_valid": row["process_valid"],
                "family": row.get("family"),
                "route_id": row.get("route_id"),
                "stage": row["stage"],
                "char_end": row["char_end"],
                "hidden_score": row["best_component_score"],
                "yes_minus_no": row["yes_minus_no"],
                "marker_count": row["marker_count"],
                "audit_labels_todo": {
                    "true_local_error": None,
                    "false_alarm_but_valid": None,
                    "hesitation_only": None,
                    "local_recomputation": None,
                    "explicit_repair": None,
                    "answer_anchoring": None,
                    "ignored_risk": None,
                },
                **window_text(src["completion"], int(row["char_end"]), radius),
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--data", default=str(E132_DATA))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=4096)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--layer-window", type=int, default=1)
    p.add_argument("--hidden-layers", nargs="+", type=int, default=None)
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--trigger-threshold", type=float, default=0.0)
    p.add_argument("--window-radius", type=int, default=220)
    p.add_argument("--max-windows", type=int, default=80)
    return p.parse_args()


def row_validity_class(row: dict[str, Any]) -> str:
    if row["process_valid"]:
        if str(row["synthetic_variant"]).startswith("suspicious"):
            return "suspicious_valid"
        if row["synthetic_variant"] == "low_conf_valid":
            return "low_conf_valid"
        if row["synthetic_variant"] == "unusual_valid":
            return "unusual_valid"
        return "clean_or_markerless_valid"
    if row["synthetic_variant"] == "unrepaired_invalid":
        return "unrepaired_invalid"
    return "repaired_or_subtle_invalid"


def main() -> None:
    args = parse_args()
    rows = load_jsonl(Path(args.data))
    rows = sorted(rows, key=lambda r: int(r["audit_idx"]))
    if args.max_rows:
        # Keep variant coverage deterministic.
        by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_variant[row["synthetic_variant"]].append(row)
        selected: list[dict[str, Any]] = []
        per_variant = max(1, args.max_rows // max(1, len(by_variant)))
        for variant in sorted(by_variant):
            selected.extend(by_variant[variant][:per_variant])
        rows = sorted(selected[: args.max_rows], key=lambda r: int(r["audit_idx"]))

    for row in rows:
        row["process_valid"] = bool(row["manual_process_valid"])
        row["validity_class"] = row_validity_class(row)

    if args.dry_run:
        out = {
            "experiment": "E132_E134_nonthinking_probe_dry_run",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "model_key": args.model_key,
            "rows": len(rows),
            "by_variant": dict(Counter(r["synthetic_variant"] for r in rows)),
            "by_validity_class": dict(Counter(r["validity_class"] for r in rows)),
            "leakage_audit": {
                "metadata_labels_in_prompt_rows": 0,
                "note_zh": "dry-run only inspects data selection; model prompt will contain only problem and completion.",
            },
        }
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{args.model_key}_e132_e134_dry_run.json"
        write_json(path, out)
        print(json.dumps({"dry_run": True, "out": rel(path), "rows": len(rows)}, ensure_ascii=False, indent=2))
        return

    started = datetime.now().isoformat(timespec="seconds")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    local_only = args.local_files_only or is_local_model(spec)
    print(f"[{started}] loading {args.model_key} rows={len(rows)}", flush=True)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    best = best_hidden_layer(args.model_key, args.best_layer)
    hidden_layers = selected_hidden_layers(best, len(layers), args.layer_window, args.hidden_layers)
    component_plan = e90.build_component_plan(layers, hidden_layers)
    directions, centers, component_keys = e90.train_component_directions(model, tok, use_chat, device, args.max_model_len, hidden_layers, component_plan)
    best_key = f"{best}:residual_hidden_state" if f"{best}:residual_hidden_state" in component_keys else component_keys[0]
    print(f"best_key={best_key}; hidden_layers={hidden_layers}; components={len(component_keys)}", flush=True)

    scored_rows = []
    prefix_rows = []
    for i, row in enumerate(rows, start=1):
        rec = collect_item(
            model,
            tok,
            use_chat,
            device,
            args.max_model_len,
            hidden_layers,
            component_plan,
            directions,
            centers,
            component_keys,
            row,
        )
        best_score = float(rec["component_validity_scores"].get(best_key, 0.0))
        scored = {
            **{k: row.get(k) for k in [
                "audit_idx",
                "task_id",
                "source_task_id",
                "family",
                "route_id",
                "synthetic_variant",
                "validity_class",
                "process_valid",
                "is_acpi",
                "suspicious_marker_present",
            ]},
            **rec,
            "best_component_key": best_key,
            "best_component_score": best_score,
            "hidden_trigger": best_score <= args.trigger_threshold,
        }
        scored_rows.append(scored)
        for pt in trigger_points(row):
            prec = collect_item(
                model,
                tok,
                use_chat,
                device,
                args.max_model_len,
                hidden_layers,
                component_plan,
                directions,
                centers,
                component_keys,
                row,
                int(pt["char_end"]),
            )
            pbest = float(prec["component_validity_scores"].get(best_key, 0.0))
            prefix_rows.append(
                {
                    **{k: row.get(k) for k in [
                        "audit_idx",
                        "task_id",
                        "source_task_id",
                        "family",
                        "route_id",
                        "synthetic_variant",
                        "validity_class",
                        "process_valid",
                        "is_acpi",
                    ]},
                    **pt,
                    **prec,
                    "best_component_key": best_key,
                    "best_component_score": pbest,
                    "hidden_trigger": pbest <= args.trigger_threshold,
                }
            )
        if i % 24 == 0 or i == len(rows):
            print(f"scored {i}/{len(rows)} rows; prefixes={len(prefix_rows)}", flush=True)

    labels = [bool(r["process_valid"]) for r in scored_rows]
    best_scores = [float(r["best_component_score"]) for r in scored_rows]
    yes_no = [float(r["yes_minus_no"]) for r in scored_rows]
    e133 = {
        "n": len(scored_rows),
        "hidden_auc_process_valid": auc(labels, best_scores),
        "yes_no_auc_process_valid": auc(labels, yes_no),
        "confidence_matched": confidence_matched(scored_rows, "best_component_score"),
        "residualized_hidden_label_corr_controlling_confidence_entropy_length_markers": residualized_correlation(scored_rows, "best_component_score"),
    }
    trigger_windows = build_trigger_windows(rows, prefix_rows, args.window_radius, args.max_windows)
    leakage_counts = Counter()
    for row in scored_rows + prefix_rows:
        for key, value in row.get("prompt_leakage_flags", {}).items():
            leakage_counts[key] += int(bool(value))

    result = {
        "experiment": "E132_E134_nonthinking_probe",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "best_hidden_layer": best,
        "selected_hidden_layers": hidden_layers,
        "component_keys": component_keys,
        "best_component_key": best_key,
        "rows": scored_rows,
        "prefix_rows": prefix_rows,
        "summary": summarize_rows(scored_rows, best_key),
        "prefix_summary": summarize_rows(prefix_rows, best_key),
        "E133_confidence_matched_process_probe": e133,
        "E134_trigger_window_audit_sheet": trigger_windows,
        "leakage_audit": {
            **dict(leakage_counts),
            "passed": all(v == 0 for v in leakage_counts.values()),
            "note_zh": "verifier prompts contain only problem and visible trace/prefix; labels and spans are offline metadata only.",
        },
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e132_e134_nonthinking_probe_{suffix}.json"
    write_json(out, result)
    print(json.dumps({
        "out": rel(out),
        "model_key": args.model_key,
        "rows": len(scored_rows),
        "prefix_rows": len(prefix_rows),
        "E133": e133,
        "leakage_audit": result["leakage_audit"],
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
