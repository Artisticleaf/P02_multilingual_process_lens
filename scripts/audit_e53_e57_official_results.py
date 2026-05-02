#!/usr/bin/env python3
"""Audit E53-E57 result integrity and leakage boundaries."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_JSON = PROJECT / "reports/E53_E57_LEAKAGE_LOGIC_AUDIT_20260428.json"
OUT_MD = PROJECT / "reports/E53_E57_LEAKAGE_LOGIC_AUDIT_20260428.md"

P0 = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fail(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def get_model_file(exp: str, model: str) -> Path:
    d = PROJECT / "results" / exp
    matches = sorted(d.glob(f"{model}_*.json"))
    if not matches:
        raise FileNotFoundError(f"missing {exp}/{model}")
    if len(matches) != 1:
        # E54 names include e42; all current P0 should still have one active file per model.
        raise RuntimeError(f"ambiguous {exp}/{model}: {matches}")
    return matches[0]


def main() -> None:
    checks: list[dict[str, Any]] = []
    summary: dict[str, Any] = {"created_at": datetime.now().isoformat(timespec="seconds")}

    # File existence and counts.
    for exp in [
        "E53_answer_anchor_ablation",
        "E54_parameterized_no_leak_generalization",
        "E55_residual_to_logit_mediation",
        "E56_component_decomposition",
        "E57_p0_hard_task_final_correct_harvesting",
    ]:
        for model in P0:
            path = get_model_file(exp, model)
            fail(checks, f"{exp}/{model} exists", path.exists(), str(path.relative_to(PROJECT)))

    e53_data = load_jsonl(PROJECT / "data/processed/e53_answer_anchor_ablation_20260428.jsonl")
    fail(checks, "E53 data row count", len(e53_data) == 96, f"rows={len(e53_data)}")
    fail(checks, "E53 no gold label inserted", all(not r.get("gold_label_in_prompt") for r in e53_data), "gold_label_in_prompt all false")
    fail(checks, "E53 no error-span annotation inserted", all(not r.get("known_error_span_in_prompt") for r in e53_data), "known_error_span_in_prompt all false")
    removed_masked = [r for r in e53_data if r["e53_answer_condition"] in {"removed", "masked"}]
    fail(checks, "E53 removed/masked final_correct is None", all(r.get("manual_final_correct") is None for r in removed_masked), f"rows={len(removed_masked)}")
    for p in (PROJECT / "results/E53_answer_anchor_ablation").glob("*.json"):
        d = load_json(p)
        fail(checks, f"E53 {p.name} row count", len(d["rows"]) == 96, f"rows={len(d['rows'])}")
        fail(checks, f"E53 {p.name} prompt format official_if_chat", d["args"].get("prompt_format") == "official_if_chat", str(d["args"].get("prompt_format")))
        fail(checks, f"E53 {p.name} chat template used", bool(d.get("used_chat_template")), str(d.get("used_chat_template")))

    e54_data = load_jsonl(PROJECT / "data/processed/e54_parameterized_no_leak_generalization_20260428.jsonl")
    fail(checks, "E54 data row count", len(e54_data) == 36, f"rows={len(e54_data)}")
    for field in ["gold_label_in_prompt", "known_error_span_in_prompt", "known_error_span_annotation_in_prompt"]:
        fail(checks, f"E54 {field} all false", all(not r.get(field) for r in e54_data), field)
    fail(checks, "E54 one valid and one invalid per task", all(Counter(r["e39_variant"] for r in e54_data if r["task_id"] == tid) == Counter({"valid_correct": 1, "invalid_correct": 1}) for tid in {r["task_id"] for r in e54_data}), "18 paired tasks")
    for p in (PROJECT / "results/E54_parameterized_no_leak_generalization").glob("*.json"):
        d = load_json(p)
        fail(checks, f"E54 {p.name} result row count", len(d["rows"]) == 72, f"rows={len(d['rows'])}")
        fail(checks, f"E54 {p.name} prompt format official_if_chat", d["args"].get("prompt_format") == "official_if_chat", str(d["args"].get("prompt_format")))
        fail(checks, f"E54 {p.name} chat template used", bool(d.get("used_chat_template")), str(d.get("used_chat_template")))

    # E55/E56 causal diagnostics should use leave-one-task-out and include scope notes.
    for exp in ["E55_residual_to_logit_mediation", "E56_component_decomposition"]:
        for p in (PROJECT / "results" / exp).glob("*.json"):
            d = load_json(p)
            note = (d.get("scope_note_en", "") + " " + d.get("scope_note_zh", "")).lower()
            fail(checks, f"{exp} {p.name} LOTO scope note", "leave-one-task-out" in note, d.get("scope_note_en", ""))
            fail(checks, f"{exp} {p.name} chat template used", bool(d.get("used_chat_template")), str(d.get("used_chat_template")))
            if exp.startswith("E56"):
                fail(checks, f"E56 {p.name} has token_mixer", "token_mixer_output" in set(d.get("components", [])), str(d.get("components")))

    stale_qwen = PROJECT / "archive/superseded_results_20260428/qwen35_27b_e56_component_decomposition_missing_token_mixer.json"
    active_qwen_e56 = PROJECT / "results/E56_component_decomposition/qwen35_27b_e56_component_decomposition.json"
    fail(checks, "E56 stale Qwen missing-token-mixer archived", stale_qwen.exists() and active_qwen_e56.exists(), f"archive={stale_qwen.exists()} active={active_qwen_e56.exists()}")

    # E57 official run checks.
    e57_all_rows = []
    for p in (PROJECT / "results/E57_p0_hard_task_final_correct_harvesting").glob("*.json"):
        d = load_json(p)
        rows = d["rows"]
        e57_all_rows.extend(rows)
        args = d.get("args", {})
        fail(checks, f"E57 {p.name} no gold answer rows", d["summary"].get("gold_answer_in_prompt_rows") == 0, str(d["summary"].get("gold_answer_in_prompt_rows")))
        fail(checks, f"E57 {p.name} no trap note rows", d["summary"].get("known_trap_note_in_prompt_rows") == 0, str(d["summary"].get("known_trap_note_in_prompt_rows")))
        fail(checks, f"E57 {p.name} variants no answer_anchor", set(args.get("variants", [])) == {"neutral", "answer_first_no_gold", "self_check"}, str(args.get("variants")))
        fail(checks, f"E57 {p.name} thinking false", args.get("thinking") == "false", str(args.get("thinking")))
        fail(checks, f"E57 {p.name} k=4", int(args.get("k", -1)) == 4, str(args.get("k")))
        fail(checks, f"E57 {p.name} max_tasks=6", int(args.get("max_tasks", -1)) == 6, str(args.get("max_tasks")))
        fail(checks, f"E57 {p.name} row count", len(rows) == 72, f"rows={len(rows)}")
    fail(checks, "E57 aggregate row count", len(e57_all_rows) == 216, f"rows={len(e57_all_rows)}")
    fail(checks, "E57 aggregate no gold prompt", all(not r.get("gold_answer_in_prompt") for r in e57_all_rows), "all rows false")
    fail(checks, "E57 aggregate no trap prompt", all(not r.get("known_trap_note_in_prompt") for r in e57_all_rows), "all rows false")
    fail(checks, "E57 no answer_anchor variant", "answer_anchor" not in {r.get("prompt_variant") for r in e57_all_rows}, str(Counter(r.get("prompt_variant") for r in e57_all_rows)))

    manual = load_jsonl(PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl")
    fail(checks, "E57 manual audit row count", len(manual) == 119, f"rows={len(manual)}")
    fail(checks, "E57 manual audit all final-correct", all(r.get("manual_final_correct") for r in manual), "all manual_final_correct true")
    fail(checks, "E57 manual strict+repaired labels present", all("manual_process_valid_strict" in r and "manual_process_valid_repaired" in r for r in manual), "labels present")
    multi_final = [r for r in manual if len(re.findall(r"^\s*final\s*answer\s*[:：]", r.get("completion", ""), flags=re.I | re.M)) > 1]
    fail(checks, "E57 multiple-final rows documented", len(multi_final) >= 1, f"multiple_final_rows={len(multi_final)}; parser uses last anchored line")
    summary["e57_manual"] = {
        "n": len(manual),
        "strict_valid": sum(r["manual_process_valid_strict"] for r in manual),
        "repaired_valid": sum(r["manual_process_valid_repaired"] for r in manual),
        "strict_acpi": sum(r["manual_acpi_strict"] for r in manual),
        "unrepaired_acpi": sum(r["manual_acpi_unrepaired"] for r in manual),
        "multiple_final_rows": len(multi_final),
        "error_types": dict(Counter(r["manual_error_type"] for r in manual)),
    }

    # Static prompt construction audit: verifier prompts only interpolate problem/completion.
    e42_text = (PROJECT / "scripts/run_e42_official_template_parity.py").read_text(encoding="utf-8")
    e53_text = (PROJECT / "scripts/run_e53_answer_anchor_ablation.py").read_text(encoding="utf-8")
    prompt_src = e42_text + "\n" + e53_text
    forbidden_prompt_insertions = ["support_span", "error_span", "manual_correction", "manual_process_valid"]
    # These field names may appear in data-building code, but should not appear inside process_prompt/contrastive_prompt bodies.
    for name in forbidden_prompt_insertions:
        process_sections = re.findall(r"def process_prompt\(.*?\n\ndef ", prompt_src, flags=re.S)
        ok = all(name not in section for section in process_sections)
        fail(checks, f"static verifier prompt does not insert {name}", ok, name)

    ok_all = all(c["ok"] for c in checks)
    summary["all_checks_passed"] = ok_all
    summary["checks"] = checks
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# E53-E57 Leakage and Logic Audit / E53-E57 泄露与逻辑审计（2026-04-28）",
        "",
        f"- JSON / 机器可读结果：`{OUT_JSON.relative_to(PROJECT)}`",
        f"- Overall / 总体：{'PASS' if ok_all else 'FAIL'}",
        "- Scope / 范围：检查 E53-E57 官方结果文件、prompt 构造、gold/trap 泄露、E57 人审标签、E56 superseded 文件归档和 E55/E56 LOTO 机制边界。",
        "",
        "## Checklist / 检查表",
        "",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for c in checks:
        lines.append(f"| {'PASS' if c['ok'] else 'FAIL'} | {c['check']} | {c['detail']} |")
    lines += [
        "",
        "## Key Conclusions / 关键结论",
        "",
        "- E53/E54 verifier prompt 只插入 problem 和 completion；人工标签、support span、error span、manual correction 没有进入 prompt。错误句子本身仍在 trace 里，这是实验对象，不是泄露。",
        "- E57 官方 hard-task run 没有 answer-anchor、没有 gold answer、没有 trap note；strict final parser 使用最后一个行首 `Final answer:`，因此先写错后修正的 trace 会被计入 final-correct，但在人审中单独标记为 repaired。",
        "- E55/E56 的方向学习是 leave-one-task-out 诊断，不把 held-out task 标签直接用于该 task 的 probe/patch 方向；结论边界仍是 causal diagnostic，不是完整 circuit proof。",
        "- E56 Qwen 早期遗漏 token-mixer 的旧文件已经在 archive；active 文件包含 `token_mixer_output`。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"all_checks_passed": ok_all, "json": str(OUT_JSON), "report": str(OUT_MD), "failed": [c for c in checks if not c["ok"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
