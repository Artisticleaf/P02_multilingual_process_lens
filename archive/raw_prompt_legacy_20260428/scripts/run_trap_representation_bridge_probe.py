#!/usr/bin/env python3
"""Layerwise contextual representation probe for language-semantic traps."""
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
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

CASES: list[dict[str, str]] = [
    {
        "id": "zh_qiwuzhe",
        "concept": "pay75",
        "text": "在折扣语境中，“七五折”表示顾客支付原价的75%，也就是优惠25%。",
        "target": "七五折",
    },
    {
        "id": "en_pay75_original",
        "concept": "pay75",
        "text": "In a discount context, '75% of the original price' means the customer pays 75% and receives 25% off.",
        "target": "75% of the original price",
    },
    {
        "id": "en_25off",
        "concept": "pay75",
        "text": "In a discount context, '25% off' means the customer pays 75% of the original price.",
        "target": "25% off",
    },
    {
        "id": "zh_youhui25",
        "concept": "pay75",
        "text": "在折扣语境中，“优惠25%”表示减去原价的25%，顾客支付75%。",
        "target": "优惠25%",
    },
    {
        "id": "en_75off",
        "concept": "off75",
        "text": "In a discount context, '75% off' means the customer pays 25% of the original price.",
        "target": "75% off",
    },
    {
        "id": "zh_youhui75",
        "concept": "off75",
        "text": "在折扣语境中，“优惠75%”表示减去原价的75%，顾客支付25%。",
        "target": "优惠75%",
    },
    {
        "id": "zh_dabazhe",
        "concept": "pay80",
        "text": "在折扣语境中，“打八折”表示顾客支付原价的80%，也就是优惠20%。",
        "target": "打八折",
    },
    {
        "id": "en_pay80_original",
        "concept": "pay80",
        "text": "In a discount context, '80% of the original price' means the customer pays 80% and receives 20% off.",
        "target": "80% of the original price",
    },
    {
        "id": "en_20off",
        "concept": "pay80",
        "text": "In a discount context, '20% off' means the customer pays 80% of the original price.",
        "target": "20% off",
    },
    {
        "id": "en_80discount",
        "concept": "off80",
        "text": "In a discount context, '80% discount' means the customer pays 20% of the original price.",
        "target": "80% discount",
    },
    {
        "id": "zh_deriv_3x_valid",
        "concept": "linear_derivative_valid",
        "text": "在求导语境中，“(3x)'=3”是因为 x 的导数是1，系数3保留。",
        "target": "(3x)'=3",
    },
    {
        "id": "en_deriv_3x_valid",
        "concept": "linear_derivative_valid",
        "text": "In differentiation, '(3x)' = 3' because the derivative of x is 1 and the coefficient 3 is preserved.",
        "target": "(3x)' = 3",
    },
    {
        "id": "zh_deriv_3x_bad_constant",
        "concept": "linear_derivative_bad_constant",
        "text": "错误说法：“3x是常数，所以(3x)'=0”。这里把线性项误当作常数。",
        "target": "3x是常数",
    },
    {
        "id": "en_deriv_3x_bad_constant",
        "concept": "linear_derivative_bad_constant",
        "text": "Wrong rule: '3x is a constant, so (3x)' = 0.' This mistakes a linear term for a constant.",
        "target": "3x is a constant",
    },
]

CONTRASTS = [
    {"name": "qiwuzhe_pay75_vs_75off", "query": "zh_qiwuzhe", "positive": ["en_pay75_original", "en_25off", "zh_youhui25"], "negative": ["en_75off", "zh_youhui75"]},
    {"name": "youhui25_pay75_vs_75off", "query": "zh_youhui25", "positive": ["en_25off", "en_pay75_original", "zh_qiwuzhe"], "negative": ["en_75off", "zh_youhui75"]},
    {"name": "dabazhe_pay80_vs_80discount", "query": "zh_dabazhe", "positive": ["en_pay80_original", "en_20off"], "negative": ["en_80discount"]},
    {"name": "deriv_3x_valid_vs_constant_error", "query": "zh_deriv_3x_valid", "positive": ["en_deriv_3x_valid"], "negative": ["zh_deriv_3x_bad_constant", "en_deriv_3x_bad_constant"]},
]


