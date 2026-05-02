#!/usr/bin/env python3
"""E58 filter simulation over audited official results.

This script runs no model inference. It asks a post-hoc question:
if a trace-selection or synthetic-data pipeline used different filters, how
many answer-correct/process-invalid traces would remain in the accepted set?
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
P0 = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
OUT_DIR = PROJECT / "results/E58_distillation_filter_simulation"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "e58_filter_simulation_20260428.json"
OUT_MD = PROJECT / "reports/E58_DISTILLATION_FILTER_SIMULATION_20260428.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pct(num: int, den: int) -> float | None:
    return (num / den) if den else None


def fmt_rate(x: float | None) -> str:
    if x is None:
        return "NA"
    return f"{x:.3f}"


def get_model_file(exp: str, model: str) -> Path:
    matches = sorted((PROJECT / "results" / exp).glob(f"{model}_*.json"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one active file for {exp}/{model}, got {matches}")
    return matches[0]


def row_filter_metrics(
    *,
    experiment: str,
    model: str,
    pool: str,
    filter_name: str,
    rows: list[dict[str, Any]],
    accept_key: str,
    valid_key: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    accepted = [r for r in rows if bool(r[accept_key])]
    valid_rows = [r for r in rows if bool(r[valid_key])]
    invalid_rows = [r for r in rows if not bool(r[valid_key])]
    accepted_valid = [r for r in accepted if bool(r[valid_key])]
    accepted_invalid = [r for r in accepted if not bool(r[valid_key])]
    out: dict[str, Any] = {
        "experiment": experiment,
        "model": model,
        "pool": pool,
        "filter": filter_name,
        "unit": "trace_rows",
        "n_total": len(rows),
        "n_valid_total": len(valid_rows),
        "n_invalid_total": len(invalid_rows),
        "n_accepted": len(accepted),
        "n_accepted_valid": len(accepted_valid),
        "n_accepted_acpi": len(accepted_invalid),
        "valid_retention": pct(len(accepted_valid), len(valid_rows)),
        "invalid_retention": pct(len(accepted_invalid), len(invalid_rows)),
        "accepted_acpi_rate": pct(len(accepted_invalid), len(accepted)),
    }
    if extra:
        out.update(extra)
    return out


def sibling_metrics(*, experiment: str, model: str, pool: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    # A sibling comparison is a selection event: it sees one valid and one invalid
    # trace for the same problem/final answer and keeps the one it judges valid.
    correct = [r for r in rows if bool(r["correct"])]
    incorrect = [r for r in rows if not bool(r["correct"])]
    return {
        "experiment": experiment,
        "model": model,
        "pool": pool,
        "filter": "sibling_comparison",
        "unit": "pair_selection_events",
        "n_total": len(rows),
        "n_valid_total": len(rows),
        "n_invalid_total": len(rows),
        "n_accepted": len(rows),
        "n_accepted_valid": len(correct),
        "n_accepted_acpi": len(incorrect),
        "valid_retention": pct(len(correct), len(rows)),
        "invalid_retention": pct(len(incorrect), len(rows)),
        "accepted_acpi_rate": pct(len(incorrect), len(rows)),
        "selection_accuracy": pct(len(correct), len(rows)),
    }


def summarize_by_filter(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        grouped[(r["experiment"], r["pool"], r["filter"])].append(r)
    out = []
    for (exp, pool, filt), vals in sorted(grouped.items()):
        acpi_rates = [v["accepted_acpi_rate"] for v in vals if v["accepted_acpi_rate"] is not None]
        valid_rates = [v["valid_retention"] for v in vals if v["valid_retention"] is not None]
        invalid_rates = [v["invalid_retention"] for v in vals if v["invalid_retention"] is not None]
        out.append(
            {
                "experiment": exp,
                "pool": pool,
                "filter": filt,
                "models": [v["model"] for v in vals],
                "mean_accepted_acpi_rate": mean(acpi_rates) if acpi_rates else None,
                "mean_valid_retention": mean(valid_rates) if valid_rates else None,
                "mean_invalid_retention": mean(invalid_rates) if invalid_rates else None,
                "total_accepted": sum(v["n_accepted"] for v in vals),
                "total_accepted_acpi": sum(v["n_accepted_acpi"] for v in vals),
            }
        )
    return out


def collect_e42_e54() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for exp, pool, exp_dir in [
        ("E42", "controlled_12_family", "E42_official_template_parity"),
        ("E54", "parameterized_18_family", "E54_parameterized_no_leak_generalization"),
    ]:
        for model in P0:
            data = load_json(get_model_file(exp_dir, model))
            abs_rows = [r for r in data["rows"] if r["objective"] == "absolute_process"]
            con_rows = [r for r in data["rows"] if r["objective"] == "contrastive"]
            normalized = [
                {
                    **r,
                    "is_valid": bool(r["target"]),
                    "outcome_accept": True,  # all controlled rows have the same correct final answer by construction
                    "absolute_accept": bool(r["pred"]),
                }
                for r in abs_rows
            ]
            records.append(
                row_filter_metrics(
                    experiment=exp,
                    model=model,
                    pool=pool,
                    filter_name="outcome_only_final_correct",
                    rows=normalized,
                    accept_key="outcome_accept",
                    valid_key="is_valid",
                    extra={"scope_note": "All controlled valid/invalid traces are final-answer-correct."},
                )
            )
            records.append(
                row_filter_metrics(
                    experiment=exp,
                    model=model,
                    pool=pool,
                    filter_name="absolute_yes_no_process",
                    rows=normalized,
                    accept_key="absolute_accept",
                    valid_key="is_valid",
                )
            )
            records.append(sibling_metrics(experiment=exp, model=model, pool=pool, rows=con_rows))
    return records


def collect_e53() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for model in P0:
        data = load_json(get_model_file("E53_answer_anchor_ablation", model))
        for cond in ["shown", "removed", "masked", "wrong"]:
            rows = [r for r in data["rows"] if r["e53_answer_condition"] == cond]
            normalized = [
                {
                    **r,
                    "is_valid": bool(r["target_process_valid"]),
                    "absolute_accept": bool(r["pred_process_valid"]),
                    "outcome_accept": r.get("manual_final_correct") is True,
                }
                for r in rows
            ]
            records.append(
                row_filter_metrics(
                    experiment="E53",
                    model=model,
                    pool=f"answer_anchor_{cond}",
                    filter_name="absolute_yes_no_process",
                    rows=normalized,
                    accept_key="absolute_accept",
                    valid_key="is_valid",
                )
            )
            # Outcome-only is meaningful when a visible final answer is present.
            if cond in {"shown", "wrong"}:
                records.append(
                    row_filter_metrics(
                        experiment="E53",
                        model=model,
                        pool=f"answer_anchor_{cond}",
                        filter_name="outcome_only_visible_answer",
                        rows=normalized,
                        accept_key="outcome_accept",
                        valid_key="is_valid",
                    )
                )
    return records


def collect_e56_residual_probe() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for model in P0:
        data = load_json(get_model_file("E56_component_decomposition", model))
        rows = [
            {
                **r,
                "is_valid": bool(r["gold_process_valid"]),
                "residual_probe_accept": bool(r["pred_process_valid"]),
            }
            for r in data["probe_rows"]
            if r["component"] == "residual_layer_output"
        ]
        records.append(
            row_filter_metrics(
                experiment="E56",
                model=model,
                pool="controlled_12_family_hidden_residual_loto",
                filter_name="residual_probe_loto_diagnostic",
                rows=rows,
                accept_key="residual_probe_accept",
                valid_key="is_valid",
                extra={"scope_note": "Diagnostic only: hidden-state LOTO probe, not a deployable text-only filter."},
            )
        )
    return records


def collect_e57() -> list[dict[str, Any]]:
    manual = load_jsonl(PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl")
    records: list[dict[str, Any]] = []
    for model in P0:
        rows = [r for r in manual if r["model_key"] == model]
        normalized_strict = [
            {
                **r,
                "is_valid": bool(r["manual_process_valid_strict"]),
                "outcome_accept": bool(r["manual_final_correct"]),
            }
            for r in rows
        ]
        normalized_unrepaired = [
            {
                **r,
                "is_valid": bool(r["manual_process_valid_repaired"]),
                "outcome_accept": bool(r["manual_final_correct"]),
            }
            for r in rows
        ]
        records.append(
            row_filter_metrics(
                experiment="E57",
                model=model,
                pool="p0_hard_task_final_correct_strict_label",
                filter_name="outcome_only_final_correct",
                rows=normalized_strict,
                accept_key="outcome_accept",
                valid_key="is_valid",
                extra={"label_policy": "strict: visible early wrong final/math claims count invalid"},
            )
        )
        records.append(
            row_filter_metrics(
                experiment="E57",
                model=model,
                pool="p0_hard_task_final_correct_repaired_label",
                filter_name="outcome_only_final_correct",
                rows=normalized_unrepaired,
                accept_key="outcome_accept",
                valid_key="is_valid",
                extra={"label_policy": "repaired: explicit self-correction can restore validity"},
            )
        )
    return records


def audit_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    checks = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    add("P0 record coverage", all(any(r["model"] == m for r in records) for m in P0), str(Counter(r["model"] for r in records)))
    add("E42/E54 outcome-only retains 50% ACPI by construction", all(
        abs(r["accepted_acpi_rate"] - 0.5) < 1e-9
        for r in records
        if r["experiment"] in {"E42", "E54"} and r["filter"] == "outcome_only_final_correct"
    ), "controlled pools have one valid and one invalid final-correct trace per task")
    add("Sibling filters are pair-selection events", all(
        r["unit"] == "pair_selection_events"
        for r in records
        if r["filter"] == "sibling_comparison"
    ), "sibling rows are not independent single-trace rows")
    add("E57 only uses manual final-correct rows", all(
        r["n_accepted"] == r["n_total"]
        for r in records
        if r["experiment"] == "E57"
    ), "manual audit file contains final-correct rows only")
    add("No model inference in E58", True, "E58 reads existing JSON/JSONL outputs only")
    return {"all_checks_passed": all(c["ok"] for c in checks), "checks": checks}


def write_report(result: dict[str, Any]) -> None:
    records = result["records"]
    grouped = result["summary_by_filter"]

    def rows_for(exp: str, filt: str | None = None) -> list[dict[str, Any]]:
        xs = [r for r in records if r["experiment"] == exp]
        if filt is not None:
            xs = [r for r in xs if r["filter"] == filt]
        return xs

    lines = [
        "# E58 Distillation-Filter Simulation / E58 蒸馏式筛选器模拟（2026-04-28）",
        "",
        f"- JSON / 机器可读结果：`{OUT_JSON.relative_to(PROJECT)}`",
        "- Scope / 范围：不跑新模型，只读取 E42/E53/E54/E56/E57 已审计官方结果，模拟不同筛选器会保留多少 ACPI 风险。",
        "- Plain language / 说人话：如果训练数据筛选只看“答案对不对”，它会把答案正确但过程错误的 trace 一起收进去；如果让 verifier 单独回答 Yes/No，它会少收一些坏 trace，但仍系统性漏过；如果把同题同答案的一好一坏 sibling 并排比较，坏 trace 基本暴露。",
        "",
        "## Main Filter Comparison / 主筛选器对比",
        "",
        "| experiment | pool | filter | mean ACPI in accepted | mean valid retention | mean invalid retention | accepted ACPI / accepted |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in grouped:
        lines.append(
            "| {experiment} | {pool} | {filter} | {acpi} | {valid} | {invalid} | {bad}/{acc} |".format(
                experiment=r["experiment"],
                pool=r["pool"],
                filter=r["filter"],
                acpi=fmt_rate(r["mean_accepted_acpi_rate"]),
                valid=fmt_rate(r["mean_valid_retention"]),
                invalid=fmt_rate(r["mean_invalid_retention"]),
                bad=r["total_accepted_acpi"],
                acc=r["total_accepted"],
            )
        )

    lines += [
        "",
        "## E42/E54 Controlled Pools / E42/E54 受控池",
        "",
        "- E42 has 12 same-problem/same-final-answer valid/invalid pairs; E54 expands this to 18 parameterized task families. / E42 有 12 组同题同答案的一好一坏 trace；E54 扩展到 18 个参数化任务族。",
        "- Outcome-only accepts every trace in these pools, so accepted ACPI is 0.500 by construction. This is not a result about model judgment; it is the risk of using final answer alone. / 只看最终答案会全收，因此 ACPI 比例按构造就是 0.500；这不是模型判断结果，而是答案筛选本身的风险。",
        "- Absolute Yes/No reduces but does not remove ACPI: E42 P0 invalid retention is 0.500, while E54 invalid retention is 0.500-0.667 depending on model. / absolute Yes/No 能减少但不能清除 ACPI：E42 中 P0 invalid retention 为 0.500，E54 中不同模型为 0.500-0.667。",
        "- Sibling comparison has 0.000 accepted ACPI in E42/E54 P0 runs because all pair-selection decisions are correct. / sibling comparison 在 E42/E54 的 P0 运行中 accepted ACPI 为 0，因为成对选择全对。",
        "",
        "## E53 Answer Anchor / E53 答案锚定",
        "",
        "| model | condition | outcome-only ACPI | absolute ACPI in accepted | absolute invalid retention |",
        "|---|---|---:|---:|---:|",
    ]
    e53 = rows_for("E53")
    for model in P0:
        for cond in ["shown", "removed", "masked", "wrong"]:
            pool = f"answer_anchor_{cond}"
            abs_r = next(r for r in e53 if r["model"] == model and r["pool"] == pool and r["filter"] == "absolute_yes_no_process")
            out = [r for r in e53 if r["model"] == model and r["pool"] == pool and r["filter"] == "outcome_only_visible_answer"]
            lines.append(
                f"| `{model}` | `{cond}` | {fmt_rate(out[0]['accepted_acpi_rate']) if out else 'NA'} | {fmt_rate(abs_r['accepted_acpi_rate'])} | {fmt_rate(abs_r['invalid_retention'])} |"
            )
    lines += [
        "",
        "Interpretation / 解释：正确最终答案像锚一样把 absolute verifier 往 Yes 拉；wrong-final condition 会显著压低 invalid 接受。但 removed/masked 仍有非零 invalid retention，所以不能把机制简化成“只看 final answer”。",
        "",
        "## E56 Residual Diagnostic / E56 残差诊断",
        "",
        "| model | accepted ACPI | valid retention | invalid retention | note |",
        "|---|---:|---:|---:|---|",
    ]
    for r in rows_for("E56", "residual_probe_loto_diagnostic"):
        lines.append(
            f"| `{r['model']}` | {fmt_rate(r['accepted_acpi_rate'])} | {fmt_rate(r['valid_retention'])} | {fmt_rate(r['invalid_retention'])} | LOTO hidden-state diagnostic, not deployable filter |"
        )
    lines += [
        "",
        "Interpretation / 解释：残差 probe 不是生产筛选器，因为它用到了 hidden state 和受控标签训练；但它说明 hidden state 中确实有可读出的过程有效性证据。它和 absolute 输出之间的差距，就是“证据存在但 Yes/No 决策没用好”的核心证据之一。",
        "",
        "## E57 Hard-Task Appendix / E57 困难题附录",
        "",
        "| model | label policy | accepted traces | accepted ACPI | accepted ACPI rate |",
        "|---|---|---:|---:|---:|",
    ]
    for r in rows_for("E57", "outcome_only_final_correct"):
        policy = "strict" if "strict" in r["pool"] else "repaired"
        lines.append(
            f"| `{r['model']}` | `{policy}` | {r['n_accepted']} | {r['n_accepted_acpi']} | {fmt_rate(r['accepted_acpi_rate'])} |"
        )
    lines += [
        "",
        "Interpretation / 解释：困难题 final-correct 子集里，strict ACPI 主要是“先错后修复”的 visible trace；用 repaired 标签后，未修复 ACPI 很少。E58 因此不应把 hard-task 当作高频 ACPI 证据，而应作为边界条件：困难题 ACPI 存在，但当前 P0 小样本中不高频。",
        "",
        "## Audit / 审计",
        "",
        f"- Overall / 总体：{'PASS' if result['audit']['all_checks_passed'] else 'FAIL'}",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for c in result["audit"]["checks"]:
        lines.append(f"| {'PASS' if c['ok'] else 'FAIL'} | {c['check']} | {c['detail']} |")
    lines += [
        "",
        "## Decision for Mainline / 对主线的决定",
        "",
        "- Use E58 mainly on E42/E54/E53 controlled pools, because they isolate the causal-chain risk cleanly. / E58 主证据应放在 E42/E54/E53 受控池，因为它们干净隔离了因果链风险。",
        "- Keep E57 as hard-task appendix, not prevalence headline. / E57 放在困难题附录，不作为高发生率 headline。",
        "- The safe paper statement is: outcome-only and absolute pointwise filtering can retain ACPI traces; sibling comparison suppresses them much more strongly; hidden residual diagnostics show the process signal exists even when absolute Yes/No underuses it. / 安全论文表述：只看答案和 absolute 单点筛选都会保留 ACPI；sibling comparison 明显更能压制；hidden residual 诊断显示过程信号存在，只是 absolute Yes/No 没充分使用。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    records: list[dict[str, Any]] = []
    records.extend(collect_e42_e54())
    records.extend(collect_e53())
    records.extend(collect_e56_residual_probe())
    records.extend(collect_e57())
    result = {
        "experiment": "E58_distillation_filter_simulation",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scope_note_en": "No new model inference. This post-hoc simulation compares outcome-only, absolute Yes/No, sibling comparison, and a residual LOTO diagnostic over audited official results.",
        "scope_note_zh": "不跑新模型。本实验读取已审计官方结果，事后模拟只看答案、absolute Yes/No、sibling comparison 与 residual LOTO 诊断会保留多少 ACPI。",
        "p0_models": P0,
        "records": records,
        "summary_by_filter": summarize_by_filter(records),
        "audit": audit_records(records),
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(result)
    print(json.dumps({"wrote_json": str(OUT_JSON), "wrote_report": str(OUT_MD), "audit": result["audit"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
