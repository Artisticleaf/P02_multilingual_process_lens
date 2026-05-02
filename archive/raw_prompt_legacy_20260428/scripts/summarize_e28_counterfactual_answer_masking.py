#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def fmt(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def read_labels(path: Path) -> dict[int, dict]:
    return {int(json.loads(line)["audit_idx"]): json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/E28_counterfactual_answer_masking_absolute_verifier")
    p.add_argument("--label-file", default="data/processed/e28_counterfactual_answer_masking_20260427.jsonl")
    p.add_argument("--out", default="reports/E28_counterfactual_answer_masking_summary.md")
    args = p.parse_args()
    labels = read_labels(Path(args.label_file))
    rows = []
    for path in sorted(Path(args.results_dir).glob("*_manual_trace_verifier.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["verifier_model_key"]
        for r in data["rows"]:
            lab = labels[int(r["audit_idx"])]
            rr = dict(r)
            rr.update(
                verifier=model,
                e28_variant=lab["e28_variant"],
                process_condition=lab["e28_process_condition"],
                answer_condition=lab["e28_answer_condition"],
            )
            rows.append(rr)
    models = sorted({r["verifier"] for r in rows})
    lines = [
        "# E28 Counterfactual Answer-Masking Summary / E28 反事实与答案遮蔽总结",
        "",
        f"Labels / 标签: `{args.label_file}`.",
        f"Results / 结果: `{args.results_dir}`.",
        "",
        "E28 holds the problem and most arithmetic text fixed, then changes only the local lexical process phrase and the final-answer line. / E28 固定题目和大部分算术文本，只改变局部词汇过程短语与最终答案行。",
        "",
        "## Overall / 总体",
        "",
        "| verifier | mode | prompt | n | acc | yes rate | process-invalid false accept | ACPI false accept | mean yes-no margin |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        for mode in ["process_only", "training_candidate"]:
            for prompt in ["en", "zh"]:
                g = [r for r in rows if r["verifier"] == model and r["mode"] == mode and r["prompt_lang"] == prompt]
                inv = [r for r in g if r["manual_process_valid"] is False]
                acpi = [r for r in g if r["is_acpi"]]
                lines.append(
                    f"| {model} | {mode} | {prompt} | {len(g)} | {fmt(sum(r['correct'] for r in g)/len(g))} | "
                    f"{fmt(sum(r['pred'] for r in g)/len(g))} | {fmt(sum(r['pred'] for r in inv)/len(inv))} | "
                    f"{fmt(sum(r['pred'] for r in acpi)/len(acpi))} | {fmt(mean(r['yes_minus_no_logprob'] for r in g))} |"
                )
    lines.extend([
        "",
        "## Process-Only Variant Rates / 只审过程的变体接受率",
        "",
        "| verifier | prompt | variant | yes rate | mean yes-no margin |",
        "|---|---|---|---:|---:|",
    ])
    variant_order = ["valid_correct", "invalid_correct", "valid_masked", "invalid_masked", "valid_wrong", "invalid_wrong"]
    for model in models:
        for prompt in ["en", "zh"]:
            for variant in variant_order:
                g = [
                    r
                    for r in rows
                    if r["verifier"] == model
                    and r["mode"] == "process_only"
                    and r["prompt_lang"] == prompt
                    and r["e28_variant"] == variant
                ]
                lines.append(f"| {model} | {prompt} | {variant} | {fmt(sum(r['pred'] for r in g)/len(g))} | {fmt(mean(r['yes_minus_no_logprob'] for r in g))} |")
    lines.extend([
        "",
        "## Lexical-Error Margin Effect / 词汇错误对边际的影响",
        "",
        "Negative delta means the invalid lexical phrase lowers the verifier's Yes-vs-No margin, even if it does not cross the rejection threshold. / delta 为负表示无效词汇短语降低了 verifier 的 Yes 相对 No 边际，即使没有越过拒绝阈值。",
        "",
        "| verifier | prompt | answer condition | valid yes | invalid yes | invalid-valid margin delta |",
        "|---|---|---|---:|---:|---:|",
    ])
    for model in models:
        for prompt in ["en", "zh"]:
            for answer in ["correct", "masked", "wrong"]:
                gv = [
                    r
                    for r in rows
                    if r["verifier"] == model
                    and r["mode"] == "process_only"
                    and r["prompt_lang"] == prompt
                    and r["process_condition"] == "valid"
                    and r["answer_condition"] == answer
                ]
                gi = [
                    r
                    for r in rows
                    if r["verifier"] == model
                    and r["mode"] == "process_only"
                    and r["prompt_lang"] == prompt
                    and r["process_condition"] == "invalid"
                    and r["answer_condition"] == answer
                ]
                delta = mean(r["yes_minus_no_logprob"] for r in gi) - mean(r["yes_minus_no_logprob"] for r in gv)
                lines.append(
                    f"| {model} | {prompt} | {answer} | {fmt(sum(r['pred'] for r in gv)/len(gv))} | "
                    f"{fmt(sum(r['pred'] for r in gi)/len(gi))} | {fmt(delta)} |"
                )
    lines.extend([
        "",
        "## Human-Readable Takeaways / 人话结论",
        "",
        "- The local lexical error almost always lowers the Yes-vs-No margin, so the verifier state is not completely blind to the error. / 局部词汇错误几乎总会压低 Yes-vs-No 边际，说明 verifier 状态并非完全看不见错误。",
        "- The margin reduction often does not cross zero, especially when the final answer remains correct; this is the threshold/objective mismatch. / 但边际下降经常没有跨过 0，尤其最终答案仍正确时；这就是阈值/目标错配。",
        "- Wrong or missing final-answer lines change process-only margins, so even a prompt that says 'judge process only' still partly uses answer-format evidence. / 错误或缺失答案行会改变只审过程的边际，说明“只审过程”的提示仍会混入答案/格式证据。",
    ])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; rows={len(rows)} models={len(models)}")


if __name__ == "__main__":
    main()
