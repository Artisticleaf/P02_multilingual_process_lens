#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def fmt(x):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    abs_dir = Path("results/E30_non_discount_absolute_verifier")
    con_dir = Path("results/E30_non_discount_contrastive_verifier")
    lines = [
        "# E30 Non-Discount Verifier Summary / E30 非折扣 verifier 总结",
        "",
        "Subset / 子集: `data/processed/e30_non_discount_verifier_subset_20260427.jsonl` contains one valid sibling and one ACPI sibling for the inequality-boundary row. / 子集包含一个有效 sibling 与一个不等式边界 ACPI sibling。",
        "",
        "## Absolute Verifier / 绝对式 verifier",
        "",
        "| verifier | mode | prompt | n | acc | yes rate | ACPI false accept | mean margin |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for path in sorted(abs_dir.glob("*_manual_trace_verifier.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["verifier_model_key"]
        for s in data["summary"]:
            if s["slice"] == "all":
                lines.append(
                    f"| {model} | {s['mode']} | {s['prompt_lang']} | {s['n']} | {fmt(s['accuracy'])} | {fmt(s['yes_rate'])} | {fmt(s['acpi_false_accept_rate'])} | {fmt(s['mean_margin'])} |"
                )
    lines.extend([
        "",
        "## Contrastive Verifier / 对比式 verifier",
        "",
        "| verifier | rows | acc | mean target margin | order behavior |",
        "|---|---:|---:|---:|---|",
    ])
    for path in sorted(con_dir.glob("*_contrastive_acpi_verifier.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        model = data["verifier_model_key"]
        overall = next(s for s in data["summary"] if s["slice_type"] == "all")
        preds = ", ".join(f"{r['prompt_lang']}/{r['order']}->{r['pred']}" for r in data["rows"])
        lines.append(f"| {model} | {len(data['rows'])} | {fmt(overall['acc'])} | {fmt(overall['mean_margin'])} | {preds} |")
    lines.extend([
        "",
        "## Human-Readable Takeaways / 人话结论",
        "",
        "- All four absolute verifiers accepted the non-discount ACPI row under both English and Chinese prompts. / 四个绝对式 verifier 在中英提示下都接受了这条非折扣 ACPI。",
        "- Contrastive verification was mixed: Qwen3.5-9B selected the invalid sibling in both orders, while Gemma4 and Qwen3.5-27B showed A-position bias and Qwen14 showed B-position bias. / 对比式结果混合：Qwen3.5-9B 两种顺序都能选中无效 sibling，Gemma4 与 Qwen3.5-27B 有 A 位置偏置，Qwen14 有 B 位置偏置。",
        "- This mirrors S6: absolute Yes/No is over-permissive, while sibling comparison can reveal signal but must be order-balanced. / 这与 S6 一致：绝对 Yes/No 过宽，对比式能暴露信号但必须做顺序平衡。",
    ])
    out = Path("reports/E30_non_discount_verifier_summary.md")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
