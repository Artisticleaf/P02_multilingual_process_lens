#!/usr/bin/env python3
"""Summarize completed E153-E161 artifacts without touching active queues.

The script intentionally reads only final JSON / audit JSON files.  Checkpoint
JSONL files from currently running jobs are reported as queue health, not as
completed scientific evidence.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

OUT_MD = PROJECT / "reports/E153_E161_COMPLETED_DATA_SYNTHESIS_20260501.md"
OUT_JSON = PROJECT / "reports/E153_E161_COMPLETED_DATA_SYNTHESIS_20260501.json"
OUT_KG = PROJECT / "reports/E153_E161_CLAIM_KG_20260501.json"

E153_DENSE = PROJECT / "results/E153_nonthinking_difficult_scenario_generation/e153_dense_generation_audit_summary_20260501.json"
E153_MOE = PROJECT / "results/E153_nonthinking_difficult_scenario_generation/e153_moe_generation_audit_summary_20260501.json"
E153_ERR = PROJECT / "results/E153_nonthinking_error_finding/e153_error_finding_audit_summary_20260501.json"
E159_DIR = PROJECT / "results/E159_answer_preserving_difficult_generation"
E160_DIR = PROJECT / "results/E160_thinking_answer_preserving_generation"
E161_DIR = PROJECT / "results/E161_answer_preserving_error_repair"
TASK_AUDIT = PROJECT / "reports/E159_TASK_BANK_AUDIT_20260501.json"
E159_PROCESS_AUDIT = E159_DIR / "e159_process_acpi_audit_summary_20260501.json"
QUEUE_STATUS = PROJECT / "logs/e159_e161_overnight_status_20260501.jsonl"

REPAIR_RE = re.compile(
    r"\b(check|self-check|verify|recheck|mistake|wrong|correct|correction|revise|however|actually|wait)\b"
    r"|检查|复核|错误|错了|更正|修正|重新|但是|然而",
    re.IGNORECASE,
)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def pct(num: int | float, den: int | float) -> str:
    if not den:
        return "n/a"
    return f"{100.0 * num / den:.1f}%"


def counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return {k: int(v) for k, v in sorted(counter.items())}


def infer_model_file_mode(path: Path) -> tuple[str, str]:
    data = read_json(path) or {}
    model = str(data.get("model_key") or path.name.split("_E")[0])
    thinking = bool(data.get("summary", {}).get("thinking"))
    return model, "thinking" if thinking else "nonthinking"


def summarize_generation_file(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if data is None:
        raise FileNotFoundError(path)
    rows = data.get("rows", [])
    summary = data.get("summary", {})
    repair_markers = 0
    final_line_counts: Counter[str] = Counter()
    wrong_rows = []
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_variant: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        comp = str(r.get("completion", ""))
        repair_markers += int(bool(REPAIR_RE.search(comp)))
        final_count = len(re.findall(r"(?im)^\s*Final answer\s*:", comp))
        final_line_counts[str(final_count)] += 1
        for bucket in (by_family[str(r.get("family", "unknown"))], by_variant[str(r.get("prompt_variant", "unknown"))]):
            bucket["n"] += 1
            bucket["final_correct"] += int(bool(r.get("manual_final_correct")))
            bucket["missing_final_marker"] += int(not bool(r.get("final_marker_found")))
            bucket["hit_max"] += int(bool(r.get("hit_max_new_tokens")))
        if not r.get("manual_final_correct"):
            wrong_rows.append(
                {
                    "task_id": r.get("task_id"),
                    "family": r.get("family"),
                    "prompt_variant": r.get("prompt_variant"),
                    "gold_answer": r.get("gold_answer"),
                    "extracted_final": r.get("extracted_final"),
                    "hit_max_new_tokens": bool(r.get("hit_max_new_tokens")),
                    "final_marker_found": bool(r.get("final_marker_found")),
                }
            )
    model, mode = infer_model_file_mode(path)
    return {
        "path": str(path.relative_to(PROJECT)),
        "model_key": model,
        "mode": mode,
        "generated": int(summary.get("generated", len(rows))),
        "selected_tasks": int(summary.get("selected_tasks", 0)),
        "final_correct": int(summary.get("final_correct", sum(int(bool(r.get("manual_final_correct"))) for r in rows))),
        "missing_final_marker": int(summary.get("missing_final_marker", sum(int(not bool(r.get("final_marker_found"))) for r in rows))),
        "hit_max": int(summary.get("hit_max", sum(int(bool(r.get("hit_max_new_tokens"))) for r in rows))),
        "repair_marker_rows_auto": repair_markers,
        "final_answer_line_count_hist": counter_to_dict(final_line_counts),
        "leakage_audit": summary.get("leakage_audit", {}),
        "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
        "by_variant": {k: dict(v) for k, v in sorted(by_variant.items())},
        "wrong_rows": wrong_rows,
    }


def compare_e159_e160_qwen(e159: dict[str, Any], e160: dict[str, Any]) -> dict[str, Any]:
    e159_data = read_json(PROJECT / e159["path"]) or {}
    e160_data = read_json(PROJECT / e160["path"]) or {}
    key = lambda r: (r.get("task_id"), r.get("prompt_variant"), r.get("sample_idx"))
    left = {key(r): r for r in e159_data.get("rows", [])}
    right = {key(r): r for r in e160_data.get("rows", [])}
    shared = sorted(set(left) & set(right))
    buckets: Counter[str] = Counter()
    thinking_hit_max_when_nonthinking_correct = []
    family_delta: dict[str, Counter[str]] = defaultdict(Counter)
    for k in shared:
        a = left[k]
        b = right[k]
        ac = bool(a.get("manual_final_correct"))
        bc = bool(b.get("manual_final_correct"))
        label = ("nt_correct" if ac else "nt_wrong") + "__" + ("th_correct" if bc else "th_wrong")
        buckets[label] += 1
        fam = str(a.get("family", "unknown"))
        family_delta[fam][label] += 1
        if ac and not bc and b.get("hit_max_new_tokens"):
            thinking_hit_max_when_nonthinking_correct.append(
                {
                    "task_id": a.get("task_id"),
                    "family": fam,
                    "prompt_variant": a.get("prompt_variant"),
                    "thinking_extracted_final": b.get("extracted_final"),
                    "gold_answer": b.get("gold_answer"),
                    "thinking_final_marker_found": bool(b.get("final_marker_found")),
                }
            )
    return {
        "shared_rows": len(shared),
        "confusion": counter_to_dict(buckets),
        "by_family_confusion": {k: dict(v) for k, v in sorted(family_delta.items())},
        "thinking_hit_max_when_nonthinking_correct": thinking_hit_max_when_nonthinking_correct,
    }


def summarize_e161_files() -> list[dict[str, Any]]:
    out = []
    for path in sorted(E161_DIR.glob("*.json")):
        data = read_json(path)
        if not data:
            continue
        summary = data.get("summary", {})
        out.append(
            {
                "path": str(path.relative_to(PROJECT)),
                "model_key": data.get("model_key"),
                "jobs": summary.get("jobs"),
                "pred_correct": summary.get("pred_correct"),
                "location_match": summary.get("location_match"),
                "repair_final_correct": summary.get("repair_final_correct"),
                "hit_max": summary.get("hit_max"),
                "by_slice": summary.get("by_slice", {}),
                "leakage_audit": summary.get("leakage_audit", {}),
            }
        )
    return out


def queue_state() -> dict[str, Any]:
    rows = read_jsonl(QUEUE_STATUS)
    return {
        "status_path": str(QUEUE_STATUS.relative_to(PROJECT)),
        "events": rows,
        "last_event": rows[-1] if rows else None,
        "completed_steps": [r.get("step") for r in rows if r.get("status") == "done"],
        "started_not_done": [
            r.get("step")
            for r in rows
            if r.get("status") == "start" and r.get("step") not in {x.get("step") for x in rows if x.get("status") == "done"}
        ],
    }


def build_kg(synthesis: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": synthesis["created_at"],
        "scope": "E153-E161 completed-data KG snapshot, with running jobs excluded from evidence counts.",
        "nodes": [
            {
                "id": "claim.solve_vs_audit_separation",
                "type": "claim",
                "zh": "会从头解题，不等于会审计已有推理过程。",
                "en": "Solving from scratch and auditing a given reasoning trace are separable abilities.",
                "status": "strong_current_evidence",
                "evidence": ["E153_generation_audits", "E153_error_finding_audit"],
            },
            {
                "id": "claim.natural_unrepaired_acpi_prevalence",
                "type": "claim",
                "zh": "自然生成的未修复 ACPI 在多样化中等难题中尚未显示高频。",
                "en": "Natural unrepaired ACPI has not yet appeared frequently in diverse moderate hard-task generation.",
                "status": "not_supported_as_broad_prevalence_yet",
                "evidence": ["E153_generation_audits"],
            },
            {
                "id": "claim.answer_preserving_traps_needed",
                "type": "claim",
                "zh": "要高效诱发 ACPI，任务需要局部错误仍能保持最终答案的结构。",
                "en": "Efficient ACPI induction needs answer-preserving structures where a local error can leave the final answer unchanged.",
                "status": "controlled_surface_supported_natural_generation_negative",
                "evidence": ["E159_task_bank_audit", "E159_nonthinking_generation", "E159_process_acpi_audit"],
            },
            {
                "id": "claim.hidden_state_method",
                "type": "claim",
                "zh": "隐藏层信号应在审计后用 teacher-forced replay 保存，作为可解释性主证据。",
                "en": "Hidden-state evidence should be cached after audit with teacher-forced replay.",
                "status": "method_policy_set_pending_E156_replay",
                "evidence": ["history_hidden_state_policy"],
            },
        ],
        "edges": [
            {
                "source": "E153_generation_audits",
                "target": "claim.natural_unrepaired_acpi_prevalence",
                "relation": "constrains",
                "zh": "E153 产生大量正确顺序 trace，但 0 个未修复 ACPI，因此限制了“自然高频”说法。",
            },
            {
                "source": "E153_error_finding_audit",
                "target": "claim.solve_vs_audit_separation",
                "relation": "supports",
                "zh": "同一批能力强的模型在找错/定位上出现误报、漏报和错定位。",
            },
            {
                "source": "E159_nonthinking_generation",
                "target": "claim.answer_preserving_traps_needed",
                "relation": "prepares_evidence",
                "zh": "E159 在 10 类保答案陷阱上生成并审计 360 条 non-thinking trace；自然生成未出现未修复 ACPI，但产生 357 条干净有效 replay 种子。",
            },
            {
                "source": "E161_oracle_span_repair",
                "target": "claim.hidden_state_method",
                "relation": "pending_upper_bound",
                "zh": "E161 将区分 blind 找错、定位和显式 span 上界修复。",
            },
        ],
    }


def render_markdown(s: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# E153-E161 Completed Data Synthesis / 已完成数据综合统计")
    lines.append("")
    lines.append(f"- Created at / 生成时间：`{s['created_at']}`.")
    lines.append("- Scope / 范围：只统计已经完整写入 final JSON 或审计 summary 的数据；正在运行的 checkpoint 不进入科学结论。")
    lines.append("")
    q = s["queue_state"]
    lines.append("## Queue Status / 队列状态")
    lines.append("")
    lines.append(f"- Last event / 最后事件：`{q.get('last_event')}`.")
    lines.append(f"- Completed steps / 已完成步骤：{', '.join(q.get('completed_steps') or [])}.")
    pending = q.get("started_not_done") or []
    lines.append(f"- Running or pending / 正在运行或等待：{', '.join(pending) if pending else 'none detected from status file'}.")
    lines.append("")

    lines.append("## E153 Generation / E153 自然解题生成")
    lines.append("")
    e153 = s["e153_generation"]
    for model, item in e153["by_model"].items():
        lines.append(
            f"- `{model}`: n={item['n']}, manual final correct={item['manual_final_correct']} ({pct(item['manual_final_correct'], item['n'])}), "
            f"clean valid prefill candidates={item['clean_valid_prefill_candidate']}, language-trait traces={item['language_trait_use']}, "
            f"unrepaired ACPI={item['manual_acpi_unrepaired']}."
        )
    lines.append("- Interpretation / 解释：E153 说明多样化任务能产生大量顺序、可重放的高质量 trace，但没有支持“自然未修复 ACPI 高频存在”。")
    lines.append("")

    lines.append("## E153 Error Finding / E153 找错定位")
    lines.append("")
    for model, item in s["e153_error_finding"]["by_model"].items():
        lines.append(
            f"- `{model}`: n={item['n']}, last-pred correct={item['last_pred_correct']} ({pct(item['last_pred_correct'], item['n'])}), "
            f"valid false positives={item['valid_false_positive_last']}/{item['valid_n']}, "
            f"invalid false negatives={item['invalid_false_negative_last']}/{item['invalid_n']}, "
            f"invalid location match={item['invalid_location_match_last']}/{item['invalid_n']}, hit-max={item['hit_max']}."
        )
    lines.append("- Interpretation / 解释：这里的强信号是“会解题”和“会审计过程”分离。Qwen 更敏感但更容易误报；Gemma dense 更保守；MoE 最保守，漏报更多。")
    lines.append("")

    lines.append("## E159 Non-Thinking Generation / E159 non-thinking 保答案陷阱生成")
    lines.append("")
    for item in s["e159_generation"]:
        lines.append(
            f"- `{item['model_key']}`: generated={item['generated']}, final-correct={item['final_correct']} ({pct(item['final_correct'], item['generated'])}), "
            f"missing-final-marker={item['missing_final_marker']}, hit-max={item['hit_max']}, auto repair-marker rows={item['repair_marker_rows_auto']}."
        )
    audit = s.get("e159_process_acpi_audit")
    if audit:
        lines.append(
            f"- Process audit / 过程审计：n={audit['n']}, audited final-correct={audit['manual_final_correct_audit']} ({pct(audit['manual_final_correct_audit'], audit['n'])}), "
            f"process-valid={audit['process_valid_strict']} ({pct(audit['process_valid_strict'], audit['n'])}), "
            f"runner format false-negatives={audit['runner_false_negative_format']}, unrepaired ACPI={audit['acpi_unrepaired']}, "
            f"clean valid prefill candidates={audit['clean_valid_prefill_candidate']}."
        )
        lines.append("- Interpretation / 解释：E159 自然生成没有产出 unrepaired ACPI；它的价值转为提供大批干净有效 replay 种子，以及给 E161/E156 的受控 invalid-reference/mutation 机制实验提供任务面。")
    else:
        lines.append("- Caveat / 注意：E159 的 final-correct 是自动答案判定；过程有效性字段仍未人工审计，所以不能据此直接声称自然 ACPI。")
    lines.append("")

    lines.append("## E160 Thinking Contrast / E160 thinking 对照")
    lines.append("")
    if s["e160_generation"]:
        for item in s["e160_generation"]:
            lines.append(
                f"- `{item['model_key']}`: generated={item['generated']}, final-correct={item['final_correct']} ({pct(item['final_correct'], item['generated'])}), "
                f"missing-final-marker={item['missing_final_marker']}, hit-max={item['hit_max']}, auto repair-marker rows={item['repair_marker_rows_auto']}."
            )
    else:
        lines.append("- No completed final E160 file yet. / 暂无完整 E160 final 文件。")
    cmp = s.get("e159_e160_qwen_compare")
    if cmp:
        lines.append(
            f"- Qwen shared rows / Qwen 同题同 prompt 对照：{cmp['shared_rows']} rows; confusion={cmp['confusion']}."
        )
        lines.append("- Interpretation / 解释：Qwen thinking 目前因 4096 token 上限产生明显截断，不能简单说 thinking 更好；应先调大 token 或单独审计截断行。")
    lines.append("")

    lines.append("## E161 Controlled Repair / E161 受控找错与修复")
    lines.append("")
    if s["e161_error_repair"]:
        for item in s["e161_error_repair"]:
            lines.append(
                f"- `{item['model_key']}`: jobs={item['jobs']}, pred_correct={item['pred_correct']}, location_match={item['location_match']}, repair_final_correct={item['repair_final_correct']}, hit_max={item['hit_max']}."
            )
    else:
        lines.append("- No completed E161 final file yet. / E161 尚无完整 final 文件。")
    lines.append("")

    lines.append("## Claim State / 当前 claim 状态")
    lines.append("")
    for c in s["claim_state"]:
        lines.append(f"- {c['id']}: {c['evidence_maturity']}. {c['zh']}")
    lines.append("")
    lines.append("## Next Analysis Actions / 后续分析动作")
    lines.append("")
    for item in s["next_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    dense = read_json(E153_DENSE) or {"by_model": {}}
    moe = read_json(E153_MOE) or {"by_model": {}}
    e153_generation_by_model = {}
    e153_generation_by_model.update(dense.get("by_model", {}))
    e153_generation_by_model.update(moe.get("by_model", {}))
    e153_err = read_json(E153_ERR) or {"by_model": {}, "by_slice": {}}
    task_audit = read_json(TASK_AUDIT) or {}
    e159_process_audit = read_json(E159_PROCESS_AUDIT)

    e159 = [
        summarize_generation_file(p)
        for p in sorted(E159_DIR.glob("*_E159_answer_preserving_generation_nonthinking_*.json"))
        if not p.name.startswith("_")
    ]
    e160 = [
        summarize_generation_file(p)
        for p in sorted(E160_DIR.glob("*_E160_thinking_answer_preserving_generation_thinking_*.json"))
        if not p.name.startswith("_")
    ]

    qwen_e159 = next((x for x in e159 if x["model_key"] == "qwen35_27b"), None)
    qwen_e160 = next((x for x in e160 if x["model_key"] == "qwen35_27b"), None)
    compare = compare_e159_e160_qwen(qwen_e159, qwen_e160) if qwen_e159 and qwen_e160 else None

    synthesis = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scope_note": "Completed final artifacts only; active checkpoints are excluded from evidence counts.",
        "queue_state": queue_state(),
        "e159_task_bank_audit": task_audit,
        "e159_process_acpi_audit": e159_process_audit,
        "e153_generation": {
            "sources": [str(E153_DENSE.relative_to(PROJECT)), str(E153_MOE.relative_to(PROJECT))],
            "by_model": e153_generation_by_model,
        },
        "e153_error_finding": {
            "source": str(E153_ERR.relative_to(PROJECT)),
            "by_model": e153_err.get("by_model", {}),
            "by_slice": e153_err.get("by_slice", {}),
        },
        "e159_generation": e159,
        "e160_generation": e160,
        "e159_e160_qwen_compare": compare,
        "e161_error_repair": summarize_e161_files(),
        "claim_state": [
            {
                "id": "C1_solve_vs_audit_separation",
                "evidence_maturity": "strong / 强",
                "zh": "E153 已支持：模型会从头做题，但检查已有过程时会误报、漏报或定位错步。",
            },
            {
                "id": "C2_natural_unrepaired_acpi_prevalence",
                "evidence_maturity": "weak-to-negative for broad prevalence / 对广泛自然高频说法较弱且偏负",
                "zh": "E153 多样化自然生成没有发现未修复 ACPI；后续要靠保答案结构与人工过程审计寻找高质量样本。",
            },
            {
                "id": "C3_answer_preserving_trap_surface",
                "evidence_maturity": "process-audited negative for natural ACPI, strong seed pool / 已过程审计；自然 ACPI 为负，种子池强",
                "zh": "E159 已完成并审计 10 类、40 题、三模型 360 条 non-thinking 生成；自然未修复 ACPI 为 0，但得到 357 条干净有效 prefill 种子。",
            },
            {
                "id": "C4_thinking_contrast",
                "evidence_maturity": "partial / 部分完成",
                "zh": "E160 目前只有 Qwen 完整落盘；thinking 因截断较多，不能直接当作性能提升证据。",
            },
            {
                "id": "C5_hidden_explainability",
                "evidence_maturity": "method fixed, data pending / 方法确定，数据待跑",
                "zh": "隐藏层主方案已确定为审计后 teacher-forced replay；E159/E161 审计后应接 E156 cache。",
            },
        ],
        "next_actions": [
            "等待 E160 Gemma dense 和 E161 完整落盘后，用本脚本重跑综合统计。",
            "对 E159 process audit 的 357 条 clean-valid 行抽样做第二轮人工复核，再选入 E156 hidden replay。",
            "用 E159 invalid reference traces 和 clean-valid generated traces 构造 mutation/prefill 对照，而不是继续期待同一设置自然产出大量 ACPI。",
            "E161 完成后比较 blind_global、blind_localize_only、oracle_span_repair，判断显式错步提示能否提升 non-thinking 修复。",
            "把审计后的 clean-valid、mutated-invalid、natural-wrong、localized-failure 四类样本送入 E156 teacher-forced hidden replay。",
        ],
    }

    kg = build_kg(synthesis)
    OUT_JSON.write_text(json.dumps(synthesis, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_KG.write_text(json.dumps(kg, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(synthesis), encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(PROJECT)}")
    print(f"wrote {OUT_JSON.relative_to(PROJECT)}")
    print(f"wrote {OUT_KG.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
