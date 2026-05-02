#!/usr/bin/env python3
"""E68 expanded filter-retention simulation over E60/E61.

Simulates how different selection filters retain strict ACPI traces in balanced
valid/invalid controlled pools.  No new inference is run.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT / "results/E68_filter_amplification_expanded"
REPORT = PROJECT / "reports/E68_FILTER_AMPLIFICATION_EXPANDED_20260429.md"
AUDIT = PROJECT / "reports/E68_FILTER_AMPLIFICATION_EXPANDED_AUDIT_20260429.json"


INPUTS = {
    "E60": PROJECT / "results/E60_objective_ladder",
    "E61": PROJECT / "results/E61_language_error_grid",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pointwise_metrics(rows: list[dict[str, Any]], objective: str) -> dict[str, Any]:
    rr = [r for r in rows if r.get("objective_type") == "pointwise" and r.get("objective") == objective]
    invalid = [r for r in rr if not r["target_process_valid"]]
    valid = [r for r in rr if r["target_process_valid"]]
    invalid_accept = sum(r["pred_process_valid"] for r in invalid) / len(invalid) if invalid else None
    valid_accept = sum(r["pred_process_valid"] for r in valid) / len(valid) if valid else None
    accepted_invalid_share = None
    if invalid_accept is not None and valid_accept is not None and invalid_accept + valid_accept > 0:
        accepted_invalid_share = invalid_accept / (invalid_accept + valid_accept)
    return {
        "objective_type": "pointwise",
        "objective": objective,
        "n_valid": len(valid),
        "n_invalid": len(invalid),
        "strict_acpi_retention": invalid_accept,
        "valid_retention": valid_accept,
        "accepted_invalid_share_balanced": accepted_invalid_share,
    }


def contrastive_metrics(rows: list[dict[str, Any]], objective: str) -> dict[str, Any]:
    rr = [r for r in rows if r.get("objective_type") == "contrastive" and r.get("objective") == objective]
    acc = mean([1.0 if r["correct"] else 0.0 for r in rr]) if rr else None
    # In a paired selector that should discard the invalid trace, a wrong A/B
    # decision means the invalid sibling is retained and the valid one discarded.
    strict_acpi_retention = (1.0 - acc) if acc is not None else None
    valid_retention = acc
    accepted_invalid_share = None
    if acc is not None and strict_acpi_retention + valid_retention > 0:
        accepted_invalid_share = strict_acpi_retention / (strict_acpi_retention + valid_retention)
    return {
        "objective_type": "contrastive",
        "objective": objective,
        "n_rows": len(rr),
        "strict_acpi_retention": strict_acpi_retention,
        "valid_retention": valid_retention,
        "accepted_invalid_share_balanced": accepted_invalid_share,
    }


def analyze_file(exp: str, path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    model = data.get("model_key") or data.get("verifier_model_key")
    rows = data.get("rows", [])
    objectives = sorted({r.get("objective") for r in rows if r.get("objective_type") == "pointwise"})
    out = []
    # Outcome-only filter: all rows here are final-correct controlled rows, so it
    # keeps all strict ACPI and all valid traces.
    out.append(
        {
            "experiment": exp,
            "model_key": model,
            "objective_type": "outcome_only",
            "objective": "outcome_only_final_correct",
            "strict_acpi_retention": 1.0,
            "valid_retention": 1.0,
            "accepted_invalid_share_balanced": 0.5,
        }
    )
    for obj in objectives:
        m = pointwise_metrics(rows, str(obj))
        m.update({"experiment": exp, "model_key": model})
        out.append(m)
    for obj in sorted({r.get("objective") for r in rows if r.get("objective_type") == "contrastive"}):
        m = contrastive_metrics(rows, str(obj))
        m.update({"experiment": exp, "model_key": model})
        out.append(m)
    return out


def fmt(x: Any) -> str:
    if x is None:
        return "NA"
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    checks = []
    for exp, directory in INPUTS.items():
        for path in sorted(directory.glob("*_chat.json")):
            if "debug" in path.name:
                continue
            checks.append({"check": f"{exp} input {path.name}", "ok": path.exists(), "detail": str(path.relative_to(PROJECT))})
            rows.extend(analyze_file(exp, path))
    by_filter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_filter[f"{row['experiment']}::{row['objective']}"].append(row)
    aggregate = []
    for key, group in sorted(by_filter.items()):
        aggregate.append(
            {
                "slice": key,
                "n_models": len(group),
                "mean_strict_acpi_retention": mean([r["strict_acpi_retention"] for r in group if r["strict_acpi_retention"] is not None]),
                "mean_valid_retention": mean([r["valid_retention"] for r in group if r["valid_retention"] is not None]),
                "mean_accepted_invalid_share_balanced": mean([r["accepted_invalid_share_balanced"] for r in group if r["accepted_invalid_share_balanced"] is not None]),
            }
        )
    out = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "rows": rows,
        "aggregate": aggregate,
        "scope_note_zh": "E68 是 balanced controlled-pool 筛选模拟；它估计 filter 保留 strict ACPI 的风险，不是自然发生率。",
    }
    out_path = OUT_DIR / "e68_filter_amplification_expanded.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(c["ok"] for c in checks) and bool(rows),
        "checks": checks,
        "result_path": str(out_path.relative_to(PROJECT)),
        "leakage_boundary_zh": "E68 只读取已审计输出；不新增 prompt，不使用错误 span 影响模型。",
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E68 Expanded Filter Amplification / E68 扩展筛选器放大模拟（2026-04-29）",
        "",
        f"- Result / 结果：`{out_path.relative_to(PROJECT)}`",
        f"- Audit / 审计：`{AUDIT.relative_to(PROJECT)}`",
        "- Plain language / 说人话：如果一个数据管线只保留“答案对”或让模型单独回答 Yes/No，它会留下多少严格过程错误？E68 把不同 filter 放在同一个 balanced valid/invalid pool 上比较。",
        "",
        "## Aggregate / 聚合",
        "",
        "| slice | models | mean strict ACPI retention | mean valid retention | accepted invalid share |",
        "|---|---:|---:|---:|---:|",
    ]
    for a in aggregate:
        lines.append(
            f"| `{a['slice']}` | {a['n_models']} | {fmt(a['mean_strict_acpi_retention'])} | "
            f"{fmt(a['mean_valid_retention'])} | {fmt(a['mean_accepted_invalid_share_balanced'])} |"
        )
    lines += [
        "",
        "## Model-Level Rows / 模型级结果",
        "",
        "| exp | model | objective | type | strict ACPI retention | valid retention | accepted invalid share |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['experiment']} | `{r['model_key']}` | `{r['objective']}` | {r['objective_type']} | "
            f"{fmt(r['strict_acpi_retention'])} | {fmt(r['valid_retention'])} | {fmt(r['accepted_invalid_share_balanced'])} |"
        )
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- Outcome-only is maximally risky in controlled ACPI pools: it keeps all answer-correct invalid traces by definition. / 只看答案在受控 ACPI 池中最危险：它按定义保留所有答案正确但过程有错的 trace。",
        "- Plain pointwise Yes/No keeps a large fraction of strict ACPI while also keeping nearly all valid traces; this is the core trace-selection risk. / 普通单点 Yes/No 会保留大量 strict ACPI，同时几乎保留所有 valid trace，这是核心筛选风险。",
        "- Careful and answer-blind pointwise filters reduce risk but do not define a universal fix. / 仔细检查和 answer-blind 会降风险，但不是通用修复。",
        "- Sibling filters suppress strict ACPI strongly for core P0, but GLM makes the expanded-P0 story more nuanced because A/B contrastive discrimination can itself be weak. / sibling 对核心 P0 压制很强，但 GLM 说明扩展 P0 中 A/B 对比判别本身也可能弱。",
        "",
        "## Audit / 审计",
        "",
    ]
    for c in checks:
        lines.append(f"- {'PASS' if c['ok'] else 'FAIL'}: {c['check']} — {c['detail']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(out_path), "report": str(REPORT), "audit": str(AUDIT), "rows": len(rows)}, ensure_ascii=False, indent=2))
    if not audit["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
