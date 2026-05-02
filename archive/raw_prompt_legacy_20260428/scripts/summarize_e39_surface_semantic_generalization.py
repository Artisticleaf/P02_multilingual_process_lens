#!/usr/bin/env python3
"""Summarize E39 controlled surface-semantic generalization verifier results."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def fmt(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_results(results_dir: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted(results_dir.glob("*_manual_trace_verifier.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "e39_surface_semantic_generalization" not in str(data.get("manual_jsonl", "")):
            # Keep compatibility if only E39 files are in the directory, but skip obvious non-E39 inputs.
            pass
        data["_path"] = str(path)
        out.append(data)
    return out


def safe_rate(rows: list[dict[str, Any]], pred_value: bool = True) -> float | None:
    if not rows:
        return None
    return sum(1 for r in rows if bool(r["pred"]) == pred_value) / len(rows)


def summarize(results: list[dict[str, Any]], labels: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    label_by_idx = {r["audit_idx"]: r for r in labels}
    lines = [
        "# E39 Surface-Semantic Generalization Summary / E39 表层语义泛化实验汇总",
        "",
        f"Created / 创建时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "E39 is a controlled diagnostic set with 12 surface-semantic trap families and 6 variants per family. / E39 是受控诊断集，包含 12 类表层语义陷阱，每类 6 个变体。",
        "The central slice is `invalid_correct`: the local process semantics is wrong but the final answer is correct. / 核心切片是 `invalid_correct`：局部过程语义错误，但最终答案正确。",
        "",
        "## Overall verifier behavior / 整体 verifier 行为",
        "",
        "| verifier | mode | prompt | n | accuracy | yes rate | process-invalid false accept | ACPI false accept | mean margin |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    aggregate: dict[str, Any] = {"models": {}}
    for data in results:
        model = data["verifier_model_key"]
        aggregate["models"].setdefault(model, {"input_path": data.get("_path")})
        for s in data.get("summary", []):
            if s["slice"] != "all":
                continue
            lines.append(
                f"| {model} | {s['mode']} | {s['prompt_lang']} | {s['n']} | {fmt(s['accuracy'])} | {fmt(s['yes_rate'])} | "
                f"{fmt(s['process_invalid_false_accept_rate'])} | {fmt(s['acpi_false_accept_rate'])} | {fmt(s['mean_margin'])} |"
            )
        rows = data.get("rows", [])
        model_detail = {}
        for mode in ["process_only", "training_candidate"]:
            for lang in ["en", "zh"]:
                sub = [r for r in rows if r["mode"] == mode and r["prompt_lang"] == lang]
                acpi = [r for r in sub if label_by_idx[r["audit_idx"]].get("e39_variant") == "invalid_correct"]
                model_detail[f"{mode}_{lang}_acpi_accept"] = safe_rate(acpi, True)
        aggregate["models"][model].update(model_detail)
    lines.extend(["", "## ACPI task-level false accepts / ACPI 任务级误接受", ""])
    for data in results:
        model = data["verifier_model_key"]
        rows = data.get("rows", [])
        lines.extend([f"### {model}", ""])
        lines.append("| task / 任务 | input | process-only EN | process-only ZH | training-candidate EN | training-candidate ZH | margin EN/ZH process-only |")
        lines.append("|---|---|---:|---:|---:|---:|---|")
        acpi_by_task: dict[str, dict[str, Any]] = {}
        for r in rows:
            lab = label_by_idx[r["audit_idx"]]
            if lab.get("e39_variant") != "invalid_correct":
                continue
            item = acpi_by_task.setdefault(lab["task_id"], {"label": lab, "rows": []})
            item["rows"].append(r)
        for task, item in sorted(acpi_by_task.items()):
            lab = item["label"]
            vals = {}
            margins = {}
            for r in item["rows"]:
                key = (r["mode"], r["prompt_lang"])
                vals[key] = bool(r["pred"])
                margins[key] = r["yes_minus_no_logprob"]
            lines.append(
                f"| {task} | {lab['input_lang']} | {vals.get(('process_only','en'))} | {vals.get(('process_only','zh'))} | "
                f"{vals.get(('training_candidate','en'))} | {vals.get(('training_candidate','zh'))} | "
                f"{fmt(margins.get(('process_only','en')))} / {fmt(margins.get(('process_only','zh')))} |"
            )
        lines.append("")
    lines.extend([
        "## Plain-language read / 人话结论",
        "",
        "- If a verifier accepts many `invalid_correct` rows, it is using the correct final answer or downstream self-correction too strongly relative to the local process error. / 如果 verifier 接受很多 `invalid_correct` 行，说明它过度依赖最终答案或后续自我修正，而没有足够惩罚局部过程错误。",
        "- If `training_candidate` reduces acceptance relative to `process_only`, the same model has some usable evidence but the absolute process-only objective/threshold is too permissive. / 如果 `training_candidate` 比 `process_only` 更少接受，说明同一模型有可用证据，但绝对只审过程目标/阈值太宽。",
        "- Task-level rows identify which semantic families should be promoted to hidden-state patching in E40/E41. / 任务级表格用于挑选 E40/E41 hidden-state patch 的候选语义族。",
    ])
    return lines, aggregate


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default=str(PROJECT / "results/E39_surface_semantic_generalization_absolute_verifier"))
    p.add_argument("--label-file", default=str(PROJECT / "data/processed/e39_surface_semantic_generalization_20260428.jsonl"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/E39_surface_semantic_generalization_summary_20260428.md"))
    p.add_argument("--out-json", default=str(PROJECT / "results/E39_surface_semantic_generalization_absolute_verifier/summary.json"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    results = load_results(Path(args.results_dir))
    if not results:
        raise SystemExit(f"No verifier result files in {args.results_dir}")
    labels = load_jsonl(Path(args.label_file))
    lines, aggregate = summarize(results, labels)
    Path(args.out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps({"aggregate": aggregate}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out_md} and {args.out_json}")


if __name__ == "__main__":
    main()
