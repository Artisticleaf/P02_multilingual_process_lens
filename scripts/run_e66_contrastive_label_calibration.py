#!/usr/bin/env python3
"""E66 contrastive label/position calibration audit.

Reads E60/E61 sibling-comparison logits and separates process discrimination
from A/B output-head or position priors.  No model inference is run here.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT / "results/E66_contrastive_label_calibration"
REPORT = PROJECT / "reports/E66_CONTRASTIVE_LABEL_CALIBRATION_20260429.md"
AUDIT = PROJECT / "reports/E66_CONTRASTIVE_LABEL_CALIBRATION_AUDIT_20260429.json"


INPUTS = [
    ("E60", PROJECT / "results/E60_objective_ladder"),
    ("E61", PROJECT / "results/E61_language_error_grid"),
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_files() -> list[tuple[str, Path]]:
    out = []
    for exp, directory in INPUTS:
        for path in sorted(directory.glob("*_chat.json")):
            out.append((exp, path))
    return out


def analyze(exp: str, path: Path) -> list[dict[str, Any]]:
    result = read_json(path)
    model_key = result.get("model_key") or result.get("verifier_model_key")
    rows = [r for r in result.get("rows", []) if r.get("objective_type") == "contrastive"]
    out = []
    for objective in sorted({r["objective"] for r in rows}):
        rr = [r for r in rows if r["objective"] == objective]
        if not rr:
            continue
        scores = [float(r["a_score"] - r["b_score"]) for r in rr]
        global_ab_bias = mean(scores)
        raw_acc = mean([1.0 if r["correct"] else 0.0 for r in rr])
        pred_a_rate = mean([1.0 if r["pred"] == "A" else 0.0 for r in rr])
        calibrated_acc = mean(
            [
                1.0
                if ("A" if float(r["a_score"] - r["b_score"]) - global_ab_bias >= 0 else "B") == r["target"]
                else 0.0
                for r in rr
            ]
        )

        groups: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        for r in rr:
            groups[str(r["pair_id"])][str(r["order"])] = r
        pair_rows = []
        for pair_id, g in groups.items():
            if "bad_A" not in g or "bad_B" not in g:
                continue
            s_bad_a = float(g["bad_A"]["a_score"] - g["bad_A"]["b_score"])
            s_bad_b = float(g["bad_B"]["a_score"] - g["bad_B"]["b_score"])
            canceled = s_bad_a - s_bad_b
            correct_count = int(bool(g["bad_A"].get("correct"))) + int(bool(g["bad_B"].get("correct")))
            pair_rows.append(
                {
                    "pair_id": pair_id,
                    "pair_canceled_process_margin": canceled,
                    "pair_canceled_correct": canceled > 0,
                    "both_orders_correct": correct_count == 2,
                    "one_order_correct": correct_count == 1,
                    "no_order_correct": correct_count == 0,
                    "bad_A_score_AminusB": s_bad_a,
                    "bad_B_score_AminusB": s_bad_b,
                }
            )
        pair_acc = mean([1.0 if r["pair_canceled_correct"] else 0.0 for r in pair_rows]) if pair_rows else None
        both = sum(1 for r in pair_rows if r["both_orders_correct"])
        one = sum(1 for r in pair_rows if r["one_order_correct"])
        none = sum(1 for r in pair_rows if r["no_order_correct"])
        out.append(
            {
                "experiment": exp,
                "source_path": str(path.relative_to(PROJECT)),
                "model_key": model_key,
                "objective": objective,
                "n_rows": len(rr),
                "n_pairs": len(pair_rows),
                "raw_row_accuracy": raw_acc,
                "pred_A_rate": pred_a_rate,
                "global_AminusB_bias": global_ab_bias,
                "global_bias_calibrated_row_accuracy": calibrated_acc,
                "order_canceled_pair_accuracy": pair_acc,
                "both_orders_correct_pairs": both,
                "one_order_correct_pairs": one,
                "no_order_correct_pairs": none,
                "pair_rows": pair_rows,
            }
        )
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
    for exp, path in iter_files():
        if "debug" in path.name:
            continue
        checks.append({"check": f"input exists {path.name}", "ok": path.exists(), "detail": str(path.relative_to(PROJECT))})
        rows.extend(analyze(exp, path))
    out = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "rows": rows,
        "scope_note_en": "E66 reuses already-audited E60/E61 logits. It does not insert labels/spans into model prompts and runs no new inference.",
        "scope_note_zh": "E66 复用已审计的 E60/E61 logit，不向模型 prompt 插入标签或 span，也不进行新推理。",
    }
    out_path = OUT_DIR / "e66_contrastive_label_calibration.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(c["ok"] for c in checks) and bool(rows),
        "checks": checks,
        "result_path": str(out_path.relative_to(PROJECT)),
        "leakage_boundary_zh": "E66 是后处理校准；它只读取模型对 A/B 的分数，不改变 prompt，也不使用人工错误 span。",
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E66 Contrastive Label Calibration / E66 对比式标签校准（2026-04-29）",
        "",
        f"- Result / 结果：`{out_path.relative_to(PROJECT)}`",
        f"- Audit / 审计：`{AUDIT.relative_to(PROJECT)}`",
        "- Plain language / 说人话：sibling comparison 让模型比较 A/B 两条 trace，但 A/B 字母本身也可能有先验。E66 把“模型懂不懂哪条过程错”和“输出头偏爱 A 还是 B”拆开看。",
        "",
        "## Calibration Table / 校准表",
        "",
        "| exp | model | objective | raw acc | pred_A | global A-B bias | calibrated row acc | order-canceled pair acc | both/one/none pairs |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['experiment']} | `{r['model_key']}` | `{r['objective']}` | {fmt(r['raw_row_accuracy'])} | "
            f"{fmt(r['pred_A_rate'])} | {fmt(r['global_AminusB_bias'])} | {fmt(r['global_bias_calibrated_row_accuracy'])} | "
            f"{fmt(r['order_canceled_pair_accuracy'])} | {r['both_orders_correct_pairs']}/{r['one_order_correct_pairs']}/{r['no_order_correct_pairs']} |"
        )
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- Core P0 boundary / 核心 P0 边界：Qwen35-27B、Gemma4-31B 和多数 Gemma4-26B-A4B 条件下，raw sibling 已经接近或达到 1.0；校准不是主因。 / For the core P0 models, raw sibling is already near-perfect, so calibration is not the main explanation.",
        "- GLM boundary / GLM 边界：GLM-4.7-Flash 的 raw sibling 明显受 A/B 或位置偏置影响；简单全局校准只能小幅改善，order-canceled pair accuracy 也仍明显低于核心 P0。这说明 GLM 不只是输出格式坏，而是 contrastive process discrimination 本身也更弱。 / GLM has strong A/B or position bias; simple calibration helps only partly, so contrastive process discrimination is weaker than in core P0.",
        "- Scientific update / 科学更新：我们的 claim 应把 sibling comparison 写成“通常更强、能暴露很多 absolute 没用好的过程信号”，而不是“所有模型上必然完美”。这反而给论文增加一个机制点：verifier 决策还会被输出头标签先验重整。 / The claim should say sibling is usually stronger and exposes many underused process signals, not that it is always perfect; this adds a mechanism point about output-head label priors.",
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
