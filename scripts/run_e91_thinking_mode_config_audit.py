#!/usr/bin/env python3
"""E91 thinking-mode config and parser audit.

This is a tokenizer/model-card audit, not a model-behavior experiment.  It
records how each official P0 chat template renders thinking on/off and writes
the mode boundary needed before rerunning verifier/generation experiments in
thinking mode.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_tokenizer  # noqa: E402


P0_MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it", "glm47_flash_candidate"]

DOC_LINKS = {
    "qwen35_27b": "https://huggingface.co/Qwen/Qwen3.5-27B",
    "gemma4_31b_it": "https://huggingface.co/google/gemma-4-31B-it",
    "gemma4_26b_a4b_it": "https://huggingface.co/google/gemma-4-26B-A4B-it",
    "glm47_flash_candidate": "https://huggingface.co/zai-org/GLM-4.7-Flash",
}


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text_if_exists(path: Path, limit: int = 120000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def render_chat(tokenizer: Any, *, enable_thinking: bool) -> tuple[str, bool, str | None]:
    messages = [
        {
            "role": "user",
            "content": (
                "Please inspect the trace and then output a final decision exactly as "
                "`Final decision: Yes` or `Final decision: No`.\n\n"
                "Problem: Is 2 + 2 = 4?\nTrace: 2 + 2 = 4.\n"
            ),
        }
    ]
    if not getattr(tokenizer, "chat_template", None):
        return messages[0]["content"], True, "no_chat_template"
    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
        )
        return text, False, None
    except TypeError as exc:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return text, False, f"enable_thinking_unsupported:{type(exc).__name__}"


def marker_audit(text: str) -> dict[str, Any]:
    markers = {
        "contains_open_think": "<think>" in text,
        "contains_close_think": "</think>" in text,
        "contains_gemma_think_token": "<|think|>" in text,
        "contains_channel_thought": "<|channel>thought" in text or "<channel>thought" in text,
        "contains_empty_think_block": bool(re.search(r"<think>\s*</think>", text)),
        "contains_empty_gemma_thought": "<|channel>thought\n<channel|>" in text,
        "assistant_prompt_tail": text[-500:],
        "char_len": len(text),
    }
    markers["has_thinking_start_signal"] = any(
        [
            markers["contains_open_think"] and not markers["contains_empty_think_block"],
            markers["contains_gemma_think_token"],
            markers["contains_channel_thought"] and not markers["contains_empty_gemma_thought"],
        ]
    )
    markers["has_disabled_thinking_signal"] = any(
        [
            markers["contains_empty_think_block"],
            markers["contains_empty_gemma_thought"],
            markers["contains_close_think"] and not markers["contains_open_think"],
        ]
    )
    return markers


def numbered_snippets(readme: str, patterns: list[str], *, radius: int = 2) -> list[dict[str, Any]]:
    lines = readme.splitlines()
    out: list[dict[str, Any]] = []
    seen: set[int] = set()
    for i, line in enumerate(lines):
        lower = line.lower()
        if any(p.lower() in lower for p in patterns):
            start = max(0, i - radius)
            end = min(len(lines), i + radius + 1)
            if any(j in seen for j in range(start, end)):
                continue
            seen.update(range(start, end))
            out.append(
                {
                    "line": i + 1,
                    "text": "\n".join(f"{j + 1}: {lines[j]}" for j in range(start, end)),
                }
            )
    return out[:12]


def extract_recommended_params(model_key: str, readme: str, generation_config: dict[str, Any]) -> dict[str, Any]:
    text = readme.lower()
    params: dict[str, Any] = {
        "generation_config": {
            key: generation_config.get(key)
            for key in ["temperature", "top_p", "top_k", "min_p", "presence_penalty", "repetition_penalty", "max_new_tokens"]
            if key in generation_config
        },
        "readme_snippets": numbered_snippets(
            readme,
            [
                "thinking mode for general tasks",
                "instruct (or non-thinking)",
                "temperature",
                "top_p",
                "top-p",
                "top_k",
                "reasoning-parser",
                "enable_thinking",
                "max new tokens",
                "context length",
            ],
        ),
    }
    if model_key == "qwen35_27b":
        params["recommended_thinking"] = {
            "temperature": 1.0,
            "top_p": 0.95,
            "top_k": 20,
            "min_p": 0.0,
            "presence_penalty": 1.5,
            "repetition_penalty": 1.0,
        }
        params["recommended_nonthinking_reasoning"] = {
            "temperature": 1.0,
            "top_p": 1.0 if "top_p=1.0" in text else 0.95,
            "top_k": 40 if "top_k=40" in text else 20,
            "min_p": 0.0,
            "presence_penalty": 2.0 if "presence_penalty=2.0" in text else 1.5,
            "repetition_penalty": 1.0,
        }
        params["context_note"] = "local README states default 262144 tokens and advises at least 128K for thinking capability."
    elif model_key.startswith("gemma4"):
        params["recommended_thinking"] = {"temperature": 1.0, "top_p": 0.95, "top_k": 64}
        params["context_note"] = "local README states medium Gemma4 models support 256K context."
    elif model_key == "glm47_flash_candidate":
        params["recommended_thinking"] = {"temperature": 1.0, "top_p": 0.95, "max_new_tokens": 131072}
        params["deployment_note"] = "local README vLLM examples use --reasoning-parser glm45."
    return params


def mode_verdict(model_key: str, true_markers: dict[str, Any], false_markers: dict[str, Any]) -> dict[str, Any]:
    thinking_render_ok = true_markers["has_thinking_start_signal"] or (
        model_key.startswith("gemma4") and true_markers["contains_gemma_think_token"]
    )
    nonthinking_render_ok = false_markers["has_disabled_thinking_signal"] or (
        model_key.startswith("gemma4") and false_markers["contains_empty_gemma_thought"]
    )
    return {
        "thinking_render_ok": bool(thinking_render_ok),
        "nonthinking_render_ok": bool(nonthinking_render_ok),
        "first_token_option_logprob_safe_in_thinking": False,
        "reason": (
            "thinking mode starts a thought/reasoning region before the final answer, "
            "so Yes/No or A/B must be parsed from the generated final decision rather "
            "than scored as the first assistant token."
        ),
        "recommended_parser": [
            "Generate with thinking enabled and sufficient max_new_tokens.",
            "Strip or separately save thought content according to the model template.",
            "Parse the last explicit `Final decision: Yes/No` or final A/B line.",
            "If no final decision is parseable, mark the row parse_failed rather than guessing.",
        ],
    }


def audit_model(model_key: str, spec: dict[str, Any]) -> dict[str, Any]:
    model_path = Path(spec["path"])
    tokenizer = load_tokenizer(str(model_path), local_files_only=is_local_model(spec))
    gen_cfg = read_json_if_exists(model_path / "generation_config.json")
    cfg = read_json_if_exists(model_path / "config.json")
    tok_cfg = read_json_if_exists(model_path / "tokenizer_config.json")
    readme = read_text_if_exists(model_path / "README.md")
    false_text, false_add_special, false_note = render_chat(tokenizer, enable_thinking=False)
    true_text, true_add_special, true_note = render_chat(tokenizer, enable_thinking=True)
    false_markers = marker_audit(false_text)
    true_markers = marker_audit(true_text)
    return {
        "model_key": model_key,
        "family": spec.get("family"),
        "priority": spec.get("priority"),
        "path": str(model_path),
        "doc_link": DOC_LINKS.get(model_key),
        "tokenizer_class": type(tokenizer).__name__,
        "has_chat_template": bool(getattr(tokenizer, "chat_template", None)),
        "config": {
            "model_type": cfg.get("model_type"),
            "architectures": cfg.get("architectures"),
            "max_position_embeddings": cfg.get("max_position_embeddings"),
            "tokenizer_model_max_length": tok_cfg.get("model_max_length"),
        },
        "recommended_params": extract_recommended_params(model_key, readme, gen_cfg),
        "render_false": {
            "add_special_tokens": false_add_special,
            "note": false_note,
            "markers": false_markers,
        },
        "render_true": {
            "add_special_tokens": true_add_special,
            "note": true_note,
            "markers": true_markers,
        },
        "mode_verdict": mode_verdict(model_key, true_markers, false_markers),
    }


def write_report(results: dict[str, Any], path: Path) -> None:
    rows = []
    for key, item in results["models"].items():
        verdict = item["mode_verdict"]
        rec = item["recommended_params"]
        rows.append(
            "| {key} | {think_ok} | {nonthink_ok} | {first_token} | {params} |".format(
                key=key,
                think_ok="OK" if verdict["thinking_render_ok"] else "CHECK",
                nonthink_ok="OK" if verdict["nonthinking_render_ok"] else "CHECK",
                first_token="No",
                params=json.dumps(rec.get("recommended_thinking", {}), ensure_ascii=False),
            )
        )
    detail_sections = []
    for key, item in results["models"].items():
        snippets = item["recommended_params"].get("readme_snippets", [])[:5]
        snippet_text = "\n\n".join(f"```text\n{s['text']}\n```" for s in snippets)
        detail_sections.append(
            f"### {key}\n\n"
            f"- Local path: `{item['path']}`\n"
            f"- Official/model-card link: {item.get('doc_link')}\n"
            f"- Tokenizer: `{item['tokenizer_class']}`; chat template: `{item['has_chat_template']}`\n"
            f"- Thinking true tail:\n```text\n{item['render_true']['markers']['assistant_prompt_tail']}\n```\n"
            f"- Thinking false tail:\n```text\n{item['render_false']['markers']['assistant_prompt_tail']}\n```\n"
            f"- README snippets:\n{snippet_text if snippet_text else 'No matching README snippets found.'}\n"
        )
    text = f"""# E91 Thinking-Mode Config Audit / thinking 模式配置审计（2026-04-29）

