#!/usr/bin/env python3
"""Run E171 hidden-monitor rescue on baseline-wrong original problems.

Pipeline:
1. Load E171 non-thinking baseline rows for one model.
2. Keep only clean original-problem failures from that same model.
3. Teacher-force the model over automatic prefixes of its own wrong trace.
4. Select a trigger with the E166 calibrated hidden monitor.
5. Compare non-thinking continuation, hidden-generic warning, hidden-localized
   warning, random-span warning, and the reused baseline answer.
"""
from __future__ import annotations

import argparse
import json
import random
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
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))

import run_e49_hard_task_conditioning_official as e49  # noqa: E402
import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
import run_e166_hardened_hidden_monitor_replay as e166  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

OUT_DIR = PROJECT / "results/E171_main_claim_hidden_rescue"
CALIBRATION = PROJECT / "reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.json"

PROMPT_VARIANTS = {
    "baseline_regenerate": (
        "Solve the following problem carefully. Show the reasoning needed to justify the result. "
        "Do not give the final answer before the reasoning. End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}"
    ),
    "prefix_continue": (
        "Continue the partial solution below. Do not restart unless the partial solution itself requires revision. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "hidden_generic_warning": (
        "A hidden monitor raised a low-confidence warning somewhere in the partial solution below. "
        "Recheck the partial solution from the original problem, correct it if needed, and continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "hidden_localized_warning": (
        "A hidden monitor flagged this visible span as potentially abnormal: `{localized_span}`. "
        "This signal was computed from the model's hidden/component state after the causal prefix, not from a gold answer. "
        "Correct the local step if needed, then continue. End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
    "random_matched_warning": (
        "A hidden monitor flagged this visible span as potentially abnormal: `{random_span}`. "
        "Recheck that location first; avoid changing unrelated correct steps. Then continue. "
        "End with exactly one line `Final answer: <answer>`.\n\n"
        "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
    ),
}

BOXED_RE = re.compile(r"\\boxed\s*\{\s*(-?\d+(?:\.\d+)?)\s*\}", re.IGNORECASE)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def load_baseline_rows(path_text: str, model_key: str) -> tuple[list[dict[str, Any]], str]:
    if path_text:
        path = Path(path_text)
        if path.suffix == ".jsonl":
            return load_jsonl(path), rel_or_str(path)
        data = load_json(path)
        return list(data.get("rows", [])), rel_or_str(path)
    matches = sorted(OUT_DIR.glob(f"{model_key}_e171_baseline_nonthinking*.json"))
    matches = [p for p in matches if "smoke" not in p.name] or matches
    if matches:
        data = load_json(matches[-1])
        return list(data.get("rows", [])), str(matches[-1].relative_to(PROJECT))
    ckpt = PROJECT / f"logs/e171_baseline_{model_key}_checkpoint_20260502.jsonl"
    rows = load_jsonl(ckpt)
    return list({r["task_id"]: r for r in rows}.values()), str(ckpt.relative_to(PROJECT))


def rel_or_str(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT))
    except ValueError:
        return str(path)


def calibration_for_model(model_key: str) -> dict[str, Any]:
    data = load_json(CALIBRATION)
    for row in data["models"]:
        if row["model_key"] == model_key:
            return row
    raise KeyError(f"No E166 calibration for {model_key}")


def clean_failure_rows(rows: list[dict[str, Any]], include_no_final: bool, include_hitmax: bool) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if bool(row.get("manual_final_correct")):
            continue
        if not include_hitmax and bool(row.get("hit_max_new_tokens")):
            continue
        body = reasoning_body(str(row.get("completion", ""))).strip()
        if body:
            out.append(row)
    return out


def reasoning_body(completion: str) -> str:
    matches = list(re.finditer(r"^\s*final\s*answer\s*[:：]\s*[^\n]+", completion, flags=re.IGNORECASE | re.MULTILINE))
    if matches:
        return completion[: matches[-1].start()].strip()
    boxed = list(re.finditer(r"\\boxed\s*\{[^}]+\}", completion, flags=re.IGNORECASE))
    if boxed:
        return completion[: boxed[-1].start()].strip()
    return completion.strip()


