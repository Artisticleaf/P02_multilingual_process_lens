#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean


VARIANT_ORDER = [
    "valid_correct",
    "invalid_correct",
    "valid_masked",
    "invalid_masked",
    "valid_wrong",
    "invalid_wrong",
]


def fmt(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def read_labels(path: Path) -> dict[int, dict]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[int(row["audit_idx"])] = row
    return out


def yes_rate(rows: list[dict]) -> float | None:
    if not rows:
        return None
    return sum(bool(r["pred"]) for r in rows) / len(rows)


def margin(rows: list[dict]) -> float | None:
    if not rows:
        return None
    return mean(float(r["yes_minus_no_logprob"]) for r in rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/E31_non_discount_counterfactual_absolute_verifier")
    p.add_argument("--label-file", default="data/processed/e31_non_discount_counterfactual_20260427.jsonl")
    p.add_argument("--out", default="reports/E31_non_discount_counterfactual_summary.md")
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
                e31_variant=lab["e31_variant"],
                process_condition=lab["e31_process_condition"],
                answer_condition={"gold": "correct"}.get(lab["e31_answer_condition"], lab["e31_answer_condition"]),
                known_error_spans=lab.get("known_error_spans", []),
            )
            rows.append(rr)

    models = sorted({r["verifier"] for r in rows})
    tasks = sorted({r["task_id"] for r in rows})
    lines = [
        "# E31 Non-Discount Counterfactual Summary / E31 非折扣反事实总结",
        "",
        f"Labels / 标签: `{args.label_file}`.",
        f"Results / 结果: `{args.results_dir}`.",
        "",
        "E31 uses hand-controlled siblings for five non-discount traps. Each task has a valid process and an invalid local process phrase, crossed with correct, masked, and wrong final-answer lines. / E31 为 5 类非折扣陷阱构造人工受控 sibling：每题有有效过程和局部无效过程短语，并与正确、遮蔽、错误三种最终答案行交叉。",
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
                    f"{fmt(yes_rate(g))} | {fmt(yes_rate(inv))} | {fmt(yes_rate(acpi))} | {fmt(margin(g))} |"
                )

    lines.extend(
        [
            "",
            "## Process-Only Variant Rates / 只审过程的变体接受率",
            "",
            "| verifier | prompt | variant | yes rate | mean yes-no margin |",
            "|---|---|---|---:|---:|",
        ]
    )
    for model in models:
        for prompt in ["en", "zh"]:
            for variant in VARIANT_ORDER:
                g = [
                    r
                    for r in rows
                    if r["verifier"] == model
                    and r["mode"] == "process_only"
                    and r["prompt_lang"] == prompt
                    and r["e31_variant"] == variant
                ]
                lines.append(f"| {model} | {prompt} | {variant} | {fmt(yes_rate(g))} | {fmt(margin(g))} |")

    lines.extend(
        [
            "",
            "## Local-Error Margin Effect / 局部错误对边际的影响",
            "",
            "Negative delta means the invalid phrase lowers the verifier's Yes-vs-No margin relative to the valid sibling. / delta 为负表示无效短语相对有效 sibling 压低 verifier 的 Yes 相对 No 边际。",
            "",
            "| verifier | prompt | answer condition | valid yes | invalid yes | invalid-valid margin delta |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
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
                delta = None if not gv or not gi else margin(gi) - margin(gv)
                lines.append(f"| {model} | {prompt} | {answer} | {fmt(yes_rate(gv))} | {fmt(yes_rate(gi))} | {fmt(delta)} |")

    lines.extend(
        [
            "",
            "## ACPI False Accept by Trap / 按陷阱看 ACPI 误接受",
            "",
            "This table uses only `invalid_correct` rows: the final answer is right but one local process phrase is wrong. / 本表只看 `invalid_correct` 行：最终答案正确，但局部过程短语错误。",
            "",
            "| prompt | task | accepted / total | accept rate | mean yes-no margin | bad phrase in the controlled trace |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for prompt in ["en", "zh"]:
        for task in tasks:
            g = [
                r
                for r in rows
                if r["mode"] == "process_only"
                and r["prompt_lang"] == prompt
                and r["manual_risk"] == "e31_invalid_correct"
                and r["task_id"] == task
            ]
            spans = sorted({s for r in g for s in r.get("known_error_spans", [])})
            lines.append(
                f"| {prompt} | {task} | {sum(bool(r['pred']) for r in g)} / {len(g)} | {fmt(yes_rate(g))} | {fmt(margin(g))} | {', '.join(spans)} |"
            )

    lines.extend(
        [
            "",
            "## Human-Readable Takeaways / 人话结论",
            "",
            "- E31 confirms that the phenomenon is not discount-only: controlled ratio-denominator, inequality-boundary, unit, geometry, and combinatorics traps can produce answer-correct but process-invalid rows. / E31 证明现象不只属于折扣题：受控的比例分母、边界量词、单位、几何和组合陷阱都能构成“答案对但过程错”的行。",
            "- The model split is scientifically useful: Gemma4 and Qwen3.5-27B still over-accept heavily; Qwen14 is much stricter on these controlled non-discount errors. / 模型分化本身有价值：Gemma4 与 Qwen3.5-27B 仍明显过度接受；Qwen14 对这些受控非折扣错误严格得多。",
            "- The invalid phrase usually lowers the Yes-vs-No margin even when it is still accepted, so the verifier often has graded evidence but the final threshold/objective does not use it cleanly. / 无效短语通常会压低 Yes-vs-No 边际，即使最终仍被接受；这说明 verifier 常有连续证据，但最终阈值/目标没有干净使用它。",
            "- Natural prevalence and controlled possibility must be separated: E30 found few natural non-discount ACPI rows, while E31 shows many controlled non-discount ACPI rows are accepted by verifiers. / 需要区分自然发生率和受控可行性：E30 的自然非折扣 ACPI 较少，E31 则显示受控非折扣 ACPI 仍常被 verifier 接受。",
        ]
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}; rows={len(rows)} models={len(models)}")


if __name__ == "__main__":
    main()
