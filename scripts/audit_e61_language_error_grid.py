#!/usr/bin/env python3
"""Audit and summarize E61 language-route x error-taxonomy results."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

PROJECT = Path(__file__).resolve().parents[1]
P0 = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
DATA = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
PAIRS = PROJECT / "configs/e61_language_error_grid_pairs.yaml"
RESULT_DIR = PROJECT / "results/E61_language_error_grid"
OUT_JSON = PROJECT / "reports/E61_LANGUAGE_ERROR_GRID_AUDIT_20260429.json"
OUT_MD = PROJECT / "reports/E61_LANGUAGE_ERROR_GRID_20260429.md"
POINTWISE = ["plain_yes_no", "careful_yes_no", "answer_blind_yes_no", "locate_then_judge_yes_no"]
CONTRASTIVE = ["sibling_comparison", "careful_sibling_comparison"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def result_path(model: str) -> Path:
    return RESULT_DIR / f"{model}_e61_language_error_grid_chat.json"


def slice_row(data: dict[str, Any], objective: str, slice_type: str = "all", slice_name: str = "all") -> dict[str, Any]:
    for row in data.get("summary", []):
        if row["objective"] == objective and row["slice_type"] == slice_type and row["slice"] == slice_name:
            return row
    raise KeyError((objective, slice_type, slice_name))


def fmt(x: float | None) -> str:
    return "NA" if x is None else f"{x:.3f}"


def prompt_source_clean() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    src = (PROJECT / "scripts/run_e61_language_error_grid.py").read_text(encoding="utf-8")
    prompt_bodies = re.findall(r"def (?:pointwise_prompt|contrastive_prompt).*?(?=\n\ndef |\n\nclass |\n\ndef main)", src, flags=re.S)
    forbidden = [
        "support_span",
        "error_span",
        "manual_correction",
        "manual_process_valid",
        "known_error_span",
        "gold_label",
    ]
    for name in forbidden:
        ok = all(name not in body for body in prompt_bodies)
        add_check(checks, f"E61 prompt source does not insert {name}", ok, name)
    return checks


def summarize_existing(data_by_model: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    objective_table: list[dict[str, Any]] = []
    route_table: list[dict[str, Any]] = []
    family_table: list[dict[str, Any]] = []
    route_family_table: list[dict[str, Any]] = []
    for model, data in data_by_model.items():
        for obj in POINTWISE + CONTRASTIVE:
            s = slice_row(data, obj)
            row = {"model": model, "objective": obj, "objective_type": s["objective_type"], "n": s["n"], "accuracy": s["accuracy"]}
            if s["objective_type"] == "pointwise":
                row.update({"acpi_accept_rate": s["acpi_accept_rate"], "valid_accept_rate": s["valid_accept_rate"], "yes_rate": s["yes_rate"], "mean_margin": s["mean_margin"]})
            else:
                row.update({"sibling_error_rate": 1 - s["accuracy"], "pred_A_rate": s["pred_A_rate"], "mean_target_margin": s["mean_target_margin"]})
            objective_table.append(row)
        for obj in ["plain_yes_no", "careful_yes_no", "locate_then_judge_yes_no", "sibling_comparison"]:
            for s in data.get("summary", []):
                if s["objective"] != obj:
                    continue
                if s["slice_type"] == "route_id":
                    route_table.append({"model": model, **s})
                elif s["slice_type"] == "family":
                    family_table.append({"model": model, **s})
                elif s["slice_type"] == "route_family":
                    route_family_table.append({"model": model, **s})
    return objective_table, route_table, family_table, route_family_table


def collect_sibling_errors(data_by_model: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for model, data in data_by_model.items():
        for row in data.get("rows", []):
            if row.get("objective_type") != "contrastive" or row.get("correct"):
                continue
            errors.append(
                {
                    "model": model,
                    "objective": row["objective"],
                    "task_id": row["task_id"],
                    "family": row.get("family"),
                    "route_id": row.get("route_id"),
                    "order": row.get("order"),
                    "target": row.get("target"),
                    "pred": row.get("pred"),
                    "margin_target_minus_other": row.get("margin_target_minus_other"),
                }
            )
    return errors


def mean_by_objective(objective_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for obj in POINTWISE + CONTRASTIVE:
        vals = [r for r in objective_table if r["objective"] == obj]
        if not vals:
            continue
        row = {"objective": obj, "objective_type": vals[0]["objective_type"], "models": [v["model"] for v in vals], "mean_accuracy": mean(v["accuracy"] for v in vals)}
        if vals[0]["objective_type"] == "pointwise":
            row.update({"mean_acpi_accept_rate": mean(v["acpi_accept_rate"] for v in vals), "mean_valid_accept_rate": mean(v["valid_accept_rate"] for v in vals), "mean_yes_rate": mean(v["yes_rate"] for v in vals)})
        else:
            row.update({"mean_sibling_error_rate": mean(v["sibling_error_rate"] for v in vals), "mean_target_margin": mean(v["mean_target_margin"] for v in vals)})
        out.append(row)
    return out


def aggregate_slice(rows: list[dict[str, Any]], objective: str, slice_type: str, metric: str) -> list[dict[str, Any]]:
    groups: dict[str, list[float]] = defaultdict(list)
    ns: dict[str, int] = defaultdict(int)
    for r in rows:
        if r["objective"] == objective and r["slice_type"] == slice_type and r.get(metric) is not None:
            groups[r["slice"]].append(float(r[metric]))
            ns[r["slice"]] += int(r["n"])
    return [{"slice": k, "mean": mean(v), "models": len(v), "total_scored_rows": ns[k]} for k, v in sorted(groups.items())]


def main() -> None:
    checks: list[dict[str, Any]] = []
    rows = read_jsonl(DATA)
    pairs_doc = read_yaml(PAIRS)
    pairs = pairs_doc["pairs"]
    by_idx = {int(r["audit_idx"]): r for r in rows}
    add_check(checks, "E61 data row count", len(rows) == 96, f"rows={len(rows)}")
    add_check(checks, "E61 pair count", len(pairs) == 48, f"pairs={len(pairs)}")
    add_check(checks, "E61 route count", len({r.get("route_id") for r in rows}) == 6, str(sorted({r.get("route_id") for r in rows})))
    add_check(checks, "E61 family count", len({r.get("family") for r in rows}) == 8, str(sorted({r.get("family") for r in rows})))
    flags = ["gold_label_in_prompt", "known_error_span_in_prompt", "known_error_span_annotation_in_prompt", "manual_correction_in_prompt"]
    for flag in flags:
        bad = [r["audit_idx"] for r in rows if r.get(flag)]
        add_check(checks, f"E61 metadata flag false: {flag}", not bad, f"bad={bad[:10]} count={len(bad)}")
    pair_ok = True
    pair_details = []
    for p in pairs:
        valid = by_idx.get(int(p["valid_idx"]))
        bad = by_idx.get(int(p["bad_idx"]))
        ok = bool(valid and bad and valid["task_id"] == bad["task_id"] == p["task_id"] and valid["problem"] == bad["problem"] == p["problem"] and valid["manual_process_valid"] is True and bad["manual_process_valid"] is False and valid["manual_final_correct"] is True and bad["manual_final_correct"] is True)
        if not ok:
            pair_ok = False
            pair_details.append(p["id"])
    add_check(checks, "E61 pair valid/bad integrity", pair_ok, f"bad_pairs={pair_details[:10]} count={len(pair_details)}")
    checks.extend(prompt_source_clean())

    data_by_model: dict[str, dict[str, Any]] = {}
    for model in P0:
        path = result_path(model)
        add_check(checks, f"E61 result exists for {model}", path.exists(), str(path.relative_to(PROJECT)))
        if not path.exists():
            continue
        data = read_json(path)
        data_by_model[model] = data
        result_rows = data.get("rows", [])
        add_check(checks, f"{model} row count", len(result_rows) == 576, f"rows={len(result_rows)}")
        add_check(checks, f"{model} chat template used", bool(data.get("used_chat_template")), str(data.get("used_chat_template")))
        add_check(checks, f"{model} prompt format", data.get("prompt_format") == "official_if_chat", str(data.get("prompt_format")))
        add_check(checks, f"{model} leakage audit zero", all(v == 0 for k, v in data.get("leakage_audit", {}).items() if k.endswith("_rows")), str(data.get("leakage_audit")))
        counts = Counter((r["objective_type"], r["objective"]) for r in result_rows)
        expected = {("pointwise", obj): 96 for obj in POINTWISE} | {("contrastive", obj): 96 for obj in CONTRASTIVE}
        add_check(checks, f"{model} objective counts", counts == expected, str(dict(counts)))
        orders = Counter((r["objective"], r.get("order")) for r in result_rows if r["objective_type"] == "contrastive")
        order_ok = all(orders[(obj, "bad_A")] == 48 and orders[(obj, "bad_B")] == 48 for obj in CONTRASTIVE)
        add_check(checks, f"{model} sibling order balance", order_ok, str(dict(orders)))

    objective_table, route_table, family_table, route_family_table = summarize_existing(data_by_model)
    mean_obj = mean_by_objective(objective_table)
    sibling_errors = collect_sibling_errors(data_by_model)
    aggregate = {
        "plain_by_route_acpi_accept": aggregate_slice(route_table, "plain_yes_no", "route_id", "acpi_accept_rate"),
        "careful_by_route_acpi_accept": aggregate_slice(route_table, "careful_yes_no", "route_id", "acpi_accept_rate"),
        "locate_by_route_acpi_accept": aggregate_slice(route_table, "locate_then_judge_yes_no", "route_id", "acpi_accept_rate"),
        "sibling_by_route_accuracy": aggregate_slice(route_table, "sibling_comparison", "route_id", "accuracy"),
        "plain_by_family_acpi_accept": aggregate_slice(family_table, "plain_yes_no", "family", "acpi_accept_rate"),
        "careful_by_family_acpi_accept": aggregate_slice(family_table, "careful_yes_no", "family", "acpi_accept_rate"),
        "sibling_by_family_accuracy": aggregate_slice(family_table, "sibling_comparison", "family", "accuracy"),
    }
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "all_checks_passed": all(c["ok"] for c in checks),
        "completed_models": sorted(data_by_model),
        "pending_models": [m for m in P0 if m not in data_by_model],
        "checks": checks,
        "objective_table": objective_table,
        "mean_by_objective": mean_obj,
        "route_table": route_table,
        "family_table": family_table,
        "route_family_table": route_family_table,
        "sibling_errors": sibling_errors,
        "aggregate": aggregate,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# E61 Language-Route × Error-Taxonomy Grid / E61 语言路径 × 错误类型网格（2026-04-29）",
        "",
        f"- JSON audit / 机器可读审计：`{OUT_JSON.relative_to(PROJECT)}`",
        f"- Completed models / 已完成模型：{', '.join(sorted(data_by_model)) or 'none'}",
        f"- Pending models / 待完成模型：{', '.join(result['pending_models']) or 'none'}",
        "- Scope / 范围：6 条语言路径 × 8 类错误，每个 cell 一条 valid-correct 和一条 invalid-correct trace；不把标签、span 或人工修正写入 prompt。",
        "- Plain language / 说人话：这一步回答“我们是不是只是在 discount 或少数英文短题上看到现象”。",
        "",
        "## Mean Across Completed P0 / 已完成 P0 均值",
        "",
        "| objective | type | mean accuracy | mean ACPI accept / sibling error | mean valid accept | note |",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in mean_obj:
        if r["objective_type"] == "pointwise":
            lines.append(f"| `{r['objective']}` | pointwise | {fmt(r['mean_accuracy'])} | {fmt(r['mean_acpi_accept_rate'])} | {fmt(r['mean_valid_accept_rate'])} | single-trace Yes/No / 单条 trace 判断 |")
        else:
            lines.append(f"| `{r['objective']}` | contrastive | {fmt(r['mean_accuracy'])} | {fmt(r['mean_sibling_error_rate'])} | NA | pairwise sibling / 成对判断 |")
    if not mean_obj:
        lines.append("| pending | pending | NA | NA | NA | results not finished yet / 结果尚未完成 |")

    lines += ["", "## By Model / 按模型", "", "| model | objective | accuracy | ACPI accept / sibling error | valid accept | yes/pred-A rate |", "|---|---|---:|---:|---:|---:|"]
    for r in objective_table:
        if r["objective_type"] == "pointwise":
            lines.append(f"| `{r['model']}` | `{r['objective']}` | {fmt(r['accuracy'])} | {fmt(r['acpi_accept_rate'])} | {fmt(r['valid_accept_rate'])} | {fmt(r['yes_rate'])} |")
        else:
            lines.append(f"| `{r['model']}` | `{r['objective']}` | {fmt(r['accuracy'])} | {fmt(r['sibling_error_rate'])} | NA | {fmt(r['pred_A_rate'])} |")

    def add_agg(title: str, key: str) -> None:
        lines.extend(["", f"## {title}", "", "| slice | mean | models | total scored rows |", "|---|---:|---:|---:|"])
        vals = aggregate[key]
        if not vals:
            lines.append("| pending | NA | 0 | 0 |")
        for v in vals:
            lines.append(f"| `{v['slice']}` | {fmt(v['mean'])} | {v['models']} | {v['total_scored_rows']} |")

    add_agg("Plain Yes/No ACPI Accept by Route / 普通 Yes/No 按语言路径", "plain_by_route_acpi_accept")
    add_agg("Careful Yes/No ACPI Accept by Route / 仔细 Yes/No 按语言路径", "careful_by_route_acpi_accept")
    add_agg("Sibling Accuracy by Route / Sibling 按语言路径", "sibling_by_route_accuracy")
    add_agg("Plain Yes/No ACPI Accept by Family / 普通 Yes/No 按错误类型", "plain_by_family_acpi_accept")
    add_agg("Careful Yes/No ACPI Accept by Family / 仔细 Yes/No 按错误类型", "careful_by_family_acpi_accept")
    add_agg("Sibling Accuracy by Family / Sibling 按错误类型", "sibling_by_family_accuracy")

    def metric_for(objective: str, metric: str) -> float | None:
        for row in mean_obj:
            if row["objective"] == objective:
                return row.get(metric)
        return None

    def slice_list(vals: list[dict[str, Any]], n: int = 3) -> str:
        return ", ".join(f"{x['slice']}={fmt(x['mean'])}" for x in vals[:n]) or "NA"

    top_plain_routes = sorted(aggregate["plain_by_route_acpi_accept"], key=lambda x: x["mean"], reverse=True)
    top_plain_families = sorted(aggregate["plain_by_family_acpi_accept"], key=lambda x: x["mean"], reverse=True)
    top_careful_families = sorted(aggregate["careful_by_family_acpi_accept"], key=lambda x: x["mean"], reverse=True)

    lines += [
        "",
        "## Interpretation / 解释",
        "",
        f"- Main result: plain pointwise ACPI accept is {fmt(metric_for('plain_yes_no', 'mean_acpi_accept_rate'))} across P0; careful/answer-blind/locate reduce it to {fmt(metric_for('careful_yes_no', 'mean_acpi_accept_rate'))}/{fmt(metric_for('answer_blind_yes_no', 'mean_acpi_accept_rate'))}/{fmt(metric_for('locate_then_judge_yes_no', 'mean_acpi_accept_rate'))}. / 主结果：P0 普通 pointwise ACPI 接受为 {fmt(metric_for('plain_yes_no', 'mean_acpi_accept_rate'))}；careful/answer-blind/locate 分别降到 {fmt(metric_for('careful_yes_no', 'mean_acpi_accept_rate'))}/{fmt(metric_for('answer_blind_yes_no', 'mean_acpi_accept_rate'))}/{fmt(metric_for('locate_then_judge_yes_no', 'mean_acpi_accept_rate'))}。",
        f"- Sibling remains much stronger but is no longer literally perfect in the broader grid: normal/careful sibling accuracy is {fmt(metric_for('sibling_comparison', 'mean_accuracy'))}/{fmt(metric_for('careful_sibling_comparison', 'mean_accuracy'))}. / sibling 仍明显更强，但在更广 E61 网格中不再字面完美：普通/仔细 sibling 准确率为 {fmt(metric_for('sibling_comparison', 'mean_accuracy'))}/{fmt(metric_for('careful_sibling_comparison', 'mean_accuracy'))}。",
        "- The sibling errors come from `gemma4_26b_a4b_it` and concentrate in `romanized_zh`; this marks transliteration as a harder route, not a solved corner case. / sibling 错误来自 `gemma4_26b_a4b_it`，且集中在 `romanized_zh`；这说明拼音/转写路径是更难路线，不是已解决的边角情况。",
        f"- Highest plain pointwise route risks: {slice_list(top_plain_routes, 2)}. / 普通 pointwise 风险最高的语言路径如前。",
        f"- Highest plain pointwise family risks: {slice_list(top_plain_families, 3)}; careful still leaves risk on {slice_list(top_careful_families, 3)}. / 普通 pointwise 风险最高的错误类型如前；careful 后仍留下这些高风险类型。",
        "- Scientific update: E61 strengthens generalization beyond discount-like examples and sharpens the boundary: contrastive comparison is robust but not an oracle, especially under transliterated-language traces. / 科学更新：E61 加强了‘不是 discount 个例’的泛化证据，同时收紧边界：对比判断很稳，但不是 oracle，尤其在转写语言 trace 上。",
        "",
    ]
    if sibling_errors:
        lines += [
            "### Sibling Errors / sibling 错误明细",
            "",
            "| model | objective | task | family | route | order | target | pred | margin |",
            "|---|---|---|---|---|---|---|---|---:|",
        ]
        for e in sibling_errors:
            lines.append(
                f"| `{e['model']}` | `{e['objective']}` | `{e['task_id']}` | `{e['family']}` | `{e['route_id']}` | `{e['order']}` | `{e['target']}` | `{e['pred']}` | {fmt(e.get('margin_target_minus_other'))} |"
            )
        lines.append("")

    lines += [
        "## Audit / 审计",
        "",
        f"- Overall / 总体：{'PASS' if result['all_checks_passed'] else 'PENDING_OR_FAIL'}",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for c in checks:
        lines.append(f"| {'PASS' if c['ok'] else 'FAIL'} | {c['check']} | {c['detail']} |")
    lines += [
        "",
        "## Boundary / 边界",
        "",
        "- E61 is a controlled trace-selection generalization experiment, not a natural prevalence estimate. / E61 是受控 trace-selection 泛化实验，不是自然发生率估计。",
        "- Error spans and support spans exist in the data file for post-hoc audit, but the runner does not insert them into prompts. / 数据文件中有 error/support span 供事后审计，但 runner 不会把它们插入 prompt。",
        "- Sibling comparison is a contrastive diagnostic; mechanism interventions remain separate oracle diagnostics. / sibling 是对比诊断；机制干预仍是单独的 oracle 诊断。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}; all_checks_passed={result['all_checks_passed']}; completed={sorted(data_by_model)}")


if __name__ == "__main__":
    main()
