#!/usr/bin/env python3
"""E78 hidden-probe false-positive audit over E61 best-layer residuals.

Collects final-token residuals at the E65 best layer and runs artifact checks:
label permutation, leave-one-task, leave-one-family, leave-one-route, and
valid/invalid error rates. Prompts contain only problem and trace.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import socket
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

DATA_PATH = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
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


def process_prompt(problem: str, completion: str) -> str:
    return (
        "You are auditing a reasoning trace. Judge only whether the reasoning steps are valid. "
        "If any mathematical, code-execution, table-reading, unit, language-semantic, or proof step is wrong, "
        "the process is invalid even if the final answer is correct. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {completion}\nAre the visible reasoning steps valid? Answer:"
    )


def build_items() -> list[dict[str, Any]]:
    rows = load_jsonl(DATA_PATH)
    return [
        {
            "item_id": str(r["audit_idx"]),
            "task_id": r["task_id"],
            "family": r.get("family"),
            "route_id": r.get("route_id"),
            "problem": r["problem"],
            "completion": r["completion"],
            "label": bool(r["manual_process_valid"]),
            "gold_label_in_prompt": bool(r.get("gold_label_in_prompt", False)),
            "error_span_annotation_in_prompt": bool(r.get("known_error_span_annotation_in_prompt", False)),
        }
        for r in rows
    ]


def get_best_layer(model_key: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    path = E65_DIR / f"{model_key}_e65_e61_layer_sweep.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return int(data["best_all_layer"]["layer"])


def collect_features(model, tok, items: list[dict[str, Any]], use_chat: bool, device: torch.device, layer: int, max_model_len: int) -> torch.Tensor:
    feats = []
    for i, item in enumerate(items, start=1):
        prompt, add_special = render_prompt(tok, process_prompt(item["problem"], item["completion"]), use_chat)
        ids = tok.encode(prompt, add_special_tokens=add_special)[-max_model_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
        feats.append(out.hidden_states[layer][0, -1, :].detach().float().cpu())
        del out, input_ids, attn
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if i % 12 == 0 or i == len(items):
            print(f"hidden {i}/{len(items)}", flush=True)
    return torch.stack(feats)


def direction_for(X: torch.Tensor, labels: list[bool], train_idx: list[int]) -> tuple[torch.Tensor, torch.Tensor] | None:
    y = torch.tensor([labels[i] for i in train_idx], dtype=torch.bool)
    if int(y.sum()) == 0 or int((~y).sum()) == 0:
        return None
    x = X[train_idx]
    pos = x[y].mean(dim=0)
    neg = x[~y].mean(dim=0)
    d = pos - neg
    d = d / (d.norm() + 1e-8)
    c = x.mean(dim=0)
    return d, c


def evaluate_holdout(X: torch.Tensor, items: list[dict[str, Any]], labels: list[bool], holdout_key: str) -> list[dict[str, Any]]:
    values = sorted({str(item[holdout_key]) for item in items if item.get(holdout_key) is not None})
    rows = []
    for val in values:
        test = [i for i, item in enumerate(items) if str(item.get(holdout_key)) == val]
        train = [i for i in range(len(items)) if i not in set(test)]
        dc = direction_for(X, labels, train)
        if dc is None:
            continue
        d, c = dc
        for i in test:
            score = float((X[i] - c) @ d)
            pred = score > 0
            rows.append({
                "control": f"leave_one_{holdout_key}",
                "heldout": val,
                "item_id": items[i]["item_id"],
                "task_id": items[i]["task_id"],
                "family": items[i].get("family"),
                "route_id": items[i].get("route_id"),
                "gold_process_valid": labels[i],
                "pred_process_valid": bool(pred),
                "score": score,
                "correct": bool(pred) == labels[i],
            })
    return rows


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return max(0.0, center - half), min(1.0, center + half)


def metric_row(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    k = sum(r["correct"] for r in rows)
    valid = [r for r in rows if r["gold_process_valid"]]
    invalid = [r for r in rows if not r["gold_process_valid"]]
    fp = sum((not r["gold_process_valid"]) is False and (not r["pred_process_valid"]) for r in [])  # unused safeguard
    valid_false_positive = sum(not r["pred_process_valid"] for r in valid)
    invalid_false_negative = sum(r["pred_process_valid"] for r in invalid)
    lo, hi = wilson(k, n)
    return {
        "control": name,
        "n": n,
        "correct": k,
        "accuracy": k / n if n else None,
        "wilson95_low": lo,
        "wilson95_high": hi,
        "valid_n": len(valid),
        "valid_false_positive_rate": valid_false_positive / len(valid) if valid else None,
        "invalid_n": len(invalid),
        "invalid_false_negative_rate": invalid_false_negative / len(invalid) if invalid else None,
    }


def permutation_null(X: torch.Tensor, items: list[dict[str, Any]], labels: list[bool], n_perm: int, seed: int) -> list[float]:
    rnd = random.Random(seed)
    out = []
    idx = list(range(len(labels)))
    for _ in range(n_perm):
        shuffled = labels[:]
        rnd.shuffle(shuffled)
        rows = evaluate_holdout(X, items, shuffled, "task_id")
        if rows:
            out.append(sum(r["correct"] for r in rows) / len(rows))
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E78_hidden_probe_false_positive_audit"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--layer", type=int, default=None)
    p.add_argument("--n-perm", type=int, default=100)
    p.add_argument("--seed", type=int, default=20260429)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    items = build_items()
    labels = [bool(x["label"]) for x in items]
    layer = get_best_layer(args.model_key, args.layer)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E78 layer={layer} n={len(items)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    X = collect_features(model, tok, items, use_chat, device, layer, args.max_model_len)
    control_rows = []
    for key in ["task_id", "family", "route_id"]:
        control_rows.extend(evaluate_holdout(X, items, labels, key))
    metrics = []
    for name in ["leave_one_task_id", "leave_one_family", "leave_one_route_id"]:
        rows = [r for r in control_rows if r["control"] == name]
        metrics.append(metric_row(name, rows))
    baseline_rows = [r for r in control_rows if r["control"] == "leave_one_task_id"]
    baseline_acc = sum(r["correct"] for r in baseline_rows) / len(baseline_rows)
    perms = permutation_null(X, items, labels, args.n_perm, args.seed)
    p_value = (1 + sum(v >= baseline_acc for v in perms)) / (1 + len(perms)) if perms else None
    result = {
        "experiment": "E78_hidden_probe_false_positive_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "dataset": "E61",
        "layer": layer,
        "items_count": len(items),
        "used_chat_template": use_chat,
        "args": vars(args),
        "metrics": metrics,
        "permutation_null": {
            "n_perm": len(perms),
            "mean_accuracy": mean(perms) if perms else None,
            "max_accuracy": max(perms) if perms else None,
            "baseline_leave_one_task_accuracy": baseline_acc,
            "p_value_ge_baseline": p_value,
        },
        "control_rows": control_rows,
        "leakage_audit": {
            "gold_label_in_prompt_rows": sum(1 for x in items if x.get("gold_label_in_prompt")),
            "known_error_span_annotation_in_prompt_rows": sum(1 for x in items if x.get("error_span_annotation_in_prompt")),
            "manual_labels_in_prompt_rows": 0,
            "note_zh": "Prompt 只含 problem 与 trace；manual_process_valid 只用于离线 probe 标签。",
        },
        "scope_note_zh": "E78 是假阳性/泛化审计；当前版本覆盖 label permutation、leave-one-task/family/route、valid false-positive 和 invalid false-negative，不等同于 span-local causal proof。",
    }
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e78_hidden_probe_false_positive_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("METRICS", json.dumps(metrics, ensure_ascii=False), flush=True)
    print("PERM", result["permutation_null"], flush=True)


if __name__ == "__main__":
    main()
