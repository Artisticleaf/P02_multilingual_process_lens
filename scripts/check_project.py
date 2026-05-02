#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def version(modname: str) -> str:
    try:
        mod = __import__(modname)
        return getattr(mod, "__version__", "ok")
    except Exception as exc:  # noqa: BLE001
        return f"MISSING: {exc!r}"


def main() -> None:
    info = {
        "python": sys.executable,
        "project": str(PROJECT),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "all"),
        "packages": {m: version(m) for m in ["torch", "transformers", "safetensors", "accelerate", "yaml", "numpy", "sklearn"]},
    }
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used", "--format=csv,noheader"],
                text=True,
            )
            info["gpus"] = [line.strip() for line in out.splitlines() if line.strip()]
        except Exception as exc:  # noqa: BLE001
            info["gpus_error"] = repr(exc)
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
