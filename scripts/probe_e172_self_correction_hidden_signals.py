#!/usr/bin/env python3
"""Probe hidden signals around E172 p09/p10 self-correction spans.

This is a targeted teacher-forced replay over already generated baseline
traces.  Prompts contain only the original problem and the visible prefix; the
event labels and gold answers stay offline.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))

import run_e166_hardened_hidden_monitor_replay as e166  # noqa: E402
import run_e172_aime2026_hidden_gate_realtime as e172_gate  # noqa: E402
import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

BASELINE_JSONL = PROJECT / "logs/e172_aime2026_baseline_qwen35_27b_checkpoint_20260502.jsonl"
OUT_DIR = PROJECT / "results/E172_aime2026_self_correction_hidden_signals"
CALIBRATION_JSON = PROJECT / "reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.json"

EVENT_SPECS = {
    "e172_aime2026_p09": [
        {
            "event_id": "p09_before_overlap_case5",
            "event_type": "pre_double_count_suspect",
            "anchor": "Case 5: $v = F_3$.",
            "position": "start",
            "note": "Start of the overlapping case analysis before the model notices double counting.",
        },
        {
            "event_id": "p09_same_set_notice",
            "event_type": "overlap_notice",
            "anchor": "These are the same set of sequences.",
            "position": "end",
            "note": "Model explicitly recognizes that two case descriptions refer to the same sequences.",
        },
        {
            "event_id": "p09_double_count_notice",
            "event_type": "double_count_notice",
            "anchor": "Yes, if I sum them up, I double count.",
            "position": "end",
            "note": "Explicit double-counting realization.",
        },
        {
            "event_id": "p09_restart_pair_count",
            "event_type": "repair_plan",
            "anchor": "Let's restart the counting by the value $v$ and the pair of positions $(i, j)$.",
            "position": "end",
            "note": "Switch to non-overlapping repeated-value/position-pair count.",
        },
        {
            "event_id": "p09_valid_pair_formula",
            "event_type": "post_repair_method",
            "anchor": "So Total = $6 \\times (\\text{number of valid pairs}) \\times 120$.",
            "position": "end",
            "note": "New counting formula after the repair.",
        },
        {
            "event_id": "p09_valid_pairs_total",
            "event_type": "post_repair_result",
            "anchor": "Total = 9.",
            "position": "end",
            "note": "Repaired valid-pair count.",
        },
    ],
    "e172_aime2026_p10": [
        {
            "event_id": "p10_wait_problem_statement",
            "event_type": "ambiguity_trigger",
            "anchor": "Wait, the problem states $\\overline{AC}$ is perpendicular to $\\overline{BC}$?",
            "position": "end",
            "note": "First explicit interruption to re-read the geometry condition.",
        },
        {
            "event_id": "p10_ambiguous_phrase",
            "event_type": "ambiguity_notice",
            "anchor": "This phrasing is slightly ambiguous.",
            "position": "end",
            "note": "Model names the condition as ambiguous.",
        },
        {
            "event_id": "p10_impossible_literal_read",
            "event_type": "invalid_interpretation_rejected",
            "anchor": "The latter is impossible because rotation preserves angles, and $\\angle C \\neq 90^\\circ$.",
            "position": "end",
            "note": "Rejects a literal or rotated-side interpretation as impossible.",
        },
        {
            "event_id": "p10_typo_notice",
            "event_type": "typo_or_condition_notice",
            "anchor": "This is a typo in the user prompt or a specific condition.",
            "position": "end",
            "note": "Explicitly marks the statement as typo/condition ambiguity.",
        },
        {
            "event_id": "p10_assume_line_condition",
            "event_type": "repair_hypothesis",
            "anchor": "Let's assume the condition is: The line containing $A'C'$ is perpendicular to the line containing $BC$.",
            "position": "end",
            "note": "Chooses a concrete interpretation to continue.",
        },
        {
            "event_id": "p10_convex_order_verified",
            "event_type": "post_repair_consistency_check",
            "anchor": "This is strictly increasing. So the hexagon is convex and the vertices are in that order.",
            "position": "end",
            "note": "Checks the chosen interpretation is consistent with hexagon order.",
        },
        {
            "event_id": "p10_take_small_theta",
            "event_type": "post_repair_choice",
            "anchor": "Since we assumed small rotation for the order $A, A', C...$, we take $\\theta = 90-C$.",
            "position": "end",
            "note": "Commits to the selected rotation branch.",
        },
    ],
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def torch_load(path: Path) -> dict[str, Any]:
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def label_logprob(logits: torch.Tensor, tok, options: list[str]) -> float | None:
    logp = F.log_softmax(logits.float(), dim=-1)
    vals = []
    for opt in options:
        ids = tok.encode(opt, add_special_tokens=False)
        if ids:
            vals.append(float(logp[int(ids[0])].item()))
    return max(vals) if vals else None


def next_token_meta(model, tok, prompt: str, add_special_tokens: bool, device: torch.device, max_len: int) -> dict[str, Any]:
    ids = tok.encode(prompt, add_special_tokens=add_special_tokens)
    truncated_left = max(0, len(ids) - max_len)
    ids = ids[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        try:
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=False, use_cache=False, logits_to_keep=1)
        except TypeError:
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=False, use_cache=False)
    logits = out.logits[0, -1].float()
    logp = F.log_softmax(logits, dim=-1)
    probs = torch.softmax(logits, dim=-1)
    top = torch.topk(logp, k=min(10, logp.numel()))
    top_tokens = [tok.decode([int(i)]) for i in top.indices.tolist()]
    meta = {
        "input_tokens": len(ids),
        "truncated_left_tokens": truncated_left,
        "next_token_entropy": float(-(probs * logp).sum().item()),
        "next_token_top_logprobs": [float(x) for x in top.values.tolist()],
        "next_token_top_tokens": top_tokens,
        "wait_logprob": label_logprob(logits, tok, [" Wait", "Wait", " wait", "wait"]),
        "but_logprob": label_logprob(logits, tok, [" But", "But", " but", "but"]),
        "however_logprob": label_logprob(logits, tok, [" However", "However", " however", "however"]),
        "actually_logprob": label_logprob(logits, tok, [" Actually", "Actually", " actually", "actually"]),
        "error_logprob": label_logprob(logits, tok, [" error", "error", " Error", "Error"]),
        "wrong_logprob": label_logprob(logits, tok, [" wrong", "wrong", " Wrong", "Wrong"]),
        "correct_logprob": label_logprob(logits, tok, [" correct", "correct", " Correct", "Correct"]),
        "restart_logprob": label_logprob(logits, tok, [" restart", "restart", " Restart", "Restart"]),
        "assume_logprob": label_logprob(logits, tok, [" assume", "assume", " Assume", "Assume"]),
        "ambiguous_logprob": label_logprob(logits, tok, [" ambiguous", "ambiguous", " Ambiguous", "Ambiguous"]),
    }
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return meta


def load_calibration(model_key: str) -> dict[str, Any]:
    data = load_json(CALIBRATION_JSON)
    for row in data["models"]:
        if row["model_key"] == model_key:
            return row
    raise KeyError(model_key)


def load_cached_directions(calibration: dict[str, Any], best_key: str) -> tuple[list[str], torch.Tensor, torch.Tensor, str]:
    rel = calibration.get("component_cache_pt", "")
    if not rel:
        raise RuntimeError("Calibration row does not point to a component cache")
    path = PROJECT / rel
    cache = torch_load(path)
    keys = list(cache["component_keys"])
    if best_key not in keys:
        raise RuntimeError(f"Best key {best_key} not in {path}")
    return keys, cache["monitor_directions"].float().cpu(), cache["monitor_centers"].float().cpu(), str(path.relative_to(PROJECT))


def prefix_end_for_anchor(completion: str, spec: dict[str, str]) -> int:
    anchor = spec["anchor"]
    pos = completion.find(anchor)
    if pos < 0:
        raise ValueError(f"Anchor not found for {spec['event_id']}: {anchor}")
    if spec.get("position", "end") == "start":
        return pos
    return pos + len(anchor)


def visible_span(text: str, end: int, chars: int) -> str:
    return text[max(0, end - chars) : end].strip()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_27b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--baseline-jsonl", default=str(BASELINE_JSONL))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--span-chars", type=int, default=700)
    p.add_argument("--tag", default="p09_p10_20260502")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = {r["task_id"]: r for r in load_jsonl(Path(args.baseline_jsonl))}
    missing = [task_id for task_id in EVENT_SPECS if task_id not in rows]
    if missing:
        raise SystemExit(f"Missing target rows in baseline jsonl: {missing}")

    registry = read_yaml(args.registry)["models"]
    spec = dict(registry[args.model_key])
    spec["_model_key"] = args.model_key
    calibration = load_calibration(args.model_key)
    best_key = calibration["best_key"]
    best_tuple = e172_gate.component_key_tuple(best_key)
    component_keys, directions_all, centers_all, direction_source = load_cached_directions(calibration, best_key)
    best_idx = component_keys.index(best_key)

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E172 self-correction hidden probe events={sum(len(v) for v in EVENT_SPECS.values())}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    hidden_layers = sorted({int(k.split(':', 1)[0]) for k in component_keys})
    component_plan = e90.build_component_plan(layers, hidden_layers)

    vectors: list[torch.Tensor] = []
    out_rows: list[dict[str, Any]] = []
    for task_id, events in EVENT_SPECS.items():
        base = rows[task_id]
        completion = base["completion"]
        for event in events:
            end = prefix_end_for_anchor(completion, event)
            prefix = completion[:end]
            prompt, used_chat, add = e172_gate.render_monitor_prompt(tok, spec, base["problem"], prefix)
            feats, monitor_meta = e166.collect_prefill_activation(
                model,
                tok,
                prompt,
                add,
                device,
                args.max_model_len,
                hidden_layers,
                component_plan,
            )
            next_meta = next_token_meta(model, tok, prompt, add, device, args.max_model_len)
            vecs = []
            scores = {}
            risks = {}
            for key_idx, key_text in enumerate(component_keys):
                key_tuple = e172_gate.component_key_tuple(key_text)
                if key_tuple not in feats:
                    vecs.append(torch.zeros_like(directions_all[key_idx]))
                    continue
                feat = feats[key_tuple].float().cpu()
                score = float(((feat - centers_all[key_idx]) * directions_all[key_idx]).sum().item())
                scores[key_text] = score
                risks[key_text] = -score
                vecs.append(feat.to(torch.float16))
            best_score = scores[best_key]
            best_risk = -best_score
            cache_index = len(vectors)
            vectors.append(torch.stack(vecs))
            high_threshold = float(calibration["best_key_record"]["high_precision_threshold"])
            budget_threshold = float(calibration["best_key_record"]["budgeted_threshold"])
            rec = {
                "cache_index": cache_index,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "experiment": "E172_self_correction_hidden_signal_probe",
                "model_key": args.model_key,
                "task_id": task_id,
                "problem_idx": int(base["problem_idx"]),
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "event_note_offline": event["note"],
                "anchor_text_offline": event["anchor"],
                "prefix_char_end": end,
                "prefix_token_estimate": len(tok.encode(prefix, add_special_tokens=False)),
                "visible_span": visible_span(completion, end, args.span_chars),
                "lookahead_after_prefix": completion[end : end + args.span_chars].strip(),
                "prompt_used_chat_template": used_chat,
                "prompt_add_special_tokens": add,
                "selected_hidden_layers": hidden_layers,
                "component_keys": component_keys,
                "best_key": best_key,
                "best_validity_score": best_score,
                "best_risk": best_risk,
                "high_precision_threshold": high_threshold,
                "budgeted_threshold": budget_threshold,
                "crosses_high_precision": bool(best_risk >= high_threshold),
                "crosses_budgeted": bool(best_risk >= budget_threshold),
                "component_validity_scores": scores,
                "component_risks": risks,
                **monitor_meta,
                **next_meta,
            }
            out_rows.append(rec)
            print(
                f"probe {task_id} {event['event_id']} risk={best_risk:.3f} hp={rec['crosses_high_precision']} budget={rec['crosses_budgeted']} input_tokens={rec['input_tokens']}",
                flush=True,
            )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"_{args.tag}" if args.tag else ""
    out_json = out_dir / f"{args.model_key}_e172_self_correction_hidden_signals{tag}.json"
    out_pt = out_dir / f"{args.model_key}_e172_self_correction_hidden_signals{tag}.pt"
    tensor = torch.stack([v.cpu() for v in vectors]) if vectors else torch.empty(0)
    torch.save(
        {
            "component_final_token_vectors": tensor,
            "component_keys": component_keys,
            "monitor_directions": directions_all.to(torch.float16).cpu(),
            "monitor_centers": centers_all.to(torch.float16).cpu(),
            "row_meta": [
                {
                    "cache_index": r["cache_index"],
                    "task_id": r["task_id"],
                    "event_id": r["event_id"],
                    "event_type": r["event_type"],
                    "prefix_char_end": r["prefix_char_end"],
                    "best_risk": r["best_risk"],
                }
                for r in out_rows
            ],
            "note": "Teacher-forced final-prefix-token component states for E172 p09/p10 self-correction events. Prompts used only problem and visible prefix.",
        },
        out_pt,
    )
    result = {
        "experiment": "E172_self_correction_hidden_signal_probe",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "baseline_jsonl": str(Path(args.baseline_jsonl).relative_to(PROJECT)),
        "component_cache_pt": str(out_pt.relative_to(PROJECT)),
        "component_cache_shape": list(tensor.shape),
        "calibration": {
            "best_key": best_key,
            "best_key_index": best_idx,
            "direction_source": direction_source,
            "high_precision_threshold": float(calibration["best_key_record"]["high_precision_threshold"]),
            "budgeted_threshold": float(calibration["best_key_record"]["budgeted_threshold"]),
        },
        "args": vars(args),
        "rows": out_rows,
        "leakage_audit": {
            "prompt_fields_used": ["problem", "prefix_text"],
            "gold_answer_in_prompt_rows": 0,
            "event_label_in_prompt_rows": 0,
            "anchor_text_in_prompt_rows": 0,
            "note": "Event labels, anchors, and gold answers are offline metadata only; monitor prompt contains only the problem and causal visible prefix.",
        },
    }
    write_json(out_json, result)
    print(f"wrote {out_json}", flush=True)
    print(f"wrote {out_pt}", flush=True)


if __name__ == "__main__":
    main()
