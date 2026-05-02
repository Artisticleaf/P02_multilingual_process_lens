#!/usr/bin/env python3
"""Summarize E105 TG closure-policy results from immutable checkpoints."""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]

REPORT_MD = PROJECT / "reports/E105_TG_CLOSURE_POLICY_20260429.md"
REPORT_JSON = PROJECT / "reports/E105_TG_CLOSURE_POLICY_20260429.json"

SOURCES = [
    {
        "path": PROJECT / "results/E105_tg_closure_policy/_smoke/qwen35_27b_e105_tg_closure_policy.json",
        "stage": "smoke_4096",
        "status": "diagnostic",
        "note_zh": "4096 token smoke；只用于 parser/泄露检查，不作为 E105 主结论。",
    },
    {
        "path": PROJECT / "logs/e105_qwen35_tg_closure_k1_checkpoint_20260429.jsonl",
        "stage": "capped_pilot_8192",
        "status": "superseded_boundary",
        "note_zh": "8192 token 有 wall-time/batch cap；被 reviewer stress 取代，但保留为 8k 不收口边界。",
    },
    {
        "path": PROJECT / "logs/e105r_qwen35_canary16k_checkpoint_20260429.jsonl",
        "stage": "reviewer_stress_16384",
        "status": "official_canary",
        "note_zh": "无 wall-time cap 的 16k canary；只覆盖 base_divisor 一题。",
    },
    {
        "path": PROJECT / "logs/e105r_qwen35_canary32k_checkpoint_20260429.jsonl",
        "stage": "reviewer_stress_32768",
        "status": "official_canary",
        "note_zh": "无 wall-time cap 的 32k final_contract canary；只覆盖 base_divisor 一题。",
    },
]


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return center - half, center + half


def fmt_rate(k: int, n: int) -> str:
    if n == 0:
        return "0/0"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k / n:.3f}, 95% CI [{lo:.3f}, {hi:.3f}]"


