#!/usr/bin/env python3
"""Generate real trace pools for later audit.

This script stores raw generations and a lightly trimmed completion. It does not label
process validity, because verifier reliability is one of the research targets.
"""
from __future__ import annotations

import argparse
import random
import re
import sys
from datetime import datetime
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device  # noqa: E402

DEFAULT_TASKS = [
    {"id": "lin_001", "en": "Solve 2x + 3 = 11.", "zh": "求解 2x + 3 = 11。", "answer": "4"},
    {"id": "area_001", "en": "A triangle has base 8 and height 5. What is its area?", "zh": "一个三角形的底为8，高为5，面积是多少？", "answer": "20"},
    {"id": "prob_001", "en": "A bag has 3 red balls and 2 blue balls. What is the probability of drawing a red ball?", "zh": "袋子里有3个红球和2个蓝球，抽到红球的概率是多少？", "answer": "3/5"},
    {"id": "avg_001", "en": "The average of 6, 10, and x is 9. Find x.", "zh": "6、10 和 x 的平均数是 9，求 x。", "answer": "11"},
    {"id": "percent_001", "en": "A $80 jacket is discounted by 25%. What is the sale price?", "zh": "一件80美元的夹克打七五折后售价是多少？", "answer": "60"},
    {"id": "ratio_001", "en": "The ratio of boys to girls is 3:5. If there are 24 boys, how many girls are there?", "zh": "男生和女生的比例是3:5。如果有24名男生，女生有多少名？", "answer": "40"},
    {"id": "rem_001", "en": "What is the remainder when 137 is divided by 9?", "zh": "137 除以 9 的余数是多少？", "answer": "2"},
    {"id": "deriv_001", "en": "Differentiate x^2 + 3x.", "zh": "求 x^2 + 3x 的导数。", "answer": "2x+3"},
]

ROUTES = [
    ("en", "en"),
    ("zh", "zh"),
    ("zh", "en"),
    ("en", "zh"),
]


def route_instruction(reason_lang: str, prompt_style: str = "default") -> str:
    concise = "请最多用 12 行推理；" if prompt_style == "concise" else ""
    if reason_lang == "zh":
        return f"请只用中文逐步推理；{concise}不要复述题目；最后单独写一行 `Final answer: <答案>`，写完立即停止。"
    concise_en = "Use at most 12 short reasoning lines; " if prompt_style == "concise" else ""
    return f"Reason step by step in English only; {concise_en}do not restate the problem; end with one line `Final answer: <answer>` and then stop."


def plain_prompt(problem: str, reason_lang: str, prompt_style: str = "default") -> str:
    if reason_lang == "zh":
        return f"{route_instruction(reason_lang, prompt_style)}\n题目：{problem}\n推理："
    return f"{route_instruction(reason_lang, prompt_style)}\nProblem: {problem}\nReasoning:"


def build_prompt(tokenizer, spec: dict, problem: str, reason_lang: str, chat_template: str, prompt_style: str = "default") -> tuple[str, bool]:
    use_chat = False
    if chat_template == "always":
        use_chat = True
    elif chat_template == "auto":
        cls = str(spec.get("class", ""))
        use_chat = bool(getattr(tokenizer, "chat_template", None)) and not cls.startswith("base")
    if use_chat and hasattr(tokenizer, "apply_chat_template"):
        messages = [
            {"role": "system", "content": route_instruction(reason_lang, prompt_style)},
            {"role": "user", "content": problem},
        ]
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), True
        except Exception:  # noqa: BLE001
            pass
    return plain_prompt(problem, reason_lang, prompt_style), False


