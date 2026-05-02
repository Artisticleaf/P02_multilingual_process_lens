#!/usr/bin/env python3
"""Build an integrated S4 evidence ledger across manual labels and verifier/probe outputs."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402


DEFAULT_ABSOLUTE_DIRS = [
    PROJECT / "results/E06_e05_manual_trace_verifier",
    PROJECT / "results/E24_s4_absolute_verifier_combined",
    PROJECT / "results/E24_s4_absolute_verifier_e18_targeted",
]
DEFAULT_CONTRASTIVE_DIRS = [
    PROJECT / "results/E12_contrastive_acpi_verifier",
    PROJECT / "results/E16_contrastive_pair_expansion",
    PROJECT / "results/E21_e18_contrastive_verifier",
    PROJECT / "results/E23_e18_clean_sibling_contrastive",
]
DEFAULT_SPAN_DIRS = [
    PROJECT / "results/E09_real_acpi_span_patch",
    PROJECT / "results/E11_real_acpi_span_patch_dense",
    PROJECT / "results/E17_real_semantic_drift_span_patch",
    PROJECT / "results/E20_e18_same_route_span_patch",
    PROJECT / "results/E22_e18_clean_sibling_span_patch",
]
DEFAULT_MODULE_DIRS = [PROJECT / "results/E19_real_acpi_module_patch"]
DEFAULT_PAIR_YAMLS = [
    PROJECT / "configs/e11_real_acpi_pairs_extended.yaml",
    PROJECT / "configs/e18_manual_targeted_pairs.yaml",
    PROJECT / "configs/e22_e18_clean_sibling_pairs.yaml",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing_files(dirs: list[Path], pattern: str) -> list[Path]:
    files: list[Path] = []
    for d in dirs:
        if d.exists():
            files.extend(sorted(d.glob(pattern)))
    return files


def load_pairs(paths: list[Path]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    pairs: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        for pair in read_yaml(path)["pairs"]:
            if pair["id"] in seen:
                continue
            item = dict(pair)
            item["source_yaml"] = str(path)
            pairs.append(item)
            seen.add(pair["id"])
    return pairs


def load_absolute(paths: list[Path]) -> dict[int, list[dict[str, Any]]]:
    by_idx: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("rows", []):
            item = dict(row)
            item["source_result"] = str(path)
            item["verifier_model_key"] = data.get("verifier_model_key", item.get("verifier_model_key"))
            by_idx[int(item["audit_idx"])].append(item)
    return by_idx


def load_contrastive(paths: list[Path]) -> dict[str, list[dict[str, Any]]]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("rows", []):
            item = dict(row)
            item["source_result"] = str(path)
            item["verifier_model_key"] = data.get("verifier_model_key", item.get("verifier_model_key"))
            by_pair[item["pair_id"]].append(item)
    return by_pair


def load_patch(paths: list[Path]) -> dict[str, list[dict[str, Any]]]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        probe_model = data.get("model_key")
        for row in data.get("rows", []):
            item = dict(row)
            item["source_result"] = str(path)
            item["probe_model_key"] = probe_model
            by_pair[item["pair_id"]].append(item)
    return by_pair


def clean_patch(row: dict[str, Any]) -> bool:
    return row.get("valid_to_bad_effect", 0.0) > 0.0 and row.get("bad_to_valid_effect", 0.0) < 0.0


def robust_clean_patch(row: dict[str, Any]) -> bool:
    if not clean_patch(row):
        return False
    strength = (abs(float(row.get("valid_to_bad_effect", 0.0))) + abs(float(row.get("bad_to_valid_effect", 0.0)))) / 2.0
    # Treat tiny final-answer/problem-span blips as weak boundary evidence.
    return strength >= 0.25 and row.get("span") not in {"final_answer_span"}


def summarize_absolute(rows: list[dict[str, Any]], *, want_accept: bool | None) -> dict[str, Any]:
    if not rows:
        return {"available": False}
    proc = [r for r in rows if r.get("mode") == "process_only"]
    train = [r for r in rows if r.get("mode") == "training_candidate"]
    out: dict[str, Any] = {"available": True, "n": len(rows)}
    for name, group in [("process_only", proc), ("training_candidate", train)]:
        if not group:
            continue
        yes_rate = mean(1.0 if r.get("pred") else 0.0 for r in group)
        margin = mean(float(r.get("yes_minus_no_logprob", 0.0)) for r in group)
        out[f"{name}_n"] = len(group)
        out[f"{name}_yes_rate"] = yes_rate
        out[f"{name}_mean_margin"] = margin
        if want_accept is not None:
            out[f"{name}_failure_rate"] = yes_rate if want_accept is False else (1.0 - yes_rate)
    return out


def summarize_contrastive(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"available": False}
    return {
        "available": True,
        "n": len(rows),
        "acc": mean(1.0 if r.get("correct") else 0.0 for r in rows),
        "mean_target_margin": mean(float(r.get("margin_target_minus_other", 0.0)) for r in rows),
        "by_verifier": {
            v: {
                "n": len(g),
                "acc": mean(1.0 if r.get("correct") else 0.0 for r in g),
                "mean_target_margin": mean(float(r.get("margin_target_minus_other", 0.0)) for r in g),
            }
            for v, g in sorted(group_by(rows, "verifier_model_key").items())
        },
    }


def summarize_patch(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"available": False}
    clean = [r for r in rows if clean_patch(r)]
    robust_clean = [r for r in rows if robust_clean_patch(r)]
    best_clean = max(clean, key=lambda r: abs(float(r.get("valid_to_bad_effect", 0.0))) + abs(float(r.get("bad_to_valid_effect", 0.0))), default=None)
    best_robust = max(robust_clean, key=lambda r: abs(float(r.get("valid_to_bad_effect", 0.0))) + abs(float(r.get("bad_to_valid_effect", 0.0))), default=None)
    return {
        "available": True,
        "n": len(rows),
        "clean_direction_n": len(clean),
        "clean_direction_rate": len(clean) / len(rows),
        "robust_clean_direction_n": len(robust_clean),
        "robust_clean_direction_rate": len(robust_clean) / len(rows),
        "best_clean": best_clean,
        "best_robust_clean": best_robust,
    }


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[str(row.get(key))].append(row)
    return out


def causal_flags(bad: dict[str, Any] | None, pair_summary: dict[str, Any]) -> dict[str, bool]:
    if not bad:
        return {}
    absolute = pair_summary["absolute_bad"]
    contrastive = pair_summary["contrastive"]
    span = pair_summary["span_patch"]
    module = pair_summary["module_patch"]
    return {
        "manual_acpi": bool(bad.get("is_acpi") and bad.get("manual_final_correct") is True and bad.get("manual_process_valid") is False),
        "surface_or_process_trap": any(
            token in str(bad.get("manual_risk", "")).lower()
            for token in ["discount", "dabazhe", "qiwuzhe", "semantic", "derivative", "ratio", "arithmetic"]
        ),
        "absolute_overaccept": bool(
            absolute.get("available")
            and (
                absolute.get("process_only_yes_rate", 0.0) > 0.5
                or absolute.get("training_candidate_yes_rate", 0.0) > 0.5
            )
        ),
        "contrastive_signal": bool(contrastive.get("available") and contrastive.get("acc", 0.0) > 0.5),
        "hidden_span_signal": bool(span.get("available") and span.get("robust_clean_direction_n", 0) > 0),
        "module_mlp_signal": bool(
            module.get("available")
            and any(robust_clean_patch(r) and str(r.get("module")) == "mlp" for r in pair_summary["module_patch_rows"])
        ),
    }


def write_markdown(out_path: Path, ledger: dict[str, Any]) -> None:
    lines = [
        "# S4 Causal Chain Ledger / S4 因果链证据台账",
        "",
        f"Created / 创建时间: {ledger['created_at']}",
        "",
        "This table joins manual labels, absolute Yes/No verifier results, contrastive sibling results, and span/module patch probes. / 本表把人工标签、绝对式 Yes/No verifier、兄弟对比和 span/module patch 结果合并为同一条证据链。",
        "",
        "## Pair-Level Chain / pair 级链条",
        "",
        "| pair | bad | valid | ACPI | trap | abs overaccept | contrastive | span patch | MLP patch | boundary note |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in ledger["pairs"]:
        flags = row["causal_flags"]
        boundary = []
        if flags.get("manual_acpi") and flags.get("absolute_overaccept") and not flags.get("contrastive_signal"):
            boundary.append("contrastive weak")
        if flags.get("manual_acpi") and not flags.get("hidden_span_signal"):
            boundary.append("patch weak/missing")
        if flags.get("contrastive_signal") and flags.get("hidden_span_signal"):
            boundary.append("positive chain")
        lines.append(
            "| {pair_id} | {bad_idx} | {valid_idx} | {acpi} | {trap} | {abs_} | {con} | {span} | {mlp} | {note} |".format(
                pair_id=row["pair_id"],
                bad_idx=row["bad_idx"],
                valid_idx=row["valid_idx"],
                acpi="Y" if flags.get("manual_acpi") else "N",
                trap="Y" if flags.get("surface_or_process_trap") else "N",
                abs_="Y" if flags.get("absolute_overaccept") else "N",
                con="Y" if flags.get("contrastive_signal") else "N",
                span="Y" if flags.get("hidden_span_signal") else "N",
                mlp="Y" if flags.get("module_mlp_signal") else "N",
                note=", ".join(boundary) if boundary else "",
            )
        )
    lines.extend(
        [
            "",
            "## Aggregate / 汇总",
            "",
            f"- Pairs / pair 数: {len(ledger['pairs'])}",
            f"- Manual ACPI pairs / 人工 ACPI pair: {ledger['aggregate']['manual_acpi_pairs']}",
            f"- Absolute-overaccepted ACPI pairs / 被绝对式 verifier 过度接受的 ACPI pair: {ledger['aggregate']['absolute_overaccepted_acpi_pairs']}",
            f"- ACPI pairs with contrastive signal / 有对比信号的 ACPI pair: {ledger['aggregate']['contrastive_signal_acpi_pairs']}",
            f"- ACPI pairs with robust hidden span signal / 有稳健隐藏 span 信号的 ACPI pair: {ledger['aggregate']['hidden_span_signal_acpi_pairs']}",
            f"- ACPI pairs with MLP clean-direction signal / 有 MLP clean-direction 信号的 ACPI pair: {ledger['aggregate']['mlp_signal_acpi_pairs']}",
            "",
            "Interpretation / 解释：this is selected-pair evidence, not population prevalence. / 这是选择后的 pair 级证据，不代表总体发生率。",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/manual_e05_plus_e18_targeted_20260427.jsonl"))
    p.add_argument("--out-json", default=str(PROJECT / "results/E24_s4_causal_chain_ledger/s4_causal_chain_ledger.json"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/E24_s4_causal_chain_ledger.md"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    manual_rows = read_jsonl(Path(args.manual_jsonl))
    manual = {int(row["audit_idx"]): row for row in manual_rows}
    pairs = load_pairs(DEFAULT_PAIR_YAMLS)
    absolute = load_absolute(existing_files(DEFAULT_ABSOLUTE_DIRS, "*_manual_trace_verifier.json"))
    contrastive = load_contrastive(existing_files(DEFAULT_CONTRASTIVE_DIRS, "*_contrastive_acpi_verifier.json"))
    span_patch = load_patch(existing_files(DEFAULT_SPAN_DIRS, "*_real_acpi_span_patch.json"))
    module_patch = load_patch(existing_files(DEFAULT_MODULE_DIRS, "*_real_acpi_module_patch.json"))

    ledger_pairs = []
    for pair in pairs:
        bad = manual.get(int(pair["bad_idx"]))
        valid = manual.get(int(pair["valid_idx"]))
        span_rows = span_patch.get(pair["id"], [])
        module_rows = module_patch.get(pair["id"], [])
        pair_summary = {
            "pair_id": pair["id"],
            "trace_model_key": pair["model_key"],
            "bad_idx": pair["bad_idx"],
            "valid_idx": pair["valid_idx"],
            "bad_manual": bad,
            "valid_manual": valid,
            "absolute_bad": summarize_absolute(absolute.get(int(pair["bad_idx"]), []), want_accept=False),
            "absolute_valid": summarize_absolute(absolute.get(int(pair["valid_idx"]), []), want_accept=True),
            "contrastive": summarize_contrastive(contrastive.get(pair["id"], [])),
            "span_patch": summarize_patch(span_rows),
            "module_patch": summarize_patch(module_rows),
            "span_patch_rows": span_rows,
            "module_patch_rows": module_rows,
        }
        pair_summary["causal_flags"] = causal_flags(bad, pair_summary)
        ledger_pairs.append(pair_summary)

    acpi_pairs = [p for p in ledger_pairs if p["causal_flags"].get("manual_acpi")]
    agg = {
        "manual_acpi_pairs": len(acpi_pairs),
        "absolute_overaccepted_acpi_pairs": sum(p["causal_flags"].get("absolute_overaccept", False) for p in acpi_pairs),
        "contrastive_signal_acpi_pairs": sum(p["causal_flags"].get("contrastive_signal", False) for p in acpi_pairs),
        "hidden_span_signal_acpi_pairs": sum(p["causal_flags"].get("hidden_span_signal", False) for p in acpi_pairs),
        "mlp_signal_acpi_pairs": sum(p["causal_flags"].get("module_mlp_signal", False) for p in acpi_pairs),
    }
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "manual_jsonl": args.manual_jsonl,
        "inputs": {
            "absolute_files": [str(p) for p in existing_files(DEFAULT_ABSOLUTE_DIRS, "*_manual_trace_verifier.json")],
            "contrastive_files": [str(p) for p in existing_files(DEFAULT_CONTRASTIVE_DIRS, "*_contrastive_acpi_verifier.json")],
            "span_patch_files": [str(p) for p in existing_files(DEFAULT_SPAN_DIRS, "*_real_acpi_span_patch.json")],
            "module_patch_files": [str(p) for p in existing_files(DEFAULT_MODULE_DIRS, "*_real_acpi_module_patch.json")],
        },
        "aggregate": agg,
        "pairs": ledger_pairs,
    }
    write_json(Path(args.out_json), result)
    write_markdown(Path(args.out_md), result)
    print(f"wrote {args.out_json} and {args.out_md}")


if __name__ == "__main__":
    main()