def find_positions(tokenizer, text: str, target: str) -> tuple[dict[str, torch.Tensor], list[int], list[str]]:
    start = text.find(target)
    encoded = tokenizer(text, return_tensors="pt", add_special_tokens=True, return_offsets_mapping=True)
    offsets = encoded.pop("offset_mapping")[0].tolist()
    positions: list[int] = []
    if start >= 0:
        end = start + len(target)
        for i, (a, b) in enumerate(offsets):
            if a == b == 0:
                continue
            if max(a, start) < min(b, end):
                positions.append(i)
    if not positions:
        target_ids = tokenizer.encode(target, add_special_tokens=False)
        ids = encoded["input_ids"][0].tolist()
        for i in range(max(0, len(ids) - len(target_ids) + 1)):
            if ids[i : i + len(target_ids)] == target_ids:
                positions = list(range(i, i + len(target_ids)))
                break
    if not positions:
        positions = [int(encoded["attention_mask"].sum().item()) - 1]
    toks = tokenizer.convert_ids_to_tokens(encoded["input_ids"][0][positions].tolist())
    return encoded, positions, toks


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E08_trap_representation_bridge"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} on {args.device}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    vectors: dict[int, dict[str, torch.Tensor]] = {}
    tokenization_rows = []
    with torch.no_grad():
        for case in CASES:
            enc, positions, toks = find_positions(tokenizer, case["text"], case["target"])
            tokenization_rows.append({**case, "target_positions": positions, "target_tokens": toks, "num_target_tokens": len(positions)})
            enc = {k: v.to(device) for k, v in enc.items()}
            out = model(**enc, output_hidden_states=True, use_cache=False)
            for layer_idx, hs in enumerate(out.hidden_states):
                vec = hs[0, positions, :].mean(dim=0).detach().float().cpu()
                vectors.setdefault(layer_idx, {})[case["id"]] = F.normalize(vec, dim=0)

    layer_rows = []
    case_ids = [c["id"] for c in CASES]
    for layer_idx in sorted(vectors):
        sims = {}
        for a in case_ids:
            for b in case_ids:
                sims[f"{a}::{b}"] = float((vectors[layer_idx][a] @ vectors[layer_idx][b]).item())
        contrast_rows = []
        for c in CONTRASTS:
            q = c["query"]
            pos = [sims[f"{q}::{p}"] for p in c["positive"]]
            neg = [sims[f"{q}::{n}"] for n in c["negative"]]
            contrast_rows.append(
                {
                    "name": c["name"],
                    "query": q,
                    "mean_positive_cos": sum(pos) / len(pos),
                    "max_positive_cos": max(pos),
                    "mean_negative_cos": sum(neg) / len(neg),
                    "max_negative_cos": max(neg),
                    "mean_margin": sum(pos) / len(pos) - sum(neg) / len(neg),
                    "hard_margin": max(pos) - max(neg),
                }
            )
        layer_rows.append(
            {
                "layer": layer_idx,
                "contrasts": contrast_rows,
                "mean_contrast_margin": sum(x["mean_margin"] for x in contrast_rows) / len(contrast_rows),
                "min_contrast_margin": min(x["mean_margin"] for x in contrast_rows),
                "pairwise_cos": sims,
            }
        )
    best_by_contrast = []
    for c in CONTRASTS:
        all_rows = [next(x for x in lr["contrasts"] if x["name"] == c["name"]) | {"layer": lr["layer"]} for lr in layer_rows]
        best_by_contrast.append(max(all_rows, key=lambda x: (x["mean_margin"], x["hard_margin"])))
    best_overall = max(layer_rows, key=lambda x: (x["mean_contrast_margin"], x["min_contrast_margin"]))
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "cases": CASES,
        "contrasts": CONTRASTS,
        "tokenization": tokenization_rows,
        "layers": layer_rows,
        "best_overall_layer": {k: v for k, v in best_overall.items() if k != "pairwise_cos"},
        "best_by_contrast": best_by_contrast,
    }
    out = Path(args.out_dir) / f"{args.model_key}_trap_representation_bridge.json"
    write_json(out, result)
    print(
        f"wrote {out}; layers={len(layer_rows)} best_layer={best_overall['layer']} "
        f"mean_margin={best_overall['mean_contrast_margin']:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
