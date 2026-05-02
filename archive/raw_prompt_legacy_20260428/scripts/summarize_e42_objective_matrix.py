#!/usr/bin/env python3
"""Summarize E42 objective/threshold matrix on the E39 surface-semantic set."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]


def fmt(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.3f}"
    return str(x)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json_files(directory: Path, suffix: str) -> list[dict[str, Any]]:
    out = []
    for path in sorted(directory.glob(f"*{suffix}")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_path"] = str(path)
        out.append(data)
    return out


def rate(rows: list[dict[str, Any]], pred_key: str = "pred", value: Any = True) -> float | None:
    if not rows:
        return None
    return sum(1 for r in rows if r.get(pred_key) == value) / len(rows)


def safe_mean(xs: list[float]) -> float | None:
    return mean(xs) if xs else None


def model_sort_key(name: str) -> tuple[int, str]:
    order = {"qwen35_9b": 0, "qwen3_14b_base": 1, "qwen35_27b": 2, "gemma4_31b_it": 3}
    return (order.get(name, 99), name)


def absolute_metrics(abs_results: list[dict[str, Any]], labels: list[dict[str, Any]]) -> dict[str, Any]:
    lab = {r["audit_idx"]: r for r in labels}
    out: dict[str, Any] = {}
    for data in abs_results:
        model = data["verifier_model_key"]
        rows = data.get("rows", [])
        m: dict[str, Any] = {"input_path": data.get("_path")}
        for mode in ["process_only", "training_candidate"]:
            for lang in ["en", "zh"]:
                sub = [r for r in rows if r["mode"] == mode and r["prompt_lang"] == lang]
                for variant in ["valid_correct", "invalid_correct", "invalid_masked", "invalid_wrong"]:
                    vr = [r for r in sub if lab[r["audit_idx"]]["e39_variant"] == variant]
                    m[f"{mode}_{lang}_{variant}_accept"] = rate(vr, "pred", True)
                    m[f"{mode}_{lang}_{variant}_mean_margin"] = safe_mean([float(r["yes_minus_no_logprob"]) for r in vr])
                valid = {lab[r["audit_idx"]]["task_id"]: r for r in sub if lab[r["audit_idx"]]["e39_variant"] == "valid_correct"}
                bad = {lab[r["audit_idx"]]["task_id"]: r for r in sub if lab[r["audit_idx"]]["e39_variant"] == "invalid_correct"}
                deltas = []
                accepted_with_negative_delta = 0
                negative_delta_n = 0
                for task_id, br in bad.items():
                    if task_id not in valid:
                        continue
                    delta = float(br["yes_minus_no_logprob"]) - float(valid[task_id]["yes_minus_no_logprob"])
                    deltas.append(delta)
                    if delta < 0:
                        negative_delta_n += 1
                        if br["pred"] is True:
                            accepted_with_negative_delta += 1
                m[f"{mode}_{lang}_invalid_minus_valid_margin_delta"] = safe_mean(deltas)
                m[f"{mode}_{lang}_negative_delta_pairs"] = negative_delta_n
                m[f"{mode}_{lang}_accepted_despite_negative_delta"] = accepted_with_negative_delta
        out[model] = m
    return out


def contrastive_metrics(contrastive_results: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for data in contrastive_results:
        model = data["verifier_model_key"]
        rows = data.get("rows", [])
        m: dict[str, Any] = {"input_path": data.get("_path"), "n": len(rows)}
        for lang in ["en", "zh"]:
            sub = [r for r in rows if r["prompt_lang"] == lang]
            m[f"{lang}_acc"] = rate(sub, "correct", True)
            m[f"{lang}_mean_margin"] = safe_mean([float(r["margin_target_minus_other"]) for r in sub])
            m[f"{lang}_pred_A_rate"] = rate(sub, "pred", "A")
            bad_a = [r for r in sub if r["order"] == "bad_A"]
            bad_b = [r for r in sub if r["order"] == "bad_B"]
            m[f"{lang}_bad_A_acc"] = rate(bad_a, "correct", True)
            m[f"{lang}_bad_B_acc"] = rate(bad_b, "correct", True)
        m["overall_acc"] = rate(rows, "correct", True)
        m["overall_mean_margin"] = safe_mean([float(r["margin_target_minus_other"]) for r in rows])
        out[model] = m
    return out


def error_span_metrics(error_results: list[dict[str, Any]], labels: list[dict[str, Any]]) -> dict[str, Any]:
    lab = {r["audit_idx"]: r for r in labels}
    out: dict[str, Any] = {}
    for data in error_results:
        model = data["verifier_model_key"]
        rows = data.get("rows", [])
        m: dict[str, Any] = {"input_path": data.get("_path"), "n": len(rows)}
        for mode in ["locate_only", "locate_then_judge"]:
            for lang in ["en", "zh"]:
                sub = [r for r in rows if r["mode"] == mode and r["prompt_lang"] == lang]
                invalid = [r for r in sub if lab[r["audit_idx"]]["e39_variant"] == "invalid_correct"]
                valid = [r for r in sub if lab[r["audit_idx"]]["e39_variant"] == "valid_correct"]
                judged = [r for r in sub if r.get("judge_pred_process_valid") is not None]
                invalid_judged = [r for r in invalid if r.get("judge_pred_process_valid") is not None]
                m[f"{mode}_{lang}_span_acc"] = rate(sub, "span_correct", True)
                m[f"{mode}_{lang}_invalid_hit"] = rate(invalid, "span_correct", True)
                m[f"{mode}_{lang}_valid_none"] = rate(valid, "span_correct", True)
                m[f"{mode}_{lang}_judge_acc"] = None if not judged else sum(r["judge_pred_process_valid"] == lab[r["audit_idx"]]["manual_process_valid"] for r in judged) / len(judged)
                m[f"{mode}_{lang}_invalid_reject"] = None if not invalid_judged else sum(r["judge_pred_process_valid"] is False for r in invalid_judged) / len(invalid_judged)
                m[f"{mode}_{lang}_invalid_judged_n"] = len(invalid_judged)
        out[model] = m
    return out


def task_boundary_table(abs_results: list[dict[str, Any]], contrastive_results: list[dict[str, Any]], labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lab = {r["audit_idx"]: r for r in labels}
    task_rows: dict[str, dict[str, Any]] = {r["task_id"]: {"task_id": r["task_id"], "input_lang": r["input_lang"]} for r in labels if r["e39_variant"] == "invalid_correct"}
    for data in abs_results:
        model = data["verifier_model_key"]
        for r in data.get("rows", []):
            lr = lab[r["audit_idx"]]
            if lr["e39_variant"] == "invalid_correct" and r["mode"] == "process_only" and r["prompt_lang"] == "en":
                task_rows[lr["task_id"]][f"{model}_abs_en_accept"] = bool(r["pred"])
                task_rows[lr["task_id"]][f"{model}_abs_en_margin"] = float(r["yes_minus_no_logprob"])
    for data in contrastive_results:
        model = data["verifier_model_key"]
        by_task = defaultdict(list)
        for r in data.get("rows", []):
            by_task[r["task_id"]].append(r)
        for task_id, rows in by_task.items():
            task_rows[task_id][f"{model}_contrastive_acc"] = sum(r["correct"] for r in rows) / len(rows)
    return [task_rows[k] for k in sorted(task_rows)]


def write_report(lines: list[str], out_md: Path, aggregate: dict[str, Any], out_json: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"aggregate": aggregate}, ensure_ascii=False, indent=2), encoding="utf-8")


def build_lines(abs_m: dict[str, Any], con_m: dict[str, Any], span_m: dict[str, Any], task_rows: list[dict[str, Any]]) -> list[str]:
    models = sorted(set(abs_m) | set(con_m) | set(span_m), key=model_sort_key)
    lines = [
        "# E42 E39 Objective Matrix Summary / E42：E39 目标矩阵汇总",
        "",
        f"Created / 创建时间: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "E42 tests the causal-chain link `verifier objective/threshold -> final decision` on the same 12 E39 surface-semantic families. / E42 在同一批 12 类 E39 表层语义陷阱上检验因果链中的 `verifier 目标/阈值 -> 最终决策` 环节。",
        "The key question is not whether a model can ever detect the error; it is whether a pointwise Yes/No objective uses that evidence as reliably as contrastive or locate-then-judge objectives. / 关键问题不是模型能不能发现错误，而是单点 Yes/No 目标是否像对比式或先定位再判断目标一样可靠地使用这个证据。",
        "",
        "## 1. Objective-level result / 目标层结果",
        "",
        "| verifier | absolute process ACPI accept EN/ZH | training-candidate ACPI accept EN/ZH | invalid-masked process accept EN/ZH | invalid-wrong process accept EN/ZH | contrastive acc EN/ZH | locate-then-judge invalid span hit EN/ZH | locate-then-judge invalid reject EN/ZH |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        a = abs_m.get(model, {})
        c = con_m.get(model, {})
        s = span_m.get(model, {})
        lines.append(
            f"| {model} | {fmt(a.get('process_only_en_invalid_correct_accept'))}/{fmt(a.get('process_only_zh_invalid_correct_accept'))} | "
            f"{fmt(a.get('training_candidate_en_invalid_correct_accept'))}/{fmt(a.get('training_candidate_zh_invalid_correct_accept'))} | "
            f"{fmt(a.get('process_only_en_invalid_masked_accept'))}/{fmt(a.get('process_only_zh_invalid_masked_accept'))} | "
            f"{fmt(a.get('process_only_en_invalid_wrong_accept'))}/{fmt(a.get('process_only_zh_invalid_wrong_accept'))} | "
            f"{fmt(c.get('en_acc'))}/{fmt(c.get('zh_acc'))} | "
            f"{fmt(s.get('locate_then_judge_en_invalid_hit'))}/{fmt(s.get('locate_then_judge_zh_invalid_hit'))} | "
            f"{fmt(s.get('locate_then_judge_en_invalid_reject'))}/{fmt(s.get('locate_then_judge_zh_invalid_reject'))} |"
        )
    lines.extend([
        "",
        "Plain-language read / 人话解释：absolute Yes/No often accepts answer-correct process-invalid traces, but contrastive sibling verification is much stronger on the same rows. Locate-then-judge is informative for Qwen models, while Gemma31's generated localization format is unstable. / 绝对式 Yes/No 经常接受答案正确但过程错误的 trace；同一批 row 换成 sibling 对比后明显更强。先定位再判断对 Qwen 模型有信息量，而 Gemma31 的定位生成格式不稳定。",
        "",
        "## 2. Calibrated margin evidence / 连续边际证据",
        "",
        "| verifier | process EN invalid-valid margin delta | accepted despite negative delta EN | process ZH invalid-valid margin delta | accepted despite negative delta ZH | meaning / 含义 |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for model in models:
        a = abs_m.get(model, {})
        lines.append(
            f"| {model} | {fmt(a.get('process_only_en_invalid_minus_valid_margin_delta'))} | "
            f"{a.get('process_only_en_accepted_despite_negative_delta','')} / {a.get('process_only_en_negative_delta_pairs','')} | "
            f"{fmt(a.get('process_only_zh_invalid_minus_valid_margin_delta'))} | "
            f"{a.get('process_only_zh_accepted_despite_negative_delta','')} / {a.get('process_only_zh_negative_delta_pairs','')} | "
            "negative delta means the model has graded evidence against the invalid phrase even if the final binary answer accepts / 负 delta 表示模型对无效短语有连续负证据，即使最终二值判断仍接受 |"
        )
    lines.extend([
        "",
        "## 3. Contrastive objective details / 对比式目标细节",
        "",
        "| verifier | overall acc | mean target margin | EN pred-A rate | ZH pred-A rate | EN bad-A/bad-B acc | ZH bad-A/bad-B acc |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for model in sorted(con_m, key=model_sort_key):
        c = con_m[model]
        lines.append(
            f"| {model} | {fmt(c.get('overall_acc'))} | {fmt(c.get('overall_mean_margin'))} | "
            f"{fmt(c.get('en_pred_A_rate'))} | {fmt(c.get('zh_pred_A_rate'))} | "
            f"{fmt(c.get('en_bad_A_acc'))}/{fmt(c.get('en_bad_B_acc'))} | {fmt(c.get('zh_bad_A_acc'))}/{fmt(c.get('zh_bad_B_acc'))} |"
        )
    lines.extend([
        "",
        "This table is a direct objective intervention: trace content is unchanged, but the question changes from `is this trace valid?` to `which sibling is invalid?`. / 这张表是直接的目标干预：trace 内容不变，只把问题从“这条是否有效”换成“哪条 sibling 无效”。",
        "",
        "## 4. Boundary tasks / 边界任务",
        "",
        "| task | input | Qwen35-9B abs EN | Qwen14 abs EN | Qwen35-27B abs EN | Gemma31 abs EN | Qwen35-9B contrastive | Qwen14 contrastive | Gemma31 contrastive |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for r in task_rows:
        lines.append(
            f"| {r['task_id']} | {r['input_lang']} | "
            f"{r.get('qwen35_9b_abs_en_accept')} ({fmt(r.get('qwen35_9b_abs_en_margin'))}) | "
            f"{r.get('qwen3_14b_base_abs_en_accept')} ({fmt(r.get('qwen3_14b_base_abs_en_margin'))}) | "
            f"{r.get('qwen35_27b_abs_en_accept')} ({fmt(r.get('qwen35_27b_abs_en_margin'))}) | "
            f"{r.get('gemma4_31b_it_abs_en_accept')} ({fmt(r.get('gemma4_31b_it_abs_en_margin'))}) | "
            f"{fmt(r.get('qwen35_9b_contrastive_acc'))} | {fmt(r.get('qwen3_14b_base_contrastive_acc'))} | {fmt(r.get('gemma4_31b_it_contrastive_acc'))} |"
        )
    lines.extend([
        "",
        "Boundary read / 边界解释：`round_vs_truncate` remains a hard boundary for Qwen14 in contrastive order `bad_A`, matching E40 where its residual patch was weak. Gemma31 has several contrastive position/format failures even though it often gives large margins when correct. / `round_vs_truncate` 对 Qwen14 仍是边界，尤其 bad_A 顺序；这和 E40 中 residual patch 弱一致。Gemma31 即使正确时 margin 很大，也有若干位置/格式失败。",
        "",
        "## 5. Scientific update / 科学更新",
        "",
        "- E42 strengthens the causal-chain claim: changing only the verifier objective sharply changes decisions on the same E39 traces. / E42 强化因果链主张：只改变 verifier 目标，同一批 E39 trace 的决策就明显改变。",
        "- The failure is not pure blindness: Qwen35-27B accepts almost all ACPI under absolute English process prompts, yet reaches perfect contrastive accuracy and high locate-then-judge rejection. / 失败不是纯看不见：Qwen35-27B 在英文绝对式只审过程下几乎全接受 ACPI，但对比式达到满分，先定位再判断也能高比例拒绝。",
        "- The objective fix is not automatic: locate-only often fails because models output chain-of-thought or malformed text; Gemma31's localization is especially unstable. / 换目标并不会自动解决：locate-only 常被思考文本或格式错误破坏；Gemma31 的定位输出尤其不稳。",
        "- Answer masking/wrong-answer variants show that final-answer evidence contributes, but the magnitude is model/language dependent rather than a single universal answer-bias constant. / 答案遮蔽/错误答案变体显示最终答案确实参与决策，但强度依赖模型和提示语言，不是一个固定答案偏置常数。",
        "",
        "## 6. What this means for next experiments / 下一步实验含义",
        "",
        "1. Natural prevalence is now the largest empirical gap: E39/E42 are controlled and causal, but not population-frequency evidence. / 最大经验缺口是自然发生率：E39/E42 是受控因果证据，不是总体频率证据。",
        "2. Mechanism needs to move from residual patch to semantic transfer and steering: E40/E41 show hidden evidence and MLP participation, but not reusable semantic features. / 机制需要从 residual patch 推进到语义迁移与 steering：E40/E41 显示 hidden evidence 和 MLP 参与，但还没证明可复用语义特征。",
        "3. Hard tasks should be conditioned on final-correct traces before ACPI audit; otherwise they mostly measure generator difficulty. / 难题必须先条件化出 final-correct trace 再审 ACPI，否则主要测的是生成难度。",
    ])
    return lines


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--label-file", default=str(PROJECT / "data/processed/e39_surface_semantic_generalization_20260428.jsonl"))
    p.add_argument("--absolute-dir", default=str(PROJECT / "results/E39_surface_semantic_generalization_absolute_verifier"))
    p.add_argument("--contrastive-dir", default=str(PROJECT / "results/E42_e39_objective_matrix_contrastive"))
    p.add_argument("--error-dir", default=str(PROJECT / "results/E42_e39_objective_matrix_error_span"))
    p.add_argument("--out-md", default=str(PROJECT / "reports/E42_e39_objective_matrix_summary_20260428.md"))
    p.add_argument("--out-json", default=str(PROJECT / "results/E42_e39_objective_matrix_summary/summary.json"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    labels = load_jsonl(Path(args.label_file))
    abs_results = load_json_files(Path(args.absolute_dir), "_manual_trace_verifier.json")
    con_results = load_json_files(Path(args.contrastive_dir), "_e42_contrastive_objective.json")
    err_results = load_json_files(Path(args.error_dir), "_error_span_extraction_verifier.json")
    abs_m = absolute_metrics(abs_results, labels)
    con_m = contrastive_metrics(con_results)
    span_m = error_span_metrics(err_results, labels)
    tasks = task_boundary_table(abs_results, con_results, labels)
    aggregate = {"absolute": abs_m, "contrastive": con_m, "error_span": span_m, "task_rows": tasks}
    lines = build_lines(abs_m, con_m, span_m, tasks)
    write_report(lines, Path(args.out_md), aggregate, Path(args.out_json))
    print(f"wrote {args.out_md} and {args.out_json}")


if __name__ == "__main__":
    main()