def boundary_points(text: str, min_chars: int, chunk_chars: int) -> list[dict[str, Any]]:
    candidates: list[tuple[int, str]] = []
    for m in re.finditer(r"\n+", text):
        candidates.append((m.end(), "line_end"))
    for m in re.finditer(r"(?<=[.!?。！？；;])(?:\s+|$)", text):
        candidates.append((m.end(), "sentence_end"))
    if chunk_chars > 0:
        for end in range(chunk_chars, len(text), chunk_chars):
            snap = text.rfind(" ", 0, end)
            if snap < min_chars:
                snap = end
            candidates.append((snap, "chunk_end"))
    candidates.append((len(text), "completion_body_end"))
    out = []
    seen = set()
    previous = 0
    for end, kind in sorted(candidates, key=lambda x: x[0]):
        end = min(max(int(end), 0), len(text))
        if end < min_chars or end in seen:
            continue
        span_start = previous
        visible = text[span_start:end].strip()
        if not visible:
            visible = text[max(0, end - 360) : end].strip()
        out.append({"char_end": end, "boundary_kind": kind, "visible_span": visible})
        seen.add(end)
        previous = end
    return out


def score_risk(score: float) -> float:
    return -float(score)


def render_prefill_prompt(tokenizer, spec: dict[str, Any], problem: str, prefix: str) -> tuple[str, bool, bool]:
    row = {"problem": problem, "prefix_text": prefix}
    content = e166.render_prefill_content(row, "generation_prefill")
    return e166.render_chat(tokenizer, spec, content, "official_if_chat")


def render_generation_chat(tokenizer, spec: dict[str, Any], content: str) -> tuple[str, bool, bool]:
    use_chat = e49.should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False


def component_key_tuple(key: str) -> tuple[int, str]:
    layer, comp = key.split(":", 1)
    return int(layer), comp


def random_span(boundaries: list[dict[str, Any]], trigger_end: int, seed: int) -> str:
    pool = [b["visible_span"] for b in boundaries if int(b["char_end"]) != trigger_end and b["visible_span"].strip()]
    if not pool:
        pool = [b["visible_span"] for b in boundaries if b["visible_span"].strip()]
    if not pool:
        return "the partial solution"
    rng = random.Random(seed)
    return rng.choice(pool)


def clip_text(text: str, max_chars: int = 900) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head - 24
    return text[:head].rstrip() + " ... [middle omitted] ... " + text[-tail:].lstrip()


def canonical_extracted_answer(text: str) -> str:
    boxed = list(BOXED_RE.finditer(text))
    if boxed:
        return boxed[-1].group(1).strip()
    simple_box = re.fullmatch(r"\s*\\boxed\s*\{\s*([^}]+?)\s*\}\s*\.?\s*", text, flags=re.IGNORECASE)
    if simple_box:
        return simple_box.group(1).strip()
    return text.strip()


