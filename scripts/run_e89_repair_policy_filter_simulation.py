#!/usr/bin/env python3
"""E89 repair-policy-aware filter simulation.

Combines existing audited E71/E81/E86/E87/E88 outputs. It separates strict invalid,
repaired ACPI, and unrepaired ACPI retention, and contrasts outcome-only,
strict pointwise, repair-aware pointwise, raw sibling, label-free sibling, and
hidden/readout/manual-policy diagnostic filters.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
P0 = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it", "glm47_flash_candidate"]
OUT_DIR = PROJECT / "results/E89_repair_policy_filter_simulation"
OUT_JSON = OUT_DIR / "e89_repair_policy_filter_simulation.json"
OUT_MD = PROJECT / "reports/E89_REPAIR_POLICY_FILTER_SIMULATION_20260429.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def maybe_json(path: Path) -> Any | None:
    return load_json(path) if path.exists() else None


def rate(n: int, d: int) -> float | None:
    return n / d if d else None


def fmt(x: float | None) -> str:
    return "NA" if x is None else f"{x:.3f}"


def add_record(records: list[dict[str, Any]], *, experiment: str, model: str, pool: str, filter_name: str, trace_class: str, rows: list[dict[str, Any]], accept_key: str) -> None:
    accepted = [r for r in rows if bool(r[accept_key])]
    records.append({
        "experiment": experiment,
        "model": model,
        "pool": pool,
        "filter": filter_name,
        "trace_class": trace_class,
        "n_total": len(rows),
        "n_accepted": len(accepted),
        "retention_rate": rate(len(accepted), len(rows)),
    })


def collect_e71(records: list[dict[str, Any]]) -> None:
    for model in P0:
        p = PROJECT / "results/E71_repair_objective" / f"{model}_e71_repair_objective_chat.json"
        if not p.exists():
            continue
        data = load_json(p)
        rows = data["rows"]
        for dataset in sorted({r["dataset"] for r in rows}):
            ds_rows = [r for r in rows if r["dataset"] == dataset]
            for cls in sorted({r["trace_class"] for r in ds_rows}):
                cls_base = [r for r in ds_rows if r["trace_class"] == cls and r["objective"] == "strict_process"]
                add_record(records, experiment="E71", model=model, pool=dataset, filter_name="outcome_only_final_correct", trace_class=cls, rows=[{**r, "accept": True} for r in cls_base], accept_key="accept")
                for obj in ["strict_process", "repair_aware", "final_surviving_proof"]:
                    obj_rows = [r for r in ds_rows if r["trace_class"] == cls and r["objective"] == obj]
                    add_record(records, experiment="E71", model=model, pool=dataset, filter_name=f"pointwise_{obj}", trace_class=cls, rows=obj_rows, accept_key="pred_process_valid")


def collect_e81(records: list[dict[str, Any]]) -> None:
    for model in P0:
        p = PROJECT / "results/E81_label_free_sibling_allp0" / f"{model}_e79_label_free_sibling_chat.json"
        if not p.exists():
            continue
        data = load_json(p)
        for fmt_name in ["AB", "one_two", "first_second", "trace1_trace2", "label_free_two_pass"]:
            rows = [r for r in data["rows"] if r["format"] == fmt_name]
            if not rows:
                continue
            accepted_bad = [r for r in rows if not r["correct"]]
            records.append({
                "experiment": "E81",
                "model": model,
                "pool": "E61_language_grid_pair_selection",
                "filter": f"sibling_{fmt_name}",
                "trace_class": "controlled_invalid_pair_selected_by_mistake",
                "n_total": len(rows),
                "n_accepted": len(accepted_bad),
                "retention_rate": rate(len(accepted_bad), len(rows)),
                "selection_accuracy": rate(len(rows) - len(accepted_bad), len(rows)),
            })


def collect_e86(records: list[dict[str, Any]]) -> None:
    for model in P0:
        p = PROJECT / "results/E86_algebra_equivalence_adversarial" / f"{model}_e86_algebra_equivalence_chat.json"
        if not p.exists():
            continue
        data = load_json(p)
        invalid = [r for r in data["pointwise_rows"] if not r["gold_process_valid"]]
        valid = [r for r in data["pointwise_rows"] if r["gold_process_valid"]]
        add_record(records, experiment="E86", model=model, pool="algebra_equivalence", filter_name="outcome_only_final_correct", trace_class="adversarial_algebra_acpi", rows=[{**r, "accept": True} for r in invalid], accept_key="accept")
        add_record(records, experiment="E86", model=model, pool="algebra_equivalence", filter_name="pointwise_strict_process", trace_class="adversarial_algebra_acpi", rows=invalid, accept_key="pred_process_valid")
        add_record(records, experiment="E86", model=model, pool="algebra_equivalence", filter_name="pointwise_strict_process", trace_class="valid", rows=valid, accept_key="pred_process_valid")
        for key, filt in [("sibling_rows", "sibling_AB"), ("label_free_rows", "sibling_label_free_two_pass")]:
            rows = data[key]
            bad = [r for r in rows if not r["correct"]]
            records.append({"experiment": "E86", "model": model, "pool": "algebra_equivalence_pair_selection", "filter": filt, "trace_class": "adversarial_algebra_pair_selected_by_mistake", "n_total": len(rows), "n_accepted": len(bad), "retention_rate": rate(len(bad), len(rows)), "selection_accuracy": rate(len(rows) - len(bad), len(rows))})


def collect_e87(records: list[dict[str, Any]]) -> None:
    p = PROJECT / "results/E87_glm_readout_intervention/glm47_flash_candidate_e87_readout_intervention.json"
    data = maybe_json(p)
    if not data:
        return
    for s in data["summary"]:
        if s.get("slice_type") is not None:
            continue
        acc = s["accuracy"]
        records.append({
            "experiment": "E87",
            "model": "glm47_flash_candidate",
            "pool": "E61_language_grid_pair_selection",
            "filter": s["decision_rule"],
            "trace_class": "controlled_invalid_pair_selected_by_mistake",
            "n_total": s["n"],
            "n_accepted": None if acc is None else int(round((1 - acc) * s["n"])),
            "retention_rate": None if acc is None else 1 - acc,
            "selection_accuracy": acc,
        })


def collect_e88(records: list[dict[str, Any]]) -> None:
    p = PROJECT / "data/processed/e88_answer_first_manual_audit_20260429.jsonl"
    if not p.exists():
        return
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    for model in sorted({r["model_key"] for r in rows}):
        model_rows = [r for r in rows if r["model_key"] == model]
        classes = {
            "strict_valid": [r for r in model_rows if r["manual_process_valid_strict"]],
            "repaired_acpi": [r for r in model_rows if r["manual_acpi_strict"] and not r["manual_acpi_unrepaired"]],
            "unrepaired_acpi": [r for r in model_rows if r["manual_acpi_unrepaired"]],
        }
        for cls, cls_rows in classes.items():
            if not cls_rows:
                continue
            add_record(records, experiment="E88", model=model, pool="answer_first_no_gold_natural_final_correct", filter_name="outcome_only_final_correct", trace_class=cls, rows=[{**r, "accept": True} for r in cls_rows], accept_key="accept")
            add_record(records, experiment="E88", model=model, pool="answer_first_no_gold_natural_final_correct", filter_name="manual_strict_process_filter", trace_class=cls, rows=cls_rows, accept_key="manual_process_valid_strict")
            add_record(records, experiment="E88", model=model, pool="answer_first_no_gold_natural_final_correct", filter_name="manual_repair_aware_filter", trace_class=cls, rows=cls_rows, accept_key="manual_process_valid_repaired")


def summarize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        groups[(r["experiment"], r["pool"], r["filter"], r["trace_class"])].append(r)
    out = []
    for (exp, pool, filt, cls), vals in sorted(groups.items()):
        rates = [v["retention_rate"] for v in vals if v.get("retention_rate") is not None]
        out.append({
            "experiment": exp,
            "pool": pool,
            "filter": filt,
            "trace_class": cls,
            "models": [v["model"] for v in vals],
            "mean_retention_rate": mean(rates) if rates else None,
            "total_n": sum(v["n_total"] for v in vals),
            "total_accepted": sum(v["n_accepted"] for v in vals if isinstance(v.get("n_accepted"), int)),
        })
    return out


def audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    checks = []
    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
    add("has E71 repair-policy records", any(r["experiment"] == "E71" for r in records), "E71 rows provide strict/repaired/unrepaired trace classes")
    add("has E81 sibling records", any(r["experiment"] == "E81" for r in records), "E81 rows provide raw and label-free sibling selection")
    add("has E88 natural manual audit records", any(r["experiment"] == "E88" for r in records), "E88 rows provide answer-first/no-gold natural hard-task repaired/unrepaired labels")
    add("no new model inference", True, "E89 is a post-hoc aggregation over saved official outputs")
    add("retention rates bounded", all(r.get("retention_rate") is None or 0 <= r["retention_rate"] <= 1 for r in records), "all rates in [0,1]")
    return {"all_checks_passed": all(c["ok"] for c in checks), "checks": checks}


def write_report(result: dict[str, Any]) -> None:
    lines = [
        "# E89 Repair-Policy Filter Simulation / 修复策略感知筛选模拟（2026-04-29）",
        "",
        f"- JSON: `{OUT_JSON.relative_to(PROJECT)}`",
        "- Scope / 范围：不跑新模型；汇总 E71/E81/E86/E87/E88 已保存结果。",
        "- Plain language / 说人话：同一条 trace 是否算坏，取决于评审口径。如果口径是“任何可见错步都不允许”，修复过的草稿也算 strict invalid；如果口径是“最后保留下来的证明是否有效”，显式修复可以被接受。因此我们必须分开报告 repaired ACPI 和 unrepaired ACPI。",
        "",
        "## Main Retention Table / 主要保留率表",
        "",
        "| experiment | pool | filter | trace class | mean retention | total n | total accepted | models |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    key_rows = [r for r in result["summary"] if r["trace_class"] in {"repaired_acpi", "unrepaired_acpi", "no_clear_repair_invalid", "repair_marker_invalid", "adversarial_algebra_acpi", "adversarial_algebra_pair_selected_by_mistake", "controlled_invalid_pair_selected_by_mistake"}]
    for r in key_rows:
        lines.append(f"| {r['experiment']} | {r['pool']} | {r['filter']} | {r['trace_class']} | {fmt(r['mean_retention_rate'])} | {r['total_n']} | {r['total_accepted']} | {', '.join(r['models'])} |")
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- Outcome-only is intentionally permissive: in controlled final-correct pools it retains all ACPI traces. / 只看答案一定最宽松：受控 final-correct 池里 ACPI 会全被保留。",
        "- Strict pointwise should reject both repaired and unrepaired visible wrong steps, but E71/E86 show it can still retain invalid traces depending on model/objective. / strict 单点口径应该拒绝修复前错步和未修复错步，但 E71/E86 显示不同模型仍会漏过。",
        "- Repair-aware/final-surviving objectives are not 'wrong'; they answer a different scientific question: whether the final retained proof is valid. / repair-aware 或 final-surviving 不是错，而是在回答另一个问题：最终保留下来的证明是否有效。",
        "- Sibling and label-free filters are pair-selection diagnostics, not single-trace production filters; their accepted-ACPI rate means selecting the bad sibling by mistake. / sibling/label-free 是成对诊断，不是单条生产筛选器；accepted-ACPI 指错选坏 sibling 的概率。",
        "",
        "## Audit / 审计",
        "",
        f"- Overall / 总体：{'PASS' if result['audit']['all_checks_passed'] else 'FAIL'}",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for c in result["audit"]["checks"]:
        lines.append(f"| {'PASS' if c['ok'] else 'FAIL'} | {c['check']} | {c['detail']} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    records: list[dict[str, Any]] = []
    collect_e71(records)
    collect_e81(records)
    collect_e86(records)
    collect_e87(records)
    collect_e88(records)
    result = {
        "experiment": "E89_repair_policy_filter_simulation",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "p0_models": P0,
        "records": records,
        "summary": summarize(records),
        "audit": audit(records),
        "scope_note_zh": "E89 是事后筛选器模拟，不新增模型推理；重点是把 strict/repaired/unrepaired 口径分开，避免把修复草稿与未修复错误混为一谈。",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(result)
    print(json.dumps({"wrote": str(OUT_JSON), "report": str(OUT_MD), "audit": result["audit"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
