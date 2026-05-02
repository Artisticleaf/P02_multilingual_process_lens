#!/usr/bin/env python3
"""Summarize E36 inequality-boundary span-variant patching."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def variant_label(pair_id: str) -> str:
    for key, label in [
        ("full_condition", "完整条件短语"),
        ("lower_bound", "下界短语"),
        ("upper_bound", "上界/端点短语"),
        ("corrective_list", "后续正确列表"),
        ("full_clause", "错误短语+后续修正子句"),
    ]:
        if key in pair_id:
            return label
    return pair_id


def clean_score(row: dict[str, Any]) -> float:
    return float(row["mean_valid_to_bad_effect"]) - float(row["mean_bad_to_valid_effect"])


def fmt(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def load_results(results_dir: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted(results_dir.glob("*_real_acpi_span_patch.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_path"] = str(path)
        out.append(data)
    return out


def summarize(data_list: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    lines = [
        "# E36 Inequality Boundary Deep Dive / E36 不等式边界样例深挖",
        "",
        f"Created / 创建时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "目的：解释 E31 里 `between 3 and 7, inclusive` 这个边界样例为什么容易被 absolute verifier 接受、同时 residual span patch 又偏弱。这个坏 trace 不是纯错到底：它先写了一个错误/歧义的表层短语，随后又列出了正确集合 `4, 5, 6, 7`，所以它可能把错误证据和纠正证据混在同一条 trace 里。",
        "",
        "判读规则：`valid->bad` 为正且 `bad->valid` 为负，说明 support/error span 的隐藏表示能按预期推动 verifier margin；如果只有后续正确列表有效，而完整错误条件短语无效，说明模型更依赖下游修正/答案一致性而不是局部语义错误。",
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
        best_by_pair = []
        for pair_id, group in sorted(defaultdict(list, {pid: [r for r in rows if r["pair_id"] == pid] for pid in {r["pair_id"] for r in rows}}).items()):
            clean = [r for r in group if float(r["mean_valid_to_bad_effect"]) > 0 and float(r["mean_bad_to_valid_effect"]) < 0]
            best = max(clean or group, key=lambda r: (clean_score(r), float(r.get("mean_abs_effect", 0))))
            raw0 = raw_by_pair[pair_id][0] if raw_by_pair[pair_id] else {}
            best_by_pair.append(
                {
                    "pair_id": pair_id,
                    "variant": variant_label(pair_id),
                    "best_is_clean": bool(clean),
                    "best_layer": best["layer"],
                    "best_v2b": float(best["mean_valid_to_bad_effect"]),
                    "best_b2v": float(best["mean_bad_to_valid_effect"]),
                    "best_score": clean_score(best),
                    "base_valid_margin": raw0.get("base_valid_margin"),
                    "base_bad_margin": raw0.get("base_bad_margin"),
                    "valid_span_text": raw_by_pair[pair_id][0].get("valid_span_text") if raw_by_pair[pair_id] else "",
                    "bad_span_text": raw_by_pair[pair_id][0].get("bad_span_text") if raw_by_pair[pair_id] else "",
                }
            )
        aggregate["models"][model] = {
            "n_variants": len(best_by_pair),
            "n_clean_variants": sum(1 for r in best_by_pair if r["best_is_clean"]),
            "best_by_pair": best_by_pair,
            "input_path": data.get("_path"),
        }
        lines.extend([f"## {model}", ""])
        lines.extend([
            "| variant / 变体 | clean? / 是否方向干净 | best layer / 最强层 | valid->bad | bad->valid | base valid | base bad | bad span / 坏 span | valid span / 好 span |",
            "|---|---:|---:|---:|---:|---:|---:|---|---|",
        ])
        for r in best_by_pair:
            lines.append(
                f"| {r['variant']} | {str(r['best_is_clean'])} | {r['best_layer']} | {fmt(r['best_v2b'])} | {fmt(r['best_b2v'])} | "
                f"{fmt(r['base_valid_margin'])} | {fmt(r['base_bad_margin'])} | {r['bad_span_text']} | {r['valid_span_text']} |"
            )
        clean_n = sum(1 for r in best_by_pair if r["best_is_clean"])
        strongest = max(best_by_pair, key=lambda r: r["best_score"], default=None)
        lines.extend(["", "### 直接解释 / Plain-language interpretation", ""])
        lines.append(f"- 5 个 span 变体中有 {clean_n} 个出现方向干净的 patch 信号；这不是全无信号，而是局部语义错误的信号不稳定。")
        if strongest:
            lines.append(f"- 最强变体是 `{strongest['variant']}`，说明 verifier 隐藏状态最容易被这段 span 的表示推动，而不一定是最早的错误短语本身。")
        lines.append("- 如果 `完整条件短语` 弱、`错误短语+后续修正子句` 或 `后续正确列表` 强，边界解释就是：坏 trace 同时携带错误 phrase 和正确枚举，absolute verifier 被正确枚举/最终答案拉向接受。")
        lines.append("")
    return lines, aggregate


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default=str(PROJECT / "results/E36_inequality_boundary_span_variants"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/E36_inequality_boundary_deep_dive_20260427.md"))
    p.add_argument("--out-json", default=str(PROJECT / "results/E36_inequality_boundary_span_variants/summary.json"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    results = load_results(Path(args.results_dir))
    if not results:
        raise SystemExit(f"No result files found in {args.results_dir}")
    lines, aggregate = summarize(results)
    Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps({"aggregate": aggregate}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out_md} and {args.out_json}")


if __name__ == "__main__":
    main()
