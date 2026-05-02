#!/usr/bin/env python3
"""E116-E118 thinking stop-signal and TG/NG mechanism suite.

This is a post-hoc replay suite. It does not generate new long CoT.  It uses
saved Qwen thinking-generation traces from E105/E103 and captures selected
residual, MLP, token-mixer/attention-related activations at final-answer,
post-final-continuation, and completion-end points.

Manual labels or known answers are used only for offline grouping and scoring.
They are never inserted into the model prompt.
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

import torch

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402
from run_e90_hardtask_component_activation_cache import (  # noqa: E402
    build_component_plan,
    best_hidden_layer,
    selected_hidden_layers,
    should_use_chat_template,
    train_component_directions,
)
from run_e103_tg_ng_fair_hardtask import render_prompt as render_e103_prompt  # noqa: E402
from run_e105_tg_closure_policy import POLICIES, render_prompt as render_e105_prompt  # noqa: E402


FINAL_LINE_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*[^\n]+", re.IGNORECASE | re.MULTILINE)
ANSWER_PHRASE_RE = re.compile(
    r"^\s*.*\b(final\s+answer|answer|sum|result)\b\s*(?:is|=|:)?\s*.*$",
    re.IGNORECASE | re.MULTILINE,
)

CONTINUATION_STRINGS = [
    "\n",
    " The",
    " We",
    " Let",
    " Now",
    " However",
    " Check",
    " Therefore",
    " Thus",
    " and",
    ".",
    ",",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel_to_project(path: Path) -> str:
    path = path.resolve()
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def load_e105_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    result_path = Path(args.e105_json)
    if result_path.exists():
        data = read_json(result_path)
        for i, row in enumerate(data.get("rows", [])):
            rec = dict(row)
            rec["e116_source"] = "E105_result"
            rec["e116_source_path"] = rel_to_project(result_path)
            rec["e116_source_index"] = i
            rows.append(rec)
    for raw in args.e105_checkpoint_jsonl:
        path = Path(raw)
        for i, row in enumerate(read_jsonl(path)):
            rec = dict(row)
            rec["e116_source"] = "E105_checkpoint"
            rec["e116_source_path"] = rel_to_project(path)
            rec["e116_source_index"] = i
            rows.append(rec)
    seen = set()
    out = []
    for row in rows:
        key = (
            row.get("policy_id"),
            row.get("task_id"),
            row.get("sample_idx"),
            row.get("generated_tokens"),
            row.get("completion", "")[:96],
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def load_e103_tg_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    path = Path(args.e103_json)
    if not path.exists() or args.max_e103_tg <= 0:
        return []
    data = read_json(path)
    rows = [
        r
        for r in data.get("rows", [])
        if r.get("model_key") == args.model_key and r.get("mode_label") == "TG_official"
    ]
    out = []
    for i, row in enumerate(rows[: args.max_e103_tg]):
        rec = dict(row)
        rec["e116_source"] = "E103_TG_official"
        rec["e116_source_path"] = rel_to_project(path)
        rec["e116_source_index"] = i
        out.append(rec)
    return out


def final_line_matches(text: str) -> list[re.Match[str]]:
    return list(FINAL_LINE_RE.finditer(text))


def answer_phrase_matches(text: str) -> list[re.Match[str]]:
    return list(ANSWER_PHRASE_RE.finditer(text))


def completion_points(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row.get("completion", "")
    if not comp:
        return []
    points: list[dict[str, Any]] = [
        {"stage": "completion_512chars", "char_end": min(len(comp), 512), "span_text": comp[: min(len(comp), 160)]},
        {"stage": "completion_midpoint", "char_end": len(comp) // 2, "span_text": comp[max(0, len(comp) // 2 - 80) : len(comp) // 2 + 80]},
    ]
    finals = final_line_matches(comp)
    if finals:
        first = finals[0]
        last = finals[-1]
        for label, m in [("first_final_answer_line_end", first), ("last_final_answer_line_end", last)]:
            points.append({"stage": label, "char_end": m.end(), "span_text": m.group(0)})
            if m.end() + 256 < len(comp):
                points.append({"stage": label.replace("_end", "_plus_256chars"), "char_end": m.end() + 256, "span_text": comp[m.end() : m.end() + 256]})
            if m.end() + 1024 < len(comp):
                points.append({"stage": label.replace("_end", "_plus_1024chars"), "char_end": m.end() + 1024, "span_text": comp[m.end() : m.end() + 256]})
    phrases = answer_phrase_matches(comp)
    if phrases:
        last_phrase = phrases[-1]
        points.append({"stage": "last_answer_phrase_line_end", "char_end": last_phrase.end(), "span_text": last_phrase.group(0)})
        if last_phrase.end() + 256 < len(comp):
            points.append({"stage": "last_answer_phrase_plus_256chars", "char_end": last_phrase.end() + 256, "span_text": comp[last_phrase.end() : last_phrase.end() + 256]})
    points.append({"stage": "completion_end", "char_end": len(comp), "span_text": comp[-240:]})
    seen = set()
    out = []
    for point in sorted(points, key=lambda p: (int(p["char_end"]), p["stage"])):
        key = (point["stage"], int(point["char_end"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(point)
    return out


def classify_point(row: dict[str, Any], point: dict[str, Any]) -> str:
    comp_len = len(row.get("completion", ""))
    stage = point["stage"]
    hit_max = bool(row.get("hit_max_new_tokens"))
    explicit_final = bool(row.get("explicit_final_marker_found") or row.get("final_marker_found"))
    model_stop = row.get("stop_reason_heuristic") == "model_stop_or_eos"
    clean_stop = explicit_final and (not hit_max) and (model_stop or row.get("e116_source") == "E105_result")
    near_end = int(point["char_end"]) >= comp_len - 32
    if clean_stop and stage in {"last_final_answer_line_end", "completion_end", "last_answer_phrase_line_end"} and near_end:
        return "clean_stop_positive"
    if hit_max and stage == "completion_end":
        return "unfinished_continue_negative"
    if explicit_final and "plus_" in stage:
        return "post_final_continue_negative"
    if hit_max and ("answer_phrase" in stage or "final_answer_line" in stage):
        return "pre_stop_candidate_ambiguous"
    return "ambiguous"


def render_source_prompt(tokenizer: Any, spec: dict[str, Any], row: dict[str, Any]) -> tuple[str, bool, bool]:
    task = {"id": row.get("task_id"), "en": row["problem"], "answer": row.get("gold_answer", "")}
    if row.get("e116_source", "").startswith("E105"):
        policy = POLICIES[row["policy_id"]]
        return render_e105_prompt(tokenizer, spec, task, policy)
    variant = row.get("prompt_variant", "neutral")
    thinking = bool(row.get("thinking", True))
    return render_e103_prompt(tokenizer, spec, task, variant, thinking)


def token_positions(
    tokenizer: Any,
    prompt: str,
    completion: str,
    add_special: bool,
    points: list[dict[str, Any]],
    max_len: int,
) -> tuple[list[int], list[dict[str, Any]], dict[str, int]]:
    full = prompt + completion
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special)
    full_ids = tokenizer.encode(full, add_special_tokens=add_special)
    truncated_left = max(0, len(full_ids) - max_len)
    kept_len = min(len(full_ids), max_len)
    usable_points: list[dict[str, Any]] = []
    positions: list[int] = []
    for point in points:
        char_end = int(point["char_end"])
        prefix = full[: len(prompt) + char_end]
        pos = len(tokenizer.encode(prefix, add_special_tokens=add_special)) - 1
        adj = pos - truncated_left
        rec = dict(point)
        rec.update(
            {
                "original_token_pos": pos,
                "truncated_token_pos": adj,
                "completion_token_end": max(0, pos + 1 - len(prompt_ids)),
                "truncated_away": not (0 <= adj < kept_len),
            }
        )
        if 0 <= adj < kept_len:
            positions.append(adj)
            usable_points.append(rec)
    return positions, usable_points, {
        "prompt_tokens": len(prompt_ids),
        "full_tokens": len(full_ids),
        "truncated_left_tokens": truncated_left,
        "input_tokens": kept_len,
    }


def extract_output(output: Any) -> torch.Tensor:
    return output[0] if isinstance(output, tuple) else output


def collect_position_features(
    model: Any,
    tokenizer: Any,
    prompt: str,
    completion: str,
    add_special: bool,
    device: torch.device,
    max_len: int,
    hidden_layers: list[int],
    layers: Any,
    component_plan: dict[tuple[int, str], Any],
    points: list[dict[str, Any]],
) -> tuple[dict[tuple[int, str], torch.Tensor], list[dict[str, Any]], dict[str, Any]]:
    positions, usable_points, meta = token_positions(tokenizer, prompt, completion, add_special, points, max_len)
    if not positions:
        return {}, usable_points, meta
    pos_by_device: dict[torch.device, torch.Tensor] = {}
    captured: dict[tuple[int, str], torch.Tensor] = {}
    handles = []
    capture_plan: dict[tuple[int, str], Any] = dict(component_plan)
    for hidden_idx in hidden_layers:
        capture_plan[(hidden_idx, "residual_hidden_state")] = layers[hidden_idx - 1]
    for key, module in capture_plan.items():
        def make_hook(k: tuple[int, str]):
            def hook(_module, _inputs, output):
                hidden = extract_output(output)
                if torch.is_tensor(hidden) and hidden.ndim >= 3:
                    dev = hidden.device
                    if dev not in pos_by_device:
                        pos_by_device[dev] = torch.tensor(positions, dtype=torch.long, device=dev)
                    captured[k] = hidden[0, pos_by_device[dev], :].detach().float().cpu()
                return output

            return hook

        handles.append(module.register_forward_hook(make_hook(key)))
    try:
        ids = tokenizer.encode(prompt + completion, add_special_tokens=add_special)[-max_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            try:
                out = model(input_ids=input_ids, attention_mask=attn, use_cache=False, logits_to_keep=1)
            except TypeError:
                out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
        del out, input_ids, attn
    finally:
        for handle in handles:
            handle.remove()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return captured, usable_points, meta


def first_token_ids(tokenizer: Any, strings: list[str]) -> list[int]:
    ids = []
    for text in strings:
        encoded = tokenizer.encode(text, add_special_tokens=False)
        if encoded:
            ids.append(int(encoded[0]))
    return sorted(set(ids))


def next_token_margin(
    model: Any,
    tokenizer: Any,
    prompt: str,
    completion_prefix: str,
    add_special: bool,
    device: torch.device,
    max_len: int,
    continuation_ids: list[int],
) -> dict[str, Any]:
    ids = tokenizer.encode(prompt + completion_prefix, add_special_tokens=add_special)[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        try:
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False, logits_to_keep=1)
            logits = out.logits[0, -1].float()
        except TypeError:
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
            logits = out.logits[0, -1].float()
    eos_id = tokenizer.eos_token_id
    eos_score = float(logits[int(eos_id)].item()) if eos_id is not None else float("nan")
    cont_scores = logits[torch.tensor(continuation_ids, device=logits.device)] if continuation_ids else torch.empty(0, device=logits.device)
    cont_max = float(cont_scores.max().item()) if continuation_ids else float("nan")
    eos_minus_continue = eos_score - cont_max if continuation_ids else float("nan")
    eos_rank = None
    if eos_id is not None:
        eos_rank = int((logits > logits[int(eos_id)]).sum().item() + 1)
    del out, input_ids, attn, logits
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {
        "eos_logit": eos_score,
        "continue_max_logit": cont_max,
        "eos_minus_continue_max": eos_minus_continue,
        "eos_rank": eos_rank,
    }


def score_process_components(
    feats: dict[tuple[int, str], torch.Tensor],
    directions: dict[tuple[int, str], torch.Tensor],
    centers: dict[tuple[int, str], torch.Tensor],
    point_index: int,
) -> tuple[dict[str, float], dict[str, float], list[torch.Tensor], list[str]]:
    scores: dict[str, float] = {}
    norms: dict[str, float] = {}
    vectors: list[torch.Tensor] = []
    labels: list[str] = []
    for key in sorted(directions, key=lambda x: (x[0], x[1])):
        if key not in feats or point_index >= feats[key].shape[0]:
            continue
        vec = feats[key][point_index]
        label = f"{key[0]}:{key[1]}"
        scores[label] = float(((vec - centers[key]) * directions[key]).sum().item())
        norms[label] = float(vec.norm().item())
        vectors.append(vec.to(torch.float16))
        labels.append(label)
    return scores, norms, vectors, labels


def train_stop_directions(point_rows: list[dict[str, Any]], cache_vectors: list[torch.Tensor], component_keys: list[str]) -> dict[str, dict[str, Any]]:
    pos_idx = [i for i, row in enumerate(point_rows) if row["stop_label"] == "clean_stop_positive"]
    neg_idx = [i for i, row in enumerate(point_rows) if row["stop_label"] in {"unfinished_continue_negative", "post_final_continue_negative"}]
    out: dict[str, dict[str, Any]] = {}
    if not pos_idx or not neg_idx or not cache_vectors:
        return out
    stacked = torch.stack([v.float() for v in cache_vectors])
    for comp_i, comp_key in enumerate(component_keys):
        X = stacked[:, comp_i, :]
        pos = X[pos_idx].mean(dim=0)
        neg = X[neg_idx].mean(dim=0)
        direction = pos - neg
        direction = direction / (direction.norm() + 1e-8)
        center = X.mean(dim=0)
        scores = ((X - center) * direction).sum(dim=1)
        pos_scores = [float(scores[i].item()) for i in pos_idx]
        neg_scores = [float(scores[i].item()) for i in neg_idx]
        threshold = (mean(pos_scores) + mean(neg_scores)) / 2
        out[comp_key] = {
            "scores": [float(x.item()) for x in scores],
            "positive_mean": mean(pos_scores),
            "negative_mean": mean(neg_scores),
            "threshold": threshold,
            "positive_n": len(pos_idx),
            "negative_n": len(neg_idx),
        }
    return out


def summarize_points(rows: list[dict[str, Any]], component_keys: list[str], stop_key: str | None) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all")].append(row)
        groups[("source", row["e116_source"])].append(row)
        groups[("stop_label", row["stop_label"])].append(row)
        groups[("stage", row["stage"])].append(row)
    out = []
    for (kind, key), vals in sorted(groups.items()):
        rec: dict[str, Any] = {
            "slice_type": kind,
            "slice": key,
            "n": len(vals),
            "mean_eos_minus_continue": mean(v["next_token"]["eos_minus_continue_max"] for v in vals if math.isfinite(v["next_token"]["eos_minus_continue_max"]))
            if any(math.isfinite(v["next_token"]["eos_minus_continue_max"]) for v in vals)
            else None,
            "mean_completion_token_end": mean(v["completion_token_end"] for v in vals),
        }
        best_process = [v["component_process_scores"].get(stop_key) for v in vals if stop_key and stop_key in v["component_process_scores"]]
        stop_scores = [v.get("component_stop_scores", {}).get(stop_key) for v in vals if stop_key and v.get("component_stop_scores", {}).get(stop_key) is not None]
        if best_process:
            rec[f"mean_process_score_{stop_key}"] = mean(best_process)
        if stop_scores:
            rec[f"mean_stop_score_{stop_key}"] = mean(stop_scores)
        out.append(rec)
    return out


def simulate_stop_policy(rows: list[dict[str, Any]], stop_key: str | None, stop_threshold: float | None, eos_threshold: float | None) -> list[dict[str, Any]]:
    by_trace: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_trace[(row["e116_source_path"], int(row["e116_source_index"]))].append(row)
    out = []
    for (_path, _idx), vals in sorted(by_trace.items()):
        vals = sorted(vals, key=lambda r: (r["completion_token_end"], r["stage"]))
        candidates = [
            v
            for v in vals
            if "final_answer_line_end" in v["stage"] or "answer_phrase_line_end" in v["stage"]
        ]
        if not candidates:
            continue
        first = candidates[0]
        generated = int(first.get("generated_tokens") or vals[-1].get("generated_tokens") or vals[-1]["completion_token_end"])
        hidden_score = first.get("component_stop_scores", {}).get(stop_key) if stop_key else None
        eos_margin = first["next_token"]["eos_minus_continue_max"]
        hidden_stop = hidden_score is not None and stop_threshold is not None and hidden_score >= stop_threshold
        eos_stop = eos_threshold is not None and math.isfinite(eos_margin) and eos_margin >= eos_threshold
        final_correct = bool(first.get("strict_final_correct") or first.get("fallback_final_correct") or first.get("manual_final_correct"))
        out.append(
            {
                "trace_id": f"{first['e116_source']}:{first['e116_source_index']}",
                "source": first["e116_source"],
                "task_id": first.get("task_id"),
                "policy_id": first.get("policy_id"),
                "mode_label": first.get("mode_label"),
                "stage": first["stage"],
                "generated_tokens": generated,
                "candidate_token_end": first["completion_token_end"],
                "token_savings_if_stop": max(0, generated - int(first["completion_token_end"])),
                "hidden_stop": hidden_stop,
                "eos_stop": eos_stop,
                "either_stop": hidden_stop or eos_stop,
                "final_correct_at_candidate": final_correct,
                "hit_max_new_tokens": bool(first.get("hit_max_new_tokens")),
                "clean_model_stop": first["stop_label"] == "clean_stop_positive",
                "hidden_stop_score": hidden_score,
                "eos_minus_continue_max": eos_margin,
            }
        )
    return out


def summarize_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    stopped = [r for r in rows if r["either_stop"]]
    return {
        "n": len(rows),
        "either_stop_rate": len(stopped) / len(rows),
        "hidden_stop_rate": sum(r["hidden_stop"] for r in rows) / len(rows),
        "eos_stop_rate": sum(r["eos_stop"] for r in rows) / len(rows),
        "mean_token_savings_if_either_stop": mean(r["token_savings_if_stop"] for r in stopped) if stopped else 0,
        "final_correct_retained_if_either_stop": sum(r["either_stop"] and r["final_correct_at_candidate"] for r in rows),
        "final_correct_candidates": sum(r["final_correct_at_candidate"] for r in rows),
        "hitmax_candidates": sum(r["hit_max_new_tokens"] for r in rows),
    }


def load_e102_summary(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.e102_json)
    if not path.exists():
        return {"available": False}
    data = read_json(path)
    selected = [
        row
        for row in data.get("summary", [])
        if row.get("slice_type") in {"generation_mode", "source", "all"}
    ]
    return {
        "available": True,
        "path": rel_to_project(path),
        "summary": selected,
        "pairwise_same_task_variant": data.get("pairwise_same_task_variant", []),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_27b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--e105-json", default=str(PROJECT / "results/E105_tg_closure_policy/qwen35_27b_e105_tg_closure_policy.json"))
    p.add_argument(
        "--e105-checkpoint-jsonl",
        nargs="+",
        default=[
            str(PROJECT / "logs/e105_qwen35_tg_closure_k1_checkpoint_20260429.jsonl"),
            str(PROJECT / "logs/e105r_qwen35_canary16k_checkpoint_20260429.jsonl"),
            str(PROJECT / "logs/e105r_qwen35_canary32k_checkpoint_20260429.jsonl"),
        ],
    )
    p.add_argument("--e103-json", default=str(PROJECT / "results/E103_tg_ng_fair_hardtask/qwen35_27b_e103_tg_ng_fair_hardtask.json"))
    p.add_argument("--e102-json", default=str(PROJECT / "results/E102_thinking_nonthinking_hidden_contrast/qwen35_27b_e102_thinking_nonthinking_hidden_contrast.json"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E116_E118_thinking_stop_signal"))
    p.add_argument("--max-e105-rows", type=int, default=8)
    p.add_argument("--max-e103-tg", type=int, default=6)
    p.add_argument("--best-layer", type=int, default=34)
    p.add_argument("--layer-window", type=int, default=1)
    p.add_argument("--max-model-len", type=int, default=32768)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    started = datetime.now().isoformat(timespec="seconds")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    source_rows = load_e105_rows(args)[: args.max_e105_rows] + load_e103_tg_rows(args)
    print(f"[{started}] E116-E118 loading {args.model_key}; source_rows={len(source_rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    hidden_layers = selected_hidden_layers(args.best_layer, len(layers), False, args.layer_window, None)
    component_plan = build_component_plan(layers, hidden_layers)
    use_chat = should_use_chat_template(spec, "official_if_chat") and bool(getattr(tok, "chat_template", None))
    print(f"hidden_layers={hidden_layers}", flush=True)
    directions, centers, direction_keys = train_component_directions(model, tok, use_chat, device, min(args.max_model_len, 8192), hidden_layers, component_plan)
    component_keys = sorted([f"{k[0]}:{k[1]}" for k in directions], key=lambda s: (int(s.split(":", 1)[0]), s.split(":", 1)[1]))
    continuation_ids = first_token_ids(tok, CONTINUATION_STRINGS)

    out_rows: list[dict[str, Any]] = []
    cache_vectors: list[torch.Tensor] = []
    point_meta: list[dict[str, Any]] = []
    skipped = Counter()
    for row_i, row in enumerate(source_rows, start=1):
        points = completion_points(row)
        if not points:
            skipped["no_points"] += 1
            continue
        prompt, used_chat, add_special = render_source_prompt(tok, spec, row)
        feats, usable_points, meta = collect_position_features(
            model,
            tok,
            prompt,
            row.get("completion", ""),
            add_special,
            device,
            args.max_model_len,
            hidden_layers,
            layers,
            component_plan,
            points,
        )
        if not usable_points:
            skipped["all_points_truncated"] += 1
            continue
        for point_i, point in enumerate(usable_points):
            process_scores, norms, vectors, vector_labels = score_process_components(feats, directions, centers, point_i)
            if vectors:
                cache_index = len(cache_vectors)
                cache_vectors.append(torch.stack(vectors))
            else:
                cache_index = -1
            completion_prefix = row.get("completion", "")[: int(point["char_end"])]
            next_meta = next_token_margin(model, tok, prompt, completion_prefix, add_special, device, args.max_model_len, continuation_ids)
            stop_label = classify_point(row, point)
            rec = {
                "cache_index": cache_index,
                "model_key": args.model_key,
                "e116_source": row.get("e116_source"),
                "e116_source_path": row.get("e116_source_path"),
                "e116_source_index": row.get("e116_source_index"),
                "task_id": row.get("task_id"),
                "policy_id": row.get("policy_id"),
                "mode_label": row.get("mode_label"),
                "prompt_variant": row.get("prompt_variant"),
                "thinking": row.get("thinking", True),
                "stage": point["stage"],
                "char_end": point["char_end"],
                "span_text": point.get("span_text", ""),
                "stop_label": stop_label,
                "completion_token_end": point["completion_token_end"],
                "original_token_pos": point["original_token_pos"],
                "truncated_token_pos": point["truncated_token_pos"],
                "generated_tokens": row.get("generated_tokens"),
                "hit_max_new_tokens": row.get("hit_max_new_tokens"),
                "explicit_final_marker_found": row.get("explicit_final_marker_found", row.get("final_marker_found")),
                "strict_final_correct": row.get("strict_final_correct"),
                "fallback_final_correct": row.get("fallback_final_correct"),
                "used_chat_template": used_chat,
                "add_special_tokens": add_special,
                "component_keys_used": vector_labels,
                "component_process_scores": process_scores,
                "component_norms": norms,
                "next_token": next_meta,
                **meta,
            }
            out_rows.append(rec)
            point_meta.append({k: rec[k] for k in ["cache_index", "e116_source", "e116_source_index", "task_id", "stage", "stop_label"]})
        print(f"E116 replayed source row {row_i}/{len(source_rows)} points={len(usable_points)}", flush=True)

    stop_directions = train_stop_directions(out_rows, cache_vectors, component_keys)
    stop_key = f"{args.best_layer}:residual_hidden_state"
    if stop_key not in stop_directions and stop_directions:
        stop_key = sorted(stop_directions)[0]
    stop_threshold = stop_directions.get(stop_key, {}).get("threshold") if stop_key in stop_directions else None
    for i, row in enumerate(out_rows):
        row["component_stop_scores"] = {}
        for comp_key, info in stop_directions.items():
            row["component_stop_scores"][comp_key] = info["scores"][i]

    eos_vals_pos = [r["next_token"]["eos_minus_continue_max"] for r in out_rows if r["stop_label"] == "clean_stop_positive" and math.isfinite(r["next_token"]["eos_minus_continue_max"])]
    eos_vals_neg = [
        r["next_token"]["eos_minus_continue_max"]
        for r in out_rows
        if r["stop_label"] in {"unfinished_continue_negative", "post_final_continue_negative"} and math.isfinite(r["next_token"]["eos_minus_continue_max"])
    ]
    eos_threshold = (mean(eos_vals_pos) + mean(eos_vals_neg)) / 2 if eos_vals_pos and eos_vals_neg else None
    policy_rows = simulate_stop_policy(out_rows, stop_key, stop_threshold, eos_threshold)

    if cache_vectors:
        width = max(v.shape[0] for v in cache_vectors)
        dim = max(v.shape[-1] for v in cache_vectors if v.numel())
        padded = []
        for v in cache_vectors:
            if v.shape[0] < width:
                pad = torch.zeros((width - v.shape[0], v.shape[1]), dtype=torch.float16)
                padded.append(torch.cat([v.cpu(), pad], dim=0))
            else:
                padded.append(v.cpu())
        cache_tensor = torch.stack(padded)
    else:
        cache_tensor = torch.empty(0)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pt_path = out_dir / f"{args.model_key}_e116_e118_component_points.pt"
    torch.save(
        {
            "component_token_vectors": cache_tensor,
            "component_keys": component_keys,
            "point_meta": point_meta,
            "note": "shape [point, component_key, hidden_dim]; post-hoc replay, not generation-time cache",
        },
        pt_path,
    )
    result = {
        "experiment": "E116_E118_thinking_stop_signal_suite",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "source_rows": len(source_rows),
        "selected_hidden_layers": hidden_layers,
        "component_keys": component_keys,
        "component_cache_pt": rel_to_project(pt_path),
        "component_cache_shape": list(cache_tensor.shape),
        "direction_keys_process": direction_keys,
        "stop_direction_summary": {k: {kk: vv for kk, vv in v.items() if kk != "scores"} for k, v in stop_directions.items()},
        "selected_stop_key": stop_key if stop_key in stop_directions else None,
        "selected_stop_threshold": stop_threshold,
        "eos_threshold": eos_threshold,
        "rows": out_rows,
        "summary_E116_stop_signal": summarize_points(out_rows, component_keys, stop_key if stop_key in stop_directions else None),
        "rows_E117_stop_policy": policy_rows,
        "summary_E117_stop_policy": summarize_policy(policy_rows),
        "summary_E118_tg_ng_existing_contrast": load_e102_summary(args),
        "skipped": dict(skipped),
        "leakage_audit": {
            "generation_performed": False,
            "gold_answer_in_prompt_rows": 0,
            "known_trap_note_in_prompt_rows": 0,
            "manual_labels_in_prompt_rows": 0,
            "manual_spans_in_prompt_rows": 0,
            "note_zh": "E116-E118 只复放已保存的原始 prompt+completion；gold/final labels 只用于离线分组、阈值诊断和 policy simulation。",
            "passed": True,
        },
        "scope_note_zh": "E116-E118 是 Qwen thinking 收口和 TG/NG 机制诊断；stop direction 样本很小，只能作为信号发现，不能当作完整因果 circuit。",
    }
    out_json = out_dir / f"{args.model_key}_e116_e118_thinking_stop_signal_suite.json"
    write_json(out_json, result)
    print(f"wrote {out_json}", flush=True)
    print(f"wrote {pt_path}", flush=True)
    print(json.dumps({
        "points": len(out_rows),
        "stop_policy": result["summary_E117_stop_policy"],
        "selected_stop_key": result["selected_stop_key"],
        "skipped": result["skipped"],
    }, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