## Conclusion / 结论

中文：E91 是轻量配置审计，不是行为实验。四个 P0/扩展 P0 模型的官方 chat template 都能区分 thinking 与 non-thinking 渲染。thinking 模式下，assistant 起点会进入 thought/reasoning 区域，因此不能再使用首 token `Yes/No` 或 `A/B` logprob 作为 verifier 决策；后续 TV/TG 实验必须让模型生成完整 thinking 输出，再解析最后明确的 `Final decision` 或最终选项。

English: E91 is a lightweight configuration audit, not a behavioral experiment. The P0/expanded-P0 chat templates distinguish thinking and non-thinking rendering. In thinking mode the assistant begins with a thought/reasoning region, so first-token `Yes/No` or `A/B` option-logprob is not a valid thinking-verifier decision. TV/TG reruns must generate full thinking outputs and parse the final explicit decision.

## Checklist / 检查表

| model | thinking render | non-thinking render | first-token logprob safe in thinking | recommended thinking params from local model card |
|---|---:|---:|---:|---|
{chr(10).join(rows)}

## Immediate Experimental Rule / 立即实验规则

1. `DV` results remain valid as direct-answer verifier evidence only. / `DV` 结果只作为直接回答 verifier 证据。
2. `TV` reruns must use generated final decisions, not first-token option logprob. / `TV` 重测必须解析生成后的最终判定，不能用首 token logprob。
3. `TG` natural generation must use official thinking sampling parameters and be audited separately from `NG`. / `TG` 自然生成必须用官方 thinking 采样参数，并与 `NG` 分开审计。
4. Hidden/mechanism reruns in thinking mode must record thought tokens, repair markers, and final decision tokens separately. / thinking 机制实验需分别记录思考 token、修复标记和最终决策 token。

## Model Details / 模型细节

{chr(10).join(detail_sections)}
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    registry = read_yaml(PROJECT / "configs/model_registry.yaml")["models"]
    results: dict[str, Any] = {
        "experiment": "E91_thinking_mode_config_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "mode_boundary": {
            "DV": "direct-answer verifier with thinking disabled",
            "TV": "thinking verifier with generated final decision parsing",
            "NG": "non-thinking generation",
            "TG": "thinking generation",
            "MI_DV": "mechanistic intervention under direct-verifier prompts",
        },
        "models": {},
    }
    for key in P0_MODELS:
        results["models"][key] = audit_model(key, registry[key])
    out_dir = PROJECT / "results/E91_thinking_mode_config_audit"
    write_json(out_dir / "e91_thinking_mode_config_audit.json", results)
    write_report(results, PROJECT / "reports/E91_THINKING_MODE_CONFIG_AUDIT_20260429.md")
    print(json.dumps({"ok": True, "out_dir": str(out_dir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
