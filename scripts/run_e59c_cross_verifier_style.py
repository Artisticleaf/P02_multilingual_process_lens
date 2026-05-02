#!/usr/bin/env python3
"""Run verifier objectives on E59c style-rewritten controlled traces."""
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

P0_SOURCES = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def should_use_chat_template(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), False


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
        groups[(r["source_model_key"], r["objective"], "all")].append(r)
        if r["objective"] == "absolute_process":
            groups[(r["source_model_key"], r["objective"], f"variant={r['e39_variant']}")].append(r)
    out = []
    for (source, objective, slice_name), g in sorted(groups.items()):
        if objective == "absolute_process":
            acpi = [r for r in g if r.get("e39_variant") == "invalid_correct"]
            valid = [r for r in g if r.get("e39_variant") == "valid_correct"]
            out.append(
                {
                    "source_model_key": source,
                    "objective": objective,
                    "slice": slice_name,
                    "n": len(g),
                    "accuracy": sum(r["pred"] == r["target"] for r in g) / len(g),
                    "yes_rate": sum(bool(r["pred"]) for r in g) / len(g),
                    "acpi_accept_rate": sum(bool(r["pred"]) for r in acpi) / len(acpi) if acpi else None,
                    "valid_accept_rate": sum(bool(r["pred"]) for r in valid) / len(valid) if valid else None,
                    "mean_margin": mean(r["margin"] for r in g),
                }
            )
        else:
            out.append(
                {
                    "source_model_key": source,
                    "objective": objective,
                    "slice": slice_name,
                    "n": len(g),
                    "accuracy": sum(r["correct"] for r in g) / len(g),
                    "pred_A_rate": sum(r["pred"] == "A" for r in g) / len(g),
                    "mean_target_margin": mean(r["margin_target_minus_other"] for r in g),
                }
            )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--verifier-model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--data-dir", default=str(PROJECT / "data/processed/e59c_style_rewrite_audited"))
    p.add_argument("--pairs-dir", default=str(PROJECT / "configs/e59c_style_rewrite_pairs"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E59_cross_verifier_style"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=4096)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.verifier_model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading verifier {args.verifier_model_key}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, tokenizer)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    rows_out = []
    yes_opts = [" Yes", "Yes", " yes", "yes"]
    no_opts = [" No", "No", " no", "no"]
    a_opts = ["A", " A", "A.", " A."]
    b_opts = ["B", " B", "B.", " B."]
    for source in P0_SOURCES:
        data_path = Path(args.data_dir) / f"{source}_e59c_style_rewrite_audited.jsonl"
        pairs_path = Path(args.pairs_dir) / f"{source}_e59c_style_rewrite_pairs.yaml"
        if not data_path.exists() or not pairs_path.exists():
            print(f"skip source={source}; missing audited data or pairs", flush=True)
            continue
        focus = load_jsonl(data_path)
        manual = {int(r["audit_idx"]): r for r in focus}
        pairs = read_yaml(pairs_path)["pairs"]
        for row in focus:
            prompt_text, add_special = render_prompt(tokenizer, process_prompt(row), use_chat)
            yes_score, yes_opt = best_score(model, tokenizer, prompt_text, yes_opts, device, args.max_model_len, add_special)
            no_score, no_opt = best_score(model, tokenizer, prompt_text, no_opts, device, args.max_model_len, add_special)
            margin = yes_score - no_score
            rows_out.append(
                {
                    "objective": "absolute_process",
                    "source_model_key": source,
                    "verifier_model_key": args.verifier_model_key,
                    "audit_idx": row["audit_idx"],
                    "original_audit_idx": row["original_audit_idx"],
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
                rows_out.append(
                    {
                        "objective": "contrastive",
                        "source_model_key": source,
                        "verifier_model_key": args.verifier_model_key,
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
        print(f"scored source={source} rows={len(focus)} pairs={len(pairs)}", flush=True)
    result = {
        "experiment": "E59c_cross_verifier_style_controlled",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "verifier_model_key": args.verifier_model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "args": vars(args),
        "rows": rows_out,
        "summary": summarize(rows_out),
    }
    out = Path(args.out_dir) / f"{args.verifier_model_key}_e59c_cross_verifier_style.json"
    write_json(out, result)
    print(f"wrote {out}; rows={len(rows_out)}", flush=True)


if __name__ == "__main__":
    main()