def load_rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    path = source["path"]
    if not path.exists():
        return []
    if path.suffix == ".jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("rows", [])
    out = []
    for row in rows:
        row = dict(row)
        row["source_stage"] = source["stage"]
        row["source_status"] = source["status"]
        row["source_note_zh"] = source["note_zh"]
        row["source_path"] = str(path.relative_to(PROJECT))
        completion = row.get("completion", "")
        matches = list(
            re.finditer(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", completion, flags=re.IGNORECASE | re.MULTILINE)
        )
        last = matches[-1] if matches else None
        post_final_chars = len(completion) - last.end() if last else None
        last_line = completion.strip().splitlines()[-1] if completion.strip() else ""
        row["final_answer_line_count"] = len(matches)
        row["post_final_chars"] = post_final_chars
        row["last_line_is_final_answer"] = bool(last and post_final_chars == 0)
        row["clean_final_stop"] = bool(
            row.get("explicit_final_marker_found")
            and post_final_chars == 0
            and not row.get("hit_max_new_tokens")
        )
        row["last_line_preview"] = last_line[:160]
        out.append(row)
    return out


def bucket_summary(rows: list[dict[str, Any]], key_fields: list[str]) -> dict[str, Any]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        key = "|".join(str(row.get(field, "")) for field in key_fields)
        c = buckets[key]
        c["n"] += 1
        c["strict_final_correct"] += int(bool(row.get("strict_final_correct")))
        c["fallback_final_correct"] += int(bool(row.get("fallback_final_correct")))
        c["explicit_final_marker"] += int(bool(row.get("explicit_final_marker_found")))
        c["clean_final_stop"] += int(bool(row.get("clean_final_stop")))
        c["hit_max"] += int(bool(row.get("hit_max_new_tokens")))
        c["generated_tokens_sum"] += int(row.get("generated_tokens") or 0)
        c["repair_marker_sum"] += int(row.get("repair_marker_count") or 0)
    formatted = {}
    for key, c in sorted(buckets.items()):
        n = int(c["n"])
        formatted[key] = {
            "n": n,
            "strict_final_correct": int(c["strict_final_correct"]),
            "fallback_final_correct": int(c["fallback_final_correct"]),
            "explicit_final_marker": int(c["explicit_final_marker"]),
            "clean_final_stop": int(c["clean_final_stop"]),
            "hit_max": int(c["hit_max"]),
            "mean_generated_tokens": c["generated_tokens_sum"] / n if n else None,
            "mean_repair_markers": c["repair_marker_sum"] / n if n else None,
        }
    return formatted


def row_brief(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "source_stage",
        "source_status",
        "policy_id",
        "task_id",
        "gold_answer",
        "strict_extracted_final",
        "strict_final_correct",
        "fallback_extracted_final",
        "fallback_final_correct",
        "explicit_final_marker_found",
        "clean_final_stop",
        "hit_max_new_tokens",
        "generated_tokens",
        "max_new_tokens",
        "max_time_seconds",
        "stop_reason_heuristic",
        "batch_elapsed_seconds",
        "repair_marker_count",
        "final_answer_line_count",
        "post_final_chars",
        "last_line_is_final_answer",
        "source_path",
    ]
    return {key: row.get(key) for key in keys}


def main() -> None:
    rows: list[dict[str, Any]] = []
    for source in SOURCES:
        rows.extend(load_rows(source))

    official = [r for r in rows if r["source_status"] == "official_canary"]
    canary_by_stage = bucket_summary(official, ["source_stage"])
    canary_by_policy = bucket_summary(official, ["policy_id"])
    all_by_stage = bucket_summary(rows, ["source_stage"])

    leakage_passed = all(not r.get("gold_answer_in_prompt") and not r.get("known_trap_note_in_prompt") for r in rows)

    lines = [
        "# E105 TG Closure Policy / Qwen thinking 收口策略（2026-04-29）",
        "",
        "## 说人话结论",
        "",
        "E105 问的是：Qwen thinking 模式下，模型明明经常算到正确数字，但为什么不提交严格的 `Final answer`？这到底是 4096/8192 token 不够，还是 prompt 收口契约不够强？",
        "",
        "结果是分层的：",
        "",
        "- 8k capped pilot 中，前两条都撞满 8192 token，0/2 有明确 `Final answer` 行；这说明 8k 仍不足以解决 Qwen thinking 的不收口问题。",
        "- 16k/32k no-timecap canary 说明 Qwen 可以提交最终答案，但最好用强 final-contract prompt。`final_contract_16384` 在 16111 tokens 自然停止，`final_contract_32768` 在 13120 tokens 自然停止，二者都以 `Final answer: 70` 结尾。",
        "- 16k free/budgeted prompt 虽然出现 `Final answer`，但没有干净停止：free_think 撞满 16k 后还写了 341 个字符，budgeted_final 撞满 16k 后还写了 6214 个字符。因此只看 final marker 会高估“模型已经提交答案”。",
        "",
        "所以当前安全结论是：Qwen TG 的失败不是“没有算到答案”，而是“收口/最终提交策略不稳定”。在 TG 评估里，fallback 抽取到正确数字不能等同于模型做出了严格 final decision。",
        "",
        "## 数据来源",
        "",
        "| stage | status | source | n | 说明 |",
        "|---|---|---|---:|---|",
    ]
    for source in SOURCES:
        n = sum(1 for r in rows if r["source_stage"] == source["stage"])
        lines.append(
            f"| `{source['stage']}` | `{source['status']}` | `{source['path'].relative_to(PROJECT)}` | {n} | {source['note_zh']} |"
        )

    lines += [
        "",
        "## Stage 汇总",
        "",
        "| stage | n | strict final correct | fallback correct | explicit marker | clean final stop | hit max | mean tokens | mean repair markers |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for stage, s in all_by_stage.items():
        n = s["n"]
        lines.append(
            f"| `{stage}` | {n} | {s['strict_final_correct']}/{n} | {s['fallback_final_correct']}/{n} | "
            f"{s['explicit_final_marker']}/{n} | {s['clean_final_stop']}/{n} | {s['hit_max']}/{n} | "
            f"{s['mean_generated_tokens']:.1f} | {s['mean_repair_markers']:.1f} |"
        )

    lines += [
        "",
        "## Official Canary 按策略汇总",
        "",
        "| policy | n | strict final correct | explicit marker | clean final stop | hit max | mean tokens |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for policy, s in canary_by_policy.items():
        n = s["n"]
        lines.append(
            f"| `{policy}` | {n} | {s['strict_final_correct']}/{n} | {s['explicit_final_marker']}/{n} | "
            f"{s['clean_final_stop']}/{n} | {s['hit_max']}/{n} | {s['mean_generated_tokens']:.1f} |"
        )

    lines += [
        "",
        "## Official Canary 95% Wilson CI",
        "",
    ]
    for label, s in canary_by_stage.items():
        n = s["n"]
        lines.append(f"- `{label}` strict final correct: {fmt_rate(s['strict_final_correct'], n)}")
        lines.append(f"- `{label}` clean final stop: {fmt_rate(s['clean_final_stop'], n)}")
        lines.append(f"- `{label}` hit max: {fmt_rate(s['hit_max'], n)}")
    lines += [
        "",
        "## 逐行审计摘要",
        "",
        "| stage | policy | task | strict | fallback | marker | clean stop | hit max | tokens | post-final chars | stop reason |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['source_stage']}` | `{r['policy_id']}` | `{r['task_id']}` | "
            f"{int(bool(r['strict_final_correct']))} | {int(bool(r['fallback_final_correct']))} | "
            f"{int(bool(r['explicit_final_marker_found']))} | {int(bool(r['clean_final_stop']))} | "
            f"{int(bool(r['hit_max_new_tokens']))} | {r['generated_tokens']} | "
            f"{'' if r['post_final_chars'] is None else r['post_final_chars']} | `{r.get('stop_reason_heuristic')}` |"
        )

    lines += [
        "",
        "## 泄露与逻辑审计",
        "",
        f"- Gold answer in prompt rows / prompt 中含答案行数：{sum(int(bool(r.get('gold_answer_in_prompt'))) for r in rows)}",
        f"- Known trap note in prompt rows / prompt 中含陷阱说明行数：{sum(int(bool(r.get('known_trap_note_in_prompt'))) for r in rows)}",
        f"- Leakage audit passed / 泄露审计通过：{leakage_passed}",
        "- E105 没有保存 generation-time hidden states；它只回答收口策略问题。后续 E106/E97 应在 final-contract 条件下保存 thought token、repair marker、final decision token 附近的 residual/MLP/token-mixer/attention-related 激活。",
        "",
        "## 论文边界",
        "",
        "- 16k/32k canary 只覆盖 `aime25_base_divisor_p1`，不能写成 Qwen TG 在困难题上整体优于 NG。",
        "- `Final answer` 出现在中途但继续输出，不等于 clean final decision。严格口径应优先使用 `clean_final_stop` 或显式 final line 后无后续内容。",
        "- 8192 token 失败与 16k/32k 成功共同说明：本地 HF thinking 评估必须显式报告 token budget、wall-time cap、hit-max 和 post-final continuation。",
    ]

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E105_tg_closure_policy",
        "model_key": "qwen35_27b",
        "leakage_audit_passed": leakage_passed,
        "sources": [
            {
                "stage": s["stage"],
                "status": s["status"],
                "path": str(s["path"].relative_to(PROJECT)),
                "note_zh": s["note_zh"],
            }
            for s in SOURCES
        ],
        "summary": {
            "all_by_stage": all_by_stage,
            "official_canary_by_stage": canary_by_stage,
            "official_canary_by_policy": canary_by_policy,
        },
        "rows_brief": [row_brief(r) for r in rows],
        "safe_conclusion_zh": (
            "Qwen thinking 可以在足够 token 和强 final-contract 下提交最终答案；"
            "但 8k 仍不收口，16k free/budgeted 会出现 final marker 后继续输出。"
            "因此 TG 评估必须区分 fallback 数字、final marker 和 clean final stop。"
        ),
    }
    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {REPORT_MD}")
    print(f"wrote {REPORT_JSON}")


if __name__ == "__main__":
    main()
