#!/usr/bin/env python3
"""E106-E114 non-thinking mechanism suite.

This suite keeps the main claim in direct/non-thinking verifier mode and asks:

1. Is the hidden process-validity signal separable from readout confidence?
2. Does the signal appear in prefixes before the final answer or repair text?
3. Do long self-consistent answer-anchoring suffixes dilute the signal?
4. Can a simple hidden-gated filter reduce ACPI retention?

Prompts contain only problem + visible trace. Manual labels and error spans are
used only for offline grouping, prefix construction, and scoring.
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
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E61_DATA = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
E53_DATA = PROJECT / "data/processed/e53_answer_anchor_ablation_20260428.jsonl"
E57_AUDIT = PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl"
E88_AUDIT = PROJECT / "data/processed/e88_answer_first_manual_audit_20260429.jsonl"
E104_AUDIT = PROJECT / "data/processed/e104_tg_ng_process_audit_official_20260429.jsonl"
E65_DIR = PROJECT / "results/E65_mechanistic_layer_sweep"

FINAL_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*[^\n]+", re.IGNORECASE | re.MULTILINE)
REPAIR_RE = re.compile(
    r"\b(wait|re-?read|double[- ]?check|check|but|however|actually|correct(?:ed|ly)?|mistake|instead|on second thought)\b|可是|但是|实际|正确|错误|重新|修正",
    re.IGNORECASE,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    if mode == "raw":
        return False
    if mode == "chat":
        return True
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm", "exaone", "nemotron"} or "instruct" in cls or "post" in cls


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


def strict_prompt(problem: str, trace: str) -> str:
    return (
        "You are a strict trace-selection auditor. Judge the visible reasoning trace step by step. "
        "If any visible local step, definition, arithmetic operation, counting rule, unit conversion, semantic interpretation, algebraic transformation, or proof implication is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
        "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    )


def plain_prompt(problem: str, trace: str) -> str:
    return (
        "You are auditing a reasoning trace. Judge only whether the visible reasoning steps are valid; "
        "do not penalize missing final-answer formatting, truncation, or extra text after the answer. "
        "If any mathematical, logical, code-trace, table-interpretation, unit-conversion, or language-semantics step is wrong, answer No. "
        "If the visible reasoning steps are valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {problem}\n"
        f"Reasoning trace: {trace}\n"
        "Are the visible reasoning steps valid? Answer:"
    )


def best_label_logprob(logits: torch.Tensor, tokenizer, options: list[str]) -> tuple[float, str, int]:
    logp = F.log_softmax(logits.float(), dim=-1)
    scored = []
    for opt in options:
        ids = tokenizer.encode(opt, add_special_tokens=False)
        if ids:
            tid = int(ids[0])
            scored.append((float(logp[tid].item()), opt, tid))
    if not scored:
        raise ValueError(f"No token id for options {options}")
    return max(scored, key=lambda x: x[0])


def yes_no_metrics(logits: torch.Tensor, tokenizer) -> dict[str, Any]:
    yes, yes_opt, yes_id = best_label_logprob(logits, tokenizer, [" Yes", "Yes", " yes", "yes"])
    no, no_opt, no_id = best_label_logprob(logits, tokenizer, [" No", "No", " no", "no"])
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
        "yes_token_id": yes_id,
        "no_token_id": no_id,
    }


def best_layer_for(model_key: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    path = E65_DIR / f"{model_key}_e65_e61_layer_sweep.json"
    if path.exists():
        return int(read_json(path)["best_all_layer"]["layer"])
    return 16


def e61_items(max_items: int = 0) -> list[dict[str, Any]]:
    rows = load_jsonl(E61_DATA)
    out = []
    for row in rows:
        out.append(
            {
                "source": "E61",
                "item_id": str(row["audit_idx"]),
                "task_id": row["task_id"],
                "family": row.get("family"),
                "route_id": row.get("route_id"),
                "problem": row["problem"],
                "completion": row["completion"],
                "gold_answer": row.get("gold_answer"),
                "process_valid": bool(row["manual_process_valid"]),
                "is_acpi": bool(row.get("is_acpi")),
                "known_error_span_in_prompt": bool(row.get("known_error_span_in_prompt")),
                "known_error_span_annotation_in_prompt": bool(row.get("known_error_span_annotation_in_prompt")),
                "gold_label_in_prompt": bool(row.get("gold_label_in_prompt")),
                "manual_correction_in_prompt": bool(row.get("manual_correction_in_prompt")),
            }
        )
    if max_items:
        # Preserve paired valid/invalid coverage as much as possible by taking
        # deterministic task-sorted rows.
        out = sorted(out, key=lambda r: (r["task_id"], r["process_valid"], r["item_id"]))[:max_items]
    return out


def collect_e61_replay(
    model,
    tokenizer,
    spec: dict[str, Any],
    items: list[dict[str, Any]],
    best_layer: int,
    device: torch.device,
    max_model_len: int,
    prompt_format: str,
) -> tuple[torch.Tensor, list[dict[str, Any]]]:
    use_chat = should_use_chat_template(spec, prompt_format) and bool(getattr(tokenizer, "chat_template", None))
    X = []
    rows = []
    for i, item in enumerate(items, start=1):
        strict_content = strict_prompt(item["problem"], item["completion"])
        strict_rendered, strict_add_special = render_prompt(tokenizer, strict_content, use_chat)
        strict_ids = tokenizer.encode(strict_rendered, add_special_tokens=strict_add_special)[-max_model_len:]
        input_ids = torch.tensor([strict_ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids)
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
        if best_layer >= len(out.hidden_states):
            raise RuntimeError(f"best_layer={best_layer} but model returned {len(out.hidden_states)} hidden states")
        vec = out.hidden_states[best_layer][0, -1, :].detach().float().cpu()
        strict_metrics = yes_no_metrics(out.logits[0, -1], tokenizer)
        del out, input_ids, attn

        plain_content = plain_prompt(item["problem"], item["completion"])
        plain_rendered, plain_add_special = render_prompt(tokenizer, plain_content, use_chat)
        plain_ids = tokenizer.encode(plain_rendered, add_special_tokens=plain_add_special)[-max_model_len:]
        input_ids = torch.tensor([plain_ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids)
        with torch.no_grad():
            plain_out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
        plain_metrics = yes_no_metrics(plain_out.logits[0, -1], tokenizer)
        X.append(vec)
        rows.append(
            {
                **item,
                "prompt": plain_rendered,
                "add_special_tokens": plain_add_special,
                "strict_prompt": strict_rendered,
                "strict_add_special_tokens": strict_add_special,
                "input_tokens": len(plain_ids),
                "strict_input_tokens": len(strict_ids),
                "strict_yes_minus_no": strict_metrics["yes_minus_no"],
                "strict_readout_confidence": strict_metrics["readout_confidence"],
                "strict_label_entropy": strict_metrics["label_entropy"],
                "strict_pred_process_valid": strict_metrics["pred_process_valid"],
                "plain_yes_minus_no": plain_metrics["yes_minus_no"],
                "plain_readout_confidence": plain_metrics["readout_confidence"],
                "plain_label_entropy": plain_metrics["label_entropy"],
                "plain_pred_process_valid": plain_metrics["pred_process_valid"],
                # Default readout/confidence fields intentionally use the
                # plain absolute verifier. This is the risky objective whose
                # over-acceptance hidden gating is meant to diagnose.
                **plain_metrics,
            }
        )
        del plain_out, input_ids, attn
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if i % 12 == 0 or i == len(items):
            print(f"E61 replay {i}/{len(items)}", flush=True)
    return torch.stack(X), rows


def normalized_direction(pos: torch.Tensor, neg: torch.Tensor) -> torch.Tensor:
    direction = pos - neg
    return direction / (direction.norm() + 1e-8)


def loto_process_confidence_scores(X: torch.Tensor, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tasks = [str(r["task_id"]) for r in rows]
    labels = torch.tensor([bool(r["process_valid"]) for r in rows], dtype=torch.bool)
    conf = torch.tensor([float(r["readout_confidence"]) for r in rows], dtype=torch.float32)
    score_rows: list[dict[str, Any]] = []
    direction_rows: list[dict[str, Any]] = []
    for heldout in sorted(set(tasks)):
        train = [i for i, t in enumerate(tasks) if t != heldout]
        test = [i for i, t in enumerate(tasks) if t == heldout]
        train_labels = labels[train]
        x_train = X[train]
        process_dir = normalized_direction(x_train[train_labels].mean(0), x_train[~train_labels].mean(0))
        process_center = x_train.mean(0)
        train_conf = conf[train]
        median_conf = float(torch.median(train_conf).item())
        high = train_conf >= median_conf
        if bool(high.any()) and bool((~high).any()):
            conf_dir = normalized_direction(x_train[high].mean(0), x_train[~high].mean(0))
            conf_center = x_train.mean(0)
            cosine = float(F.cosine_similarity(process_dir, conf_dir, dim=0).item())
        else:
            conf_dir = torch.zeros_like(process_dir)
            conf_center = x_train.mean(0)
            cosine = None
        direction_rows.append(
            {
                "heldout_task": heldout,
                "process_confidence_direction_cosine": cosine,
                "train_median_readout_confidence": median_conf,
            }
        )
        for i in test:
            process_score = float(((X[i] - process_center) @ process_dir).item())
            conf_score = float(((X[i] - conf_center) @ conf_dir).item()) if cosine is not None else None
            score_rows.append(
                {
                    "item_id": rows[i]["item_id"],
                    "task_id": rows[i]["task_id"],
                    "family": rows[i].get("family"),
                    "route_id": rows[i].get("route_id"),
                    "gold_process_valid": bool(rows[i]["process_valid"]),
                    "pred_process_valid_from_hidden": process_score > 0,
                    "hidden_process_score": process_score,
                    "hidden_confidence_score": conf_score,
                    "readout_confidence": float(rows[i]["readout_confidence"]),
                    "label_entropy": float(rows[i]["label_entropy"]),
                    "yes_minus_no": float(rows[i]["yes_minus_no"]),
                    "pred_process_valid_from_yes_no": bool(rows[i]["pred_process_valid"]),
                    "is_acpi": bool(rows[i].get("is_acpi")),
                }
            )
    return score_rows, direction_rows


def auc_score(labels: list[bool], scores: list[float]) -> float | None:
    pos = [(s, i) for i, (y, s) in enumerate(zip(labels, scores)) if y]
    neg = [(s, i) for i, (y, s) in enumerate(zip(labels, scores)) if not y]
    if not pos or not neg:
        return None
    wins = 0.0
    total = len(pos) * len(neg)
    for sp, _ in pos:
        for sn, _ in neg:
            if sp > sn:
                wins += 1
            elif sp == sn:
                wins += 0.5
    return wins / total


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    mx = mean(xs)
    my = mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def residualize(y: torch.Tensor, controls: torch.Tensor) -> torch.Tensor:
    ones = torch.ones((controls.shape[0], 1), dtype=controls.dtype)
    Xc = torch.cat([ones, controls], dim=1)
    sol = torch.linalg.lstsq(Xc, y[:, None]).solution
    pred = (Xc @ sol).squeeze(1)
    return y - pred


def summarize_confidence_process(score_rows: list[dict[str, Any]], direction_rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [bool(r["gold_process_valid"]) for r in score_rows]
    hidden_scores = [float(r["hidden_process_score"]) for r in score_rows]
    readout_conf = [float(r["readout_confidence"]) for r in score_rows]
    entropy = [float(r["label_entropy"]) for r in score_rows]
    yes_no_correct = [bool(r["pred_process_valid_from_yes_no"]) == bool(r["gold_process_valid"]) for r in score_rows]
    hidden_correct = [bool(r["pred_process_valid_from_hidden"]) == bool(r["gold_process_valid"]) for r in score_rows]
    # Partial correlation: residualize both hidden score and label against readout confidence + label entropy.
    y = torch.tensor([1.0 if v else 0.0 for v in labels], dtype=torch.float64)
    h = torch.tensor(hidden_scores, dtype=torch.float64)
    c = torch.tensor(list(zip(readout_conf, entropy)), dtype=torch.float64)
    partial = pearson(residualize(h, c).tolist(), residualize(y, c).tolist())

    by_quadrant: dict[str, Counter[str]] = defaultdict(Counter)
    conf_median = median(readout_conf)
    for row in score_rows:
        q = f"{'valid' if row['gold_process_valid'] else 'invalid'}|{'high_conf' if row['readout_confidence'] >= conf_median else 'low_conf'}"
        by_quadrant[q]["n"] += 1
        by_quadrant[q]["hidden_correct"] += int(bool(row["pred_process_valid_from_hidden"]) == bool(row["gold_process_valid"]))
        by_quadrant[q]["yes_no_correct"] += int(bool(row["pred_process_valid_from_yes_no"]) == bool(row["gold_process_valid"]))

    matched = confidence_matched_pairs(score_rows)
    cosines = [r["process_confidence_direction_cosine"] for r in direction_rows if r["process_confidence_direction_cosine"] is not None]
    return {
        "n": len(score_rows),
        "hidden_process_auc_valid": auc_score(labels, hidden_scores),
        "readout_confidence_auc_valid": auc_score(labels, readout_conf),
        "hidden_accuracy": sum(hidden_correct) / len(hidden_correct) if hidden_correct else None,
        "yes_no_accuracy": sum(yes_no_correct) / len(yes_no_correct) if yes_no_correct else None,
        "hidden_label_partial_corr_controlling_readout_confidence_entropy": partial,
        "hidden_score_vs_readout_confidence_corr": pearson(hidden_scores, readout_conf),
        "hidden_score_vs_label_entropy_corr": pearson(hidden_scores, entropy),
        "direction_cosine_mean": mean(cosines) if cosines else None,
        "direction_cosine_abs_mean": mean([abs(x) for x in cosines]) if cosines else None,
        "direction_cosine_min": min(cosines) if cosines else None,
        "direction_cosine_max": max(cosines) if cosines else None,
        "readout_confidence_median": conf_median,
        "quadrants": {
            k: {
                "n": int(v["n"]),
                "hidden_accuracy": v["hidden_correct"] / v["n"] if v["n"] else None,
                "yes_no_accuracy": v["yes_no_correct"] / v["n"] if v["n"] else None,
            }
            for k, v in sorted(by_quadrant.items())
        },
        "confidence_matched_pairs": matched,
    }


def median(vals: list[float]) -> float:
    vals = sorted(vals)
    n = len(vals)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2:
        return vals[mid]
    return 0.5 * (vals[mid - 1] + vals[mid])


def confidence_matched_pairs(score_rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in score_rows if r["gold_process_valid"]]
    invalid = [r for r in score_rows if not r["gold_process_valid"]]
    pairs = []
    for bad in invalid:
        same_family = [v for v in valid if v.get("family") == bad.get("family")]
        pool = same_family or valid
        good = min(pool, key=lambda v: abs(float(v["readout_confidence"]) - float(bad["readout_confidence"])))
        pairs.append(
            {
                "invalid_item_id": bad["item_id"],
                "valid_item_id": good["item_id"],
                "family": bad.get("family"),
                "confidence_gap": abs(float(good["readout_confidence"]) - float(bad["readout_confidence"])),
                "hidden_orders_valid_above_invalid": float(good["hidden_process_score"]) > float(bad["hidden_process_score"]),
                "yes_no_orders_valid_above_invalid": float(good["yes_minus_no"]) > float(bad["yes_minus_no"]),
            }
        )
    return {
        "n": len(pairs),
        "mean_confidence_gap": mean([p["confidence_gap"] for p in pairs]) if pairs else None,
        "hidden_pair_accuracy": sum(p["hidden_orders_valid_above_invalid"] for p in pairs) / len(pairs) if pairs else None,
        "yes_no_pair_accuracy": sum(p["yes_no_orders_valid_above_invalid"] for p in pairs) / len(pairs) if pairs else None,
        "pairs_brief": pairs[:24],
    }


def global_directions(X: torch.Tensor, rows: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
    labels = torch.tensor([bool(r["process_valid"]) for r in rows], dtype=torch.bool)
    conf = torch.tensor([float(r["readout_confidence"]) for r in rows], dtype=torch.float32)
    high = conf >= torch.median(conf)
    process_dir = normalized_direction(X[labels].mean(0), X[~labels].mean(0))
    conf_dir = normalized_direction(X[high].mean(0), X[~high].mean(0))
    return {"process_valid_minus_invalid": process_dir, "confidence_high_minus_low": conf_dir}


def patched_forward_metrics(
    model,
    tokenizer,
    layer_module,
    prompt: str,
    add_special: bool,
    device: torch.device,
    max_model_len: int,
    delta: torch.Tensor,
) -> dict[str, Any]:
    ids = tokenizer.encode(prompt, add_special_tokens=add_special)[-max_model_len:]
    patch_pos = len(ids) - 1
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)

    def extract_output(output):
        return output[0] if isinstance(output, tuple) else output

    def replace_output(output, hidden):
        if isinstance(output, tuple):
            return (hidden,) + tuple(output[1:])
        return hidden

    def hook(_module, _inputs, output):
        hidden = extract_output(output).clone()
        hidden[:, patch_pos, :] = hidden[:, patch_pos, :] + delta.to(device=hidden.device, dtype=hidden.dtype)
        return replace_output(output, hidden)

    handle = layer_module.register_forward_hook(hook)
    try:
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
        metrics = yes_no_metrics(out.logits[0, -1], tokenizer)
        del out
    finally:
        handle.remove()
    del input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return metrics


def steering_diagnostic(
    model,
    tokenizer,
    rows: list[dict[str, Any]],
    directions: dict[str, torch.Tensor],
    best_layer: int,
    device: torch.device,
    max_model_len: int,
    steering_max_items: int,
    alpha: float,
) -> dict[str, Any]:
    if steering_max_items <= 0:
        return {"enabled": False, "rows": [], "summary": []}
    layers = get_transformer_layers(model)
    module_idx = max(0, min(best_layer - 1, len(layers) - 1))
    layer_module = layers[module_idx]
    invalid_accept = [r for r in rows if (not r["process_valid"]) and r["pred_process_valid"]]
    valid = [r for r in rows if r["process_valid"]]
    selected = (invalid_accept[: steering_max_items // 2] + valid[: steering_max_items - len(invalid_accept[: steering_max_items // 2])])[:steering_max_items]
    out_rows = []
    for i, row in enumerate(selected, start=1):
        base = {
            "yes_minus_no": float(row["yes_minus_no"]),
            "readout_confidence": float(row["readout_confidence"]),
            "pred_process_valid": bool(row["pred_process_valid"]),
        }
        deltas = {
            "process_toward_valid": alpha * directions["process_valid_minus_invalid"],
            "process_toward_invalid": -alpha * directions["process_valid_minus_invalid"],
            "confidence_toward_high": alpha * directions["confidence_high_minus_low"],
            "confidence_toward_low": -alpha * directions["confidence_high_minus_low"],
        }
        patched = {}
        for name, delta in deltas.items():
            patched[name] = patched_forward_metrics(
                model, tokenizer, layer_module, row["prompt"], row["add_special_tokens"], device, max_model_len, delta
            )
        out_rows.append(
            {
                "item_id": row["item_id"],
                "task_id": row["task_id"],
                "gold_process_valid": bool(row["process_valid"]),
                "base": base,
                "patched": patched,
            }
        )
        print(f"steering {i}/{len(selected)}", flush=True)
    summary = []
    for patch_name in ["process_toward_valid", "process_toward_invalid", "confidence_toward_high", "confidence_toward_low"]:
        effects = [r["patched"][patch_name]["yes_minus_no"] - r["base"]["yes_minus_no"] for r in out_rows]
        conf_effects = [r["patched"][patch_name]["readout_confidence"] - r["base"]["readout_confidence"] for r in out_rows]
        flips = [r["patched"][patch_name]["pred_process_valid"] != r["base"]["pred_process_valid"] for r in out_rows]
        summary.append(
            {
                "patch": patch_name,
                "n": len(out_rows),
                "mean_yes_minus_no_effect": mean(effects) if effects else None,
                "mean_readout_confidence_effect": mean(conf_effects) if conf_effects else None,
                "flip_count": sum(flips),
            }
        )
    return {
        "enabled": True,
        "best_hidden_layer": best_layer,
        "patched_module_index": module_idx,
        "alpha": alpha,
        "rows": out_rows,
        "summary": summary,
    }


def score_prompt_with_direction(
    model,
    tokenizer,
    spec: dict[str, Any],
    problem: str,
    trace: str,
    direction: torch.Tensor,
    center: torch.Tensor,
    best_layer: int,
    device: torch.device,
    max_model_len: int,
    prompt_format: str,
) -> dict[str, Any]:
    use_chat = should_use_chat_template(spec, prompt_format) and bool(getattr(tokenizer, "chat_template", None))
    prompt, add = render_prompt(tokenizer, strict_prompt(problem, trace), use_chat)
    ids = tokenizer.encode(prompt, add_special_tokens=add)[-max_model_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
    vec = out.hidden_states[best_layer][0, -1, :].detach().float().cpu()
    metrics = yes_no_metrics(out.logits[0, -1], tokenizer)
    score = float(((vec - center) @ direction).item())
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {
        "input_tokens": len(ids),
        "hidden_process_score_global": score,
        "hidden_pred_process_valid_global": score > 0,
        **metrics,
    }


def prefix_points(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row.get("completion", "")
    err = row.get("manual_error_span") or row.get("error_span") or ""
    points = []
    if err and err in comp:
        start = comp.find(err)
        if start > 0:
            points.append({"stage": "before_error_span", "char_end": start, "span_text": comp[max(0, start - 120) : start]})
        points.append({"stage": "error_span_end", "char_end": start + len(err), "span_text": err})
    first_final = next(FINAL_RE.finditer(comp), None)
    if first_final:
        points.append({"stage": "first_final_answer_end", "char_end": first_final.end(), "span_text": first_final.group(0)})
    err_pos = comp.find(err) if err else -1
    repair = None
    for m in REPAIR_RE.finditer(comp):
        if err_pos < 0 or m.start() > err_pos:
            repair = m
            break
    if repair:
        points.append({"stage": "repair_trigger_end", "char_end": repair.end(), "span_text": repair.group(0)})
        points.append({"stage": "post_repair_240chars", "char_end": min(len(comp), repair.end() + 240), "span_text": comp[repair.start() : min(len(comp), repair.end() + 240)]})
    last_final = None
    for m in FINAL_RE.finditer(comp):
        last_final = m
    if last_final:
        points.append({"stage": "last_final_answer_end", "char_end": last_final.end(), "span_text": last_final.group(0)})
    if comp:
        points.append({"stage": "completion_end", "char_end": len(comp), "span_text": comp[-160:]})
    seen = set()
    out = []
    for p in sorted(points, key=lambda x: (x["char_end"], x["stage"])):
        key = (p["stage"], p["char_end"])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def load_prefix_source_rows(model_key: str, max_rows: int) -> list[dict[str, Any]]:
    rows = []
    for source, path in [("E57", E57_AUDIT), ("E88", E88_AUDIT), ("E104", E104_AUDIT)]:
        for r in load_jsonl(path):
            if r.get("model_key") != model_key:
                continue
            if source == "E104" and r.get("thinking"):
                continue
            if r.get("manual_acpi_strict") or r.get("manual_acpi_unrepaired") or r.get("manual_repair_present"):
                row = dict(r)
                row["source"] = source
                rows.append(row)
    rows = sorted(rows, key=lambda r: (not bool(r.get("manual_acpi_unrepaired")), not bool(r.get("manual_acpi_strict")), r.get("task_id", ""), r.get("manual_audit_idx", r.get("e88_audit_idx", r.get("e104_audit_idx", 0)))))
    return rows[:max_rows] if max_rows else rows


def prefix_emergence(
    model,
    tokenizer,
    spec: dict[str, Any],
    model_key: str,
    direction: torch.Tensor,
    center: torch.Tensor,
    best_layer: int,
    device: torch.device,
    max_model_len: int,
    prompt_format: str,
    max_rows: int,
) -> dict[str, Any]:
    source_rows = load_prefix_source_rows(model_key, max_rows)
    out = []
    for row in source_rows:
        for point in prefix_points(row):
            trace = row["completion"][: point["char_end"]]
            scored = score_prompt_with_direction(
                model, tokenizer, spec, row["problem"], trace, direction, center, best_layer, device, max_model_len, prompt_format
            )
            out.append(
                {
                    "source": row["source"],
                    "task_id": row.get("task_id"),
                    "audit_idx": row.get("manual_audit_idx", row.get("e88_audit_idx", row.get("e104_audit_idx"))),
                    "manual_acpi_strict": bool(row.get("manual_acpi_strict")),
                    "manual_acpi_unrepaired": bool(row.get("manual_acpi_unrepaired")),
                    "manual_repair_present": bool(row.get("manual_repair_present")),
                    "stage": point["stage"],
                    "char_end": point["char_end"],
                    "span_text": point["span_text"],
                    **scored,
                }
            )
        print(f"prefix rows scored {len(out)}", flush=True)
    return {"source_rows": len(source_rows), "rows": out, "summary": summarize_by_stage(out)}


def summarize_by_stage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["stage"])].append(row)
    out = []
    for stage, g in sorted(groups.items()):
        out.append(
            {
                "stage": stage,
                "n": len(g),
                "accept_rate": sum(r["pred_process_valid"] for r in g) / len(g),
                "mean_yes_minus_no": mean([r["yes_minus_no"] for r in g]),
                "mean_hidden_process_score": mean([r["hidden_process_score_global"] for r in g]),
            }
        )
    return out


def long_context_dilution(
    model,
    tokenizer,
    spec: dict[str, Any],
    items: list[dict[str, Any]],
    direction: torch.Tensor,
    center: torch.Tensor,
    best_layer: int,
    device: torch.device,
    max_model_len: int,
    prompt_format: str,
    max_items: int,
) -> dict[str, Any]:
    invalid = [r for r in items if not r["process_valid"]][:max_items]
    suffix_units = {
        "suffix_0": "",
        "suffix_300": "\nI checked the result again. The final answer remains {answer}. The reasoning above is consistent with that result.",
        "suffix_1200": "\n".join(
            [
                "I checked the result again. The final answer remains {answer}. The reasoning above is consistent with that result."
                for _ in range(8)
            ]
        ),
    }
    out = []
    for item in invalid:
        for condition, template in suffix_units.items():
            suffix = template.format(answer=item.get("gold_answer") or "")
            trace = item["completion"] + suffix
            scored = score_prompt_with_direction(
                model, tokenizer, spec, item["problem"], trace, direction, center, best_layer, device, max_model_len, prompt_format
            )
            out.append(
                {
                    "item_id": item["item_id"],
                    "task_id": item["task_id"],
                    "family": item.get("family"),
                    "condition": condition,
                    "suffix_chars": len(suffix),
                    **scored,
                }
            )
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in out:
        groups[row["condition"]].append(row)
    summary = []
    for condition, g in sorted(groups.items()):
        summary.append(
            {
                "condition": condition,
                "n": len(g),
                "accept_rate": sum(r["pred_process_valid"] for r in g) / len(g),
                "mean_yes_minus_no": mean([r["yes_minus_no"] for r in g]),
                "mean_hidden_process_score": mean([r["hidden_process_score_global"] for r in g]),
                "mean_readout_confidence": mean([r["readout_confidence"] for r in g]),
            }
        )
    return {"rows": out, "summary": summary}


def answer_anchor_probe(
    model,
    tokenizer,
    spec: dict[str, Any],
    direction: torch.Tensor,
    center: torch.Tensor,
    best_layer: int,
    device: torch.device,
    max_model_len: int,
    prompt_format: str,
    max_items: int,
) -> dict[str, Any]:
    rows = load_jsonl(E53_DATA)
    rows = sorted(rows, key=lambda r: (r["task_id"], r["e53_process_variant"], r["e53_answer_condition"], r["audit_idx"]))
    if max_items:
        rows = rows[:max_items]
    out = []
    for row in rows:
        scored = score_prompt_with_direction(
            model, tokenizer, spec, row["problem"], row["completion"], direction, center, best_layer, device, max_model_len, prompt_format
        )
        out.append(
            {
                "audit_idx": row["audit_idx"],
                "task_id": row["task_id"],
                "answer_condition": row["e53_answer_condition"],
                "process_variant": row["e53_process_variant"],
                "manual_process_valid": bool(row["manual_process_valid"]),
                "is_acpi": bool(row.get("is_acpi")),
                **scored,
            }
        )
    groups: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in out:
        groups[(row["answer_condition"], bool(row["manual_process_valid"]))].append(row)
    summary = []
    for (cond, valid), g in sorted(groups.items()):
        summary.append(
            {
                "answer_condition": cond,
                "manual_process_valid": valid,
                "n": len(g),
                "accept_rate": sum(r["pred_process_valid"] for r in g) / len(g),
                "mean_yes_minus_no": mean([r["yes_minus_no"] for r in g]),
                "mean_hidden_process_score": mean([r["hidden_process_score_global"] for r in g]),
            }
        )
    return {"rows": out, "summary": summary}


def hidden_gated_filter(score_rows: list[dict[str, Any]]) -> dict[str, Any]:
    out = []
    for row in score_rows:
        base_accept = bool(row["pred_process_valid_from_yes_no"])
        hidden_accept = bool(row["hidden_process_score"] > 0)
        gated_accept = base_accept and hidden_accept
        out.append({**row, "base_accept": base_accept, "hidden_accept": hidden_accept, "gated_accept": gated_accept})
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in out:
        if row["gold_process_valid"]:
            key = "valid"
        elif row.get("is_acpi"):
            key = "acpi_invalid"
        else:
            key = "invalid"
        groups[key].append(row)
    summary = []
    for key, g in sorted(groups.items()):
        summary.append(
            {
                "slice": key,
                "n": len(g),
                "base_accept_rate": sum(r["base_accept"] for r in g) / len(g),
                "hidden_accept_rate": sum(r["hidden_accept"] for r in g) / len(g),
                "gated_accept_rate": sum(r["gated_accept"] for r in g) / len(g),
            }
        )
    return {"rows": out, "summary": summary}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E106_E114_nonthinking_mechanism_suite"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--max-e61-items", type=int, default=0)
    p.add_argument("--steering-max-items", type=int, default=16)
    p.add_argument("--steering-alpha", type=float, default=2.0)
    p.add_argument("--prefix-max-rows", type=int, default=8)
    p.add_argument("--dilution-max-items", type=int, default=12)
    p.add_argument("--anchor-max-items", type=int, default=48)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    started = datetime.now().isoformat(timespec="seconds")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    best_layer = best_layer_for(args.model_key, args.best_layer)
    print(f"[{started}] loading {args.model_key} for E106-E114 best_layer={best_layer}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    items = e61_items(args.max_e61_items)
    X, replay_rows = collect_e61_replay(model, tokenizer, spec, items, best_layer, device, args.max_model_len, args.prompt_format)
    score_rows, direction_rows = loto_process_confidence_scores(X, replay_rows)
    confidence_process_summary = summarize_confidence_process(score_rows, direction_rows)
    directions = global_directions(X, replay_rows)
    global_process_dir = directions["process_valid_minus_invalid"]
    global_center = X.mean(0)

    steering = steering_diagnostic(
        model,
        tokenizer,
        replay_rows,
        directions,
        best_layer,
        device,
        args.max_model_len,
        args.steering_max_items,
        args.steering_alpha,
    )
    prefix = prefix_emergence(
        model,
        tokenizer,
        spec,
        args.model_key,
        global_process_dir,
        global_center,
        best_layer,
        device,
        args.max_model_len,
        args.prompt_format,
        args.prefix_max_rows,
    )
    dilution = long_context_dilution(
        model,
        tokenizer,
        spec,
        replay_rows,
        global_process_dir,
        global_center,
        best_layer,
        device,
        args.max_model_len,
        args.prompt_format,
        args.dilution_max_items,
    )
    anchor = answer_anchor_probe(
        model,
        tokenizer,
        spec,
        global_process_dir,
        global_center,
        best_layer,
        device,
        args.max_model_len,
        args.prompt_format,
        args.anchor_max_items,
    )
    gated = hidden_gated_filter(score_rows)
    leakage_passed = all(
        not r.get("gold_label_in_prompt")
        and not r.get("known_error_span_in_prompt")
        and not r.get("known_error_span_annotation_in_prompt")
        and not r.get("manual_correction_in_prompt")
        for r in replay_rows
    )
    result = {
        "experiment": "E106_E114_nonthinking_mechanism_suite",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "best_hidden_layer": best_layer,
        "sections": {
            "E106_E107_confidence_vs_process": {
                "summary": confidence_process_summary,
                "score_rows": score_rows,
                "direction_rows": direction_rows,
            },
            "E108_process_vs_confidence_direction": {
                "direction_rows": direction_rows,
                "summary": {
                    "mean_cosine": confidence_process_summary["direction_cosine_mean"],
                    "mean_abs_cosine": confidence_process_summary["direction_cosine_abs_mean"],
                },
            },
            "E109_steering_specificity": steering,
            "E110_prefix_emergence": prefix,
            "E111_long_context_dilution": dilution,
            "E112_answer_anchor_hidden_mediation": anchor,
            "E114_hidden_gated_filter": gated,
        },
        "leakage_audit": {
            "gold_label_in_prompt_rows": sum(int(bool(r.get("gold_label_in_prompt"))) for r in replay_rows),
            "known_error_span_in_prompt_rows": sum(int(bool(r.get("known_error_span_in_prompt"))) for r in replay_rows),
            "known_error_span_annotation_in_prompt_rows": sum(int(bool(r.get("known_error_span_annotation_in_prompt"))) for r in replay_rows),
            "manual_correction_in_prompt_rows": sum(int(bool(r.get("manual_correction_in_prompt"))) for r in replay_rows),
            "passed": leakage_passed,
            "note_zh": "E61/E53/E57/E88/E104 的人工标签、错误 span 和修复标签只用于离线分组、prefix 截断与评分；strict verifier prompt 只包含 problem 与 visible trace。",
        },
        "scope_note_zh": "E106-E114 是 non-thinking/direct-verifier 机制套件；它测试 process-validity hidden signal 是否能与 readout confidence 区分，并做小规模 steering/prefix/dilution/gated-filter 诊断。不是 thinking 终止机制实验。",
    }
    out = Path(args.out_dir) / f"{args.model_key}_e106_e114_nonthinking_mechanism_suite.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print(json.dumps({
        "model_key": args.model_key,
        "best_hidden_layer": best_layer,
        "confidence_process": confidence_process_summary,
        "gated_summary": gated["summary"],
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
