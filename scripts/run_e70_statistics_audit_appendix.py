#!/usr/bin/env python3
"""E70 statistics and audit appendix.

Computes binomial Wilson intervals and E61 leave-one-family sensitivity for the
main verifier-risk metrics.  No model inference is run.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT / "results/E70_statistics_audit_appendix"
REPORT = PROJECT / "reports/E70_STATISTICS_AUDIT_APPENDIX_20260429.md"
AUDIT = PROJECT / "reports/E70_STATISTICS_AUDIT_APPENDIX_AUDIT_20260429.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def fmt(x: Any) -> str:
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def collect_metric_rows() -> list[dict[str, Any]]:
    out = []
    for exp, directory in [
        ("E60", PROJECT / "results/E60_objective_ladder"),
        ("E61", PROJECT / "results/E61_language_error_grid"),
    ]:
        for path in sorted(directory.glob("*_chat.json")):
            data = read_json(path)
            model = data.get("model_key") or data.get("verifier_model_key")
            rows = data.get("rows", [])
            for objective in sorted({r.get("objective") for r in rows if r.get("objective_type") == "pointwise"}):
                rr = [r for r in rows if r.get("objective_type") == "pointwise" and r.get("objective") == objective and not r["target_process_valid"]]
                k = sum(1 for r in rr if r["pred_process_valid"])
                lo, hi = wilson(k, len(rr))
                out.append(
                    {
                        "experiment": exp,
                        "model_key": model,
                        "objective": objective,
                        "metric": "strict_acpi_accept",
                        "k": k,
                        "n": len(rr),
                        "value": k / len(rr) if rr else None,
                        "wilson95_low": lo,
                        "wilson95_high": hi,
                    }
                )
            for objective in sorted({r.get("objective") for r in rows if r.get("objective_type") == "contrastive"}):
                rr = [r for r in rows if r.get("objective_type") == "contrastive" and r.get("objective") == objective]
                k = sum(1 for r in rr if r["correct"])
                lo, hi = wilson(k, len(rr))
                out.append(
                    {
                        "experiment": exp,
                        "model_key": model,
                        "objective": objective,
                        "metric": "sibling_accuracy",
                        "k": k,
                        "n": len(rr),
                        "value": k / len(rr) if rr else None,
                        "wilson95_low": lo,
                        "wilson95_high": hi,
                    }
                )
    return out


def e61_leave_one_family() -> list[dict[str, Any]]:
    out = []
    for path in sorted((PROJECT / "results/E61_language_error_grid").glob("*_chat.json")):
        data = read_json(path)
        model = data.get("model_key")
        rows = data.get("rows", [])
        families = sorted({r.get("family") for r in rows if r.get("family")})
        for objective in ["plain_yes_no", "careful_yes_no", "answer_blind_yes_no", "locate_then_judge_yes_no"]:
            base = [
                r
                for r in rows
                if r.get("objective_type") == "pointwise"
                and r.get("objective") == objective
                and not r["target_process_valid"]
            ]
            base_rate = mean([1.0 if r["pred_process_valid"] else 0.0 for r in base])
            vals = []
            for fam in families:
                rr = [r for r in base if r.get("family") != fam]
                vals.append(mean([1.0 if r["pred_process_valid"] else 0.0 for r in rr]))
            out.append(
                {
                    "model_key": model,
                    "objective": objective,
                    "metric": "E61_strict_acpi_accept_leave_one_family",
                    "base": base_rate,
                    "min_leave_one": min(vals),
                    "max_leave_one": max(vals),
                    "range": max(vals) - min(vals),
                }
            )
        for objective in ["sibling_comparison", "careful_sibling_comparison"]:
            base = [r for r in rows if r.get("objective_type") == "contrastive" and r.get("objective") == objective]
            base_rate = mean([1.0 if r["correct"] else 0.0 for r in base])
            vals = []
            for fam in families:
                rr = [r for r in base if r.get("family") != fam]
                vals.append(mean([1.0 if r["correct"] else 0.0 for r in rr]))
            out.append(
                {
                    "model_key": model,
                    "objective": objective,
                    "metric": "E61_sibling_accuracy_leave_one_family",
                    "base": base_rate,
                    "min_leave_one": min(vals),
                    "max_leave_one": max(vals),
                    "range": max(vals) - min(vals),
                }
            )
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metric_rows = collect_metric_rows()
    loo_rows = e61_leave_one_family()
    out = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "metric_rows": metric_rows,
        "e61_leave_one_family": loo_rows,
        "scope_note_zh": "E70 提供统计区间和 leave-one-family 敏感性；不是新推理实验。",
    }
    out_path = OUT_DIR / "e70_statistics_audit_appendix.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "passed": bool(metric_rows) and bool(loo_rows),
        "result_path": str(out_path.relative_to(PROJECT)),
        "checks": [
            {"check": "metric rows non-empty", "ok": bool(metric_rows), "detail": str(len(metric_rows))},
            {"check": "E61 LOO rows non-empty", "ok": bool(loo_rows), "detail": str(len(loo_rows))},
        ],
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E70 Statistics and Audit Appendix / E70 统计与审计附录（2026-04-29）",
        "",
        f"- Result / 结果：`{out_path.relative_to(PROJECT)}`",
        f"- Audit / 审计：`{AUDIT.relative_to(PROJECT)}`",
        "- Plain language / 说人话：E70 不再跑模型，而是给关键比例加置信区间，并检查 E61 结论是不是被某一个错误类型单独撑起来。",
        "",
        "## Wilson Intervals / Wilson 区间",
        "",
        "| exp | model | objective | metric | k/n | value | 95% CI |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for r in metric_rows:
        lines.append(
            f"| {r['experiment']} | `{r['model_key']}` | `{r['objective']}` | {r['metric']} | "
            f"{r['k']}/{r['n']} | {fmt(r['value'])} | [{fmt(r['wilson95_low'])}, {fmt(r['wilson95_high'])}] |"
        )
    lines += [
        "",
        "## E61 Leave-One-Family / E61 留一错误类型敏感性",
        "",
        "| model | objective | metric | base | min LOO | max LOO | range |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in loo_rows:
        lines.append(
            f"| `{r['model_key']}` | `{r['objective']}` | {r['metric']} | {fmt(r['base'])} | "
            f"{fmt(r['min_leave_one'])} | {fmt(r['max_leave_one'])} | {fmt(r['range'])} |"
        )
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- The main pointwise ACPI-acceptance effect has wide but nonzero uncertainty because controlled pools are intentionally diagnostic, not massive benchmark samples. / 单点 ACPI 接受率的区间较宽，因为这些池是诊断集而不是海量 benchmark。",
        "- E61 leave-one-family checks show whether a result depends on one error family; high ranges flag where the paper should avoid overgeneralizing. / E61 留一检查告诉我们结论是否被某一类错误单独驱动；range 高时论文不能过度泛化。",
        "- GLM rows should be reported as expanded-P0 boundary evidence, not mixed into the original core-P0 headline without qualification. / GLM 应作为扩展 P0 边界证据报告，不能不加限定地混入核心 P0 headline。",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(out_path), "report": str(REPORT), "audit": str(AUDIT)}, ensure_ascii=False, indent=2))
    if not audit["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
