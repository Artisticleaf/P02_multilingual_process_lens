#!/usr/bin/env python3
"""Appendix-level audit for paper-facing evaluation settings.

The goal is not to prove that every historical exploratory run was ideal.  It
checks the result families that currently support the paper claim and records
whether each setting is correct, corrected by a robustness rerun, or only
usable as a named stress-test setting.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from transformers import AutoConfig, AutoTokenizer

PROJECT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def model_layers_from_config(path: str) -> int | None:
    cfg = AutoConfig.from_pretrained(path, trust_remote_code=True, local_files_only=True)
    text_cfg = getattr(cfg, "text_config", None)
    return getattr(text_cfg, "num_hidden_layers", None) or getattr(cfg, "num_hidden_layers", None)


def dtype_from_config(path: str) -> str | None:
    cfg = AutoConfig.from_pretrained(path, trust_remote_code=True, local_files_only=True)
    text_cfg = getattr(cfg, "text_config", None)
    dtype = getattr(text_cfg, "torch_dtype", None) or getattr(cfg, "torch_dtype", None) or getattr(cfg, "dtype", None)
    return str(dtype) if dtype is not None else None


def has_chat_template(path: str) -> bool:
    tok = AutoTokenizer.from_pretrained(path, trust_remote_code=True, local_files_only=True, use_fast=True)
    return bool(getattr(tok, "chat_template", None))


def expected_chat(spec: dict[str, Any]) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls


def status(ok: bool, note: str = "") -> dict[str, Any]:
    return {"ok": bool(ok), "note": note}


def check_layer_config(config_path: Path, registry: dict[str, Any]) -> dict[str, Any]:
    data = read_yaml(config_path)
    issues = []
    by_model = {}
    for pair in data.get("pairs", []):
        key = pair.get("model_key")
        if key not in registry:
            continue
        n_layers = model_layers_from_config(registry[key]["path"])
        layers = pair.get("layers") or pair.get("module_layers") or []
        bad = [int(x) for x in layers if n_layers is not None and (int(x) < 0 or int(x) >= n_layers)]
        by_model.setdefault(key, {"n_layers": n_layers, "checked_pairs": 0, "invalid_layers": []})
        by_model[key]["checked_pairs"] += 1
        if bad:
            by_model[key]["invalid_layers"].append({"pair_id": pair.get("id"), "invalid": bad})
            issues.append({"config": str(config_path), "pair_id": pair.get("id"), "model_key": key, "invalid": bad, "n_layers": n_layers})
    return {"ok": not issues, "issues": issues, "by_model": by_model}


def main() -> None:
    registry = read_yaml(PROJECT / "configs/model_registry.yaml")["models"]
    now = datetime.now().isoformat(timespec="seconds")
    checks: dict[str, Any] = {}
    issues: list[str] = []

    model_keys = ["qwen35_9b", "qwen35_27b", "qwen3_14b_base", "gemma4_31b_it", "gemma4_26b_a4b_it"]
    model_rows = {}
    for key in model_keys:
        spec = registry[key]
        path = Path(spec["path"])
        try:
            layers = model_layers_from_config(str(path))
            dtype = dtype_from_config(str(path))
            chat = has_chat_template(str(path))
            exp_chat = expected_chat(spec)
            ok = path.exists() and layers is not None and (chat if exp_chat else True)
            if not ok:
                issues.append(f"model_config:{key}")
            model_rows[key] = {
                "path_exists": path.exists(),
                "family": spec.get("family"),
                "class": spec.get("class"),
                "layers": layers,
                "dtype": dtype,
                "has_chat_template": chat,
                "expected_chat_template": exp_chat,
                "ok": ok,
            }
        except Exception as exc:  # noqa: BLE001
            issues.append(f"model_config:{key}:{exc}")
            model_rows[key] = {"ok": False, "error": repr(exc)}
    checks["model_configs"] = model_rows

    e39 = read_jsonl(PROJECT / "data/processed/e39_surface_semantic_generalization_20260428.jsonl")
    e42 = read_jsonl(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl")
    variant_counts = Counter(r["e39_variant"] for r in e39)
    focus_counts = Counter((r["task_id"], r["e39_variant"]) for r in e42)
    e39_ok = len(e39) == 72 and set(variant_counts.values()) == {12}
    e42_ok = len(e42) == 24 and all(focus_counts[(task, var)] == 1 for task in {r["task_id"] for r in e42} for var in ["valid_correct", "invalid_correct"])
    label_ok = all((r["e39_variant"] != "invalid_correct") or (r["is_acpi"] and r["manual_final_correct"] and not r["manual_process_valid"]) for r in e42)
    checks["data_and_labels"] = {
        "e39_rows": len(e39),
        "e39_variant_counts": dict(variant_counts),
        "e42_focus_rows": len(e42),
        "tasks": len({r["task_id"] for r in e42}),
        "balanced_e39": e39_ok,
        "balanced_e42_focus": e42_ok,
        "acpi_label_logic_ok": label_ok,
        "ok": e39_ok and e42_ok and label_ok,
    }
    if not checks["data_and_labels"]["ok"]:
        issues.append("data_and_labels")

    layer_checks = {}
    for rel in [
        "configs/e39_surface_semantic_pairs_qwen35_9b.yaml",
        "configs/e39_surface_semantic_pairs_qwen3_14b.yaml",
        "configs/e43_paraphrase_transfer_pairs.yaml",
    ]:
        layer_checks[rel] = check_layer_config(PROJECT / rel, registry)
        if not layer_checks[rel]["ok"]:
            issues.append(f"layer_config:{rel}")
    checks["layer_configs"] = layer_checks

    parity_dir = PROJECT / "results/E42_official_template_parity"
    parity_expected = {
        "qwen35_9b": True,
        "qwen35_27b": True,
        "qwen3_14b_base": False,
        "gemma4_31b_it": True,
        "gemma4_26b_a4b_it": True,
    }
    parity_rows = {}
    for key, exp_chat in parity_expected.items():
        matches = sorted(parity_dir.glob(f"{key}_e42_official_template_parity_*.json"))
        ok = False
        row: dict[str, Any] = {"files": [str(p) for p in matches]}
        if matches:
            data = read_json(matches[-1])
            abs_rows = [r for r in data["rows"] if r["objective"] == "absolute_process"]
            con_rows = [r for r in data["rows"] if r["objective"] == "contrastive"]
            by_pair = defaultdict(Counter)
            for r in con_rows:
                by_pair[r["pair_id"]][r["order"]] += 1
            order_balanced = bool(by_pair) and all(c["bad_A"] == 1 and c["bad_B"] == 1 for c in by_pair.values())
            ok = (
                data.get("prompt_format") == "official_if_chat"
                and data.get("used_chat_template") == exp_chat
                and len(abs_rows) == 24
                and len(con_rows) == 24
                and order_balanced
            )
            row.update(
                {
                    "used_chat_template": data.get("used_chat_template"),
                    "prompt_format": data.get("prompt_format"),
                    "rows": len(data.get("rows", [])),
                    "absolute_rows": len(abs_rows),
                    "contrastive_rows": len(con_rows),
                    "contrastive_order_balanced": order_balanced,
                    "ok": ok,
                }
            )
        else:
            row["ok"] = False
        parity_rows[key] = row
        if not ok:
            issues.append(f"official_template_parity:{key}")
    checks["official_template_parity"] = parity_rows

    patch_path = PROJECT / "results/E40_official_template_span_patch/qwen35_9b_real_acpi_span_patch.json"
    patch_summary_path = PROJECT / "results/E40_official_template_span_patch/summary.json"
    if patch_path.exists() and patch_summary_path.exists():
        patch = read_json(patch_path)
        patch_summary = read_json(patch_summary_path)["aggregate"]["models"]["qwen35_9b"]
        layer_values = sorted({int(r["layer"]) for r in patch.get("rows", [])})
        patch_ok = (
            patch.get("used_chat_template") is True
            and patch.get("add_special_tokens") is False
            and len(patch.get("rows", [])) == 120
            and patch_summary.get("clean_pairs") == 12
            and all(0 <= x < model_rows["qwen35_9b"]["layers"] for x in layer_values)
        )
        checks["official_template_hidden_patch"] = {
            "path": str(patch_path),
            "used_chat_template": patch.get("used_chat_template"),
            "add_special_tokens": patch.get("add_special_tokens"),
            "rows": len(patch.get("rows", [])),
            "layers": layer_values,
            "clean_pairs": patch_summary.get("clean_pairs"),
            "ok": patch_ok,
        }
        if not patch_ok:
            issues.append("official_template_hidden_patch")
    else:
        checks["official_template_hidden_patch"] = {"ok": False, "missing": [str(patch_path), str(patch_summary_path)]}
        issues.append("official_template_hidden_patch")

    archived_audit = PROJECT / "archive/raw_prompt_legacy_20260428/logs/audit_e42_objective_matrix_20260428.json"
    checks["archived_raw_e42_audit_note"] = {
        "ok": archived_audit.exists(),
        "path": str(archived_audit),
        "note_en": "The raw-prompt E42 matrix audit is intentionally archived; active paper-facing checks rely on official-template parity.",
        "note_zh": "raw-prompt E42 矩阵审计已按要求归档；当前论文主证据检查依赖 official-template parity。",
    }

    passed = not issues
    out = {
        "created_at": now,
        "project": str(PROJECT),
        "passed": passed,
        "issues": issues,
        "checks": checks,
        "scope_note_en": "Paper-facing E39-E42 deterministic verifier and hidden-patch settings; older raw runs remain named stress tests unless rerun with official chat templates.",
        "scope_note_zh": "本审计覆盖论文主证据所依赖的 E39-E42 确定性 verifier 与 hidden patch 设置；更早 raw 运行若未复跑官方 chat 模板，只作为已命名压力测试。",
    }
    out_path = PROJECT / "logs/audit_eval_settings_appendix_20260428.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "issues": issues, "out": str(out_path)}, ensure_ascii=False, indent=2))
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
