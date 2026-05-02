#!/usr/bin/env python3
"""E87 GLM readout intervention diagnostics.

No new model inference. Uses E84 GLM hidden/readout records to compare raw A/B,
global bias centering, two-order antisymmetrization, hidden readout replacement,
and label-free two-pass replacement. This isolates whether GLM's sibling failure
is a lack of process evidence or an output-label/readout bottleneck.
"""
from __future__ import annotations

import argparse
import json
import socket
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_E84 = PROJECT / "results/E84_glm_readout_mediation/glm47_flash_candidate_e84_readout_mediation_chat.json"
OUT_DIR = PROJECT / "results/E87_glm_readout_intervention"
REPORT = PROJECT / "reports/E87_GLM_READOUT_INTERVENTION_20260429.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(x: float | None) -> str:
    return "NA" if x is None else f"{x:.3f}"


def summarize_binary(rows: list[dict[str, Any]], pred_key: str = "correct") -> float | None:
    return sum(bool(r[pred_key]) for r in rows) / len(rows) if rows else None


def group_summary(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[str(r.get(key) or "")].append(r)
    out = []
    for k, vals in sorted(groups.items()):
        if not k:
            continue
        out.append({"slice_type": key, "slice": k, "n": len(vals), "accuracy": summarize_binary(vals), "mean_margin": mean(v["decision_margin"] for v in vals)})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e84-json", default=str(DEFAULT_E84))
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    args = ap.parse_args()

    data = load_json(Path(args.e84_json))
    pair_rows = data["pair_rows"]
    order_rows = data["raw_ab_order_rows"]
    by_pair = defaultdict(dict)
    for r in order_rows:
        by_pair[r["pair_id"]][r["order"]] = r
    global_ab_bias = mean(r["a_score"] - r["b_score"] for r in order_rows)

    raw_rows = []
    centered_rows = []
    anti_rows = []
    hidden_rows = []
    label_free_rows = []
    for r in order_rows:
        raw_margin = r["a_score"] - r["b_score"]
        target_margin = raw_margin if r["target_side"] == "A" else -raw_margin
        raw_correct = (raw_margin >= 0) if r["target_side"] == "A" else (raw_margin < 0)
        raw_rows.append({**r, "decision_margin": target_margin, "correct": raw_correct})
        centered = raw_margin - global_ab_bias
        centered_target = centered if r["target_side"] == "A" else -centered
        centered_correct = (centered >= 0) if r["target_side"] == "A" else (centered < 0)
        centered_rows.append({**r, "decision_margin": centered_target, "correct": centered_correct})
    pair_meta = {r["pair_id"]: r for r in pair_rows}
    for pair_id, orders in sorted(by_pair.items()):
        if "bad_first" not in orders or "bad_second" not in orders:
            continue
        m1 = orders["bad_first"]["a_score"] - orders["bad_first"]["b_score"]
        m2 = orders["bad_second"]["a_score"] - orders["bad_second"]["b_score"]
        bias_component = 0.5 * (m1 + m2)
        antisym_margin = 0.5 * (m1 - m2)
        meta = pair_meta[pair_id]
        anti_rows.append({
            "pair_id": pair_id,
            "task_id": meta.get("task_id"),
            "family": meta.get("family"),
            "route_id": meta.get("route_id"),
            "decision_margin": antisym_margin,
            "correct": antisym_margin >= 0,
            "bias_component": bias_component,
            "raw_bad_first_a_minus_b": m1,
            "raw_bad_second_a_minus_b": m2,
        })
        hidden_rows.append({
            "pair_id": pair_id,
            "task_id": meta.get("task_id"),
            "family": meta.get("family"),
            "route_id": meta.get("route_id"),
            "decision_margin": meta["hidden_margin"],
            "correct": bool(meta["hidden_correct"]),
        })
        label_free_rows.append({
            "pair_id": pair_id,
            "task_id": meta.get("task_id"),
            "family": meta.get("family"),
            "route_id": meta.get("route_id"),
            "decision_margin": meta["label_free_margin"],
            "correct": bool(meta["label_free_correct"]),
        })

    decision_sets = {
        "raw_ab_single_order": raw_rows,
        "global_bias_centered_ab": centered_rows,
        "two_order_antisymmetric_ab": anti_rows,
        "hidden_readout_replacement": hidden_rows,
        "label_free_two_pass_replacement": label_free_rows,
    }
    summary = []
    for name, rows in decision_sets.items():
        summary.append({
            "decision_rule": name,
            "n": len(rows),
            "accuracy": summarize_binary(rows),
            "mean_decision_margin": mean(r["decision_margin"] for r in rows) if rows else None,
        })
        summary.extend({"decision_rule": name, **s} for s in group_summary(rows, "family"))

    result = {
        "experiment": "E87_glm_readout_intervention",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "host": socket.gethostname(),
        "source_e84_json": str(Path(args.e84_json).relative_to(PROJECT)),
        "model_key": data.get("model_key"),
        "layer": data.get("layer"),
        "global_ab_bias_a_minus_b": global_ab_bias,
        "summary": summary,
        "raw_rows": raw_rows,
        "centered_rows": centered_rows,
        "antisymmetric_pair_rows": anti_rows,
        "hidden_readout_rows": hidden_rows,
        "label_free_rows": label_free_rows,
        "leakage_audit": {"new_model_inference": False, "manual_labels_in_prompt_rows": 0, "note_zh": "E87 不重新查询模型；只对 E84 已保存的 balanced order logits/hidden margins 做读出层干预模拟。"},
        "scope_note_zh": "这不是激活 patch，而是 readout/decision-rule intervention：如果把原始 A/B 单次读出换成去偏或 label-free/hidden 读出，GLM 的 sibling 失败是否消失。",
    }
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "glm47_flash_candidate_e87_readout_intervention.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    by_name = {r["decision_rule"]: r for r in summary if r.get("slice_type") is None}
    lines = [
        "# E87 GLM Readout Intervention / GLM 读出干预诊断（2026-04-29）",
        "",
        f"- JSON: `{out.relative_to(PROJECT)}`",
        "- Scope / 范围：不做新推理，读取 E84 的 GLM A/B logits、label-free margin 和 hidden margin。",
        "- Plain language / 说人话：如果 GLM 真的看不出哪条 trace 有错，那么换任何读出方式都救不了；如果只是 A/B 标签读出有偏，那么去掉标签/顺序偏置后准确率会明显恢复。",
        "",
        "| decision rule | n | accuracy | mean margin |",
        "|---|---:|---:|---:|",
    ]
    for name in ["raw_ab_single_order", "global_bias_centered_ab", "two_order_antisymmetric_ab", "hidden_readout_replacement", "label_free_two_pass_replacement"]:
        r = by_name[name]
        lines.append(f"| `{name}` | {r['n']} | {pct(r['accuracy'])} | {pct(r['mean_decision_margin'])} |")
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- `raw_ab_single_order` is the ordinary one-shot A/B sibling decision. / `raw_ab_single_order` 是普通单次 A/B sibling 判断。",
        "- `global_bias_centered_ab` subtracts the average A-minus-B prior from all rows. / `global_bias_centered_ab` 只减去全局 A/B 标签先验。",
        "- `two_order_antisymmetric_ab` asks both orders and keeps the antisymmetric part, so stable A/B label bias cancels. / `two_order_antisymmetric_ab` 同一对 trace 交换顺序问两次，只保留反对称信号，从而抵消稳定标签偏置。",
        "- `hidden_readout_replacement` uses the E84 residual validity margin instead of A/B label logits. / `hidden_readout_replacement` 不看 A/B 输出头，而看 E84 残差过程有效性 margin。",
        "- `label_free_two_pass_replacement` checks each trace pointwise and compares No-Yes invalid scores. / `label_free_two_pass_replacement` 分别检查两条 trace，再比较 No-Yes invalid 分数。",
        "",
        "Main scientific boundary / 科学边界：E87 证明的是 GLM 的主要失败位于读出/输出格式层面；它不声称已经定位到完整神经 circuit。",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "report": str(REPORT), "global_ab_bias": global_ab_bias, "summary": by_name}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
