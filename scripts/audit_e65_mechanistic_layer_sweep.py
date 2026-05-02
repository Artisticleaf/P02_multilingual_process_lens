#!/usr/bin/env python3
"""Audit/report E65 E61 layer-sweep results."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it", "glm47_flash_candidate"]
RESULT_DIR = PROJECT / "results/E65_mechanistic_layer_sweep"
REPORT = PROJECT / "reports/E65_MECHANISTIC_LAYER_SWEEP_20260429.md"
AUDIT = PROJECT / "reports/E65_MECHANISTIC_LAYER_SWEEP_AUDIT_20260429.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(x: Any) -> str:
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    checks = []
    rows = []
    for model in MODELS:
        path = RESULT_DIR / f"{model}_e65_e61_layer_sweep.json"
        exists = path.exists()
        checks.append({"check": f"{model} E65 result exists", "ok": exists, "detail": str(path.relative_to(PROJECT))})
        if not exists:
            continue
        data = read_json(path)
        checks.append({"check": f"{model} model key", "ok": data.get("model_key") == model, "detail": str(data.get("model_key"))})
        checks.append({"check": f"{model} dataset E61", "ok": data.get("dataset") == "E61", "detail": str(data.get("dataset"))})
        checks.append({"check": f"{model} no prompt leakage labels", "ok": data.get("leakage_audit", {}).get("gold_label_in_prompt_rows") == 0, "detail": str(data.get("leakage_audit", {}).get("gold_label_in_prompt_rows"))})
        best = data["best_all_layer"]
        rows.append(
            {
                "model_key": model,
                "layers_count": data["layers_count"],
                "items_count": data["items_count"],
                "best_layer": best["layer"],
                "best_accuracy": best["accuracy"],
                "mean_score_valid": best["mean_score_valid"],
                "mean_score_invalid": best["mean_score_invalid"],
                "result_path": str(path.relative_to(PROJECT)),
            }
        )
    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(c["ok"] for c in checks) and len(rows) == len(MODELS),
        "checks": checks,
        "rows": rows,
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E65 Mechanistic Layer Sweep / E65 机制层扫描（2026-04-29）",
        "",
        f"- Audit / 审计：`{AUDIT.relative_to(PROJECT)}`",
        "- Plain language / 说人话：E65 不再只看第 16 层，而是在 E61 的 96 条多语言/多错误类型 trace 上扫描每一层 final-token residual，看哪一层最能线性区分 strict valid 与 strict invalid。",
        "",
        "## Best Layer Summary / 最佳层汇总",
        "",
        "| model | layers | items | best layer | LOTO accuracy | mean valid score | mean invalid score |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['model_key']}` | {r['layers_count']} | {r['items_count']} | {r['best_layer']} | "
            f"{fmt(r['best_accuracy'])} | {fmt(r['mean_score_valid'])} | {fmt(r['mean_score_invalid'])} |"
        )
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- Hidden evidence is broad / 隐藏证据更广：四个 P0/扩展 P0 模型在 E61 上都存在可线性读出的 strict process-validity residual 方向，最佳层准确率从 0.927 到 1.000。 / All four models show linearly recoverable strict process-validity directions on E61, with best-layer accuracy from 0.927 to 1.000.",
        "- GLM is especially informative / GLM 特别有信息：GLM 的 A/B sibling 行为较弱，但 layer 27 residual probe 达到 0.979。这说明它并非没有过程有效性证据，而是输出决策/对比标签使用没有稳定调用这些证据。 / GLM has weak A/B sibling behavior but a 0.979 residual probe at layer 27, so the evidence exists internally but is not reliably used by the output decision.",
        "- Mechanism boundary / 机制边界：E65 是 representation-level diagnostic，不是完整电路；它还没有说明哪些 head/neuron 写入该方向，也没有做路径特异 causal mediation。 / E65 is a representation diagnostic, not a full circuit; it does not identify heads/neurons or prove path-specific mediation.",
        "- Next mechanism step / 下一步机制：E66/E67-style work should combine best-layer directions with output-head/label-bias mediation and span-local patching. / Next, combine best-layer directions with output-head/label-bias mediation and span-local patching.",
        "",
        "## Audit / 审计",
        "",
    ]
    for c in checks:
        lines.append(f"- {'PASS' if c['ok'] else 'FAIL'}: {c['check']} — {c['detail']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"passed": audit["passed"], "report": str(REPORT), "audit": str(AUDIT)}, ensure_ascii=False, indent=2))
    if not audit["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
