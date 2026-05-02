#!/usr/bin/env python3
"""Summarize E40 residual span patching over E39 surface-semantic traps."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def fmt(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def task_from_pair(pair_id: str) -> str:
    # e39_<task>_bad..._valid..._<model>
    if not pair_id.startswith("e39_"):
        return pair_id
    rest = pair_id[len("e39_"):]
    return rest.split("_bad", 1)[0]


def load_results(results_dir: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted(results_dir.glob("*_real_acpi_span_patch.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_path"] = str(path)
        out.append(data)
    return out


def clean_score(r: dict[str, Any]) -> float:
    return float(r["mean_valid_to_bad_effect"]) - float(r["mean_bad_to_valid_effect"])


def summarize(data_list: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    lines = [
        "# E40 Surface-Semantic Residual Span Patch Summary / E40 表层语义 residual span patch 汇总",
        "",
        f"Created / 创建时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "E40 asks whether the new E39 surface-semantic traps contain patchable hidden process evidence. / E40 问的是：E39 新增表层语义陷阱里是否也有可 patch 的隐藏过程证据。",
        "A clean direction means `valid->bad` raises the Yes-minus-No process margin on the bad trace and `bad->valid` lowers it on the valid trace. / 干净方向指 `valid->bad` 提高坏 trace 的 Yes-No 过程边际，同时 `bad->valid` 降低好 trace 的边际。",
        "",
    ]
    aggregate: dict[str, Any] = {"models": {}}
    for data in data_list:
        model = data["model_key"]
        rows = data.get("by_span_layer_pair", [])
        raw_rows = data.get("rows", [])
        raw_by_pair = defaultdict(list)
        for r in raw_rows:
            raw_by_pair[r["pair_id"]].append(r)
        best_rows = []
        for pair_id in sorted({r["pair_id"] for r in rows}):
            group = [r for r in rows if r["pair_id"] == pair_id and r["span"] == "support_error_span"]
            clean = [r for r in group if r["mean_valid_to_bad_effect"] > 0 and r["mean_bad_to_valid_effect"] < 0]
            best = max(clean or group, key=lambda r: (clean_score(r), float(r.get("mean_abs_effect", 0))))
            raw0 = raw_by_pair[pair_id][0] if raw_by_pair[pair_id] else {}
            best_rows.append(
                {
                    "pair_id": pair_id,
                    "task": task_from_pair(pair_id),
                    "best_is_clean": bool(clean),
                    "best_layer": best["layer"],
                    "best_v2b": float(best["mean_valid_to_bad_effect"]),
                    "best_b2v": float(best["mean_bad_to_valid_effect"]),
                    "base_valid": raw0.get("base_valid_margin"),
                    "base_bad": raw0.get("base_bad_margin"),
                    "bad_span": raw0.get("bad_span_text"),
                    "valid_span": raw0.get("valid_span_text"),
                }
            )
        aggregate["models"][model] = {
            "input_path": data.get("_path"),
            "n_pairs": len(best_rows),
            "clean_pairs": sum(1 for r in best_rows if r["best_is_clean"]),
            "best_rows": best_rows,
        }
        lines.extend([f"## {model}", ""])
        clean_n = sum(1 for r in best_rows if r["best_is_clean"])
        lines.append(f"Clean residual support/error signal: {clean_n}/{len(best_rows)} pairs. / 干净 residual support/error 信号：{clean_n}/{len(best_rows)} 对。")
        lines.append("")
        lines.append("| task / 任务 | clean? | layer | valid->bad | bad->valid | base valid | base bad | bad span / 错误 span | valid span / 支持 span |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---|---|")
        for r in best_rows:
            lines.append(
                f"| {r['task']} | {r['best_is_clean']} | {r['best_layer']} | {fmt(r['best_v2b'])} | {fmt(r['best_b2v'])} | "
                f"{fmt(r['base_valid'])} | {fmt(r['base_bad'])} | {r['bad_span']} | {r['valid_span']} |"
            )
        lines.append("")
    lines.extend([
        "## Interpretation rule / 解释规则",
        "",
        "- Many clean pairs support generalization of the hidden process-signal claim beyond discount and E31. / 多数 pair 干净支持 hidden process signal 泛化到折扣和 E31 之外。",
        "- A high bad base margin plus clean patch means the verifier has evidence but the final threshold still accepts. / 坏 trace 基础边际高且 patch 干净，说明有证据但最终阈值仍接受。",
        "- Weak or unclean pairs should become boundary cases, not be hidden in averages. / 弱或不干净 pair 应作为边界样例，而不是被平均值掩盖。",
    ])
    return lines, aggregate


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default=str(PROJECT / "results/E40_surface_semantic_span_patch"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/E40_surface_semantic_span_patch_summary_20260428.md"))
    p.add_argument("--out-json", default=str(PROJECT / "results/E40_surface_semantic_span_patch/summary.json"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    results = load_results(Path(args.results_dir))
    if not results:
        raise SystemExit(f"No span patch results found in {args.results_dir}")
    lines, aggregate = summarize(results)
    Path(args.out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps({"aggregate": aggregate}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out_md} and {args.out_json}")


if __name__ == "__main__":
    main()
