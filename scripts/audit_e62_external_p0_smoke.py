#!/usr/bin/env python3
"""Audit and report E62 external P0 candidate smoke tests."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
CANDIDATES = [
    "nemotron_cascade2_30b_a3b_candidate",
    "glm47_flash_candidate",
    "exaone45_33b_candidate",
]
RESULT_DIR = PROJECT / "results/E62_external_p0_smoke"
OUT_JSON = PROJECT / "reports/E62_EXTERNAL_P0_SMOKE_AUDIT_20260429.json"
OUT_MD = PROJECT / "reports/E62_EXTERNAL_P0_SMOKE_20260429.md"


def load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_bool(x: Any) -> str:
    return "PASS" if x else "FAIL"


def short_failure(check: dict[str, Any] | None) -> str:
    if not check:
        return "missing"
    if check.get("ok"):
        return "ok"
    return f"{check.get('error_type')}: {str(check.get('error', ''))[:180]}"


def check_by_name(data: dict[str, Any], name: str) -> dict[str, Any] | None:
    for c in data.get("checks", []):
        if c.get("name") == name:
            return c
    return None


def main() -> None:
    rows = []
    checks = []
    for key in CANDIDATES:
        path = RESULT_DIR / f"{key}_e62_external_p0_smoke.json"
        data = load(path)
        exists = data is not None
        checks.append({"check": f"result exists for {key}", "ok": exists, "detail": str(path.relative_to(PROJECT))})
        if not data:
            rows.append({"model_key": key, "exists": False, "promote": False, "reason": "missing result"})
            continue
        summary = data.get("summary", {})
        args = data.get("args", {})
        auto_cfg = check_by_name(data, "auto_config")
        tok = check_by_name(data, "tokenizer_chat")
        hf = check_by_name(data, "hf_dynamic")
        static = check_by_name(data, "static_probe")
        license_probe = check_by_name(data, "license_probe")
        checks.extend(
            [
                {"check": f"{key} license probe", "ok": bool(license_probe and license_probe.get("ok")), "detail": short_failure(license_probe)},
                {"check": f"{key} static probe", "ok": bool(static and static.get("ok")), "detail": short_failure(static)},
                {"check": f"{key} tokenizer probe", "ok": bool(tok and tok.get("ok")), "detail": short_failure(tok)},
                {"check": f"{key} auto config probe", "ok": bool(auto_cfg and auto_cfg.get("ok")), "detail": short_failure(auto_cfg)},
            ]
        )
        if not args.get("skip_hf_dynamic"):
            checks.append({"check": f"{key} HF dynamic probe", "ok": bool(hf and hf.get("ok") and summary.get("hf_dynamic_ok")), "detail": short_failure(hf)})
        else:
            checks.append({"check": f"{key} HF dynamic probe", "ok": False, "detail": "not attempted in this environment"})
        reason_parts = []
        if not summary.get("license_ok_for_noncommercial_research"):
            reason_parts.append("license not cleared for local noncommercial research")
        if not summary.get("auto_config_ok"):
            reason_parts.append("AutoConfig/backend unsupported")
        if not summary.get("tokenizer_ok"):
            reason_parts.append("tokenizer/chat-template unsupported")
        if not summary.get("hf_dynamic_ok"):
            reason_parts.append("HF dynamic option-logprob/hidden-state/layer smoke failed or skipped")
        if not reason_parts:
            reason_parts.append("all promotion-gate checks passed")
        rows.append(
            {
                "model_key": key,
                "exists": True,
                "license_class": summary.get("license_class"),
                "usage_gate": summary.get("usage_gate"),
                "model_type": summary.get("model_type"),
                "architectures": summary.get("architectures"),
                "auto_config_ok": summary.get("auto_config_ok"),
                "tokenizer_ok": summary.get("tokenizer_ok"),
                "hf_dynamic_ok": summary.get("hf_dynamic_ok"),
                "vllm_static_ok": summary.get("vllm_static_ok"),
                "promote": summary.get("promote_to_expanded_p0"),
                "skip_hf_dynamic": args.get("skip_hf_dynamic"),
                "reason": "; ".join(reason_parts),
                "result_path": str(path.relative_to(PROJECT)),
            }
        )
    promoted = [r["model_key"] for r in rows if r.get("promote")]
    not_promoted = [r["model_key"] for r in rows if not r.get("promote")]
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "all_required_results_present": all(r.get("exists") for r in rows),
        "promoted_candidates": promoted,
        "not_promoted_candidates": not_promoted,
        "rows": rows,
        "checks": checks,
        "boundary_zh": "E62 是准入 smoke，不是科学主结果。只有通过 license/backend/HF hidden-state/option-logprob/layer-discovery 的候选才能进入 E63 官方复现。",
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# E62 External P0 Candidate Smoke / E62 外部 P0 候选准入测试（2026-04-29）",
        "",
        f"- JSON audit / 机器可读审计：`{OUT_JSON.relative_to(PROJECT)}`",
        "- Purpose / 目的：决定 Nemotron、GLM、EXAONE 是否能从 candidate 进入 expanded P0 official evidence。",
        "- Plain language / 说人话：下载完成不等于能进主证据；必须能在本机可靠加载、按官方/本地 chat template 打分，并能拿 hidden states 做机制实验。",
        "",
        "## Promotion Table / 准入表",
        "",
        "| candidate | license | model type | tokenizer | AutoConfig | HF hidden/logprob | vLLM static | promote? | reason |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['model_key']}` | `{r.get('license_class')}` | `{r.get('model_type')}` | {fmt_bool(r.get('tokenizer_ok'))} | {fmt_bool(r.get('auto_config_ok'))} | {fmt_bool(r.get('hf_dynamic_ok'))} | {fmt_bool(r.get('vllm_static_ok'))} | {fmt_bool(r.get('promote'))} | {r.get('reason')} |"
        )
    lines += [
        "",
        "## Interpretation / 解释",
        "",
        "- Passing static license/config checks is not enough for official evidence; E63 requires HF hidden-state and deterministic option-logprob support. / 只通过静态许可/配置不够；E63 需要 HF hidden-state 和确定性 option-logprob 支持。",
        "- If a candidate fails because the local backend lacks architecture support, the scientific conclusion is not that the model lacks the phenomenon; it is only not admitted into official evidence under the current environment. / 如果候选失败原因是本地后端缺少架构支持，科学含义不是模型没有该现象，而是当前环境不能把它纳入官方证据。",
        "- EXAONE is non-commercial research/education only under the local license text; any future publication should cite and respect that boundary. / EXAONE 本地许可为非商业研究/教育用途；后续论文应标注并遵守该边界。",
        "",
        "## Audit Checks / 审计检查",
        "",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for c in checks:
        lines.append(f"| {'PASS' if c['ok'] else 'FAIL'} | {c['check']} | {c['detail']} |")
    lines += [
        "",
        "## Boundary / 边界",
        "",
        "- E62 is a technical admission gate, not a verifier-risk experiment. / E62 是技术准入，不是 verifier 风险实验。",
        "- Candidates that do not pass E62 must remain `pending_smoke` or be demoted; they must not enter main claim synthesis. / 未通过 E62 的候选必须保持 pending 或降级，不能进入主 claim 综合。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"promoted": promoted, "not_promoted": not_promoted, "out": str(OUT_MD)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
