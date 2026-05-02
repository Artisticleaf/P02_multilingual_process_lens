#!/usr/bin/env python3
"""Write an E166-E169 hidden-monitor KG snapshot.

This file records method state and completed E166 replay artifacts. It does not
turn running checkpoints into evidence; missing full runs are marked pending.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "reports/E166_E169_HIDDEN_MONITOR_CLAIM_KG_20260502.json"
RESULT_DIR = PROJECT / "results/E166_hardened_hidden_monitor_replay"
PREFIX_AUDIT = PROJECT / "reports/E166_HARDENED_MONITOR_PREFIX_STATIC_AUDIT_20260502.json"
CALIBRATION_AUDIT = PROJECT / "reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.json"
STATUS = PROJECT / "logs/e166_hidden_monitor_replay_status_20260502.jsonl"
E167_CASE_AUDIT = PROJECT / "reports/E167_HIDDEN_DERIVED_REPAIR_CASES_STATIC_AUDIT_20260502.json"
E167_SUMMARY = PROJECT / "reports/E167_HIDDEN_DERIVED_REPAIR_CASES_SUMMARY_20260502.json"
E167_STATUS = PROJECT / "logs/e167_hidden_derived_repair_status_20260502.jsonl"
E167_RESULT_DIR = PROJECT / "results/E167_hidden_derived_repair"
E171_TASK_SUMMARY = PROJECT / "reports/E171_MAIN_CLAIM_TASK_BANK_SUMMARY_20260502.json"
E171_PIPELINE_AUDIT = PROJECT / "reports/E171_MAIN_CLAIM_PIPELINE_AUDIT_20260502.json"
E171_RESULT_DIR = PROJECT / "results/E171_main_claim_hidden_rescue"
E171_STATUS = PROJECT / "logs/e171_main_claim_hidden_rescue_status_20260502.jsonl"


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compact_replay(path: Path) -> dict[str, Any]:
    data = read_json(path) or {}
    rows = data.get("rows", [])
    target_rows = [r for r in rows if r.get("monitor_target_offline")]
    valid_rows = [r for r in rows if r.get("trace_class") == "valid"]
    invalid_non_target = [r for r in rows if r.get("trace_class") != "valid" and not r.get("monitor_target_offline")]
    return {
        "path": str(path.relative_to(PROJECT)),
        "model_key": data.get("model_key"),
        "prompt_mode": data.get("prompt_mode"),
        "rows": len(rows),
        "component_cache_pt": data.get("component_cache_pt"),
        "component_cache_shape": data.get("component_cache_shape"),
        "component_keys": data.get("component_keys", []),
        "selected_hidden_layers": data.get("selected_hidden_layers", []),
        "monitor_target_rows": len(target_rows),
        "valid_control_rows": len(valid_rows),
        "invalid_non_target_rows": len(invalid_non_target),
        "mean_yes_minus_no_target": mean([r.get("yes_minus_no") for r in target_rows]),
        "mean_yes_minus_no_valid": mean([r.get("yes_minus_no") for r in valid_rows]),
        "leakage_audit": data.get("leakage_audit", {}),
    }


def mean(vals: list[Any]) -> float | None:
    nums = [float(v) for v in vals if isinstance(v, int | float)]
    if not nums:
        return None
    return sum(nums) / len(nums)


def replay_artifacts() -> list[dict[str, Any]]:
    return [compact_replay(p) for p in sorted(RESULT_DIR.glob("*_e166_generation_prefill*.json"))]


def main() -> None:
    prefix_audit = read_json(PREFIX_AUDIT) or {}
    calibration_audit = read_json(CALIBRATION_AUDIT)
    replays = replay_artifacts()
    full_replays = [r for r in replays if "full_20260502" in r["path"]]
    smoke_replays = [r for r in replays if "smoke_first_sample_20260502" in r["path"]]
    kg = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scope": "E166-E171 hidden-monitor method KG; E171 is the main-claim rescue experiment on same-model original-problem baseline failures.",
        "prefix_bank_audit": prefix_audit,
        "calibration_audit_path": str(CALIBRATION_AUDIT.relative_to(PROJECT)) if calibration_audit else None,
        "calibration_summary": summarize_calibration(calibration_audit),
        "e167_case_audit_path": str(E167_CASE_AUDIT.relative_to(PROJECT)) if E167_CASE_AUDIT.exists() else None,
        "e167_case_summary_path": str(E167_SUMMARY.relative_to(PROJECT)) if E167_SUMMARY.exists() else None,
        "e167_case_summary": summarize_e167_cases(read_json(E167_CASE_AUDIT), read_json(E167_SUMMARY)),
        "queue_state": {
            "status_path": str(STATUS.relative_to(PROJECT)),
            "events": read_jsonl(STATUS),
        },
        "e167_queue_state": {
            "status_path": str(E167_STATUS.relative_to(PROJECT)),
            "events": read_jsonl(E167_STATUS),
            "result_files": [str(p.relative_to(PROJECT)) for p in sorted(E167_RESULT_DIR.glob("*_e167_*.json"))],
        },
        "e171_state": {
            "task_summary_path": str(E171_TASK_SUMMARY.relative_to(PROJECT)) if E171_TASK_SUMMARY.exists() else None,
            "task_summary": read_json(E171_TASK_SUMMARY),
            "pipeline_audit_path": str(E171_PIPELINE_AUDIT.relative_to(PROJECT)) if E171_PIPELINE_AUDIT.exists() else None,
            "pipeline_audit": read_json(E171_PIPELINE_AUDIT),
            "status_path": str(E171_STATUS.relative_to(PROJECT)),
            "events": read_jsonl(E171_STATUS),
            "result_files": [str(p.relative_to(PROJECT)) for p in sorted(E171_RESULT_DIR.glob("*_e171_*.json"))],
        },
        "smoke_replays": smoke_replays,
        "full_replays": full_replays,
        "nodes": [
            {
                "id": "experiment.E166_hidden_monitor_calibration",
                "type": "experiment",
                "status": "smoke_passed_full_running_or_pending" if smoke_replays and len(full_replays) < 3 else "full_artifacts_present",
                "zh": "E166 在加难 multi-family prefix 库上用 teacher-forced causal replay 读取 residual、MLP、token-mixer/attention、norm、entropy/logprob 信号。",
                "en": "E166 reads residual, MLP, token-mixer/attention, norm, entropy, and logprob signals on hardened multi-family prefixes by teacher-forced causal replay.",
            },
            {
                "id": "claim.localized_upper_bound_not_method",
                "type": "claim_boundary",
                "status": "explicit",
                "zh": "E162/E165 的 localized 是人工或构造已知 span，只能作为行为上界；真正方法必须由 hidden monitor 导出位置。",
                "en": "E162/E165 localized spans are human or construction-known behavioral upper bounds; the actual method must derive positions from the hidden monitor.",
            },
            {
                "id": "claim.hidden_monitor_method_ready",
                "type": "claim",
                "status": "calibration_supported_main_claim_rescue_pending" if calibration_audit else "pipeline_smoke_supported_threshold_pending",
                "zh": "E166 全量显示 hidden/component risk 能在因果 prefix 上区分真实错步结束点和正确 prefix；主 claim 的救回收益必须由 E171 证明。",
                "en": "Full E166 shows hidden/component risk separates true wrong-step endpoints from valid prefixes under causal replay; main-claim rescue gains must be proven by E171.",
            },
            {
                "id": "experiment.E167_hidden_derived_repair",
                "type": "experiment",
                "status": e167_status(),
                "zh": "E167 用 E166 阈值导出的自动边界 span，而不是人工错步末尾，测试 controlled trace 上的 non-thinking 局部修复；它不是主 claim 的直接证明。",
                "en": "E167 tests non-thinking localized repair on controlled traces using E166 threshold-derived automatic-boundary spans, not human wrong-step endpoints; it is not direct proof of the main claim.",
            },
            {
                "id": "experiment.E171_main_claim_hidden_rescue",
                "type": "experiment",
                "status": e171_status(),
                "zh": "E171 只保留同一模型原题 non-thinking baseline 做错的题，在模型自己的错误 trace 上读取 hidden monitor，再测试 hidden-generic/localized repair 是否救回且更省 completion token。",
                "en": "E171 keeps same-model original-problem non-thinking baseline failures, reads hidden monitor signals on the model's own wrong trace, then tests whether hidden-generic/localized repair rescues answers with lower completion-token cost.",
            },
            {
                "id": "claim.hidden_signal_main_claim_boundary",
                "type": "claim_boundary",
                "status": "explicit",
                "zh": "只有 E171 这类 baseline-wrong rescue 才能支持“hidden 信号帮助模型做对原本不会做的题”；E167 controlled trace 只能作为方法和成本参考。",
                "en": "Only E171-style baseline-wrong rescue can support the claim that hidden signals help a model solve what it otherwise failed; E167 controlled traces are method and cost references.",
            },
        ],
        "edges": [
            {
                "source": "experiment.E166_hidden_monitor_calibration",
                "relation": "tests",
                "target": "claim.hidden_monitor_method_ready",
                "zh": "E166 检验 hidden state 是否能在因果 prefix 上区分真实错步、非目标错误 prefix 和正确 prefix。",
            },
            {
                "source": "claim.localized_upper_bound_not_method",
                "relation": "constrains",
                "target": "experiment.E167_hidden_derived_repair",
                "zh": "E167 的 localized 位置必须来自 E166 hidden monitor 的自动边界触发，而不能继续使用人工错步末尾候选点。",
            },
            {
                "source": "experiment.E167_hidden_derived_repair",
                "relation": "precondition_for",
                "target": "experiment.E171_main_claim_hidden_rescue",
                "zh": "E167 校验 hidden-derived text warning 的 prompt 边界；E171 才检验原题 baseline 错误是否能被救回。",
            },
            {
                "source": "experiment.E171_main_claim_hidden_rescue",
                "relation": "tests",
                "target": "claim.hidden_signal_main_claim_boundary",
                "zh": "E171 的入口是同模型原题错误，因此能直接检验 hidden 信号是否帮助模型做对原本不会做的题。",
            },
        ],
    }
    OUT.write_text(json.dumps(kg, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(PROJECT)}")


def summarize_calibration(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not data:
        return []
    out = []
    for model in data.get("models", []):
        best = model.get("best_key_record", {})
        hp = best.get("high_precision_eval", {}) or {}
        loc = model.get("localization_best_high_precision", {}) or {}
        out.append(
            {
                "model_key": model.get("model_key"),
                "best_key": model.get("best_key"),
                "target_vs_valid_auc": best.get("target_vs_valid_auc"),
                "target_vs_non_target_auc": best.get("target_vs_non_target_auc"),
                "target_recall_at_valid90": hp.get("target_recall"),
                "valid_false_trigger_rate": hp.get("valid_false_trigger_rate"),
                "target_top1_rate": loc.get("target_top1_rate"),
                "target_top2_rate": loc.get("target_top2_rate"),
            }
        )
    return out


def summarize_e167_cases(audit: dict[str, Any] | None, summary: dict[str, Any] | None) -> dict[str, Any]:
    if not audit and not summary:
        return {}
    return {
        "passed": audit.get("passed") if audit else None,
        "cases": audit.get("cases") if audit else summary.get("cases") if summary else None,
        "by_model": audit.get("by_model", {}) if audit else {},
        "by_policy": audit.get("by_policy", {}) if audit else {},
        "hidden_trigger_boundary_kinds": audit.get("hidden_trigger_boundary_kinds", {}) if audit else {},
        "hidden_trigger_sources": audit.get("hidden_trigger_sources", {}) if audit else {},
        "manual_target_trigger_rows": audit.get("manual_target_trigger_rows") if audit else None,
        "offline_hidden_span_contains_manual_span_rows": audit.get("offline_hidden_span_contains_manual_span_rows") if audit else None,
        "trigger_candidate_policy": summary.get("trigger_candidate_policy") if summary else "auto_boundary_only",
        "leakage_policy": summary.get("leakage_policy") if summary else "",
    }


def e167_status() -> str:
    events = read_jsonl(E167_STATUS)
    if any(e.get("status") == "all_done" for e in events):
        return "full_artifacts_present"
    if events:
        return "full_queue_running"
    if E167_CASE_AUDIT.exists():
        return "case_bank_smoke_ready"
    return "planned"


def e171_status() -> str:
    events = read_jsonl(E171_STATUS)
    if any(e.get("status") == "all_done" for e in events):
        return "full_artifacts_present"
    if events:
        return "full_queue_running_or_waiting"
    audit = read_json(E171_PIPELINE_AUDIT)
    if audit and audit.get("passed"):
        return "task_bank_and_pipeline_audit_passed_queue_waiting"
    return "planned"


if __name__ == "__main__":
    main()
