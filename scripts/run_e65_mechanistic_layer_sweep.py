#!/usr/bin/env python3
"""E65 layer-wise residual process-validity probe.

This is a no-training diagnostic: for each controlled pointwise prompt, collect
the final-token residual hidden state at every layer, then evaluate a
leave-one-task-out valid-vs-invalid direction.  Prompts contain only the problem
and trace, never manual labels or error spans.
"""
from __future__ import annotations

import argparse
import json
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
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls


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
        f"Problem: {problem}\n"
        f"Reasoning trace: {completion}\n"
        "Are the visible reasoning steps valid? Answer:"
    )


def build_items(dataset: str) -> list[dict[str, Any]]:
    if dataset == "E42":
        rows = load_jsonl(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl")
        out = []
        for row in rows:
            if row.get("e39_variant") not in {"valid_correct", "invalid_correct"}:
                continue
            out.append(
                {
                    "dataset": "E42",
                    "task_id": row["task_id"],
                    "item_id": str(row["audit_idx"]),
                    "problem": row["problem"],
                    "completion": row["completion"],
                    "process_valid": bool(row["manual_process_valid"]),
                    "family": row.get("task_id"),
                    "route_id": None,
                }
            )
        return sorted(out, key=lambda r: (r["task_id"], r["process_valid"], r["item_id"]))
    if dataset == "E61":
        rows = load_jsonl(PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl")
        return [
            {
                "dataset": "E61",
                "task_id": row["task_id"],
                "item_id": str(row["audit_idx"]),
                "problem": row["problem"],
                "completion": row["completion"],
                "process_valid": bool(row["manual_process_valid"]),
                "family": row.get("family"),
                "route_id": row.get("route_id"),
            }
            for row in rows
        ]
    raise ValueError(f"unknown dataset: {dataset}")


def collect_hidden(model, tokenizer, items: list[dict[str, Any]], use_chat: bool, device: torch.device, max_model_len: int) -> list[torch.Tensor]:
    per_layer: list[list[torch.Tensor]] | None = None
    for i, item in enumerate(items, start=1):
        content = process_prompt(item["problem"], item["completion"])
        prompt, add_special = render_prompt(tokenizer, content, use_chat)
        ids = tokenizer.encode(prompt, add_special_tokens=add_special)[-max_model_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attention_mask = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            y = model(input_ids=input_ids, attention_mask=attention_mask, output_hidden_states=True, use_cache=False)
        states = [h[0, -1, :].detach().float().cpu() for h in y.hidden_states]
        if per_layer is None:
            per_layer = [[] for _ in states]
        for layer, vec in enumerate(states):
            per_layer[layer].append(vec)
        del y, input_ids, attention_mask
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if i % 12 == 0 or i == len(items):
            print(f"hidden {i}/{len(items)}", flush=True)
    assert per_layer is not None
    return [torch.stack(vecs) for vecs in per_layer]


def loto_direction(X: torch.Tensor, labels: list[bool], tasks: list[str], heldout_task: str) -> tuple[torch.Tensor, torch.Tensor]:
    train = [i for i, t in enumerate(tasks) if t != heldout_task]
    y = torch.tensor([labels[i] for i in train], dtype=torch.bool)
    x = X[train]
    pos = x[y].mean(dim=0)
    neg = x[~y].mean(dim=0)
    direction = pos - neg
    direction = direction / (direction.norm() + 1e-8)
    center = x.mean(dim=0)
    return direction, center


def probe_layer(X: torch.Tensor, items: list[dict[str, Any]], layer: int) -> list[dict[str, Any]]:
    labels = [bool(r["process_valid"]) for r in items]
    tasks = [str(r["task_id"]) for r in items]
    out = []
    for heldout in sorted(set(tasks)):
        direction, center = loto_direction(X, labels, tasks, heldout)
        for i, item in enumerate(items):
            if str(item["task_id"]) != heldout:
                continue
            score = float((X[i] - center) @ direction)
            pred = score > 0
            out.append(
                {
                    "layer": layer,
                    "heldout_task": heldout,
                    "item_id": item["item_id"],
                    "task_id": item["task_id"],
                    "family": item.get("family"),
                    "route_id": item.get("route_id"),
                    "score": score,
                    "pred_process_valid": bool(pred),
                    "gold_process_valid": bool(item["process_valid"]),
                    "correct": bool(pred) == bool(item["process_valid"]),
                }
            )
    return out


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all", str(row["layer"]))].append(row)
        if row.get("family"):
            groups[("family", str(row["family"]), str(row["layer"]))].append(row)
        if row.get("route_id"):
            groups[("route_id", str(row["route_id"]), str(row["layer"]))].append(row)
    out = []
    for (slice_type, slice_name, layer), g in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1], int(x[0][2]))):
        out.append(
            {
                "slice_type": slice_type,
                "slice": slice_name,
                "layer": int(layer),
                "n": len(g),
                "accuracy": sum(r["correct"] for r in g) / len(g),
                "mean_score_valid": mean([r["score"] for r in g if r["gold_process_valid"]]) if any(r["gold_process_valid"] for r in g) else None,
                "mean_score_invalid": mean([r["score"] for r in g if not r["gold_process_valid"]]) if any(not r["gold_process_valid"] for r in g) else None,
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--dataset", choices=["E42", "E61"], default="E61")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E65_mechanistic_layer_sweep"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    items = build_items(args.dataset)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E65 dataset={args.dataset} n={len(items)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    X_by_layer = collect_hidden(model, tok, items, use_chat, device, args.max_model_len)
    probe_rows = []
    for layer, X in enumerate(X_by_layer):
        probe_rows.extend(probe_layer(X, items, layer))
    summary = summarize(probe_rows)
    all_summary = [r for r in summary if r["slice_type"] == "all"]
    best = max(all_summary, key=lambda r: r["accuracy"])
    result = {
        "experiment": "E65_mechanistic_layer_sweep",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "dataset": args.dataset,
        "used_chat_template": use_chat,
        "args": vars(args),
        "items_count": len(items),
        "layers_count": len(X_by_layer),
        "best_all_layer": best,
        "probe_rows": probe_rows,
        "summary": summary,
        "leakage_audit": {
            "gold_label_in_prompt_rows": 0,
            "known_error_span_annotation_in_prompt_rows": 0,
            "manual_correction_in_prompt_rows": 0,
            "note_zh": "manual_process_valid 只用于离线 probe 标签，未进入 prompt；prompt 只包含 problem 与 trace。",
        },
        "scope_note_zh": "E65 是层扫描诊断；它说明哪个层的 residual 表示可线性读出过程有效性，不等同于完整电路证明。",
    }
    out = Path(args.out_dir) / f"{args.model_key}_e65_{args.dataset.lower()}_layer_sweep.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("BEST", best, flush=True)


if __name__ == "__main__":
    main()
