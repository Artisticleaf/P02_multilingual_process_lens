#!/usr/bin/env python3
"""E147: Fine-grained per-anchor risk timecourse on p28.

For each self-correction anchor in p28's completion, sample hidden risk
at 100-char intervals from 500 chars before to 500 chars after the anchor.
Produces per-anchor risk profiles to map the exact temporal shape of the
pre-turnaround signal.
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
OUT_DIR = PROJECT / "results/E147_p28_fine_grained_risk_timecourse"

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


def component_key_tuple(key: str) -> tuple[int, str]:
    hidden_idx, comp = key.split(":", 1)
    return int(hidden_idx), comp


def prefill_and_score(
    model, tokenizer, spec, problem, prefix_text, device, max_model_len,
    hidden_layers, component_plan, monitor_key_tuple, direction, center,
) -> dict[str, Any]:
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


def sample_around_anchor(
    model, tokenizer, spec, task, completion, anchor_pos, device, max_model_len,
    hidden_layers, component_plan, monitor_key_tuple, direction, center,
    window_chars: int = 500, step_chars: int = 100,
) -> list[dict[str, Any]]:
    """Sample hidden risk at regular intervals around a specific anchor position."""
    problem = task["problem"]
    samples = []
    for offset in range(-window_chars, window_chars + step_chars, step_chars):
        pos = anchor_pos + offset
        if pos < 50:
            continue
        if pos > len(completion):
            continue
        prefix = completion[:pos]
        try:
            scores = prefill_and_score(
                model, tokenizer, spec, problem, prefix, device,
                max_model_len, hidden_layers, component_plan,
                monitor_key_tuple, direction, center,
            )
            samples.append({
                "offset_from_anchor": offset,
                "char_position": pos,
                **scores,
            })
        except Exception as e:
            samples.append({"offset_from_anchor": offset, "char_position": pos, "error": str(e)})
    return samples


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_27b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--baseline-jsonl", default=str(
        PROJECT / "logs/e172_aime2026_baseline_qwen35_27b_max81920_resume_20260502.jsonl"
    ))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--step-chars", type=int, default=100)
    p.add_argument("--window-chars", type=int, default=500)
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--tag", default="")
    args = p.parse_args()

    registry = read_yaml(args.registry)["models"]
    spec = dict(registry[args.model_key])
    spec["_model_key"] = args.model_key
    cal = load_json(CALIBRATION)
    cal_model = [m for m in cal["models"] if m["model_key"] == args.model_key][0]
    best_key = cal_model["best_key"]
    best_tuple = component_key_tuple(best_key)
    hp_threshold = float(cal_model["best_key_record"]["high_precision_eval"]["threshold"])
    budgeted_threshold = float(cal_model["best_key_record"]["budgeted_eval"]["threshold"])

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E147 fine-grained p28 timecourse", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    hidden_layers = [best_tuple[0]]
    component_plan = e90.build_component_plan(layers, hidden_layers)
    direction, center, _ = e172_gate.load_monitor_direction_center(
        cal_model, best_key, model, tok, spec, device, args.max_model_len,
        hidden_layers, component_plan,
    )

    all_rows = load_jsonl(Path(args.baseline_jsonl))
    p28 = [r for r in all_rows if r["task_id"] == "e172_aime2026_p28"][0]
    comp = p28["completion"]
    problem = p28["problem"]

    anchors = []
    for m in SELF_CORRECTION_RE.finditer(comp):
        anchors.append({
            "anchor_text": m.group(),
            "char_start": m.start(),
            "char_end": m.end(),
        })

    print(f"\n=== E147: p28 fine-grained risk timecourse ===")
    print(f"Completion: {len(comp)} chars, {len(anchors)} anchors")
    print(f"Window: ±{args.window_chars} chars, step: {args.step_chars} chars")
    print(f"Total samples per anchor: ~{2 * args.window_chars // args.step_chars + 1}")

    per_anchor_profiles = []
    for i, anchor in enumerate(anchors):
        a_text = anchor["anchor_text"]
        a_pos = anchor["char_start"]
        ctx_before = comp[max(0, a_pos - 60):a_pos]
        ctx_after = comp[a_pos + len(a_text):min(len(comp), a_pos + len(a_text) + 60)]
        print(f"\n  Anchor {i+1}/{len(anchors)}: \"{a_text}\" at pos {a_pos}")
        print(f"    context: ...{ctx_before}[{a_text}]{ctx_after}...")

        samples = sample_around_anchor(
            model, tok, spec, p28, comp, a_pos, device, args.max_model_len,
            hidden_layers, component_plan, best_tuple, direction, center,
            window_chars=args.window_chars, step_chars=args.step_chars,
        )

        # Classify each sample
        for s in samples:
            offset = s["offset_from_anchor"]
            if offset < -50:
                s["segment"] = "pre_correction"
            elif offset > 50:
                s["segment"] = "post_correction"
            else:
                s["segment"] = "at_correction"

        by_seg = defaultdict(list)
        for s in samples:
            if "risk" in s:
                by_seg[s["segment"]].append(s["risk"])

        print(f"    pre_corr: n={len(by_seg.get('pre_correction',[]))} mean={mean(by_seg['pre_correction']):.3f}" if by_seg.get('pre_correction') else "    pre_corr: no data")
        print(f"    at_corr: n={len(by_seg.get('at_correction',[]))} mean={mean(by_seg['at_correction']):.3f}" if by_seg.get('at_correction') else "    at_corr: no data")
        print(f"    post_corr: n={len(by_seg.get('post_correction',[]))} mean={mean(by_seg['post_correction']):.3f}" if by_seg.get('post_correction') else "    post_corr: no data")

        per_anchor_profiles.append({
            "anchor_index": i,
            "anchor_text": a_text,
            "char_start": a_pos,
            "char_end": anchor["char_end"],
            "context_before": ctx_before,
            "context_after": ctx_after,
            "by_segment": {
                seg: {
                    "n": len(vals),
                    "mean_risk": mean(vals) if vals else None,
                    "std_risk": stdev(vals) if len(vals) > 1 else None,
                }
                for seg, vals in by_seg.items()
            },
            "samples": samples,
        })

    # Aggregate: pre-turnaround signal per anchor
    print(f"\n=== Per-anchor pre-turnaround signal ===")
    for ap in per_anchor_profiles:
        pre = ap["by_segment"].get("pre_correction", {})
        post = ap["by_segment"].get("post_correction", {})
        at_c = ap["by_segment"].get("at_correction", {})
        pre_mean = pre.get("mean_risk")
        post_mean = post.get("mean_risk")
        at_mean = at_c.get("mean_risk")
        if pre_mean is not None and at_mean is not None:
            delta = pre_mean - at_mean
            signal = "STRONG" if delta > 0.5 else ("moderate" if delta > 0.1 else "weak/none")
            post_str = f"{post_mean:.3f}" if post_mean else "N/A"
            print(f"  anchor {ap['anchor_index']}: pre={pre_mean:.3f} at={at_mean:.3f} post={post_str} delta_pre_at={delta:+.3f} [{signal}]")
        else:
            print(f"  anchor {ap['anchor_index']}: insufficient data")

    # Build summary
    all_pre = []
    all_post = []
    all_at = []
    for ap in per_anchor_profiles:
        for s in ap["samples"]:
            if "risk" in s:
                if s["segment"] == "pre_correction":
                    all_pre.append(s["risk"])
                elif s["segment"] == "post_correction":
                    all_post.append(s["risk"])
                elif s["segment"] == "at_correction":
                    all_at.append(s["risk"])

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "best_key": best_key,
        "task_id": "e172_aime2026_p28",
        "window_chars": args.window_chars,
        "step_chars": args.step_chars,
        "n_anchors": len(anchors),
        "aggregate": {
            "pre_correction": {
                "n": len(all_pre),
                "mean_risk": mean(all_pre) if all_pre else None,
                "std_risk": stdev(all_pre) if len(all_pre) > 1 else None,
            },
            "at_correction": {
                "n": len(all_at),
                "mean_risk": mean(all_at) if all_at else None,
                "std_risk": stdev(all_at) if len(all_at) > 1 else None,
            },
            "post_correction": {
                "n": len(all_post),
                "mean_risk": mean(all_post) if all_post else None,
                "std_risk": stdev(all_post) if len(all_post) > 1 else None,
            },
        },
        "per_anchor": per_anchor_profiles,
    }

    tag = f"_{args.tag}" if args.tag else ""
    out_path = Path(args.out_dir) / f"p28_fine_grained_risk_timecourse{tag}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(out_path, summary)
    print(f"\nwrote {out_path}", flush=True)

    if all_pre and all_at:
        print(f"\n=== E147 KEY FINDING ===")
        print(f"pre_correction mean_risk: {mean(all_pre):.3f} (n={len(all_pre)})")
        print(f"at_correction mean_risk:  {mean(all_at):.3f} (n={len(all_at)})")
        print(f"post_correction mean_risk: {mean(all_post):.3f} (n={len(all_post)})" if all_post else "")
        print(f"pre - at delta: {mean(all_pre) - mean(all_at):+.3f}")


if __name__ == "__main__":
    main()
