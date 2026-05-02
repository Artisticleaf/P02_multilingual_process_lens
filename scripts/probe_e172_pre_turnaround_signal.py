#!/usr/bin/env python3
"""Probe hidden states around self-correction anchors in baseline completions.

For each "Wait..." / self-correction moment, capture hidden risk before,
at, and after the anchor. Compare with confident-reasoning control segments.
This tests whether hidden states carry a "pre-turnaround signal" that
precedes explicit CoT self-correction.
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
from statistics import mean, stdev
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))

import run_e166_hardened_hidden_monitor_replay as e166  # noqa: E402
import run_e172_aime2026_hidden_gate_realtime as e172_gate  # noqa: E402
import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import (  # noqa: E402
    get_transformer_layers, is_local_model, load_causal_lm,
    load_tokenizer, model_device, visible_device_label,
)

CALIBRATION = PROJECT / "reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.json"
OUT_DIR = PROJECT / "results/E172_aime2026_pre_turnaround_signal"

SELF_CORRECTION_RE = re.compile(
    r'\b(W|w)ait\b|\bbut actually\b|\bthat is wrong\b|\bincorrect\b|'
    r'\bI made a mistake\b|\bnot right\b|\blet me re(?:think|do|start)\b|'
    r'\bhold on\b|\bthis contradicts\b|\bthat doesn.?t (?:seem|look) right\b|'
    r'\bactually no\b|\bthis is not\b|\bthat can.?t be right\b|'
    r'\bI think I mis(?:sed|understood)\b|\bsomething is off\b',
    re.IGNORECASE
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_calibration(model_key: str) -> dict[str, Any]:
    data = load_json(CALIBRATION)
    for row in data["models"]:
        if row["model_key"] == model_key:
            return row
    raise KeyError(f"No calibration for {model_key}")


def component_key_tuple(key: str) -> tuple[int, str]:
    hidden_idx, comp = key.split(":", 1)
    return int(hidden_idx), comp


def find_correction_anchors(text: str) -> list[dict[str, Any]]:
    """Find all self-correction anchor positions in the text."""
    anchors = []
    for m in SELF_CORRECTION_RE.finditer(text):
        anchors.append({
            "anchor_text": m.group(),
            "char_start": m.start(),
            "char_end": m.end(),
        })
    return anchors


def find_confident_segments(text: str, min_chars: int = 400) -> list[dict[str, Any]]:
    """Find segments of confident reasoning (no self-correction nearby)."""
    # Find all correction positions
    correction_positions = set()
    for m in SELF_CORRECTION_RE.finditer(text):
        for i in range(max(0, m.start() - 200), min(len(text), m.end() + 200)):
            correction_positions.add(i)

    # Find clean segments
    segments = []
    i = 0
    while i < len(text):
        if i not in correction_positions:
            start = i
            while i < len(text) and i not in correction_positions:
                i += 1
            seg_len = i - start
            if seg_len >= min_chars:
                # Take the end of the segment (most stable reasoning)
                seg_text = text[start:i]
                mid = start + seg_len // 2
                segments.append({
                    "char_mid": mid,
                    "char_start": start,
                    "char_end": i,
                    "text_snippet": text[max(start, mid-60):mid+60],
                })
        else:
            i += 1
    return segments


def prefill_and_score(
    model, tokenizer, spec, problem, prefix_text, device, max_model_len,
    hidden_layers, component_plan, monitor_key_tuple, direction, center,
) -> dict[str, Any]:
    """Teacher-force a prefix and return hidden validity/risk scores."""
    content = e166.render_prefill_content(
        {"problem": problem, "prefix_text": prefix_text}, "generation_prefill"
    )
    prompt, used_chat, add_special = e166.render_chat(
        tokenizer, spec, content, "official_if_chat"
    )
    feats, meta = e166.collect_prefill_activation(
        model, tokenizer, prompt, add_special, device, max_model_len,
        hidden_layers, component_plan,
    )
    if monitor_key_tuple not in feats:
        raise RuntimeError(f"Key {monitor_key_tuple} not in features")
    validity = float(((feats[monitor_key_tuple] - center) * direction).sum().item())
    risk = -validity
    return {"validity_score": validity, "risk": risk, **meta}


def sample_completion_trajectory(
    model, tokenizer, spec, task, completion, device, max_model_len,
    hidden_layers, component_plan, monitor_key_tuple, direction, center,
    sample_every_chars: int = 300,
) -> list[dict[str, Any]]:
    """Sample hidden risk at regular intervals through the completion."""
    problem = task["problem"]
    samples = []
    pos = sample_every_chars
    while pos < len(completion):
        prefix = completion[:pos]
        try:
            scores = prefill_and_score(
                model, tokenizer, spec, problem, prefix, device,
                max_model_len, hidden_layers, component_plan,
                monitor_key_tuple, direction, center,
            )
            samples.append({
                "char_position": pos,
                **scores,
            })
        except Exception as e:
            samples.append({"char_position": pos, "error": str(e)})
        pos += sample_every_chars
    return samples


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_27b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--baseline-jsonl", default=str(
        PROJECT / "logs/e172_aime2026_baseline_qwen35_27b_max81920_resume_20260502.jsonl"
    ))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--task-ids", nargs="*", default=[])
    p.add_argument("--sample-every-chars", type=int, default=300)
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--tag", default="")
    args = p.parse_args()

    registry = read_yaml(args.registry)["models"]
    spec = dict(registry[args.model_key])
    spec["_model_key"] = args.model_key
    cal = load_calibration(args.model_key)
    best_key = cal["best_key"]
    best_tuple = component_key_tuple(best_key)
    budgeted_threshold = float(cal["best_key_record"]["budgeted_eval"]["threshold"])
    hp_threshold = float(cal["best_key_record"]["high_precision_eval"]["threshold"])

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    hidden_layers = [best_tuple[0]]
    component_plan = e90.build_component_plan(layers, hidden_layers)
    direction, center, _ = e172_gate.load_monitor_direction_center(
        cal, best_key, model, tok, spec, device, args.max_model_len,
        hidden_layers, component_plan,
    )

    all_rows = load_jsonl(Path(args.baseline_jsonl))
    target_ids = set(args.task_ids) if args.task_ids else {
        "e172_aime2026_p27", "e172_aime2026_p17", "e172_aime2026_p14", "e172_aime2026_p28"
    }
    tasks = [r for r in all_rows if r["task_id"] in target_ids]

    all_samples = []
    for task in tasks:
        tid = task["task_id"]
        comp = task["completion"]
        print(f"\n=== {tid} gold={task['gold_answer']} chars={len(comp)} correct={task['manual_final_correct']} ===", flush=True)

        # Find correction anchors
        anchors = find_correction_anchors(comp)
        print(f"  Self-correction anchors: {len(anchors)}")

        # Sample trajectory
        print(f"  Sampling every {args.sample_every_chars} chars...", flush=True)
        traj = sample_completion_trajectory(
            model, tok, spec, task, comp, device, args.max_model_len,
            hidden_layers, component_plan, best_tuple, direction, center,
            sample_every_chars=args.sample_every_chars,
        )

        # Classify each sample: near-correction or confident
        CORRECTION_WINDOW = 400  # chars
        for s in traj:
            pos = s["char_position"]
            nearby_anchors = [
                a for a in anchors
                if abs(a["char_start"] - pos) < CORRECTION_WINDOW
            ]
            if nearby_anchors:
                # Determine position relative to nearest anchor
                nearest = min(nearby_anchors, key=lambda a: abs(a["char_start"] - pos))
                delta = pos - nearest["char_start"]
                if delta < -50:
                    s["segment"] = "pre_correction"
                elif delta > 50:
                    s["segment"] = "post_correction"
                else:
                    s["segment"] = "at_correction"
                s["nearest_anchor"] = nearest["anchor_text"]
                s["delta_to_anchor"] = delta
            else:
                s["segment"] = "confident"
                s["nearest_anchor"] = None
                s["delta_to_anchor"] = None

        all_samples.append({
            "task_id": tid,
            "gold_answer": task["gold_answer"],
            "manual_final_correct": task["manual_final_correct"],
            "completion_chars": len(comp),
            "generated_tokens": task["generated_tokens"],
            "n_anchors": len(anchors),
            "anchors": anchors,
            "trajectory": traj,
        })

        # Print per-task summary
        by_seg = defaultdict(list)
        for s in traj:
            if "risk" in s:
                by_seg[s["segment"]].append(s["risk"])
        print(f"  Mean risk by segment:")
        for seg in ["confident", "pre_correction", "at_correction", "post_correction"]:
            vals = by_seg.get(seg, [])
            if vals:
                print(f"    {seg}: n={len(vals)} mean={mean(vals):.3f} std={stdev(vals):.3f}")

    # Build summary
    all_risks_by_seg = defaultdict(list)
    for task_data in all_samples:
        for s in task_data["trajectory"]:
            if "risk" in s:
                all_risks_by_seg[s["segment"]].append(s["risk"])

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "best_key": best_key,
        "high_precision_threshold": hp_threshold,
        "budgeted_threshold": budgeted_threshold,
        "by_segment": {
            seg: {
                "n": len(vals),
                "mean_risk": mean(vals) if vals else None,
                "std_risk": stdev(vals) if len(vals) > 1 else None,
                "cross_hp_ratio": sum(1 for v in vals if v >= hp_threshold) / len(vals) if vals else None,
                "cross_budgeted_ratio": sum(1 for v in vals if v >= budgeted_threshold) / len(vals) if vals else None,
            }
            for seg, vals in all_risks_by_seg.items()
        },
        "per_task": [
            {
                "task_id": td["task_id"],
                "n_anchors": td["n_anchors"],
                "by_segment": {
                    seg: {
                        "n": len([s for s in td["trajectory"] if "risk" in s and s.get("segment") == seg]),
                        "mean_risk": mean([s["risk"] for s in td["trajectory"] if "risk" in s and s.get("segment") == seg]) if [s for s in td["trajectory"] if "risk" in s and s.get("segment") == seg] else None,
                    }
                    for seg in ["confident", "pre_correction", "at_correction", "post_correction"]
                },
            }
            for td in all_samples
        ],
        "trajectories": all_samples,
    }

    tag = f"_{args.tag}" if args.tag else ""
    out_path = Path(args.out_dir) / f"{args.model_key}_e172_pre_turnaround_signal{tag}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(out_path, summary)
    print(f"\nwrote {out_path}", flush=True)

    # Print key finding
    pre = all_risks_by_seg.get("pre_correction", [])
    conf = all_risks_by_seg.get("confident", [])
    at_c = all_risks_by_seg.get("at_correction", [])
    post = all_risks_by_seg.get("post_correction", [])
    print(f"\n=== KEY FINDING ===")
    print(f"confident:       n={len(conf)} mean_risk={mean(conf):.3f}" if conf else "confident: no data")
    print(f"pre_correction:  n={len(pre)} mean_risk={mean(pre):.3f}" if pre else "pre_correction: no data")
    print(f"at_correction:   n={len(at_c)} mean_risk={mean(at_c):.3f}" if at_c else "at_correction: no data")
    print(f"post_correction: n={len(post)} mean_risk={mean(post):.3f}" if post else "post_correction: no data")
    if pre and conf:
        delta = mean(pre) - mean(conf)
        print(f"pre - confident delta: {delta:+.3f}")
        if delta > 0:
            print(">>> PRE-TURNAROUND SIGNAL DETECTED: hidden risk elevated BEFORE explicit self-correction")
        else:
            print("No pre-turnaround elevation detected")


if __name__ == "__main__":
    main()
