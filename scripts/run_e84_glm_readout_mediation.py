#!/usr/bin/env python3
"""E84 hidden-to-readout mediation for label/output bottlenecks.

For E61 paired traces, collect pointwise strict-verifier hidden states and
Yes/No logits, build leave-one-task residual validity directions, and compare
three readouts: hidden valid-vs-invalid margin, label-free no-minus-yes margin,
and raw A/B sibling target margins. This diagnoses whether GLM-style sibling
failures are hidden-state blindness or output-label/readout bottlenecks.
"""
from __future__ import annotations

import argparse
import json
import math
import socket
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

DATA_PATH = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
PAIR_PATH = PROJECT / "configs/e61_language_error_grid_pairs.yaml"
E65_DIR = PROJECT / "results/E65_mechanistic_layer_sweep"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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
        "If any visible local step, definition, arithmetic operation, counting rule, unit conversion, semantic interpretation, or proof implication is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
        "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    )


def ab_prompt(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "You are comparing two reasoning traces for the same problem. Exactly one trace contains a local process error. "
        "Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
        f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
    )


def get_best_layer(model_key: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    data = json.loads((E65_DIR / f"{model_key}_e65_e61_layer_sweep.json").read_text(encoding="utf-8"))
    return int(data["best_all_layer"]["layer"])


def label_logprob(logits: torch.Tensor, tok, options: list[str]) -> tuple[float, str]:
    logp = F.log_softmax(logits.float(), dim=-1)
    scored = []
    for opt in options:
        ids = tok.encode(opt, add_special_tokens=False)
        if ids:
            scored.append((float(logp[int(ids[0])].item()), opt))
    return max(scored, key=lambda x: x[0])


def collect_pointwise(model, tok, items: list[dict[str, Any]], use_chat: bool, device: torch.device, layer: int, max_model_len: int) -> tuple[torch.Tensor, list[dict[str, Any]]]:
    feats = []
    rows = []
    for i, item in enumerate(items, start=1):
        prompt, add = render_prompt(tok, strict_prompt(item["problem"], item["completion"]), use_chat)
        ids = tok.encode(prompt, add_special_tokens=add)[-max_model_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
        logits = out.logits[0, -1]
        yes_score, yes_opt = label_logprob(logits, tok, [" Yes", "Yes", " yes", "yes"])
        no_score, no_opt = label_logprob(logits, tok, [" No", "No", " no", "no"])
        feats.append(out.hidden_states[layer][0, -1, :].detach().float().cpu())
        rows.append({
            "audit_idx": item["audit_idx"],
            "task_id": item["task_id"],
            "family": item.get("family"),
            "route_id": item.get("route_id"),
            "gold_process_valid": bool(item["label"]),
            "yes_score": yes_score,
            "no_score": no_score,
            "invalid_score_no_minus_yes": no_score - yes_score,
            "pred_process_valid": yes_score > no_score,
            "yes_option": yes_opt,
            "no_option": no_opt,
        })
        del out, input_ids, attn
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if i % 24 == 0 or i == len(items):
            print(f"pointwise {i}/{len(items)}", flush=True)
    return torch.stack(feats), rows


def direction_for(X: torch.Tensor, labels: list[bool], train_idx: list[int]) -> tuple[torch.Tensor, torch.Tensor]:
    y = torch.tensor([labels[i] for i in train_idx], dtype=torch.bool)
    x = X[train_idx]
    pos = x[y].mean(dim=0)
    neg = x[~y].mean(dim=0)
    d = pos - neg
    d = d / (d.norm() + 1e-8)
    c = x.mean(dim=0)
    return d, c


def score_ab(model, tok, prompt_raw: str, use_chat: bool, device: torch.device, max_model_len: int) -> dict[str, Any]:
    prompt, add = render_prompt(tok, prompt_raw, use_chat)
    ids = tok.encode(prompt, add_special_tokens=add)[-max_model_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attn, use_cache=False).logits[0, -1]
    a_score, a_opt = label_logprob(logits, tok, [" A", "A", " a", "a"])
    b_score, b_opt = label_logprob(logits, tok, [" B", "B", " b", "b"])
    del input_ids, attn, logits
    return {"a_score": a_score, "b_score": b_score, "pred_side": "A" if a_score >= b_score else "B", "a_option": a_opt, "b_option": b_opt}


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx, my = mean(xs), mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def ranks(vals: list[float]) -> list[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    out = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[order[k]] = rank
        i = j + 1
    return out


def corr_summary(pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ["hidden_margin", "label_free_margin", "raw_ab_mean_target_margin"]
    out: dict[str, Any] = {}
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            xs = [float(r[a]) for r in pair_rows]
            ys = [float(r[b]) for r in pair_rows]
            out[f"pearson_{a}_vs_{b}"] = pearson(xs, ys)
            out[f"spearman_{a}_vs_{b}"] = pearson(ranks(xs), ranks(ys))
    return out


def group_summary(pair_rows: list[dict[str, Any]], order_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in pair_rows:
        groups[("all", "all")].append(r)
        groups[("family", r.get("family") or "")].append(r)
        groups[("route_id", r.get("route_id") or "")].append(r)
    for (typ, key), vals in sorted(groups.items()):
        if not key:
            continue
        out.append({
            "slice_type": typ,
            "slice": key,
            "n_pairs": len(vals),
            "hidden_pair_accuracy": sum(r["hidden_correct"] for r in vals) / len(vals),
            "label_free_pair_accuracy": sum(r["label_free_correct"] for r in vals) / len(vals),
            "mean_hidden_margin": mean(r["hidden_margin"] for r in vals),
            "mean_label_free_margin": mean(r["label_free_margin"] for r in vals),
            "mean_raw_ab_target_margin": mean(r["raw_ab_mean_target_margin"] for r in vals),
        })
    raw_acc = sum(r["correct"] for r in order_rows) / len(order_rows) if order_rows else None
    out.append({"slice_type": "raw_ab_orders", "slice": "all", "n_orders": len(order_rows), "raw_ab_accuracy": raw_acc, "predict_A_rate": sum(r["pred_side"] == "A" for r in order_rows) / len(order_rows) if order_rows else None})
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="glm47_flash_candidate")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E84_glm_readout_mediation"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--layer", type=int, default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    layer = get_best_layer(args.model_key, args.layer)
    data = load_jsonl(DATA_PATH)
    items = [{"audit_idx": int(r["audit_idx"]), "task_id": r["task_id"], "family": r.get("family"), "route_id": r.get("route_id"), "problem": r["problem"], "completion": r["completion"], "label": bool(r["manual_process_valid"])} for r in data]
    by_idx = {int(r["audit_idx"]): i for i, r in enumerate(items)}
    pair_cfg = read_yaml(PAIR_PATH)["pairs"]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E84 layer={layer} items={len(items)} pairs={len(pair_cfg)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    X, pointwise_rows = collect_pointwise(model, tok, items, use_chat, device, layer, args.max_model_len)
    labels = [bool(x["label"]) for x in items]
    pair_rows = []
    order_rows = []
    for pi, pair in enumerate(pair_cfg, start=1):
        bad_i = by_idx[int(pair["bad_idx"])]
        valid_i = by_idx[int(pair["valid_idx"])]
        test_task = pair["task_id"]
        train = [i for i, item in enumerate(items) if item["task_id"] != test_task]
        d, c = direction_for(X, labels, train)
        hidden_valid = float((X[valid_i] - c) @ d)
        hidden_bad = float((X[bad_i] - c) @ d)
        invalid_valid = pointwise_rows[valid_i]["invalid_score_no_minus_yes"]
        invalid_bad = pointwise_rows[bad_i]["invalid_score_no_minus_yes"]
        raw_margins = []
        for order in ["bad_first", "bad_second"]:
            if order == "bad_first":
                trace_a, trace_b, target = items[bad_i]["completion"], items[valid_i]["completion"], "A"
            else:
                trace_a, trace_b, target = items[valid_i]["completion"], items[bad_i]["completion"], "B"
            scored = score_ab(model, tok, ab_prompt(pair["problem"], trace_a, trace_b), use_chat, device, args.max_model_len)
            target_margin = scored["a_score"] - scored["b_score"] if target == "A" else scored["b_score"] - scored["a_score"]
            raw_margins.append(target_margin)
            order_rows.append({
                "pair_id": pair["id"], "task_id": pair["task_id"], "family": pair.get("family"), "route_id": pair.get("route_id"),
                "order": order, "target_side": target, "pred_side": scored["pred_side"], "correct": scored["pred_side"] == target,
                "target_margin": target_margin, **scored,
            })
        pair_rows.append({
            "pair_id": pair["id"],
            "task_id": pair["task_id"],
            "family": pair.get("family"),
            "route_id": pair.get("route_id"),
            "bad_idx": int(pair["bad_idx"]),
            "valid_idx": int(pair["valid_idx"]),
            "hidden_valid_score": hidden_valid,
            "hidden_bad_score": hidden_bad,
            "hidden_margin": hidden_valid - hidden_bad,
            "hidden_correct": hidden_valid > hidden_bad,
            "label_free_invalid_valid_score": invalid_valid,
            "label_free_invalid_bad_score": invalid_bad,
            "label_free_margin": invalid_bad - invalid_valid,
            "label_free_correct": invalid_bad > invalid_valid,
            "raw_ab_mean_target_margin": mean(raw_margins),
        })
        if pi % 12 == 0 or pi == len(pair_cfg):
            print(f"pairs {pi}/{len(pair_cfg)}", flush=True)
    result = {
        "experiment": "E84_glm_readout_mediation",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "layer": layer,
        "used_chat_template": use_chat,
        "args": vars(args),
        "pointwise_rows": pointwise_rows,
        "pair_rows": pair_rows,
        "raw_ab_order_rows": order_rows,
        "summary": group_summary(pair_rows, order_rows),
        "correlations": corr_summary(pair_rows),
        "leakage_audit": {"labels_in_prompt_rows": 0, "error_spans_in_prompt_rows": 0, "note_zh": "prompt 只含 problem 与 trace；valid/invalid pair 标签仅用于离线方向训练和评分。"},
        "scope_note_zh": "E84 是 readout mediation diagnostic：比较 hidden margin、label-free no-minus-yes margin 与 raw A/B margin，不单独证明完整因果 circuit。",
    }
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e84_readout_mediation_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("CORR", result["correlations"], flush=True)
    for s in result["summary"]:
        if s["slice_type"] in {"all", "raw_ab_orders"}:
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