def build_hidden_cases(
    baseline_rows: list[dict[str, Any]],
    model_key: str,
    calibration: dict[str, Any],
    model,
    tokenizer,
    spec: dict[str, Any],
    device: torch.device,
    max_model_len: int,
    layer_window: int,
    min_prefix_chars: int,
    chunk_chars: int,
    random_seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    best_key = calibration["best_key"]
    threshold = float(calibration["best_key_record"]["high_precision_eval"]["threshold"])
    best_hidden_idx, _best_comp = component_key_tuple(best_key)
    layers = get_transformer_layers(model)
    hidden_layers = e90.selected_hidden_layers(best_hidden_idx, len(layers), False, layer_window, None)
    component_plan = e90.build_component_plan(layers, hidden_layers)
    use_chat = e90.should_use_chat_template(spec, "official_if_chat") and bool(getattr(tokenizer, "chat_template", None))
    directions, centers, _ = e90.train_component_directions(model, tokenizer, use_chat, device, max_model_len, hidden_layers, component_plan)
    component_keys = sorted([f"{k[0]}:{k[1]}" for k in directions], key=lambda s: (int(s.split(":", 1)[0]), s.split(":", 1)[1]))
    component_key_tuples = [component_key_tuple(s) for s in component_keys]
    best_tuple = component_key_tuple(best_key)
    if best_tuple not in directions:
        raise RuntimeError(f"Best E166 component {best_key} not captured; captured={component_keys}")

    cache_vectors: list[torch.Tensor] = []
    cache_meta: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    for base_idx, row in enumerate(baseline_rows, start=1):
        body = reasoning_body(row["completion"])
        boundaries = boundary_points(body, min_prefix_chars, chunk_chars)
        prefix_records: list[dict[str, Any]] = []
        for prefix_idx, boundary in enumerate(boundaries):
            prefix = body[: int(boundary["char_end"])]
            prompt, used_chat, add = render_prefill_prompt(tokenizer, spec, row["problem"], prefix)
            feats, meta = e166.collect_prefill_activation(model, tokenizer, prompt, add, device, max_model_len, hidden_layers, component_plan)
            scores: dict[str, float] = {}
            vecs: list[torch.Tensor] = []
            for key in component_key_tuples:
                if key in feats:
                    label = f"{key[0]}:{key[1]}"
                    scores[label] = float(((feats[key] - centers[key]) * directions[key]).sum().item())
                    vecs.append(feats[key].to(torch.float16))
            cache_index = len(cache_vectors)
            cache_vectors.append(torch.stack(vecs) if vecs else torch.empty(0))
            best_risk = score_risk(scores[best_key])
            rec = {
                "cache_index": cache_index,
                "prefix_index": prefix_idx,
                "prefix_id": f"e171_{model_key}_{row['task_id']}_auto_{prefix_idx:03d}",
                "task_id": row["task_id"],
                "family": row["family"],
                "boundary_kind": boundary["boundary_kind"],
                "prefix_char_end": int(boundary["char_end"]),
                "visible_span": boundary["visible_span"],
                "prompt_used_chat_template": used_chat,
                "selected_hidden_layers": hidden_layers,
                "component_validity_scores": scores,
                "hidden_component_key": best_key,
                "hidden_risk": best_risk,
                "hidden_threshold": threshold,
                "hidden_threshold_crossed": bool(best_risk >= threshold),
                **meta,
            }
            prefix_records.append(rec)
            cache_meta.append(
                {
                    "cache_index": cache_index,
                    "task_id": row["task_id"],
                    "family": row["family"],
                    "prefix_id": rec["prefix_id"],
                    "prefix_char_end": rec["prefix_char_end"],
                    "boundary_kind": rec["boundary_kind"],
                    "hidden_risk": rec["hidden_risk"],
                    "hidden_threshold_crossed": rec["hidden_threshold_crossed"],
                }
            )
        if not prefix_records:
            continue
        ordered = sorted(prefix_records, key=lambda r: (r["prefix_char_end"], r["prefix_index"]))
        trigger = next((r for r in ordered if r["hidden_threshold_crossed"]), None)
        if trigger is None:
            trigger = max(ordered, key=lambda r: r["hidden_risk"])
            trigger_source = "fallback_top_risk_no_threshold_crossing"
        else:
            trigger_source = "first_high_precision_threshold_crossing"
        ranked = sorted(ordered, key=lambda r: r["hidden_risk"], reverse=True)
        trigger_rank = 1 + next(i for i, r in enumerate(ranked) if r["prefix_id"] == trigger["prefix_id"])
        trigger_end = int(trigger["prefix_char_end"])
        case = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "experiment": "E171_hidden_rescue_case",
            "case_id": f"e171_{model_key}_{row['task_id']}",
            "model_key": model_key,
            "task_id": row["task_id"],
            "source_task_id": row.get("source_task_id", ""),
            "task_source": row.get("task_source", ""),
            "source_experiment": row.get("source_experiment", ""),
            "family": row["family"],
            "difficulty_tier": row.get("difficulty_tier", ""),
            "problem": row["problem"],
            "gold_answer": row["gold_answer"],
            "baseline_completion": row["completion"],
            "baseline_reasoning_body": body,
            "baseline_extracted_final": row.get("extracted_final", ""),
            "baseline_final_marker_found": bool(row.get("final_marker_found")),
            "baseline_generated_tokens": int(row.get("generated_tokens") or 0),
            "baseline_prompt_tokens": int(row.get("prompt_tokens") or 0),
            "baseline_hit_max_new_tokens": bool(row.get("hit_max_new_tokens")),
            "baseline_manual_final_correct": bool(row.get("manual_final_correct")),
            "hidden_component_key": best_key,
            "hidden_threshold": threshold,
            "hidden_trigger_source": trigger_source,
            "hidden_trigger_prefix_id": trigger["prefix_id"],
            "hidden_trigger_prefix_char_end": trigger_end,
            "hidden_trigger_boundary_kind": trigger["boundary_kind"],
            "hidden_trigger_risk": trigger["hidden_risk"],
            "hidden_trigger_rank_by_risk": trigger_rank,
            "hidden_trigger_threshold_crossed": bool(trigger["hidden_threshold_crossed"]),
            "hidden_trigger_yes_minus_no": trigger.get("yes_minus_no"),
            "hidden_trigger_next_token_entropy": trigger.get("next_token_entropy"),
            "prefix_text": body[:trigger_end],
            "localized_span": clip_text(trigger["visible_span"]),
            "localized_span_unclipped": trigger["visible_span"],
            "random_location_span": clip_text(random_span(boundaries, trigger_end, random_seed + base_idx)),
            "automatic_prefix_candidates": len(prefix_records),
            "prefix_records": prefix_records,
            "leakage_policy": "Runtime repair prompts use problem, prefix_text, hidden-derived localized_span, or random span. Gold answer is offline only.",
        }
        cases.append(case)
        print(
            f"E171 hidden cases {len(cases)}/{len(baseline_rows)} task={row['task_id']} trigger={trigger_source} risk={trigger['hidden_risk']:.3f}",
            flush=True,
        )

    cache_info: dict[str, Any] = {
        "component_keys": component_keys,
        "component_key_tuples": component_key_tuples,
        "monitor_directions": [directions[k].to(torch.float16).cpu() for k in component_key_tuples],
        "monitor_centers": [centers[k].to(torch.float16).cpu() for k in component_key_tuples],
        "cache_vectors": cache_vectors,
        "cache_meta": cache_meta,
        "selected_hidden_layers": hidden_layers,
        "best_hidden_layer_from_e166_key": best_hidden_idx,
    }
    return cases, cache_info


