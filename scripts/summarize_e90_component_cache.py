#!/usr/bin/env python3
"""Summarize E90 residual/MLP/token-mixer component activation cache."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
IN_DIR = PROJECT / "results/E90_hardtask_component_activation_cache"
OUT_JSON = PROJECT / "reports/E90_COMPONENT_ACTIVATION_CACHE_20260429.json"
OUT_MD = PROJECT / "reports/E90_COMPONENT_ACTIVATION_CACHE_20260429.md"
COMPONENTS = [
    "residual_hidden_state",
    "token_mixer_output",
    "mlp_output",
    "post_attention_norm_output",
    "post_feedforward_norm_output",
    "input_norm_output",
    "pre_mlp_norm_output",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stage_table(data: dict[str, Any]) -> list[dict[str, Any]]:
    best = data["best_hidden_layer"]
    rows = []
    for s in data["summary"]:
        if s.get("slice_type") != "stage":
            continue
        row = {
            "stage": s["slice"],
            "n": s["n"],
            "accept_rate": s["accept_rate"],
            "mean_yes_minus_no": s["mean_yes_minus_no"],
            "best_hidden_layer": best,
        }
        for c in COMPONENTS:
            row[c] = s.get(f"mean_score_{best}:{c}")
        rows.append(row)
    return sorted(rows, key=lambda r: r["stage"])


def top_deltas(data: dict[str, Any], src: str, dst: str, k: int = 8) -> list[dict[str, Any]]:
    stages = {s["slice"]: s for s in data["summary"] if s.get("slice_type") == "stage"}
    if src not in stages or dst not in stages:
        return []
    out = []
    for key, dst_v in stages[dst].items():
        if not key.startswith("mean_score_") or not isinstance(dst_v, (int, float)):
            continue
        src_v = stages[src].get(key)
        if not isinstance(src_v, (int, float)):
            continue
        out.append({"component": key.replace("mean_score_", ""), "delta": dst_v - src_v, "abs_delta": abs(dst_v - src_v)})
    return sorted(out, key=lambda r: r["abs_delta"], reverse=True)[:k]


def fmt(x: Any) -> str:
    return "NA" if x is None else f"{x:.3f}" if isinstance(x, float) else str(x)


def write_report(result: dict[str, Any]) -> None:
    lines = [
        "# E90 Component Activation Cache / E90 组件激活缓存（2026-04-29）",
        "",
        "- Scope / 范围：在 hard-task repaired/unrepaired ACPI 个案上缓存 selected layers 的 final-token 激活，包括 residual hidden state、token-mixer/attention output、MLP output，以及可用 norm outputs。",
        "- Plain language / 说人话：这不是完整 circuit 证明，而是在同一 strict verifier prompt 下，观察“错误前缀、修复触发点、修复后、完整 trace”这些关键位置的 hidden/residual/MLP 信号如何跟 Yes/No 决策一起移动。",
        "",
        "## Main Finding / 主要发现",
        "",
        "- Gemma31 repaired ACPI：错误前缀和第一行错误 final answer 仍被 strict verifier 接受；出现 Wait/Correction 风格修复后，Yes-No logit 从强正转强负，best-layer residual、token-mixer、MLP/post-FF 等组件也同步向 invalid 方向移动。",
        "- Gemma26 unrepaired ACPI：完整 trace 仍被接受；best-layer residual 分数偏弱/负，token-mixer 与 attention-norm 在 error prefix 反而偏正，说明这里不是简单“残差里有一个强 invalid 方向但输出头不用”，而是组件证据本身更混杂，最终决策又被答案一致性拉回 Yes。",
        "- 因此 E90 支持一个更细的机制说法：过程有效性信号不是只在 residual 里；MLP/post-feedforward 与 token-mixer/attention 也携带阶段性变化，但不同模型/个案中这些组件对最终 Yes/No 读出的贡献会错配。",
        "",
    ]
    for item in result["models"]:
        lines += [
            f"## {item['model_key']} / {item['target_mode']}",
            "",
            f"- Cache shape / 缓存形状：`{item['component_cache_shape']}`；best hidden layer / 最佳 hidden 层：`{item['best_hidden_layer']}`；selected layers / 选中层：`{item['selected_hidden_layers']}`。",
            f"- Leakage audit / 泄露审计：gold={item['leakage_audit']['gold_answer_in_prompt_rows']}, labels={item['leakage_audit']['labels_in_prompt_rows']}, error_spans={item['leakage_audit']['error_spans_in_prompt_rows']}。",
            "",
            "| stage | n | accept | Yes-No | residual | token-mixer | MLP | post-attn-norm | post-FF-norm | input-norm | pre-MLP-norm |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in item["stage_table"]:
            lines.append(
                f"| {r['stage']} | {r['n']} | {fmt(r['accept_rate'])} | {fmt(r['mean_yes_minus_no'])} | "
                f"{fmt(r['residual_hidden_state'])} | {fmt(r['token_mixer_output'])} | {fmt(r['mlp_output'])} | "
                f"{fmt(r['post_attention_norm_output'])} | {fmt(r['post_feedforward_norm_output'])} | "
                f"{fmt(r['input_norm_output'])} | {fmt(r['pre_mlp_norm_output'])} |"
            )
        lines += ["", "Top component shifts / 最大组件位移：", ""]
        for key, vals in item["top_deltas"].items():
            if not vals:
                continue
            lines.append(f"- {key}: " + "; ".join(f"{v['component']} {v['delta']:+.3f}" for v in vals[:5]))
        lines.append("")
    lines += [
        "## Boundary / 边界",
        "",
        "- E90 缓存的是关键 prefix 的 final-token activations，不是全 token 全层轨迹。",
        "- 组件方向来自 E61 controlled language/error grid 的 strict verifier 方向；它能做对比诊断，但不能单独证明训练时的因果生成路径。",
        "- 当前未做 activation patch/causal mediation 到每个组件的输出 logits；下一步应在 E90 缓存基础上做 component-level patch 或 logit-lens/介入读出。",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    models = []
    for p in sorted(IN_DIR.glob("*_e90_component_cache_*_chat.json")):
        data = load_json(p)
        models.append(
            {
                "file": str(p.relative_to(PROJECT)),
                "model_key": data["model_key"],
                "target_mode": data["target_mode"],
                "best_hidden_layer": data["best_hidden_layer"],
                "selected_hidden_layers": data["selected_hidden_layers"],
                "component_cache_shape": data["component_cache_shape"],
                "component_keys": data["component_keys"],
                "leakage_audit": data["leakage_audit"],
                "stage_table": stage_table(data),
                "top_deltas": {
                    "first_final_answer_end_to_repair_trigger_end": top_deltas(data, "first_final_answer_end", "repair_trigger_end"),
                    "error_span_end_to_completion_end": top_deltas(data, "error_span_end", "completion_end"),
                    "error_span_end_to_post_repair_240chars": top_deltas(data, "error_span_end", "post_repair_240chars"),
                },
            }
        )
    result = {
        "experiment": "E90_component_activation_cache",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "models": models,
        "audit": {
            "all_checks_passed": bool(models) and all(m["leakage_audit"]["gold_answer_in_prompt_rows"] == 0 and m["leakage_audit"]["labels_in_prompt_rows"] == 0 and m["leakage_audit"]["error_spans_in_prompt_rows"] == 0 for m in models),
            "note_zh": "E90 prompt 未注入 gold、标签或人工 error span；缓存的是 verifier prompt 的关键 prefix 激活。",
        },
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(result)
    print(json.dumps({"wrote": str(OUT_JSON), "report": str(OUT_MD), "models": [m["model_key"] for m in models], "audit": result["audit"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
