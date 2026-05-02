#!/usr/bin/env python3
"""Summarize E100-E102 into a short markdown/json report."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_JSON = PROJECT / "reports/E100_E102_BATCH_MODE_HIDDEN_CONTRAST_20260429.json"
OUT_MD = PROJECT / "reports/E100_E102_BATCH_MODE_HIDDEN_CONTRAST_20260429.md"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def fmt(x: Any) -> str:
    if x is None:
        return "NA"
    if isinstance(x, float):
        return f"{x:.4g}"
    return str(x)


def main() -> None:
    e100 = load(PROJECT / "results/E100_batch_invariance_audit/qwen35_27b_e100_batch_invariance.json")
    e101 = load(PROJECT / "results/E101_batch_generation_sensitivity/qwen35_27b_e101_batch_generation_sensitivity.json")
    e102 = load(PROJECT / "results/E102_thinking_nonthinking_hidden_contrast/qwen35_27b_e102_thinking_nonthinking_hidden_contrast.json")
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "e100_available": e100 is not None,
        "e101_available": e101 is not None,
        "e102_available": e102 is not None,
        "e100_key_summary": e100.get("summary", []) if e100 else [],
        "e101_key_summary": e101.get("summary", []) if e101 else [],
        "e102_key_summary": e102.get("summary", []) if e102 else [],
        "audit": {
            "note_zh": "E100/E102 不生成新长 CoT；E101 是有硬 token 上限的小样本敏感性诊断。",
        },
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# E100-E102 Batch/Mode Hidden Contrast / batch 与 thinking 模式机制审计（2026-04-29）",
        "",
        "## 说人话结论",
        "",
        "- E100 检查固定 token 序列在 batch=1/2/4 下 residual、MLP、token-mixer、logits 是否改变；这是为了排除 batch size 污染 hidden 机制结论。",
        "- E101 是小样本生成敏感性，不作为自然发生率；它只回答 batch size 会不会让现场生成内容不同。",
        "- E102 比较已有 Qwen thinking/non-thinking trace 的内容长度、收口情况、repair marker，以及同一 strict verifier hidden process-validity 读数。",
        "",
    ]
    if e100:
        lines += ["## E100 固定序列 batch 不变性", "", "| batch | component | n | min cosine | max rel L2 | max abs |", "|---:|---|---:|---:|---:|---:|"]
        for s in e100["summary"]:
            if s["batch_size"] == 1 or s["component"].endswith("residual_hidden_state") or s["component"] in {"logits", "34:mlp_output", "34:token_mixer_output"}:
                lines.append(f"| {s['batch_size']} | {s['component']} | {s['n']} | {fmt(s['min_cosine'])} | {fmt(s['max_relative_l2'])} | {fmt(s['max_abs'])} |")
        lines.append("")
    if e101:
        lines += ["## E101 小样本生成敏感性", "", "| batch | mode | n | mean tokens | hit max | final marker | final correct |", "|---:|---|---:|---:|---:|---:|---:|"]
        for s in e101["summary"]:
            lines.append(f"| {s['batch_size']} | {s['mode_label']} | {s['n']} | {fmt(s['mean_generated_tokens'])} | {fmt(s['hit_max_rate'])} | {fmt(s['final_marker_rate'])} | {s['final_correct']} |")
        lines.append("")
    if e102:
        lines += ["## E102 thinking vs non-thinking trace 读数", "", "| slice type | slice | n | mean tokens | hit max | accept | Yes-No |", "|---|---|---:|---:|---:|---:|---:|"]
        for s in e102["summary"]:
            if s["slice_type"] in {"generation_mode", "source", "all"}:
                lines.append(f"| {s['slice_type']} | {s['slice']} | {s['n']} | {fmt(s['mean_completion_tokens'])} | {fmt(s['hit_max_rate'])} | {fmt(s['accept_rate'])} | {fmt(s['mean_yes_minus_no'])} |")
        lines += ["", "### Paired same-task/same-variant deltas", "", "| task | variant | TG tokens | NG tokens | delta tokens | delta Yes-No | delta best residual |", "|---|---|---:|---:|---:|---:|---:|"]
        for p in e102.get("pairwise_same_task_variant", []):
            lines.append(f"| {p['task_id']} | {p['prompt_variant']} | {p['tg_tokens']} | {p['ng_tokens']} | {p['delta_tokens']} | {fmt(p['delta_yes_minus_no'])} | {fmt(p['delta_best_component_score'])} |")
        lines.append("")
    lines += [
        "## 边界",
        "",
        "- E100/E102 是 replay，不是新生成；它们适合做机制审计，不适合估计自然发生率。",
        "- E101 的 token 上限故意很低，目的是避免 endless thinking；hit-max 本身就是要记录的现象。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_JSON), "report": str(OUT_MD), "available": {k: result[k] for k in ["e100_available", "e101_available", "e102_available"]}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