def save_hidden_cache(path: Path, cache_info: dict[str, Any]) -> list[int]:
    vectors = cache_info.pop("cache_vectors")
    if vectors:
        width = max(v.shape[0] for v in vectors)
        dim = max(v.shape[-1] for v in vectors if v.numel())
        padded = []
        for v in vectors:
            if v.numel() == 0:
                padded.append(torch.zeros((width, dim), dtype=torch.float16))
            elif v.shape[0] < width:
                pad = torch.zeros((width - v.shape[0], v.shape[1]), dtype=torch.float16)
                padded.append(torch.cat([v.cpu(), pad], dim=0))
            else:
                padded.append(v.cpu())
        tensor = torch.stack(padded)
    else:
        tensor = torch.empty(0)
    payload = {
        "component_final_token_vectors": tensor,
        "component_keys": cache_info["component_keys"],
        "monitor_directions": torch.stack(cache_info["monitor_directions"]).cpu() if cache_info["monitor_directions"] else torch.empty(0),
        "monitor_centers": torch.stack(cache_info["monitor_centers"]).cpu() if cache_info["monitor_centers"] else torch.empty(0),
        "prefix_meta": cache_info["cache_meta"],
        "selected_hidden_layers": cache_info["selected_hidden_layers"],
        "best_hidden_layer_from_e166_key": cache_info["best_hidden_layer_from_e166_key"],
        "note": "E171 hidden cache over model-owned baseline-wrong traces. Vectors are teacher-forced final-prefix-token component states.",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return list(tensor.shape)


def render_content(case: dict[str, Any], variant: str) -> str:
    return PROMPT_VARIANTS[variant].format(
        problem=case["problem"],
        prefix=case["prefix_text"],
        localized_span=case.get("localized_span") or "the hidden-triggered span",
        random_span=case.get("random_location_span") or "the partial solution",
    )


def is_complete_checkpoint_row(row: dict[str, Any]) -> bool:
    if bool(row.get("retained_from_baseline_failure")):
        return True
    return bool(row.get("final_marker_found")) and not bool(row.get("hit_max_new_tokens"))


def load_complete_resume_rows(path_text: str) -> tuple[dict[tuple[str, str], dict[str, Any]], Counter[str]]:
    stats: Counter[str] = Counter()
    complete: dict[tuple[str, str], dict[str, Any]] = {}
    if not path_text:
        return complete, stats
    path = Path(path_text)
    rows = load_jsonl(path)
    stats["rows_seen"] = len(rows)
    for row in rows:
        key = (row["case_id"], row["prompt_variant"])
        if is_complete_checkpoint_row(row):
            retained = dict(row)
            retained["retained_from_resume_checkpoint"] = True
            retained["resume_source_checkpoint"] = str(path)
            retained["resume_policy"] = "kept_complete_final_marker_and_not_hit_max"
            complete[key] = retained
            stats["complete_rows"] += 1
        else:
            stats["incomplete_rows_to_rerun"] += 1
    stats["unique_complete_jobs"] = len(complete)
    return complete, stats


def reused_baseline_row(case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    extracted_raw, marker, method = e49.extract_final_answer(case["baseline_completion"], allow_fallback=True)
    extracted = canonical_extracted_answer(extracted_raw)
    final_correct = e49.normalize_answer(extracted) == e49.normalize_answer(str(case["gold_answer"]))
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E171_hidden_rescue_from_baseline_wrong",
        "model_key": args.model_key,
        "case_id": case["case_id"],
        "task_id": case["task_id"],
        "task_source": case.get("task_source", ""),
        "family": case["family"],
        "prompt_variant": "baseline_regenerate",
        "thinking": False,
        "problem": case["problem"],
        "gold_answer": case["gold_answer"],
        "hidden_component_key": case["hidden_component_key"],
        "hidden_threshold": case["hidden_threshold"],
        "hidden_trigger_source": case["hidden_trigger_source"],
        "hidden_trigger_prefix_id": case["hidden_trigger_prefix_id"],
        "hidden_trigger_prefix_char_end": case["hidden_trigger_prefix_char_end"],
        "hidden_trigger_boundary_kind": case["hidden_trigger_boundary_kind"],
        "hidden_trigger_risk": case["hidden_trigger_risk"],
        "hidden_trigger_threshold_crossed": case["hidden_trigger_threshold_crossed"],
        "hidden_trigger_rank_by_risk": case["hidden_trigger_rank_by_risk"],
        "localized_span_in_prompt": "",
        "random_span_in_prompt": "",
        "gold_answer_in_prompt": False,
        "manual_label_in_prompt": False,
        "retained_from_resume_checkpoint": False,
        "retained_from_baseline_failure": True,
        "resume_source_checkpoint": args.resume_from_checkpoint or "",
        "resume_policy": "reused_deterministic_baseline_failure_for_baseline_regenerate",
        "prompt_content": PROMPT_VARIANTS["baseline_regenerate"].format(problem=case["problem"]),
        "completion": case["baseline_completion"],
        "extracted_final": extracted,
        "extracted_final_raw": extracted_raw,
        "extraction_method": method,
        "final_marker_found": marker,
        "manual_final_correct": final_correct,
        "baseline_original_wrong": True,
        "rescued_from_baseline_wrong": final_correct,
        "generated_tokens": int(case["baseline_generated_tokens"]),
        "hit_max_new_tokens": bool(case["baseline_hit_max_new_tokens"]),
    }


def summarize_rows(rows: list[dict[str, Any]], cases: list[dict[str, Any]], skipped: dict[str, int], resume_stats: Counter[str]) -> dict[str, Any]:
    by_variant: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        b = by_variant[row["prompt_variant"]]
        b["n"] += 1
        b["manual_final_correct"] += int(row["manual_final_correct"])
        b["rescued_from_baseline_wrong"] += int(row["rescued_from_baseline_wrong"])
        b["final_marker_found"] += int(row["final_marker_found"])
        b["hit_max"] += int(row["hit_max_new_tokens"])
        b["completion_tokens"] += int(row["generated_tokens"])
    return {
        "rows": len(rows),
        "cases": len(cases),
        "baseline_failure_cases": len(cases),
        "hidden_threshold_crossed_cases": sum(int(c["hidden_trigger_threshold_crossed"]) for c in cases),
        "hidden_fallback_top_risk_cases": sum(int(c["hidden_trigger_source"] == "fallback_top_risk_no_threshold_crossing") for c in cases),
        "skipped_baseline_rows": skipped,
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "completion_tokens": sum(int(r["generated_tokens"]) for r in rows),
        "resume": {
            "resume_from_checkpoint": "",
            "resume_stats": dict(resume_stats),
            "retained_complete_jobs": sum(int(bool(r.get("retained_from_resume_checkpoint"))) for r in rows),
            "generated_this_run_jobs": sum(int(not bool(r.get("retained_from_resume_checkpoint")) and not bool(r.get("retained_from_baseline_failure"))) for r in rows),
            "baseline_reused_jobs": sum(int(bool(r.get("retained_from_baseline_failure"))) for r in rows),
            "policy": "Rows with final_marker_found=true and hit_max_new_tokens=false are retained; baseline_regenerate reuses the deterministic baseline failure.",
        },
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--baseline-json", default="")
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--variants", nargs="+", default=list(PROMPT_VARIANTS))
    p.add_argument("--max-cases", type=int, default=0)
    p.add_argument("--max-new-tokens", type=int, default=16384)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--top-k", type=int, default=0)
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--resume-from-checkpoint", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--layer-window", type=int, default=1)
    p.add_argument("--min-prefix-chars", type=int, default=80)
    p.add_argument("--chunk-chars", type=int, default=420)
    p.add_argument("--include-no-final-baseline", action="store_true")
    p.add_argument("--include-hitmax-baseline", action="store_true")
    p.add_argument("--random-seed", type=int, default=20260502)
    p.add_argument("--tag", default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    unknown = sorted(set(args.variants) - set(PROMPT_VARIANTS))
    if unknown:
        raise SystemExit(f"Unknown variants: {unknown}")
    baseline_rows_all, baseline_source = load_baseline_rows(args.baseline_json, args.model_key)
    baseline_rows_all = [r for r in baseline_rows_all if r.get("model_key") == args.model_key]
    skipped = Counter()
    for row in baseline_rows_all:
        if bool(row.get("manual_final_correct")):
            skipped["baseline_correct"] += 1
        elif not args.include_hitmax_baseline and bool(row.get("hit_max_new_tokens")):
            skipped["baseline_wrong_hit_max"] += 1
        elif not reasoning_body(str(row.get("completion", ""))).strip():
            skipped["baseline_wrong_empty_reasoning_body"] += 1
    baseline_failures = clean_failure_rows(baseline_rows_all, args.include_no_final_baseline, args.include_hitmax_baseline)
    baseline_failures = sorted(baseline_failures, key=lambda r: (r.get("task_source", ""), r["family"], r["task_id"]))
    if args.max_cases > 0:
        baseline_failures = baseline_failures[: args.max_cases]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"_{args.tag}" if args.tag else ""
    case_bank_path = PROJECT / f"data/processed/e171_hidden_rescue_cases_{args.model_key}_20260502.jsonl"
    if not baseline_failures:
        case_bank_path.parent.mkdir(parents=True, exist_ok=True)
        case_bank_path.write_text("", encoding="utf-8")
        empty_summary = {
            "rows": 0,
            "cases": 0,
            "baseline_failure_cases": 0,
            "hidden_threshold_crossed_cases": 0,
            "hidden_fallback_top_risk_cases": 0,
            "skipped_baseline_rows": dict(skipped),
            "by_variant": {},
            "completion_tokens": 0,
            "resume": {"policy": "No eligible baseline-wrong rows; hidden rescue skipped for this model."},
        }
        result = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "host": socket.gethostname(),
            "cuda_visible_devices": visible_device_label(),
            "model_key": args.model_key,
            "args": vars(args),
            "baseline_source": baseline_source,
            "case_bank": str(case_bank_path.relative_to(PROJECT)),
            "hidden_cache_pt": "",
            "hidden_cache_shape": [],
            "prompt_variants": PROMPT_VARIANTS,
            "summary": empty_summary,
            "cases": [],
            "rows": [],
        }
        out_path = out_dir / f"{args.model_key}_e171_hidden_rescue{tag}.json"
        write_json(out_path, result)
        print(f"wrote {out_path}", flush=True)
        print("SUMMARY", json.dumps(empty_summary, ensure_ascii=False, sort_keys=True), flush=True)
        return

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E171 hidden rescue clean_failures={len(baseline_failures)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    calibration = calibration_for_model(args.model_key)

    cases, cache_info = build_hidden_cases(
        baseline_failures,
        args.model_key,
        calibration,
        model,
        tok,
        spec,
        device,
        args.max_model_len,
        args.layer_window,
        args.min_prefix_chars,
        args.chunk_chars,
        args.random_seed,
    )
    write_jsonl(case_bank_path, cases)
    pt_path = out_dir / f"{args.model_key}_e171_hidden_rescue_cache{tag}.pt"
    cache_shape = save_hidden_cache(pt_path, cache_info)

    all_jobs = []
    for case in cases:
        for variant in args.variants:
            if variant == "baseline_regenerate":
                all_jobs.append({"case": case, "variant": variant, "baseline_reuse": True})
                continue
            content = render_content(case, variant)
            prompt, used_chat, add_special = render_generation_chat(tok, spec, content)
            all_jobs.append({"case": case, "variant": variant, "content": content, "prompt": prompt, "used_chat": used_chat, "add_special": add_special, "baseline_reuse": False})

    resume_complete, resume_stats = load_complete_resume_rows(args.resume_from_checkpoint)
    checkpoint = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    out_rows: list[dict[str, Any]] = []
    pending = []
    if checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text("", encoding="utf-8")
    for job in all_jobs:
        key = (job["case"]["case_id"], job["variant"])
        if key in resume_complete:
            out_rows.append(resume_complete[key])
        elif job["baseline_reuse"]:
            rec = reused_baseline_row(job["case"], args)
            out_rows.append(rec)
            if checkpoint:
                with checkpoint.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        else:
            pending.append(job)
    if checkpoint:
        for row in out_rows:
            if row.get("retained_from_resume_checkpoint"):
                with checkpoint.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    for start in range(0, len(pending), args.batch_size):
        batch = pending[start : start + args.batch_size]
        add_values = {job["add_special"] for job in batch}
        if len(add_values) != 1:
            raise RuntimeError("Mixed add_special values")
        enc = tok([job["prompt"] for job in batch], return_tensors="pt", padding=True, add_special_tokens=batch[0]["add_special"]).to(device)
        gen_kwargs = dict(max_new_tokens=args.max_new_tokens, pad_token_id=pad_token_id)
        if args.temperature > 0:
            gen_kwargs.update(dict(do_sample=True, temperature=args.temperature, top_p=args.top_p, top_k=args.top_k))
        else:
            gen_kwargs.update(dict(do_sample=False))
        with torch.no_grad():
            seqs = model.generate(**enc, **gen_kwargs)
        prompt_len = enc["input_ids"].shape[1]
        for job, seq in zip(batch, seqs):
            case = job["case"]
            gen_ids = seq[prompt_len:]
            completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
            extracted_raw, marker, method = e49.extract_final_answer(completion, allow_fallback=True)
            extracted = canonical_extracted_answer(extracted_raw)
            final_correct = e49.normalize_answer(extracted) == e49.normalize_answer(str(case["gold_answer"]))
            rec = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "experiment": "E171_hidden_rescue_from_baseline_wrong",
                "model_key": args.model_key,
                "case_id": case["case_id"],
                "task_id": case["task_id"],
                "task_source": case.get("task_source", ""),
                "family": case["family"],
                "prompt_variant": job["variant"],
                "thinking": False,
                "problem": case["problem"],
                "gold_answer": case["gold_answer"],
                "hidden_component_key": case["hidden_component_key"],
                "hidden_threshold": case["hidden_threshold"],
                "hidden_trigger_source": case["hidden_trigger_source"],
                "hidden_trigger_prefix_id": case["hidden_trigger_prefix_id"],
                "hidden_trigger_prefix_char_end": case["hidden_trigger_prefix_char_end"],
                "hidden_trigger_boundary_kind": case["hidden_trigger_boundary_kind"],
                "hidden_trigger_risk": case["hidden_trigger_risk"],
                "hidden_trigger_threshold_crossed": case["hidden_trigger_threshold_crossed"],
                "hidden_trigger_rank_by_risk": case["hidden_trigger_rank_by_risk"],
                "localized_span_in_prompt": case.get("localized_span", "") if job["variant"] == "hidden_localized_warning" else "",
                "random_span_in_prompt": case.get("random_location_span", "") if job["variant"] == "random_matched_warning" else "",
                "gold_answer_in_prompt": False,
                "manual_label_in_prompt": False,
                "retained_from_resume_checkpoint": False,
                "retained_from_baseline_failure": False,
                "resume_source_checkpoint": args.resume_from_checkpoint or "",
                "resume_policy": "generated_this_run",
                "prompt_content": job["content"],
                "prompt_tokens": int(enc["input_ids"].shape[1]),
                "completion": completion,
                "extracted_final": extracted,
                "extracted_final_raw": extracted_raw,
                "extraction_method": method,
                "final_marker_found": marker,
                "manual_final_correct": final_correct,
                "baseline_original_wrong": True,
                "rescued_from_baseline_wrong": final_correct,
                "generated_tokens": int(gen_ids.numel()),
                "hit_max_new_tokens": bool(gen_ids.numel() >= args.max_new_tokens),
            }
            out_rows.append(rec)
            if checkpoint:
                with checkpoint.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"generated/resumed {len(out_rows)}/{len(all_jobs)}", flush=True)

    summary = summarize_rows(out_rows, cases, dict(skipped), resume_stats)
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "args": vars(args),
        "baseline_source": baseline_source,
        "case_bank": str(case_bank_path.relative_to(PROJECT)),
        "hidden_cache_pt": str(pt_path.relative_to(PROJECT)),
        "hidden_cache_shape": cache_shape,
        "prompt_variants": PROMPT_VARIANTS,
        "summary": summary,
        "cases": cases,
        "rows": out_rows,
    }
    out_path = out_dir / f"{args.model_key}_e171_hidden_rescue{tag}.json"
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
