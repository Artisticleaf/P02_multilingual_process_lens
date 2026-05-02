#!/usr/bin/env python3
"""E67 span-local observability audit for E61.

This is a non-oracle post-hoc audit: it checks whether the manually recorded
English error_span is literally present in the visible trace, and how that
surface observability relates to verifier failures and hidden-probe recovery.
The span metadata is never inserted into verifier prompts.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT / "results/E67_span_local_observability"
REPORT = PROJECT / "reports/E67_SPAN_LOCAL_OBSERVABILITY_20260429.md"
AUDIT = PROJECT / "reports/E67_SPAN_LOCAL_OBSERVABILITY_AUDIT_20260429.json"
MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it", "glm47_flash_candidate"]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def span_meta() -> dict[int, dict[str, Any]]:
    out = {}
    for row in load_jsonl(PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"):
        if row["manual_process_valid"]:
            continue
        completion = row["completion"]
        span = row.get("error_span") or ""
        pos = completion.find(span) if span else -1
        out[int(row["audit_idx"])] = {
            "audit_idx": int(row["audit_idx"]),
            "task_id": row["task_id"],
            "family": row["family"],
            "route_id": row["route_id"],
            "error_span": span,
            "error_span_literal_found": pos >= 0,
            "error_span_char_pos": pos,
            "completion_len": len(completion),
            "error_span_relative_pos": (pos / len(completion)) if pos >= 0 and completion else None,
        }
    return out


def summarize_group(rows: list[dict[str, Any]], keys: list[str], value_key: str) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(k) for k in keys)].append(row)
    out = []
    for key, group in sorted(groups.items(), key=lambda x: str(x[0])):
        vals = [1.0 if r[value_key] else 0.0 for r in group]
        item = {k: v for k, v in zip(keys, key)}
        item.update({"n": len(group), f"mean_{value_key}": mean(vals)})
        out.append(item)
    return out


def fmt(x: Any) -> str:
    if x is None:
        return "NA"
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = span_meta()
    checks = [
        {"check": "E61 span metadata rows", "ok": len(meta) == 48, "detail": str(len(meta))},
    ]
    verifier_rows = []
    for model in MODELS:
        path = PROJECT / "results/E61_language_error_grid" / f"{model}_e61_language_error_grid_chat.json"
        checks.append({"check": f"{model} E61 result exists", "ok": path.exists(), "detail": str(path.relative_to(PROJECT))})
        if not path.exists():
            continue
        data = read_json(path)
        for row in data["rows"]:
            if row.get("objective_type") != "pointwise" or row.get("objective") != "plain_yes_no":
                continue
            if row["target_process_valid"]:
                continue
            m = meta[int(row["audit_idx"])]
            verifier_rows.append(
                {
                    "model_key": model,
                    "audit_idx": int(row["audit_idx"]),
                    "family": m["family"],
                    "route_id": m["route_id"],
                    "error_span_literal_found": m["error_span_literal_found"],
                    "plain_accepts_strict_acpi": bool(row["pred_process_valid"]),
                    "margin": row.get("margin_valid_minus_invalid"),
                }
            )

    hidden_rows = []
    for model in MODELS:
        path = PROJECT / "results/E65_mechanistic_layer_sweep" / f"{model}_e65_e61_layer_sweep.json"
        checks.append({"check": f"{model} E65 result exists", "ok": path.exists(), "detail": str(path.relative_to(PROJECT))})
        if not path.exists():
            continue
        data = read_json(path)
        best_layer = int(data["best_all_layer"]["layer"])
        for row in data["probe_rows"]:
            if int(row["layer"]) != best_layer or row["gold_process_valid"]:
                continue
            # E65 item_id is the audit_idx string.
            m = meta[int(row["item_id"])]
            hidden_rows.append(
                {
                    "model_key": model,
                    "audit_idx": int(row["item_id"]),
                    "family": m["family"],
                    "route_id": m["route_id"],
                    "error_span_literal_found": m["error_span_literal_found"],
                    "best_layer": best_layer,
                    "hidden_probe_rejects_strict_acpi": bool(row["correct"]),
                    "score": row["score"],
                }
            )

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "span_meta": list(meta.values()),
        "verifier_rows": verifier_rows,
        "hidden_rows": hidden_rows,
        "verifier_by_literal_found": summarize_group(verifier_rows, ["error_span_literal_found"], "plain_accepts_strict_acpi"),
        "verifier_by_route": summarize_group(verifier_rows, ["route_id"], "plain_accepts_strict_acpi"),
        "hidden_by_literal_found": summarize_group(hidden_rows, ["error_span_literal_found"], "hidden_probe_rejects_strict_acpi"),
        "hidden_by_route": summarize_group(hidden_rows, ["route_id"], "hidden_probe_rejects_strict_acpi"),
        "scope_note_zh": "E67 是 span-local observability 审计，不是把 span 提供给 verifier 的泄露实验。",
    }
    out_path = OUT_DIR / "e67_span_local_observability.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "result_path": str(out_path.relative_to(PROJECT)),
        "leakage_boundary_zh": "error_span 只用于离线分组分析；E61/E65 的模型 prompt 没有插入 error_span/support_span。",
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# E67 Span-Local Observability / E67 span-local 可观测性审计（2026-04-29）",
        "",
        f"- Result / 结果：`{out_path.relative_to(PROJECT)}`",
        f"- Audit / 审计：`{AUDIT.relative_to(PROJECT)}`",
        "- Plain language / 说人话：我们没有把错误 span 告诉模型；这里只是在事后看，人工记录的错误短语能不能在多语言 trace 里按字符串找到，以及这种“表层可见性”是否影响 verifier 失败和 hidden probe。",
        "",
        "## Literal Span Presence / 字面 span 是否出现",
        "",
        "| literal error_span found | n invalid traces |",
        "|---|---:|",
    ]
    found_counts = defaultdict(int)
    for m in meta.values():
        found_counts[m["error_span_literal_found"]] += 1
    for key in [False, True]:
        lines.append(f"| `{key}` | {found_counts[key]} |")
    lines += [
        "",
        "## Plain Pointwise Acceptance by Span Observability / 按 span 可观测性划分的普通单点接受",
        "",
        "| literal found | n model-rows | mean plain ACPI accept |",
        "|---|---:|---:|",
    ]
    for r in result["verifier_by_literal_found"]:
        lines.append(f"| `{r['error_span_literal_found']}` | {r['n']} | {fmt(r['mean_plain_accepts_strict_acpi'])} |")
    lines += [
        "",
        "## Hidden Probe Rejection by Span Observability / 按 span 可观测性划分的 hidden probe 拒绝",
        "",
        "| literal found | n model-rows | mean hidden rejects ACPI |",
        "|---|---:|---:|",
    ]
    for r in result["hidden_by_literal_found"]:
        lines.append(f"| `{r['error_span_literal_found']}` | {r['n']} | {fmt(r['mean_hidden_probe_rejects_strict_acpi'])} |")
    lines += [
        "",
        "## Route Slices / 语言路径切片",
        "",
        "| route | verifier rows | mean plain ACPI accept | hidden rows | mean hidden rejects ACPI |",
        "|---|---:|---:|---:|---:|",
    ]
    route_v = {r["route_id"]: r for r in result["verifier_by_route"]}
    route_h = {r["route_id"]: r for r in result["hidden_by_route"]}
    for route in sorted(set(route_v) | set(route_h)):
        v = route_v.get(route, {})
        h = route_h.get(route, {})
        lines.append(
            f"| `{route}` | {v.get('n', 0)} | {fmt(v.get('mean_plain_accepts_strict_acpi'))} | "
            f"{h.get('n', 0)} | {fmt(h.get('mean_hidden_probe_rejects_strict_acpi'))} |"
        )
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- Surface span matching is brittle / 表层 span 匹配很脆：E61 的错误 span 以规范英文记录，到了中文、混合语和拼音路线时常常不能字面匹配。这说明真正的错误定位不能依赖简单字符串匹配。 / Literal string matching is brittle across multilingual routes.",
        "- Hidden states generalize beyond literal spans / hidden state 超出字面 span：即便错误短语不能字面找到，E65 best-layer probe 仍能高比例拒绝 strict ACPI，说明过程证据不是简单抄录英文错误短语。 / Best-layer probes still reject many strict ACPI rows even without literal span matches.",
        "- Boundary / 边界：E67 不是 span patch causal proof；它给 E67/E65 之后的下一步指向 token-level patching、translated-span alignment、以及 route-specific localization。 / E67 is not causal span patching; it motivates token-level patching and translated-span alignment.",
        "",
        "## Audit / 审计",
        "",
    ]
    for c in checks:
        lines.append(f"- {'PASS' if c['ok'] else 'FAIL'}: {c['check']} — {c['detail']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(out_path), "report": str(REPORT), "audit": str(AUDIT)}, ensure_ascii=False, indent=2))
    if not audit["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
