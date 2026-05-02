#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.anchor_eval import tokenization_report  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_tokenizer  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--config", default=str(PROJECT / "configs/anchor_smoke.yaml"))
    p.add_argument("--out", default=str(PROJECT / "results/E01_anchor_matrix/tokenizer_inventory.json"))
    p.add_argument("--include-remote", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    config = read_yaml(args.config)
    terms = config["terms"]
    rows = []
    failures = []
    for key, spec in registry.items():
        if spec.get("status") == "remote" and not args.include_remote:
            continue
        local_only = is_local_model(spec)
        try:
            tok = load_tokenizer(spec["path"], local_files_only=local_only)
            rep = tokenization_report(tok, terms)
            for row in rep:
                row["model_key"] = key
                row["model_path"] = spec["path"]
                row["family"] = spec.get("family")
            rows.extend(rep)
        except Exception as exc:  # noqa: BLE001
            failures.append({"model_key": key, "path": spec["path"], "error": repr(exc)})
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "include_remote": args.include_remote,
        "num_rows": len(rows),
        "num_failures": len(failures),
        "rows": rows,
        "failures": failures,
    }
    write_json(args.out, summary)
    print(f"wrote {args.out}; rows={len(rows)} failures={len(failures)}")
    if failures:
        for f in failures:
            print(f"FAIL {f['model_key']}: {f['error']}")


if __name__ == "__main__":
    main()
