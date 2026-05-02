#!/usr/bin/env python3
"""Summarize E139 failure-only check-rationale audit results."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT / "results/E139_check_rationale_audit"
REPORT_MD = PROJECT / "reports/E139_CHECK_RATIONALE_AUDIT_20260430.md"
REPORT_JSON = PROJECT / "reports/E139_CHECK_RATIONALE_AUDIT_20260430.json"


def load_results() -> list[dict[str, Any]]:
    paths = sorted(RESULT_DIR.glob("*_e139_check_rationale_audit.json"))
    if not paths:
        raise FileNotFoundError(f"no E139 result files in {RESULT_DIR}")
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def pct(num: int, den: int) -> str:
    return "NA" if den == 0 else f"{num / den:.3f}"


def model_summary(d: dict[str, Any]) -> dict[str, Any]:
    rows = d["rows"]
    selected = d["selected_rows"]
    strict_yes = sum(r["parsed"]["strict_decision"] == "Yes" for r in rows)
    repair_yes = sum(r["parsed"]["repair_aware_decision"] == "Yes" for r in rows)
    wrong_step_claims = sum(not r["parsed"]["claims_no_wrong_step"] for r in rows)
    later_yes = sum(r["parsed"]["later_discarded_repaired"] == "Yes" for r in rows)
    hit_max = sum(r["generation"]["hit_max_new_tokens"] for r in rows)
    final_block = sum(r["parsed"]["final_block_found"] for r in rows)
    by_check: dict[str, dict[str, Any]] = {}
    for check_type in ["global", "local"]:
        sub = [r for r in rows if r["check_type"] == check_type]
        by_check[check_type] = {
            "n": len(sub),
            "strict_yes": sum(r["parsed"]["strict_decision"] == "Yes" for r in sub),
            "repair_yes": sum(r["parsed"]["repair_aware_decision"] == "Yes" for r in sub),
            "wrong_step_quoted": sum(not r["parsed"]["claims_no_wrong_step"] for r in sub),
        }
    return {
        "model_key": d["model_key"],
        "result_file": str((RESULT_DIR / f"{d['model_key']}_e139_check_rationale_audit.json").relative_to(PROJECT)),
        "source_e136_result": d["source_e136_result"],
        "source_data_jsonl": d["source_data_jsonl"],
        "args": d["args"],
        "selected_rows_n": len(selected),
        "selected_audit_idxs": [r["audit_idx"] for r in selected],
        "selected_family_variant": dict(Counter(f"{r['family']}::{r['variant']}" for r in selected)),
        "selected_routes": dict(Counter(r["route_id"] for r in selected)),
        "selection_reasons": dict(Counter(r["selection_reason"] for r in selected)),
        "failure_policy_counts": dict(Counter(policy for r in selected for policy in r["failure_policy_names"])),
        "jobs_n": len(rows),
        "parse_ok": sum(r["parsed"]["parse_ok"] for r in rows),
        "final_block_found": final_block,
        "hit_max": hit_max,
        "strict_yes": strict_yes,
        "strict_accept_rate": strict_yes / len(rows) if rows else None,
        "repair_aware_yes": repair_yes,
        "repair_aware_accept_rate": repair_yes / len(rows) if rows else None,
        "wrong_step_quoted": wrong_step_claims,
        "later_repaired_yes": later_yes,
        "by_check": by_check,
        "leakage_audit": d["summary"]["leakage_audit"],
        "examples": [
            {
                "audit_idx": r["audit_idx"],
                "check_type": r["check_type"],
                "route_id": r["route_id"],
                "wrong_step_quoted": r["parsed"]["wrong_step_quoted"],
                "wrong_step_problem": r["parsed"]["wrong_step_problem"],
                "later_discarded_repaired": r["parsed"]["later_discarded_repaired"],
                "strict_decision": r["parsed"]["strict_decision"],
                "repair_aware_decision": r["parsed"]["repair_aware_decision"],
                "short_reason": r["parsed"]["short_reason"],
            }
            for r in rows[:4]
        ],
    }


def render_md(summary: dict[str, Any]) -> str:
    rows = summary["models"]
    lines: list[str] = []
    lines.append("# E139 Check-Rationale Audit / E139 二次检查解释审计")
    lines.append("")
    lines.append(f"- Created / 生成时间：`{summary['created_at']}`")
    lines.append("- Scope / 范围：只审计 E136 中 `base` 或二次 `check` 未能纠错的失败样本；不混入已成功纠错样本。")
    lines.append("- Mode / 模式：`non-thinking` verifier generation only. Thinking smoke hit max-token and failed parse, so it is excluded from this failure-mechanism audit.")
    lines.append("- Prompt boundary / prompt 边界：prompt 只包含题目、可见 trace，以及 local check 的 hidden-selected 可见片段；人工标签、gold answer、error-span annotation 不进入 prompt。")
    lines.append("- Scientific question / 科学问题：E136 中 check 后仍放行，是因为模型看不见错步，还是因为看见错步后按 repair-aware 草稿口径放行？")
    lines.append("")
    lines.append("## Inputs / 输入")
    lines.append("")
    lines.append("- Source data / 源数据：`data/processed/e132_suspicious_valid_controls_20260430.jsonl`")
    lines.append("- Source policy results / 源策略结果：`results/E136_suspicious_confidence_adaptive_check/`")
    lines.append("- Runner / 运行脚本：`scripts/run_e139_check_rationale_audit.py`")
    lines.append("- Queue / 队列脚本：`scripts/launch_e139_check_rationale_audit_queue_20260430.sh`")
    lines.append("- Result dir / 结果目录：`results/E139_check_rationale_audit/`")
    lines.append("- Queue status / 队列状态：`logs/e139_check_rationale_audit_status_20260430.jsonl` ended with `all_done`.")
    lines.append("")
    lines.append("## Selected Rows / 选样")
    lines.append("")
    lines.append("E139 使用 `selection=failure_only`。一行被选中必须同时满足：人工 strict 过程标签为 invalid，并且 E136 的 base 或 global/local check 至少有一个策略仍接受它。")
    lines.append("")
    lines.append("| model | selected rows | jobs | selected audit idxs | task/variant | routes |")
    lines.append("|---|---:|---:|---|---|---|")
    for r in rows:
        fam = ", ".join(f"{k}:{v}" for k, v in sorted(r["selected_family_variant"].items()))
        routes = ", ".join(f"{k}:{v}" for k, v in sorted(r["selected_routes"].items()))
        idxs = ", ".join(str(x) for x in r["selected_audit_idxs"])
        lines.append(f"| `{r['model_key']}` | {r['selected_rows_n']} | {r['jobs_n']} | {idxs} | {fam} | {routes} |")
    lines.append("")
    lines.append("All selected rows are `percentage_base::repaired_strict_invalid`: the trace contains an explicit wrong percentage-increase statement, then later computes the final answer with the correct arithmetic. / 所有被选样本都是百分比基底任务中的 repaired strict-invalid：可见 trace 先写出明确错误的语义句，后文又用正确算法得到答案。")
    lines.append("")
    lines.append("Failure policy counts / 失败策略计数：")
    lines.append("")
    lines.append("| model | failed policy counts that caused selection |")
    lines.append("|---|---|")
    for r in rows:
        counts = ", ".join(f"`{k}`:{v}" for k, v in sorted(r["failure_policy_counts"].items()))
        lines.append(f"| `{r['model_key']}` | {counts} |")
    lines.append("")
    lines.append("## Main Results / 主要结果")
    lines.append("")
    lines.append("| model | parse ok | strict Yes | repair-aware Yes | wrong step quoted | later repaired Yes | hit max |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        n = r["jobs_n"]
        lines.append(
            f"| `{r['model_key']}` | {r['parse_ok']}/{n} | "
            f"{r['strict_yes']}/{n} ({pct(r['strict_yes'], n)}) | "
            f"{r['repair_aware_yes']}/{n} ({pct(r['repair_aware_yes'], n)}) | "
            f"{r['wrong_step_quoted']}/{n} | {r['later_repaired_yes']}/{n} | {r['hit_max']}/{n} |"
        )
    lines.append("")
    lines.append("| model | global strict Yes | global repair-aware Yes | local strict Yes | local repair-aware Yes |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in rows:
        g = r["by_check"]["global"]
        l = r["by_check"]["local"]
        lines.append(
            f"| `{r['model_key']}` | {g['strict_yes']}/{g['n']} | {g['repair_yes']}/{g['n']} | "
            f"{l['strict_yes']}/{l['n']} | {l['repair_yes']}/{l['n']} |"
        )
    lines.append("")
    lines.append("Plain-language conclusion / 说人话结论：这些失败样本里，模型不是看不见错步。三模型在解释式审计中都能引用或概括错步，并且 strict trace-as-proof 口径全部判 `No`。E136 的失败主要来自另一个环节：模型看见了错步，但把后文正确计算视为已经修复，于是在 repair-aware 口径下继续判 `Yes`。")
    lines.append("")
    lines.append("This sharpens the claim: hidden risk trigger can select the bad rows, but the second-pass checker must be forced into the right evaluation policy. Otherwise it may read chain-of-thought as a repairable draft rather than as a strict proof. / 这让主张更精确：hidden 风险信号能挑出问题行，但二次检查器必须被约束到正确评价口径；否则它会把 CoT 当可修复草稿，而不是严格证明。")
    lines.append("")
    lines.append("## Examples / 样例")
    lines.append("")
    for r in rows:
        lines.append(f"### `{r['model_key']}`")
        for ex in r["examples"][:2]:
            lines.append(
                f"- `{ex['audit_idx']}` `{ex['check_type']}` `{ex['route_id']}`: "
                f"wrong step = {ex['wrong_step_quoted']!r}; "
                f"strict = `{ex['strict_decision']}`, repair-aware = `{ex['repair_aware_decision']}`; "
                f"reason = {ex['short_reason']}"
            )
        lines.append("")
    lines.append("## Audit / 审计")
    lines.append("")
    for r in rows:
        audit = r["leakage_audit"]
        lines.append(
            f"- `{r['model_key']}` leakage passed = `{audit['passed']}`; "
            f"labels in prompt = {audit['labels_in_prompt_rows']}, "
            f"gold in prompt = {audit['gold_answer_in_prompt_rows']}, "
            f"manual error span annotations in prompt = {audit['manual_error_span_annotation_in_prompt_rows']}."
        )
    lines.append("")
    lines.append("Caveats / 边界：")
    lines.append("")
    lines.append("- E139 is not a natural prevalence experiment. It explains a selected E136 failure cluster. / E139 不是自然发生率实验，只解释 E136 的一个失败簇。")
    lines.append("- The selected failure cluster is narrow: `percentage_base` repaired strict-invalid traces. It should be expanded to more task families before becoming a broad claim. / 当前失败簇较窄，需要扩展到更多任务族。")
    lines.append("- Two Gemma26 romanized-zh generations hit `max_new_tokens`; parsed strict/repair decisions are still available, but those rows should be treated as lower-quality textual examples. / Gemma26 有两条 romanized-zh 生成触顶，判定字段可解析，但文本样例质量较低。")
    lines.append("- Thinking-mode E139 is deferred. The smoke run showed thinking can consume the budget before emitting the final audit block, so it needs a separate final-contract prompt and larger token budget. / thinking 版本暂缓，需要单独设计收口 prompt 与更大 token 预算。")
    lines.append("")
    lines.append("## Claim Update / 主张更新")
    lines.append("")
    lines.append("E139 supports the narrower mechanism claim that second-pass verifier failures can occur after error detection: the model detects the wrong step, but the objective/readout makes it answer according to a repair-aware standard. This is different from saying the model has no process signal. / E139 支持更窄、更强的机制说法：二次 verifier 的失败可能发生在“已经看见错步之后”，因为 objective/readout 让它按 repair-aware 标准回答；这不是“模型没有过程信号”。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    model_results = [model_summary(d) for d in load_results()]
    order = {"qwen35_27b": 0, "gemma4_31b_it": 1, "gemma4_26b_a4b_it": 2}
    model_results.sort(key=lambda x: order.get(x["model_key"], 99))
    summary = {
        "experiment": "E139_check_rationale_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scope": "failure_only E136 base/check failures; non-thinking rationale generation",
        "models": model_results,
        "overall": {
            "models_n": len(model_results),
            "selected_rows_total": sum(r["selected_rows_n"] for r in model_results),
            "jobs_total": sum(r["jobs_n"] for r in model_results),
            "strict_yes_total": sum(r["strict_yes"] for r in model_results),
            "repair_aware_yes_total": sum(r["repair_aware_yes"] for r in model_results),
            "wrong_step_quoted_total": sum(r["wrong_step_quoted"] for r in model_results),
        },
    }
    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(summary), encoding="utf-8")
    print(json.dumps({"md": str(REPORT_MD), "json": str(REPORT_JSON), "overall": summary["overall"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
