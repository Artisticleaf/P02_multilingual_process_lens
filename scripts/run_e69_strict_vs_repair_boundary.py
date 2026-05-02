#!/usr/bin/env python3
"""E69 strict-vs-repair-aware trace-validity boundary audit.

The project deliberately uses a *strict trace-selection* label: a visible false
local step makes the trace process-invalid even if a later sentence reaches the
right answer.  E69 audits how many controlled invalid-correct traces also
contain an explicit repair/override marker, because that affects how the paper
should phrase the claim.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT / "results/E69_strict_vs_repair_boundary"
REPORT = PROJECT / "reports/E69_STRICT_VS_REPAIR_BOUNDARY_20260429.md"
AUDIT = PROJECT / "reports/E69_STRICT_VS_REPAIR_BOUNDARY_AUDIT_20260429.json"


DATASETS = {
    "E42": PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl",
    "E54": PROJECT / "data/processed/e54_parameterized_no_leak_generalization_20260428.jsonl",
    "E61": PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl",
}

REPAIR_PATTERNS = [
    r"\bbut\b",
    r"\bhowever\b",
    r"\bstill\b",
    r"\bactual(?:ly)?\b",
    r"\bcorrect(?:ly| conversion| relation)?\b",
    r"\busing the actual\b",
    r"\busing the correct\b",
    r"\bfor the requested\b",
    r"\bfor an increase\b",
    r"\bwith the correct\b",
    r"\bthen using\b",
    r"可是",
    r"但是",
    r"实际",
    r"正确",
    r"应当",
    r"应为",
    r"才是",
    r"按.*实际",
    r"按.*正确",
    r"\bDanshi\b",
    r"\bzhengque\b",
    r"\bBut\b",
]
REPAIR_RE = re.compile("|".join(f"(?:{p})" for p in REPAIR_PATTERNS), re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def classify(row: dict[str, Any]) -> dict[str, Any]:
    completion = row.get("completion", "")
    error_span = row.get("error_span") or ""
    repair_matches = [m.group(0) for m in REPAIR_RE.finditer(completion)]
    error_pos = completion.find(error_span) if error_span else -1
    first_repair_pos = min((m.start() for m in REPAIR_RE.finditer(completion)), default=-1)
    repair_after_error = bool(repair_matches) and (error_pos < 0 or first_repair_pos > error_pos)
    # This is deliberately conservative: it does not relabel strict-invalid
    # rows as valid; it only says a repair-aware reader may see an override.
    repair_boundary = "explicit_repair_or_override" if repair_after_error else "no_clear_repair_marker"
    return {
        "repair_boundary": repair_boundary,
        "repair_marker_examples": repair_matches[:4],
        "error_span_found": bool(error_span and error_span in completion),
        "error_pos": error_pos,
        "first_repair_pos": first_repair_pos,
    }


def pct(num: int, den: int) -> str:
    return f"{num / den:.3f}" if den else "NA"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    checks = []
    for dataset, path in DATASETS.items():
        exists = path.exists()
        checks.append({"check": f"{dataset} data exists", "ok": exists, "detail": str(path.relative_to(PROJECT))})
        if not exists:
            continue
        for row in load_jsonl(path):
            if not row.get("manual_final_correct") or row.get("manual_process_valid"):
                continue
            c = classify(row)
            rows.append(
                {
                    "dataset": dataset,
                    "audit_idx": row.get("audit_idx"),
                    "task_id": row.get("task_id"),
                    "family": row.get("family") or row.get("task_id"),
                    "route_id": row.get("route_id") or row.get("route"),
                    "strict_process_valid": False,
                    "final_correct": True,
                    "repair_boundary": c["repair_boundary"],
                    "repair_marker_examples": c["repair_marker_examples"],
                    "error_span_found": c["error_span_found"],
                    "error_span": row.get("error_span", ""),
                    "completion": row.get("completion", ""),
                }
            )

    overall = Counter()
    by_dataset: dict[str, Counter] = defaultdict(Counter)
    by_family: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        for bucket in [overall, by_dataset[row["dataset"]], by_family[f"{row['dataset']}::{row['family']}"]]:
            bucket["n_strict_acpi"] += 1
            bucket[row["repair_boundary"]] += 1
            bucket["error_span_found"] += int(row["error_span_found"])

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "rows": rows,
        "overall": dict(overall),
        "by_dataset": {k: dict(v) for k, v in sorted(by_dataset.items())},
        "by_family": {k: dict(v) for k, v in sorted(by_family.items())},
        "scope_note_zh": "E69 不改变官方 strict 标签；它审计 strict-invalid trace 中是否含有后续修复/覆盖语句，用于限定论文 claim。",
    }
    out_path = OUT_DIR / "e69_strict_vs_repair_boundary.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(c["ok"] for c in checks) and bool(rows),
        "checks": checks,
        "result_path": str(out_path.relative_to(PROJECT)),
        "logic_boundary_zh": "本审计只区分 strict trace-selection 与 repair-aware 阅读口径；不把人工 label 或错误 span 放入任何 verifier prompt。",
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E69 Strict vs Repair-Aware Boundary / E69 严格 trace-selection 与修复口径边界（2026-04-29）",
        "",
        f"- Result / 结果：`{out_path.relative_to(PROJECT)}`",
        f"- Audit / 审计：`{AUDIT.relative_to(PROJECT)}`",
        "- Plain language / 说人话：我们现在要非常诚实地区分两件事：一条 trace 里出现了错误局部步骤，和这条 trace 后面有没有把错误纠正回来。前者对应严格过程筛选，后者对应 repair-aware 阅读。",
        "",
        "## Overall / 总体",
        "",
        "| strict ACPI rows | explicit repair/override | no clear repair marker | error span found in text |",
        "|---:|---:|---:|---:|",
        f"| {overall['n_strict_acpi']} | {overall['explicit_repair_or_override']} ({pct(overall['explicit_repair_or_override'], overall['n_strict_acpi'])}) | {overall['no_clear_repair_marker']} ({pct(overall['no_clear_repair_marker'], overall['n_strict_acpi'])}) | {overall['error_span_found']} ({pct(overall['error_span_found'], overall['n_strict_acpi'])}) |",
        "",
        "## By Dataset / 按数据集",
        "",
        "| dataset | strict ACPI | explicit repair/override | no clear repair marker |",
        "|---|---:|---:|---:|",
    ]
    for key, c in sorted(by_dataset.items()):
        n = c["n_strict_acpi"]
        lines.append(f"| `{key}` | {n} | {c['explicit_repair_or_override']} ({pct(c['explicit_repair_or_override'], n)}) | {c['no_clear_repair_marker']} ({pct(c['no_clear_repair_marker'], n)}) |")
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- Strict claim / 严格主张：E42/E54/E61 的 invalid-correct rows 仍然是 strict process-invalid，因为可见 trace 中出现了错误数学/语义/执行断言。严格过程监督、可审计证明、教材解答筛选等场景确实会要求这样的 trace 被拒绝。 / These rows remain strict process-invalid because a visible false local assertion appears in the trace.",
        "- Repair-aware boundary / 修复口径边界：很多 controlled trace 也包含后续纠正或覆盖语句；如果某个 verifier 的目标是“最终保留下来的推理是否正确”，它接受这些 trace 并不一定是纯失败。 / Many controlled traces also contain later corrections; a repair-aware verifier may accept them for a different objective.",
        "- Paper wording / 论文表述：主文应使用 `strict trace-selection risk`，并单独报告 E57 的 `unrepaired ACPI`。不能把所有 controlled strict-invalid examples 都说成“未修复乱推碰巧对”。 / The paper should say strict trace-selection risk and separately report unrepaired ACPI; do not imply all controlled examples are unrepaired.",
        "- Why this still matters / 为什么仍重要：训练数据筛选、过程奖励模型和可解释 verifier 经常要求每个可见步骤都可靠；一个 false step 即使后来被改正，也会污染可监督过程数据和 sibling/pointwise 选择目标。 / This still matters because process-supervision filters often require every visible step to be reliable.",
        "",
        "## Examples / 示例",
        "",
        "| dataset | task | error span | repair markers |",
        "|---|---|---|---|",
    ]
    for row in rows[:10]:
        markers = ", ".join(row["repair_marker_examples"]) or "NA"
        lines.append(f"| `{row['dataset']}` | `{row['task_id']}` | `{row['error_span'][:80]}` | `{markers}` |")
    lines += ["", "## Audit / 审计", ""]
    for c in checks:
        lines.append(f"- {'PASS' if c['ok'] else 'FAIL'}: {c['check']} — {c['detail']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(out_path), "report": str(REPORT), "audit": str(AUDIT), "rows": len(rows)}, ensure_ascii=False, indent=2))
    if not audit["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
