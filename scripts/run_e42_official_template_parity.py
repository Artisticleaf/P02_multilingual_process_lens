#!/usr/bin/env python3
"""E42 official-template parity check for verifier scoring.

This script reruns the two deterministic objectives most central to the paper
claim on the E42 focus set:
  1) pointwise process-only Yes/No scoring
  2) order-balanced contrastive A/B sibling scoring

For chat/instruction models, prompts are wrapped with the model tokenizer's
chat template and empty/non-thinking mode where supported.  For base models,
raw prompts remain the primary setting.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    if mode == "raw":
        return False
    if mode == "chat":
        return True
    # official_if_chat: use chat templates for non-base/post-trained chat models.
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    # Most current Qwen/Gemma templates support enable_thinking.  If not, retry.
    try:
        text = tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, **kwargs)
    return text, False


def process_prompt(row: dict[str, Any]) -> str:
    return (
        "You are auditing a mathematical reasoning trace. Judge only whether the mathematical "
        "reasoning steps are valid; do not penalize missing final-answer formatting, truncation, "
        "or extra text after the answer. If any mathematical step is wrong, answer No. If the "
        "visible reasoning steps are mathematically valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {row['problem']}\n"
        f"Reasoning trace: {row['completion']}\n"
        "Are the visible reasoning steps mathematically valid? Answer:"
    )


def contrastive_prompt(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "You are comparing two reasoning traces for the same math problem. "
        "Exactly one trace has a local mathematical or language-semantic process error, although both may end with the same final answer. "
        "Ignore style and verbosity. Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
        f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
    )


def option_logprob(model, tokenizer, prompt: str, option: str, device: torch.device, max_model_len: int, add_special_tokens: bool) -> float:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    if not option_ids:
        return float("-inf")
    keep_prompt = max(1, max_model_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
    total = 0.0
    start = len(prompt_ids)
    for j, tok_id in enumerate(option_ids):
        total += float(F.log_softmax(logits[start + j - 1], dim=-1)[tok_id].item())
    return total


def best_score(model, tokenizer, prompt: str, options: list[str], device: torch.device, max_model_len: int, add_special_tokens: bool) -> tuple[float, str]:
    scored = [(option_logprob(model, tokenizer, prompt, opt, device, max_model_len, add_special_tokens), opt) for opt in options]
    return max(scored, key=lambda x: x[0])


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for r in rows:
        for key in [(r["objective"], "all"), (r["objective"], f"variant={r.get('e39_variant','NA')}"), (r["objective"], f"task={r['task_id']}")]:
            groups[key].append(r)
    out = []
    for (objective, slice_name), g in sorted(groups.items()):
        if objective == "absolute_process":
            acpi = [r for r in g if r.get("e39_variant") == "invalid_correct"]
            valid = [r for r in g if r.get("e39_variant") == "valid_correct"]
            out.append(
                {
                    "objective": objective,
                    "slice": slice_name,
                    "n": len(g),
                    "accuracy": sum(r["pred"] == r["target"] for r in g) / len(g),
                    "yes_rate": sum(bool(r["pred"]) for r in g) / len(g),
                    "acpi_accept_rate": sum(bool(r["pred"]) for r in acpi) / len(acpi) if acpi else None,
                    "valid_accept_rate": sum(bool(r["pred"]) for r in valid) / len(valid) if valid else None,
                    "mean_margin": mean([r["margin"] for r in g]),
                }
            )
        else:
            out.append(
                {
                    "objective": objective,
                    "slice": slice_name,
                    "n": len(g),
                    "accuracy": sum(r["correct"] for r in g) / len(g),
                    "pred_A_rate": sum(r["pred"] == "A" for r in g) / len(g),
                    "mean_target_margin": mean([r["margin_target_minus_other"] for r in g]),
                }
            )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl"))
    p.add_argument("--pairs-yaml", default=str(PROJECT / "configs/e42_e39_objective_pairs.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E42_official_template_parity"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    focus = load_jsonl(Path(args.manual_jsonl))
    manual = {r["audit_idx"]: r for r in focus}
    pairs = read_yaml(args.pairs_yaml)["pairs"]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} device={args.device} prompt_format={args.prompt_format}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tokenizer, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    rows = []

    yes_opts = [" Yes", "Yes", " yes", "yes"]
    no_opts = [" No", "No", " no", "no"]
    for row in focus:
        prompt_text, add_special = render_prompt(tokenizer, process_prompt(row), use_chat)
        yes_score, yes_opt = best_score(model, tokenizer, prompt_text, yes_opts, device, args.max_model_len, add_special)
        no_score, no_opt = best_score(model, tokenizer, prompt_text, no_opts, device, args.max_model_len, add_special)
        margin = yes_score - no_score
        rows.append(
            {
                "objective": "absolute_process",
                "audit_idx": row["audit_idx"],
                "task_id": row["task_id"],
                "e39_variant": row["e39_variant"],
                "target": bool(row["manual_process_valid"]),
                "pred": margin > 0,
                "margin": margin,
                "yes_score": yes_score,
                "no_score": no_score,
                "yes_option": yes_opt,
                "no_option": no_opt,
                "used_chat_template": use_chat,
            }
        )

    a_opts = ["A", " A", "A.", " A."]
    b_opts = ["B", " B", "B.", " B."]
    for pair in pairs:
        valid = manual[int(pair["valid_idx"])]
        bad = manual[int(pair["bad_idx"])]
        for order in ["bad_A", "bad_B"]:
            if order == "bad_A":
                trace_a, trace_b, target = bad["completion"], valid["completion"], "A"
            else:
                trace_a, trace_b, target = valid["completion"], bad["completion"], "B"
            content = contrastive_prompt(bad["problem"], trace_a, trace_b)
            prompt_text, add_special = render_prompt(tokenizer, content, use_chat)
            a_score, a_opt = best_score(model, tokenizer, prompt_text, a_opts, device, args.max_model_len, add_special)
            b_score, b_opt = best_score(model, tokenizer, prompt_text, b_opts, device, args.max_model_len, add_special)
            pred = "A" if a_score >= b_score else "B"
            margin = (a_score - b_score) if target == "A" else (b_score - a_score)
            rows.append(
                {
                    "objective": "contrastive",
                    "pair_id": pair["id"],
                    "task_id": pair["task_id"],
                    "order": order,
                    "target": target,
                    "pred": pred,
                    "correct": pred == target,
                    "margin_target_minus_other": margin,
                    "a_score": a_score,
                    "b_score": b_score,
                    "a_option": a_opt,
                    "b_option": b_opt,
                    "used_chat_template": use_chat,
                }
            )

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "verifier_model_key": args.model_key,
        "model_spec": spec,
        "prompt_format": args.prompt_format,
        "used_chat_template": use_chat,
        "args": vars(args),
        "rows": rows,
        "summary": summarize(rows),
    }
    suffix = "chat" if use_chat else "raw"
    out = Path(args.out_dir) / f"{args.model_key}_e42_official_template_parity_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}; used_chat_template={use_chat}; rows={len(rows)}", flush=True)
    for s in result["summary"]:
        if s["slice"] == "all":
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
