#!/usr/bin/env python3
"""Smoke-load a local model with vLLM and record whether the backend is usable.

This is a technical appendix helper, not an evaluation script.  It only checks
whether vLLM can initialize the model; it does not generate benchmark outputs.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import traceback
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from vllm import LLM  # noqa: E402

from mplens.io_utils import read_yaml, write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "logs"))
    p.add_argument("--tensor-parallel-size", type=int, default=1)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.5)
    p.add_argument("--max-model-len", type=int, default=1024)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--model-impl", choices=["auto", "vllm", "transformers"], default="auto")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    spec = read_yaml(args.registry)["models"][args.model_key]
    kwargs = dict(
        model=spec["path"],
        tokenizer=spec["path"],
        trust_remote_code=True,
        tensor_parallel_size=args.tensor_parallel_size,
        dtype=args.dtype,
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )
    if args.model_impl != "auto":
        kwargs["model_impl"] = args.model_impl
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "host": socket.gethostname(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "backend": "vllm",
        "ok": False,
        "error_type": None,
        "error_text": None,
        "traceback_tail": None,
    }
    try:
        llm = LLM(**kwargs)
        del llm
        result["ok"] = True
    except Exception as exc:  # noqa: BLE001 - this is an appendix smoke test.
        result["error_type"] = type(exc).__name__
        result["error_text"] = str(exc)
        result["traceback_tail"] = "\n".join(traceback.format_exc().splitlines()[-25:])
    out = Path(args.out_dir) / f"backend_compat_{args.model_key}_vllm_{args.model_impl}_20260428.json"
    write_json(out, result)
    print(json.dumps({"ok": result["ok"], "error_type": result["error_type"], "out": str(out)}, ensure_ascii=False, indent=2))
    if not result["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
