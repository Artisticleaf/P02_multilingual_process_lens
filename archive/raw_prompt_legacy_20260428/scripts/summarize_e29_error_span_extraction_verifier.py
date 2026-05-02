#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/E29_error_span_extraction_verifier")
    p.add_argument("--out", default="reports/E29_error_span_extraction_verifier_summary.md")
    args = p.parse_args()
    rows = []
    for path in sorted(Path(args.results_dir).glob("*_error_span_extraction_verifier.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data["rows"]:
            rr = dict(r)
            rr["verifier"] = data["verifier_model_key"]
            rows.append(rr)
    models = sorted({r["verifier"] for r in rows})
    lines = [
        "# E29 Error-Span Extraction Verifier Summary / E29 错误 span 抽取 verifier 总结",
        "",
        f"Results / 结果目录: `{args.results_dir}`.",
        "",
        "E29 asks a verifier to name the first invalid phrase before, or together with, a process-validity decision. / E29 要求 verifier 先指出第一处无效短语，或同时给出过程是否有效的判断。",
        "",
        "## Overall / 总体",
        "",
        "| verifier | mode | prompt | n | span acc | invalid span hit | valid NONE rate | judgement coverage | judgement acc | invalid reject rate | located-but-accepted |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        for mode in ["locate_only", "locate_then_judge"]:
            for prompt in ["en", "zh"]:
                g = [r for r in rows if r["verifier"] == model and r["mode"] == mode and r["prompt_lang"] == prompt]
                inv = [r for r in g if r["manual_process_valid"] is False]
                val = [r for r in g if r["manual_process_valid"] is True]
                judged = [r for r in g if r["judge_pred_process_valid"] is not None]
                inv_judged = [r for r in inv if r["judge_pred_process_valid"] is not None]
                located_accept = [r for r in inv_judged if r["span_correct"] and r["judge_pred_process_valid"] is True]
                lines.append(
                    f"| {model} | {mode} | {prompt} | {len(g)} | {fmt(sum(r['span_correct'] for r in g)/len(g))} | "
                    f"{fmt(sum(r['span_correct'] for r in inv)/len(inv))} | {fmt(sum(r['span_correct'] for r in val)/len(val))} | "
                    f"{fmt(len(judged)/len(g))} | "
                    f"{fmt(sum(r['judge_correct'] for r in judged)/len(judged) if judged else None)} | "
                    f"{fmt(sum(r['judge_pred_process_valid'] is False for r in inv_judged)/len(inv_judged) if inv_judged else None)} | "
                    f"{len(located_accept)} |"
                )
    lines.extend([
        "",
        "## Invalid-Trace Localization by Task / 按任务看无效 trace 定位",
        "",
        "| verifier | prompt | task | invalid n | span hit | reject coverage | reject rate | located-but-accepted n |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ])
    for model in models:
        for prompt in ["en", "zh"]:
            for task in sorted({r["task_id"] for r in rows}):
                g = [
                    r
                    for r in rows
                    if r["verifier"] == model
                    and r["mode"] == "locate_then_judge"
                    and r["prompt_lang"] == prompt
                    and r["task_id"] == task
                    and r["manual_process_valid"] is False
                ]
                if not g:
                    continue
                judged = [r for r in g if r["judge_pred_process_valid"] is not None]
                lines.append(
                    f"| {model} | {prompt} | {task} | {len(g)} | {fmt(sum(r['span_correct'] for r in g)/len(g))} | "
                    f"{fmt(len(judged)/len(g))} | {fmt(sum(r['judge_pred_process_valid'] is False for r in judged)/len(judged) if judged else None)} | "
                    f"{sum(1 for r in judged if r['span_correct'] and r['judge_pred_process_valid'] is True)} |"
                )
    lines.extend([
        "",
        "## Located But Accepted Examples / 已定位但仍接受的例子",
        "",
        "| verifier | idx | prompt | task | output excerpt |",
        "|---|---:|---|---|---|",
    ])
    count = 0
    for r in rows:
        if r["manual_process_valid"] is False and r["mode"] == "locate_then_judge" and r["span_correct"] and r["judge_pred_process_valid"] is True:
            excerpt = r["raw_output"].replace("\n", " ").replace("|", "/")[:180]
            lines.append(f"| {r['verifier']} | {r['audit_idx']} | {r['prompt_lang']} | {r['task_id']} | {excerpt} |")
            count += 1
    if count == 0:
        lines.append("|  |  |  |  | No parsed cases. / 没有解析到该类样例。 |")
    lines.extend([
        "",
        "## Human-Readable Takeaways / 人话结论",
        "",
        "- Error-span prompting is more informative than absolute Yes/No because it exposes false positives, wrong rationales, and parse/template failures. / 错误 span 提示比绝对 Yes/No 更有信息量，因为它暴露了误报、错误理由和模板解析失败。",
        "- Qwen-family locate-then-judge prompts detect the `75% discount` trap most reliably, but the `打八折=支付75%` trap remains hard. / Qwen 系在 locate-then-judge 下最稳定识别 `75% discount` 陷阱，但 `打八折=支付75%` 仍难。",
        "- Some models can name a suspicious span yet still mark the process valid, supporting the threshold/objective mismatch story; generation-format instability is a boundary for this experiment. / 有些模型能指出可疑 span 却仍判过程有效，支持阈值/目标错配；生成格式不稳定是本实验边界。",
    ])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; rows={len(rows)} models={len(models)}")


if __name__ == "__main__":
    main()