def trim_completion(text: str) -> tuple[str, dict[str, bool]]:
    flags = {"trimmed_after_second_problem": False, "trimmed_after_second_final": False}
    cut = len(text)
    markers = ["\nProblem:", "\n题目：", "\n题目:", "\nUser:", "\n用户："]
    for marker in markers:
        idx = text.find(marker)
        if idx >= 0:
            cut = min(cut, idx)
            flags["trimmed_after_second_problem"] = True
    matches = list(re.finditer(r"Final answer\s*:", text, flags=re.IGNORECASE))
    if len(matches) >= 2:
        cut = min(cut, matches[1].start())
        flags["trimmed_after_second_final"] = True
    return text[:cut].strip(), flags


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "data/raw/trace_pool_smoke_v2"))
    p.add_argument("--k", type=int, default=2)
    p.add_argument("--max-new-tokens", type=int, default=192)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--max-tasks", type=int, default=8)
    p.add_argument("--tasks-yaml", default=None, help="Optional YAML with a top-level `tasks` list matching DEFAULT_TASKS.")
    p.add_argument("--chat-template", choices=["auto", "always", "never"], default="auto")
    p.add_argument(
        "--routes",
        default=None,
        help="Optional comma/space list such as `zh->en,en->zh`; defaults to all four routes.",
    )
    p.add_argument("--seed", type=int, default=20260427)
    p.add_argument("--out-suffix", default="", help="Optional suffix before `.json` to avoid overwriting repeated targeted runs.")
    p.add_argument("--device", default="cuda")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--prompt-style", choices=["default", "concise"], default="default")
    return p.parse_args()


def parse_routes(text: str | None) -> list[tuple[str, str]]:
    if not text:
        return ROUTES
    routes: list[tuple[str, str]] = []
    for item in re.split(r"[, ]+", text.strip()):
        if not item:
            continue
        if "->" not in item:
            raise ValueError(f"Route must look like `zh->en`, got {item!r}")
        src, dst = item.split("->", 1)
        if src not in {"en", "zh"} or dst not in {"en", "zh"}:
            raise ValueError(f"Only en/zh routes are supported, got {item!r}")
        routes.append((src, dst))
    if not routes:
        raise ValueError("--routes was provided but no valid route was parsed")
    return routes


def main() -> None:
    args = parse_args()
    reg = read_yaml(args.registry)["models"]
    spec = reg[args.model_key]
    local_only = is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    rows = []
    if args.tasks_yaml:
        task_data = read_yaml(args.tasks_yaml)
        loaded_tasks = task_data.get("tasks", task_data if isinstance(task_data, list) else [])
        if not loaded_tasks:
            raise ValueError(f"No tasks found in {args.tasks_yaml}")
        tasks = loaded_tasks[: args.max_tasks]
    else:
        tasks = DEFAULT_TASKS[: args.max_tasks]
    routes = parse_routes(args.routes)
    for task in tasks:
        for input_lang, reason_lang in routes:
            problem = task[input_lang]
            prompt, used_chat = build_prompt(tok, spec, problem, reason_lang, args.chat_template, args.prompt_style)
            enc = tok(prompt, return_tensors="pt").to(device)
            for sample_idx in range(args.k):
                with torch.no_grad():
                    out = model.generate(
                        **enc,
                        do_sample=True,
                        temperature=args.temperature,
                        top_p=args.top_p,
                        max_new_tokens=args.max_new_tokens,
                        pad_token_id=tok.eos_token_id,
                    )
                raw_completion = tok.decode(out[0, enc["input_ids"].shape[1] :], skip_special_tokens=True)
                completion, trim_flags = trim_completion(raw_completion)
                rows.append(
                    {
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "model_key": args.model_key,
                        "task_id": task["id"],
                        "input_lang": input_lang,
                        "reason_lang": reason_lang,
                        "used_chat_template": used_chat,
                        "prompt": prompt,
                        "raw_completion": raw_completion,
                        "completion": completion,
                        "trim_flags": trim_flags,
                        "gold_answer": task["answer"],
                        "sample_idx": sample_idx,
                    }
                )
    suffix = args.out_suffix
    if suffix and not suffix.startswith("_"):
        suffix = "_" + suffix
    out = Path(args.out_dir) / f"{args.model_key}_trace_pool_smoke_v2{suffix}.json"
    write_json(out, {"rows": rows, "model_spec": spec, "args": vars(args)})
    print(f"wrote {out}; rows={len(rows)}")


if __name__ == "__main__":
    main()
