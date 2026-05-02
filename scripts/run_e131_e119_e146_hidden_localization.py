#!/usr/bin/env python3
"""E131 hidden/component localization on official E119/E146 process labels.

This experiment reuses the E90 direct/non-thinking strict-verifier machinery:
E61 controlled valid/invalid rows train component validity directions, then
official E119/E146 natural hard-task rows are replayed under the same strict
verifier prompt at error/final/repair/completion prefixes.
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
from statistics import mean
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PROJECT / "src"))

import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

AUDIT_JSONL = PROJECT / "data/processed/e119_e146_process_audit_official_20260430.jsonl"
OUT_DIR = PROJECT / "results/E131_e119_e146_hidden_localization"

FACTOR_RE = re.compile(
    r"\((?:3x\s*-\s*2y|4x\s*\+\s*3y|4x\s*\+\s*y|3x\s*-\s*y)\)\s*"
    r"\((?:4x\s*\+\s*3y|3x\s*-\s*2y|3x\s*-\s*y|4x\s*\+\s*y)\)",
    re.IGNORECASE,
)
WRONG_WORD_RE = re.compile(
    r"\b(wrong|incorrect|not correct|not right|not quite right|mistake|hallucinat|there are 14 such sets|re-?calculate|re-?computed?)\b|"
    r"\b(Wait|No),",
    re.IGNORECASE,
)
COUNTING_RE = re.compile(r"\b(incorrect|there are 14 such sets|14 such sets\?|wrong counting|wrong formula)\b", re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def row_id(row: dict[str, Any]) -> int:
    return int(row.get("audit_idx") or row.get("e119_audit_idx") or row.get("e146_audit_idx"))


def trace_class(row: dict[str, Any]) -> str:
    if row.get("manual_acpi_unrepaired"):
        return "unrepaired_acpi"
    if row.get("manual_acpi_strict") and row.get("manual_repair_present"):
        return "repaired_acpi"
    if row.get("manual_acpi_strict"):
        return "strict_acpi_other"
    if row.get("manual_process_valid_strict") is True and row.get("strict_final_decision"):
        return "strict_valid"
    if row.get("manual_error_type") == "unfinished_fallback_only_not_strict_decision":
        return "fallback_only_unfinished"
    return "other"


def detect_error_marker(row: dict[str, Any]) -> dict[str, Any] | None:
    comp = row.get("completion", "")
    err_type = str(row.get("manual_error_type") or "")
    span = str(row.get("manual_error_span") or "")
    if span and span in comp:
        start = comp.find(span)
        return {"stage": "detected_error_marker_end", "char_end": start + len(span), "span_text": span, "detector": "literal_manual_span"}
    if "factorization" in err_type:
        m = FACTOR_RE.search(comp)
        if m:
            return {"stage": "detected_error_marker_end", "char_end": m.end(), "span_text": m.group(0), "detector": "factorization_regex"}
    if "wrong_initial_or_intermediate_final_answer" in err_type:
        m = e90.FINAL_RE.search(comp)
        if m:
            return {"stage": "detected_error_marker_end", "char_end": m.end(), "span_text": m.group(0), "detector": "first_final_regex"}
    if "counting" in err_type:
        m = COUNTING_RE.search(comp)
        if m:
            return {"stage": "detected_error_marker_end", "char_end": m.end(), "span_text": m.group(0), "detector": "counting_error_regex"}
    if "geometry" in err_type or "shoelace" in err_type:
        m = WRONG_WORD_RE.search(comp)
        if m:
            return {"stage": "detected_error_marker_end", "char_end": m.end(), "span_text": m.group(0), "detector": "wrong_word_regex"}
    return None


def prefix_points(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row["completion"]
    points: list[dict[str, Any]] = []
    error_marker = detect_error_marker(row)
    if error_marker:
        points.append(error_marker)
        points.append(
            {
                "stage": "post_error_240chars",
                "char_end": min(len(comp), int(error_marker["char_end"]) + 240),
                "span_text": comp[int(error_marker["char_end"]) : min(len(comp), int(error_marker["char_end"]) + 240)],
                "detector": "post_error_window",
            }
        )
    first_final = e90.FINAL_RE.search(comp)
    if first_final:
        points.append({"stage": "first_final_answer_end", "char_end": first_final.end(), "span_text": first_final.group(0), "detector": "final_regex"})
    if row.get("manual_repair_present") and error_marker:
        repair = None
        for m in e90.REPAIR_RE.finditer(comp):
            if m.start() > int(error_marker["char_end"]):
                repair = m
                break
        if repair:
            points.append({"stage": "repair_trigger_end", "char_end": repair.end(), "span_text": repair.group(0), "detector": "repair_regex"})
            points.append(
                {
                    "stage": "post_repair_240chars",
                    "char_end": min(len(comp), repair.end() + 240),
                    "span_text": comp[repair.start() : min(len(comp), repair.end() + 240)],
                    "detector": "post_repair_window",
                }
            )
    last_final = None
    for m in e90.FINAL_RE.finditer(comp):
        last_final = m
    if last_final:
        points.append({"stage": "last_final_answer_end", "char_end": last_final.end(), "span_text": last_final.group(0), "detector": "final_regex"})
    points.append({"stage": "completion_end", "char_end": len(comp), "span_text": comp[-160:], "detector": "completion_end"})

    out: list[dict[str, Any]] = []
    seen = set()
    for p in sorted(points, key=lambda x: (int(x["char_end"]), x["stage"])):
        key = (p["stage"], int(p["char_end"]))
        if key not in seen:
            out.append(p)
            seen.add(key)
    return out


def select_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    all_rows = [r for r in load_jsonl(Path(args.audit_jsonl)) if r.get("model_key") == args.model_key]
    if args.target_mode == "unrepaired":
        target = [r for r in all_rows if r.get("manual_acpi_unrepaired")]
    elif args.target_mode == "repaired":
        target = [r for r in all_rows if r.get("manual_acpi_strict") and r.get("manual_repair_present") and not r.get("manual_acpi_unrepaired")]
    elif args.target_mode == "strict_acpi":
        target = [r for r in all_rows if r.get("manual_acpi_strict")]
    elif args.target_mode == "mixed":
        target = [r for r in all_rows if r.get("manual_acpi_strict")]
    else:
        raise ValueError(args.target_mode)
    target = sorted(target, key=row_id)
    if args.max_target_rows:
        target = target[: args.max_target_rows]

    if not args.include_valid_matched:
        return target

    target_tasks = {r.get("task_id") for r in target}
    target_prompts = {r.get("prompt_variant") for r in target}
    candidates = [
        r
        for r in all_rows
        if r.get("manual_process_valid_strict") is True
        and r.get("strict_final_decision")
        and r.get("task_id") in target_tasks
    ]
    by_task_prompt: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in sorted(candidates, key=row_id):
        key = (str(r.get("task_id")), str(r.get("prompt_variant")))
        by_task_prompt[key].append(r)
    valid: list[dict[str, Any]] = []
    for task in sorted(target_tasks):
        prompt_order = sorted(target_prompts)
        for prompt in prompt_order:
            valid.extend(by_task_prompt.get((str(task), str(prompt)), [])[: args.valid_per_task_prompt])
        if not any(r.get("task_id") == task for r in valid):
            valid.extend([r for r in candidates if r.get("task_id") == task][: args.valid_per_task_prompt])
    merged = {row_id(r): r for r in target + valid}
    return [merged[k] for k in sorted(merged)]


def summarize(rows: list[dict[str, Any]], component_keys: list[str], best_key: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[("all", "all")].append(r)
        for key in ["stage", "trace_class", "manual_error_type", "task_id", "prompt_variant", "run_id"]:
            groups[(key, str(r.get(key)))].append(r)
        groups[("trace_class_stage", f"{r['trace_class']}::{r['stage']}")].append(r)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        rec: dict[str, Any] = {
            "slice_type": typ,
            "slice": key,
            "n": len(vals),
            "accept_rate": sum(bool(v["pred_process_valid"]) for v in vals) / len(vals),
            "mean_yes_minus_no": mean(float(v["yes_minus_no"]) for v in vals),
        }
        for comp_key in component_keys:
            scores = [v["component_validity_scores"].get(comp_key) for v in vals if comp_key in v["component_validity_scores"]]
            if scores:
                rec[f"mean_score_{comp_key}"] = mean(float(x) for x in scores)
        best_scores = [v["component_validity_scores"].get(best_key) for v in vals if best_key in v["component_validity_scores"]]
        if best_scores:
            rec["mean_best_component_score"] = mean(float(x) for x in best_scores)
            rec["best_component_key"] = best_key
        out.append(rec)
    return out


def write_dry_run(args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    recs = []
    for r in rows:
        recs.append(
            {
                "audit_idx": row_id(r),
                "model_key": r["model_key"],
                "run_id": r.get("run_id"),
                "task_id": r.get("task_id"),
                "prompt_variant": r.get("prompt_variant"),
                "trace_class": trace_class(r),
                "manual_error_type": r.get("manual_error_type"),
                "points": [
                    {k: p[k] for k in ["stage", "char_end", "detector", "span_text"] if k in p}
                    for p in prefix_points(r)
                ],
            }
        )
    summary = {
        "experiment": "E131_e119_e146_hidden_localization_dry_run",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "args": vars(args),
        "selected_rows": len(rows),
        "by_trace_class": dict(Counter(r["trace_class"] for r in recs)),
        "rows": recs,
        "leakage_note_zh": "dry-run 不加载模型；只检查官方标签行选择和 prefix detector，不把人工标签写入 verifier prompt。",
    }
    out = out_dir / f"{args.model_key}_e131_selection_dry_run.json"
    write_json(out, summary)
    print(json.dumps({"dry_run": True, "rows": len(rows), "out": rel(out)}, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--audit-jsonl", default=str(AUDIT_JSONL))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--target-mode", choices=["mixed", "strict_acpi", "repaired", "unrepaired"], default="mixed")
    p.add_argument("--include-valid-matched", action="store_true")
    p.add_argument("--valid-per-task-prompt", type=int, default=2)
    p.add_argument("--max-target-rows", type=int, default=0)
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--layer-window", type=int, default=2)
    p.add_argument("--hidden-layers", nargs="+", type=int, default=None)
    p.add_argument("--all-layers", action="store_true")
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = select_rows(args)
    if args.dry_run:
        write_dry_run(args, rows)
        return

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E131 rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = e90.should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    best = e90.best_hidden_layer(args.model_key, args.best_layer)
    hidden_layers = e90.selected_hidden_layers(best, len(layers), args.all_layers, args.layer_window, args.hidden_layers)
    component_plan = e90.build_component_plan(layers, hidden_layers)
    print(f"hidden_layers={hidden_layers}", flush=True)
    print(f"component_keys={[f'{k[0]}:{k[1]}' for k in sorted(component_plan)]}", flush=True)
    directions, centers, _direction_keys = e90.train_component_directions(model, tok, use_chat, device, args.max_model_len, hidden_layers, component_plan)
    component_keys = sorted([f"{k[0]}:{k[1]}" for k in directions], key=lambda s: (int(s.split(":", 1)[0]), s.split(":", 1)[1]))
    component_key_tuples = [(int(s.split(":", 1)[0]), s.split(":", 1)[1]) for s in component_keys]
    best_key = f"{best}:residual_hidden_state" if f"{best}:residual_hidden_state" in component_keys else component_keys[0]

    cache_vectors: list[torch.Tensor] = []
    cache_meta: list[dict[str, Any]] = []
    out_rows: list[dict[str, Any]] = []
    for row in rows:
        for pt in prefix_points(row):
            prefix = row["completion"][: int(pt["char_end"])]
            prompt, add = e90.render_prompt(tok, e90.strict_prompt(row["problem"], prefix), use_chat)
            feats, meta = e90.collect_activation(model, tok, prompt, add, device, args.max_model_len, hidden_layers, component_plan)
            scores: dict[str, float] = {}
            vecs = []
            for key in component_key_tuples:
                if key not in feats:
                    continue
                score = float(((feats[key] - centers[key]) * directions[key]).sum().item())
                label = f"{key[0]}:{key[1]}"
                scores[label] = score
                vecs.append(feats[key].to(torch.float16))
            cache_index = len(cache_vectors)
            cache_vectors.append(torch.stack(vecs) if vecs else torch.empty(0))
            rec = {
                "cache_index": cache_index,
                "audit_idx": row_id(row),
                "source_model": row["model_key"],
                "verifier_model": args.model_key,
                "run_id": row.get("run_id"),
                "sampling_profile": row.get("sampling_profile"),
                "task_id": row["task_id"],
                "prompt_variant": row["prompt_variant"],
                "trace_class": trace_class(row),
                "manual_error_type": row.get("manual_error_type"),
                "manual_error_span": row.get("manual_error_span"),
                "manual_process_valid_strict": row.get("manual_process_valid_strict"),
                "manual_process_valid_repaired": row.get("manual_process_valid_repaired"),
                "manual_acpi_strict": row.get("manual_acpi_strict"),
                "manual_acpi_unrepaired": row.get("manual_acpi_unrepaired"),
                "stage": pt["stage"],
                "char_end": int(pt["char_end"]),
                "span_text": pt["span_text"],
                "detector": pt.get("detector"),
                "best_hidden_layer": best,
                "selected_hidden_layers": hidden_layers,
                "component_validity_scores": scores,
                **meta,
            }
            out_rows.append(rec)
            cache_meta.append({k: rec[k] for k in ["cache_index", "audit_idx", "task_id", "stage", "trace_class"]})
            print(f"cached E131 audit_idx={rec['audit_idx']} stage={pt['stage']} class={rec['trace_class']}", flush=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    target = args.target_mode
    pt_path = out_dir / f"{args.model_key}_e131_component_cache_{target}_{suffix}.pt"
    if cache_vectors:
        width = max(v.shape[0] for v in cache_vectors)
        dim = max(v.shape[-1] for v in cache_vectors if v.numel())
        padded = []
        for v in cache_vectors:
            if v.numel() == 0:
                padded.append(torch.zeros((width, dim), dtype=torch.float16))
            elif v.shape[0] < width:
                pad = torch.zeros((width - v.shape[0], v.shape[1]), dtype=torch.float16)
                padded.append(torch.cat([v.cpu(), pad], dim=0))
            else:
                padded.append(v.cpu())
        hidden_tensor = torch.stack(padded)
    else:
        hidden_tensor = torch.empty(0)
    torch.save(
        {
            "component_final_token_vectors": hidden_tensor,
            "component_keys": component_keys,
            "prefix_meta": cache_meta,
            "note": "shape [prefix, component_key, hidden_dim]; E131 uses official E119/E146 labels only offline",
        },
        pt_path,
    )
    result = {
        "experiment": "E131_e119_e146_hidden_localization",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "target_mode": args.target_mode,
        "best_hidden_layer": best,
        "selected_hidden_layers": hidden_layers,
        "component_keys": component_keys,
        "best_component_key": best_key,
        "component_cache_pt": rel(pt_path),
        "component_cache_shape": list(hidden_tensor.shape),
        "args": vars(args),
        "selection": {
            "n_rows": len(rows),
            "by_trace_class": dict(Counter(trace_class(r) for r in rows)),
            "audit_indices": [row_id(r) for r in rows],
        },
        "rows": out_rows,
        "summary": summarize(out_rows, component_keys, best_key),
        "leakage_audit": {
            "labels_in_prompt_rows": 0,
            "error_spans_in_prompt_rows": 0,
            "gold_answer_in_prompt_rows": 0,
            "note_zh": "E119/E146 manual labels and error spans are used only offline for selecting rows/prefix endpoints. The verifier prompt contains only the problem and visible trace prefix.",
        },
        "scope_note_zh": "E131 是 E119/E146 official 标签上的 direct/non-thinking verifier 机制定位；它观察 residual、MLP、token-mixer/attention 相关组件在 error/final/repair/completion 前缀处的过程有效性方向，不是 thinking verifier 实验。",
    }
    out = out_dir / f"{args.model_key}_e131_hidden_localization_{target}_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print(f"wrote {pt_path}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] in {"all", "stage", "trace_class"}:
            compact = {k: v for k, v in s.items() if k in {"slice_type", "slice", "n", "accept_rate", "mean_yes_minus_no", "mean_best_component_score"}}
            print("SUMMARY", compact, flush=True)


if __name__ == "__main__":
    main()
