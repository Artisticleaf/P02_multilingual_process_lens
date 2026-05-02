#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import random
import socket
import sys
from datetime import datetime
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.anchor_eval import (  # noqa: E402
    auto_patch_layers,
    contextual_bridge,
    process_verifier_margins,
    residual_patch_effects,
    tokenization_report,
)
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402
from mplens.text_cases import group_process_pairs  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--config", default=str(PROJECT / "configs/anchor_smoke.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E01_anchor_matrix"))
    p.add_argument("--dtype", default=None)
    p.add_argument("--device", default="cuda")
    p.add_argument("--max-pairs", type=int, default=None)
    p.add_argument("--max-process-cases", type=int, default=None)
    p.add_argument("--skip-patching", action="store_true")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    config = read_yaml(args.config)
    if args.model_key not in registry:
        raise KeyError(f"Unknown model key: {args.model_key}")
    spec = registry[args.model_key]
    seed = int(config.get("run", {}).get("seed", 20260427))
    random.seed(seed)
    torch.manual_seed(seed)

    terms = config["terms"][: args.max_pairs or config.get("run", {}).get("max_pairs", len(config["terms"]))]
    cases = config["process_cases"][: args.max_process_cases or config.get("run", {}).get("max_process_cases", len(config["process_cases"]))]
    dtype = args.dtype or config.get("run", {}).get("dtype", "bfloat16")
    local_only = args.local_files_only or is_local_model(spec)

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading tokenizer: {args.model_key} -> {spec['path']}", flush=True)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] loading model dtype={dtype} device={args.device}", flush=True)
    model = load_causal_lm(spec["path"], dtype=dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    try:
        num_layers = len(get_transformer_layers(model))
    except Exception:
        num_layers = len(getattr(model.config, "num_hidden_layers", []) or [])
    if not isinstance(num_layers, int) or num_layers <= 0:
        num_layers = int(getattr(model.config, "num_hidden_layers", 0) or 0)
    patch_layers = auto_patch_layers(num_layers) if num_layers else []

    print(f"[{datetime.now().isoformat(timespec='seconds')}] tokenization", flush=True)
    tok_report = tokenization_report(tokenizer, terms)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] contextual bridge", flush=True)
    bridge = contextual_bridge(model, tokenizer, terms, device)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] process verifier margins", flush=True)
    proc = process_verifier_margins(model, tokenizer, cases, device)
    if args.skip_patching:
        patch = {"skipped": True, "reason": "--skip-patching"}
    else:
        pairs = group_process_pairs(cases)
        print(f"[{datetime.now().isoformat(timespec='seconds')}] residual patching pairs={len(pairs)} layers={patch_layers}", flush=True)
        try:
            patch = residual_patch_effects(model, tokenizer, pairs, patch_layers, device)
        except Exception as exc:  # noqa: BLE001
            patch = {"skipped": True, "error": repr(exc), "layers_attempted": patch_layers}
            print(f"patching failed: {exc!r}", flush=True)

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "model_config": {
            "architectures": getattr(model.config, "architectures", None),
            "model_type": getattr(model.config, "model_type", None),
            "num_hidden_layers": getattr(model.config, "num_hidden_layers", None),
            "hidden_size": getattr(model.config, "hidden_size", None),
            "vocab_size": getattr(model.config, "vocab_size", None),
        },
        "dtype": dtype,
        "device": str(device),
        "num_terms": len(terms),
        "num_process_cases": len(cases),
        "patch_layers": patch_layers,
        "tokenization": tok_report,
        "contextual_bridge": bridge,
        "process_verifier": proc,
        "residual_patching": patch,
    }
    out_dir = Path(args.out_dir)
    out_path = out_dir / f"{args.model_key}_anchor_smoke.json"
    write_json(out_path, result)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] wrote {out_path}", flush=True)
    best = bridge.get("best_layer", {})
    print(
        f"SUMMARY model={args.model_key} bridge_best_layer={best.get('layer')} top1={best.get('top1')} "
        f"proc_acc={proc.get('accuracy')} invalid_fc_false_accept={proc.get('invalid_final_correct_false_accept_rate')}",
        flush=True,
    )


if __name__ == "__main__":
    main()
