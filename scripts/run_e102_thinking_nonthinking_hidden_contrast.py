#!/usr/bin/env python3
"""E102 thinking vs non-thinking trace/content/hidden contrast.

This script does not generate new long CoT.  It compares existing Qwen
thinking-generation and non-thinking-generation traces, then scores each trace
with the same strict direct-verifier prompt and E61 component directions.
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

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402
from run_e90_hardtask_component_activation_cache import (  # noqa: E402
    REPAIR_RE,
    build_component_plan,
    collect_activation,
    selected_hidden_layers,
    strict_prompt,
    train_component_directions,
)


E57_QWEN = PROJECT / "results/E57_p0_hard_task_final_correct_harvesting/qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json"
E88_QWEN = PROJECT / "results/E88_answer_first_natural_sample/qwen35_27b_e49_answer_first_no_gold_hard_task_conditioning.json"
E92_QWEN = PROJECT / "results/E92_thinking_hard_task_natural/qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json"
E92_BOXED_QWEN = PROJECT / "results/E92_thinking_hard_task_natural/e92_qwen35_27b_thinking_boxed_k2_max8192_checkpoint.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return load_jsonl(path)
    data = read_json(path)
    return list(data.get("rows", []))


def selected_rows(max_per_source: int) -> list[dict[str, Any]]:
    specs = [
        ("TG_E92", E92_QWEN, "TG"),
        ("TG_E92_boxed_truncated", E92_BOXED_QWEN, "TG"),
        ("NG_E57", E57_QWEN, "NG"),
        ("NG_E88_answer_first", E88_QWEN, "NG"),
    ]
    out = []
    for source, path, mode in specs:
        rows = [
            r
            for r in load_rows(path)
            if r.get("model_key") == "qwen35_27b"
            and (r.get("manual_final_correct") or source == "TG_E92_boxed_truncated")
        ]
        for i, row in enumerate(rows[:max_per_source]):
            rec = dict(row)
            rec["e102_source"] = source
            rec["generation_mode"] = mode
            rec["source_path"] = str(path.relative_to(PROJECT))
            rec["source_index"] = i
            out.append(rec)
    return out


def should_use_chat_template(spec: dict[str, Any]) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    return "base" not in cls and fam in {"qwen35", "gemma", "mistral", "phi", "glm"}


def render_strict(tokenizer: Any, spec: dict[str, Any], problem: str, completion: str) -> tuple[str, bool]:
    content = strict_prompt(problem, completion)
    if not should_use_chat_template(spec) or not getattr(tokenizer, "chat_template", None):
        return content, True
    messages = [{"role": "user", "content": content}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), False


def content_metrics(tokenizer: Any, row: dict[str, Any]) -> dict[str, Any]:
    comp = row.get("completion", "")
    boxed = len(re.findall(r"\\boxed\s*\{", comp))
    final_lines = len(re.findall(r"^\s*final\s*answer\s*[:：]", comp, flags=re.IGNORECASE | re.MULTILINE))
    repair = len(list(REPAIR_RE.finditer(comp)))
    ids = tokenizer.encode(comp, add_special_tokens=False)
    return {
        "completion_chars": len(comp),
        "completion_tokens": len(ids),
        "boxed_count": boxed,
        "final_answer_line_count": final_lines,
        "repair_marker_count": repair,
        "hit_max_new_tokens": bool(row.get("hit_max_new_tokens")),
        "final_marker_found": bool(row.get("final_marker_found")),
        "extraction_method": row.get("extraction_method"),
    }


def summarize(rows: list[dict[str, Any]], component_keys: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all")].append(row)
        groups[("generation_mode", row["generation_mode"])].append(row)
        groups[("source", row["e102_source"])].append(row)
        groups[("task_id", row["task_id"])].append(row)
        groups[("prompt_variant", row["prompt_variant"])].append(row)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        rec: dict[str, Any] = {
            "slice_type": typ,
            "slice": key,
            "n": len(vals),
            "mean_completion_tokens": mean(v["content"]["completion_tokens"] for v in vals),
            "mean_completion_chars": mean(v["content"]["completion_chars"] for v in vals),
            "boxed_rate": sum(v["content"]["boxed_count"] > 0 for v in vals) / len(vals),
            "final_marker_rate": sum(v["content"]["final_marker_found"] for v in vals) / len(vals),
            "hit_max_rate": sum(v["content"]["hit_max_new_tokens"] for v in vals) / len(vals),
            "mean_repair_markers": mean(v["content"]["repair_marker_count"] for v in vals),
            "mean_yes_minus_no": mean(v["strict_verifier_meta"]["yes_minus_no"] for v in vals),
            "accept_rate": sum(v["strict_verifier_meta"]["pred_process_valid"] for v in vals) / len(vals),
        }
        for comp_key in component_keys:
            scores = [v["component_validity_scores"].get(comp_key) for v in vals if comp_key in v["component_validity_scores"]]
            if scores:
                rec[f"mean_score_{comp_key}"] = mean(scores)
        out.append(rec)
    return out


def pairwise(rows: list[dict[str, Any]], best_key: str) -> list[dict[str, Any]]:
    tg = [r for r in rows if r["generation_mode"] == "TG" and r["e102_source"] == "TG_E92"]
    ng = [r for r in rows if r["generation_mode"] == "NG"]
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in ng:
        buckets[(row["task_id"], row["prompt_variant"])].append(row)
    out = []
    for row in tg:
        cand = buckets.get((row["task_id"], row["prompt_variant"]), [])
        if not cand:
            continue
        other = cand[0]
        out.append(
            {
                "task_id": row["task_id"],
                "prompt_variant": row["prompt_variant"],
                "tg_source": row["e102_source"],
                "ng_source": other["e102_source"],
                "tg_tokens": row["content"]["completion_tokens"],
                "ng_tokens": other["content"]["completion_tokens"],
                "delta_tokens": row["content"]["completion_tokens"] - other["content"]["completion_tokens"],
                "tg_yes_minus_no": row["strict_verifier_meta"]["yes_minus_no"],
                "ng_yes_minus_no": other["strict_verifier_meta"]["yes_minus_no"],
                "delta_yes_minus_no": row["strict_verifier_meta"]["yes_minus_no"] - other["strict_verifier_meta"]["yes_minus_no"],
                "tg_best_component_score": row["component_validity_scores"].get(best_key),
                "ng_best_component_score": other["component_validity_scores"].get(best_key),
                "delta_best_component_score": None
                if row["component_validity_scores"].get(best_key) is None or other["component_validity_scores"].get(best_key) is None
                else row["component_validity_scores"][best_key] - other["component_validity_scores"][best_key],
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_27b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E102_thinking_nonthinking_hidden_contrast"))
    p.add_argument("--max-per-source", type=int, default=6)
    p.add_argument("--best-layer", type=int, default=34)
    p.add_argument("--layer-window", type=int, default=1)
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    started = datetime.now().isoformat(timespec="seconds")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = selected_rows(args.max_per_source)
    print(f"[{started}] E102 loading {args.model_key}; rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    hidden_layers = selected_hidden_layers(args.best_layer, len(layers), False, args.layer_window, None)
    component_plan = build_component_plan(layers, hidden_layers)
    directions, centers, direction_keys = train_component_directions(model, tok, True, device, args.max_model_len, hidden_layers, component_plan)
    component_keys = sorted([f"{k[0]}:{k[1]}" for k in directions], key=lambda s: (int(s.split(":", 1)[0]), s.split(":", 1)[1]))
    component_key_tuples = [(int(s.split(":", 1)[0]), s.split(":", 1)[1]) for s in component_keys]
    scored_rows = []
    for i, row in enumerate(rows, start=1):
        prompt, add = render_strict(tok, spec, row["problem"], row["completion"])
        feats, meta = collect_activation(model, tok, prompt, add, device, args.max_model_len, hidden_layers, component_plan)
        scores = {}
        for key in component_key_tuples:
            if key in feats:
                scores[f"{key[0]}:{key[1]}"] = float(((feats[key] - centers[key]) * directions[key]).sum().item())
        scored_rows.append(
            {
                "source_path": row["source_path"],
                "source_index": row["source_index"],
                "e102_source": row["e102_source"],
                "generation_mode": row["generation_mode"],
                "model_key": row["model_key"],
                "task_id": row["task_id"],
                "prompt_variant": row["prompt_variant"],
                "sample_idx": row.get("sample_idx"),
                "manual_final_correct": row.get("manual_final_correct"),
                "gold_answer": row.get("gold_answer"),
                "extracted_final": row.get("extracted_final"),
                "content": content_metrics(tok, row),
                "strict_verifier_meta": meta,
                "component_validity_scores": scores,
            }
        )
        print(f"E102 scored {i}/{len(rows)}", flush=True)
    best_key = f"{args.best_layer}:residual_hidden_state"
    result = {
        "experiment": "E102_thinking_nonthinking_hidden_contrast",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "args": vars(args),
        "hidden_layers": hidden_layers,
        "component_keys": component_keys,
        "direction_keys": direction_keys,
        "rows": scored_rows,
        "summary": summarize(scored_rows, component_keys),
        "pairwise_same_task_variant": pairwise(scored_rows, best_key),
        "audit": {
            "generation_performed": False,
            "manual_labels_in_prompt_rows": 0,
            "note_zh": "E102 不生成新 CoT；只把已有 TG/NG trace 放入同一 strict direct-verifier prompt，比较内容特征和 hidden process-validity score。",
        },
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.model_key}_e102_thinking_nonthinking_hidden_contrast.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    for rec in result["summary"][:12]:
        compact = {k: v for k, v in rec.items() if k in {"slice_type", "slice", "n", "mean_completion_tokens", "mean_yes_minus_no", "accept_rate", "hit_max_rate"}}
        print("SUMMARY", compact, flush=True)


if __name__ == "__main__":
    main()
