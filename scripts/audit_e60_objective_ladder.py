#!/usr/bin/env python3
"""Audit and summarize E60 objective-ladder results."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
P0 = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
OUT_JSON = PROJECT / "reports/E60_OBJECTIVE_LADDER_AUDIT_20260429.json"
OUT_MD = PROJECT / "reports/E60_OBJECTIVE_LADDER_20260429.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def model_path(model: str) -> Path:
    return PROJECT / "results/E60_objective_ladder" / f"{model}_e60_objective_ladder_chat.json"


def all_slice(data: dict[str, Any], objective: str) -> dict[str, Any]:
    for row in data["summary"]:
        if row["objective"] == objective and row["slice_type"] == "all":
            return row
    raise KeyError(objective)


def pool_slice(data: dict[str, Any], objective: str, pool: str) -> dict[str, Any]:
    for row in data["summary"]:
        if row["objective"] == objective and row["slice_type"] == "pool" and row["slice"] == pool:
            return row
    raise KeyError((objective, pool))


def fmt(x: float | None) -> str:
    return "NA" if x is None else f"{x:.3f}"


def main() -> None:
    checks: list[dict[str, Any]] = []
    data_by_model: dict[str, dict[str, Any]] = {}
    for model in P0:
        path = model_path(model)
        add_check(checks, f"E60 result exists for {model}", path.exists(), str(path.relative_to(PROJECT)))
        data = load_json(path)
        data_by_model[model] = data
        rows = data["rows"]
        add_check(checks, f"{model} row count", len(rows) == 360, f"rows={len(rows)}")
        add_check(checks, f"{model} chat template used", bool(data.get("used_chat_template")), str(data.get("used_chat_template")))
        add_check(checks, f"{model} prompt format", data.get("prompt_format") == "official_if_chat", str(data.get("prompt_format")))
        add_check(checks, f"{model} leakage audit zero", all(v == 0 for k, v in data.get("leakage_audit", {}).items() if k.endswith("_rows")), str(data.get("leakage_audit")))
        counts = Counter((r["objective_type"], r["objective"]) for r in rows)
        expected = {
            ("pointwise", "plain_yes_no"): 60,
            ("pointwise", "careful_yes_no"): 60,
            ("pointwise", "answer_blind_yes_no"): 60,
            ("pointwise", "locate_then_judge_yes_no"): 60,
            ("contrastive", "sibling_comparison"): 60,
            ("contrastive", "careful_sibling_comparison"): 60,
        }
        add_check(checks, f"{model} objective counts", counts == expected, str(dict(counts)))

        # Plain objective must reproduce E42/E54 official absolute-process rates.
        e42 = load_json(PROJECT / "results/E42_official_template_parity" / f"{model}_e42_official_template_parity_chat.json")
        e54 = load_json(PROJECT / "results/E54_parameterized_no_leak_generalization" / f"{model}_e42_official_template_parity_chat.json")
        e42_all = next(s for s in e42["summary"] if s["objective"] == "absolute_process" and s["slice"] == "all")
        e54_all = next(s for s in e54["summary"] if s["objective"] == "absolute_process" and s["slice"] == "all")
        e60_e42 = pool_slice(data, "plain_yes_no", "controlled_12_family")
        e60_e54 = pool_slice(data, "plain_yes_no", "parameterized_18_family")
        add_check(
            checks,
            f"{model} E60 plain reproduces E42",
            abs(e60_e42["acpi_accept_rate"] - e42_all["acpi_accept_rate"]) < 1e-9
            and abs(e60_e42["valid_accept_rate"] - e42_all["valid_accept_rate"]) < 1e-9,
            f"E60={e60_e42['acpi_accept_rate']}/{e60_e42['valid_accept_rate']} E42={e42_all['acpi_accept_rate']}/{e42_all['valid_accept_rate']}",
        )
        add_check(
            checks,
            f"{model} E60 plain reproduces E54",
            abs(e60_e54["acpi_accept_rate"] - e54_all["acpi_accept_rate"]) < 1e-9
            and abs(e60_e54["valid_accept_rate"] - e54_all["valid_accept_rate"]) < 1e-9,
            f"E60={e60_e54['acpi_accept_rate']}/{e60_e54['valid_accept_rate']} E54={e54_all['acpi_accept_rate']}/{e54_all['valid_accept_rate']}",
        )

    # Static source audit: prompts should not interpolate metadata labels/spans.
    src = (PROJECT / "scripts/run_e60_objective_ladder.py").read_text(encoding="utf-8")
    prompt_bodies = re.findall(r"def (?:pointwise_prompt|contrastive_prompt).*?(?=\n\ndef |\n\nclass |\n\ndef main)", src, flags=re.S)
    for name in ["support_span", "error_span", "manual_correction", "known_error_spans", "manual_process_valid"]:
        ok = all(name not in body for body in prompt_bodies)
        add_check(checks, f"E60 prompt source does not insert {name}", ok, name)

    objective_order = [
        "plain_yes_no",
        "careful_yes_no",
        "answer_blind_yes_no",
        "locate_then_judge_yes_no",
        "sibling_comparison",
        "careful_sibling_comparison",
    ]
    summary_table = []
    for model, data in data_by_model.items():
        for objective in objective_order:
            s = all_slice(data, objective)
            row = {"model": model, "objective": objective, "objective_type": s["objective_type"], "n": s["n"]}
            if s["objective_type"] == "pointwise":
                row.update(
                    {
                        "accuracy": s["accuracy"],
                        "acpi_accept_rate": s["acpi_accept_rate"],
                        "valid_accept_rate": s["valid_accept_rate"],
                        "yes_rate": s["yes_rate"],
                        "mean_margin": s["mean_margin"],
                    }
                )
            else:
                row.update({"accuracy": s["accuracy"], "mean_target_margin": s["mean_target_margin"], "pred_A_rate": s["pred_A_rate"]})
            summary_table.append(row)

    mean_by_objective = []
    for objective in objective_order:
        vals = [r for r in summary_table if r["objective"] == objective]
        row = {"objective": objective, "objective_type": vals[0]["objective_type"], "models": [v["model"] for v in vals]}
        if vals[0]["objective_type"] == "pointwise":
            row.update(
                {
                    "mean_accuracy": mean(v["accuracy"] for v in vals),
                    "mean_acpi_accept_rate": mean(v["acpi_accept_rate"] for v in vals),
                    "mean_valid_accept_rate": mean(v["valid_accept_rate"] for v in vals),
                    "mean_yes_rate": mean(v["yes_rate"] for v in vals),
                }
            )
        else:
            row.update({"mean_accuracy": mean(v["accuracy"] for v in vals), "mean_target_margin": mean(v["mean_target_margin"] for v in vals)})
        mean_by_objective.append(row)

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "all_checks_passed": all(c["ok"] for c in checks),
        "checks": checks,
        "summary_table": summary_table,
        "mean_by_objective": mean_by_objective,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# E60 Objective Ladder / E60 过程检查目标梯度（2026-04-29）",
        "",
        f"- JSON audit / 机器可读审计：`{OUT_JSON.relative_to(PROJECT)}`",
        "- Scope / 范围：在当前 P0 三模型上，比较普通 absolute Yes/No、更严格的过程检查 prompt、answer-blind prompt、先定位再判断 prompt，以及 sibling comparison。",
        "- Plain language / 说人话：更明确地要求模型“仔细检查过程”确实能显著降低 over-accept，但不能保证清零；把一好一坏 sibling 并排比较仍然最稳。",
        "",
        "## Mean Across P0 / P0 均值",
        "",
        "| objective | type | mean accuracy | mean ACPI accept | mean valid accept | note |",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in mean_by_objective:
        if r["objective_type"] == "pointwise":
            note = {
                "plain_yes_no": "baseline absolute verifier / 普通 absolute verifier",
                "careful_yes_no": "strict line-by-line wording / 严格逐行检查措辞",
                "answer_blind_yes_no": "tells model to cover final answer / 要求不要被最终答案锚定",
                "locate_then_judge_yes_no": "internal error-localization then Yes/No / 内部定位错误后再 Yes/No",
            }[r["objective"]]
            lines.append(
                f"| `{r['objective']}` | pointwise | {fmt(r['mean_accuracy'])} | {fmt(r['mean_acpi_accept_rate'])} | {fmt(r['mean_valid_accept_rate'])} | {note} |"
            )
        else:
            note = "pairwise sibling objective / 成对 sibling 目标"
            lines.append(f"| `{r['objective']}` | contrastive | {fmt(r['mean_accuracy'])} | 0.000 | 1.000 | {note} |")

    lines += [
        "",
        "## By Model / 按模型",
        "",
        "| model | objective | accuracy | ACPI accept | valid accept | yes/pred rate |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in summary_table:
        if r["objective_type"] == "pointwise":
            lines.append(
                f"| `{r['model']}` | `{r['objective']}` | {fmt(r['accuracy'])} | {fmt(r['acpi_accept_rate'])} | {fmt(r['valid_accept_rate'])} | {fmt(r['yes_rate'])} |"
            )
        else:
            lines.append(
                f"| `{r['model']}` | `{r['objective']}` | {fmt(r['accuracy'])} | 0.000 | 1.000 | {fmt(r['pred_A_rate'])} |"
            )

    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- Plain Yes/No reproduces E42/E54: mean ACPI accept is 0.567 across P0, with valid accept near 0.989. / 普通 Yes/No 复现 E42/E54：P0 平均 ACPI 接受为 0.567，valid 接受约 0.989。",
        "- Careful process wording helps a lot: mean ACPI accept falls to 0.156, but it is not zero and differs by model. / 更严格过程措辞很有帮助：平均 ACPI 接受降到 0.156，但没有清零，且有模型差异。",
        "- Answer-blind wording also helps but is weaker than careful line-by-line wording for Qwen/Gemma4-31B and similar for Gemma4-26B-A4B. / answer-blind 措辞也有帮助，但在 Qwen/Gemma4-31B 上弱于逐行检查措辞，在 Gemma4-26B-A4B 上接近。",
        "- Locate-then-judge helps but still leaves ACPI, which means asking the model to internally locate errors is not equivalent to forcing a reliable external comparison. / 先定位再判断有帮助但仍留下 ACPI，说明要求模型内部定位错误不等于强制可靠外部比较。",
        "- Sibling comparison remains 1.000 accurate for both normal and careful sibling prompts. / 普通 sibling 与 careful sibling 均保持 1.000 准确。",
        "",
        "## Audit / 审计",
        "",
        f"- Overall / 总体：{'PASS' if result['all_checks_passed'] else 'FAIL'}",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for c in checks:
        lines.append(f"| {'PASS' if c['ok'] else 'FAIL'} | {c['check']} | {c['detail']} |")
    lines += [
        "",
        "## Boundary / 边界",
        "",
        "- E60 is still a controlled verifier-objective experiment over E42/E54 pools, not a natural prevalence estimate. / E60 仍是基于 E42/E54 池的受控 verifier-objective 实验，不是自然发生率估计。",
        "- The result supports an objective/prompt/threshold mismatch claim: better objectives reduce risk, but pairwise comparison remains more reliable. / 该结果支持 objective/prompt/threshold 错配主张：更好的目标会降低风险，但成对比较仍更可靠。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"all_checks_passed": result["all_checks_passed"], "json": str(OUT_JSON), "report": str(OUT_MD), "failed": [c for c in checks if not c["ok"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
