#!/usr/bin/env python3
"""E59a cross-verifier analysis over controlled ACPI traces.

This analysis does not run new model inference. It reads the official E42
P0 verifier outputs and asks whether the absolute-overaccept vs sibling-recover
pattern is specific to one self-verifier or shared across model families.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from statistics import mean

PROJECT = Path(__file__).resolve().parents[1]
P0 = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
E42_DIR = PROJECT / "results/E42_official_template_parity"
OUT_DIR = PROJECT / "results/E59_cross_verifier_controlled"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_e42() -> dict[str, dict]:
    out = {}
    for path in sorted(E42_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        key = data.get("verifier_model_key")
        if key in P0:
            out[key] = data
    missing = sorted(set(P0) - set(out))
    if missing:
        raise SystemExit(f"Missing E42 files for {missing}")
    return out


def pct(x: int, n: int) -> float:
    return x / n if n else 0.0


def main() -> None:
    data = load_e42()
    absolute_by_model = {}
    contrastive_by_model = {}
    matrix = []
    for model_key, d in data.items():
        abs_rows = [r for r in d["rows"] if r["objective"] == "absolute_process"]
        con_rows = [r for r in d["rows"] if r["objective"] == "contrastive"]
        invalid = [r for r in abs_rows if r["e39_variant"] == "invalid_correct"]
        valid = [r for r in abs_rows if r["e39_variant"] == "valid_correct"]
        absolute_by_model[model_key] = {r["audit_idx"]: r for r in abs_rows}
        contrastive_by_model[model_key] = con_rows
        matrix.append(
            {
                "trace_source": "controlled_e39_manual_pairs",
                "verifier_model": model_key,
                "verifier_family": d.get("model_spec", {}).get("family"),
                "self_or_external_to_trace_source": "external_to_manual_trace_source",
                "prompt_format": d.get("prompt_format"),
                "used_chat_template": bool(d.get("used_chat_template")),
                "absolute_n": len(abs_rows),
                "absolute_accuracy": pct(sum(r["pred"] == r["target"] for r in abs_rows), len(abs_rows)),
                "absolute_valid_accept_rate": pct(sum(bool(r["pred"]) for r in valid), len(valid)),
                "absolute_invalid_accept_rate": pct(sum(bool(r["pred"]) for r in invalid), len(invalid)),
                "absolute_mean_margin": mean(r["margin"] for r in abs_rows),
                "contrastive_n": len(con_rows),
                "contrastive_accuracy": pct(sum(bool(r["correct"]) for r in con_rows), len(con_rows)),
                "contrastive_pred_A_rate": pct(sum(r["pred"] == "A" for r in con_rows), len(con_rows)),
                "contrastive_mean_target_margin": mean(r["margin_target_minus_other"] for r in con_rows),
            }
        )

    # Agreement among P0 verifiers under the absolute objective.
    agreement = []
    for a, b in combinations(P0, 2):
        common = sorted(set(absolute_by_model[a]) & set(absolute_by_model[b]))
        agree = [idx for idx in common if absolute_by_model[a][idx]["pred"] == absolute_by_model[b][idx]["pred"]]
        agreement.append(
            {
                "model_a": a,
                "model_b": b,
                "n": len(common),
                "agreement": pct(len(agree), len(common)),
                "agree_count": len(agree),
            }
        )

    # Consensus rows: all P0 verifiers give the same absolute decision.
    consensus_rows = []
    by_idx = absolute_by_model[P0[0]]
    for idx in sorted(by_idx):
        preds = {m: bool(absolute_by_model[m][idx]["pred"]) for m in P0}
        margins = {m: absolute_by_model[m][idx]["margin"] for m in P0}
        row0 = by_idx[idx]
        if len(set(preds.values())) == 1:
            consensus_rows.append(
                {
                    "audit_idx": idx,
                    "task_id": row0["task_id"],
                    "e39_variant": row0["e39_variant"],
                    "manual_process_valid": bool(row0["target"]),
                    "consensus_pred_accept": next(iter(preds.values())),
                    "preds": preds,
                    "margins": margins,
                }
            )

    invalid_consensus_accept = [
        r for r in consensus_rows if r["e39_variant"] == "invalid_correct" and r["consensus_pred_accept"]
    ]
    invalid_consensus_reject = [
        r for r in consensus_rows if r["e39_variant"] == "invalid_correct" and not r["consensus_pred_accept"]
    ]

    result = {
        "experiment": "E59a_cross_verifier_controlled",
        "created_from": "official E42 P0 outputs; no new model inference",
        "scope_note_en": "This is a cross-family verifier analysis on controlled manual traces. It tests whether the verifier failure is specific to a single self-verifier. It is not yet a mutual model-generated-trace experiment.",
        "scope_note_zh": "这是在受控人工 trace 上做的跨家族 verifier 分析，用于检查失败是否只属于某个 self-verifier；它还不是模型互相审计彼此生成 trace 的完整实验。",
        "p0_models": P0,
        "matrix": matrix,
        "absolute_pairwise_agreement": agreement,
        "consensus_rows": consensus_rows,
        "summary": {
            "n_verifiers": len(P0),
            "all_p0_absolute_invalid_accept_rate": {r["verifier_model"]: r["absolute_invalid_accept_rate"] for r in matrix},
            "all_p0_contrastive_accuracy": {r["verifier_model"]: r["contrastive_accuracy"] for r in matrix},
            "mean_absolute_pairwise_agreement": mean(r["agreement"] for r in agreement),
            "consensus_rows_n": len(consensus_rows),
            "invalid_consensus_accept_n": len(invalid_consensus_accept),
            "invalid_consensus_reject_n": len(invalid_consensus_reject),
            "invalid_consensus_accept_tasks": [r["task_id"] for r in invalid_consensus_accept],
            "invalid_consensus_reject_tasks": [r["task_id"] for r in invalid_consensus_reject],
        },
    }
    out = OUT_DIR / "e59a_cross_verifier_controlled_matrix.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"wrote": str(out), "summary": result["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
