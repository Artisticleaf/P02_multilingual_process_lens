#!/usr/bin/env python3
"""E79 contrastive output-label/objective mismatch diagnostic.

Runs E61 sibling pairs through multiple label formats plus a label-free two-pass
pointwise comparator. Designed primarily for GLM, but works for any registry
model. Prompts never include manual labels/error spans.
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

DATA_PATH = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
PAIRS_PATH = PROJECT / "configs/e61_language_error_grid_pairs.yaml"

FORMATS = ["AB", "one_two", "first_second", "trace1_trace2", "label_free_two_pass"]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    if mode == "raw":
        return False
    if mode == "chat":
        return True
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return fam in {"qwen35", "gemma", "mistral", "phi", "glm", "exaone", "nemotron"} or "instruct" in cls or "post" in cls


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content, True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


def load_pairs() -> list[dict[str, Any]]:
    rows = load_jsonl(DATA_PATH)
    by_idx = {int(r["audit_idx"]): r for r in rows}
    pairs = []
    for pair in read_yaml(PAIRS_PATH)["pairs"]:
        valid = by_idx[int(pair["valid_idx"])]
        bad = by_idx[int(pair["bad_idx"])]
        pairs.append({
            "pair_id": pair["id"],
            "task_id": pair["task_id"],
            "family": pair.get("family") or bad.get("family"),
            "route_id": pair.get("route_id") or bad.get("route_id"),
            "problem": bad["problem"],
            "valid_trace": valid["completion"],
            "bad_trace": bad["completion"],
            "valid_idx": int(pair["valid_idx"]),
            "bad_idx": int(pair["bad_idx"]),
        })
    return pairs


def contrastive_prompt(problem: str, trace_a: str, trace_b: str, fmt: str) -> tuple[str, list[str], list[str], str, str]:
    if fmt == "AB":
        prompt = (
            "You are comparing two reasoning traces for the same problem. Exactly one trace contains a local process error. "
            "Choose the trace whose reasoning process is invalid. Ignore style and final-answer formatting. Answer only A or B.\n"
            f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
        )
        return prompt, ["A", " A", "A.", " A."], ["B", " B", "B.", " B."], "A", "B"
    if fmt == "one_two":
        prompt = (
            "You are comparing two reasoning traces for the same problem. Exactly one trace contains a local process error. "
            "Choose the trace whose reasoning process is invalid. Answer only 1 or 2.\n"
            f"Problem:\n{problem}\n\nTrace 1:\n{trace_a}\n\nTrace 2:\n{trace_b}\n\nInvalid trace:"
        )
        return prompt, ["1", " 1", "1.", " 1."], ["2", " 2", "2.", " 2."], "1", "2"
    if fmt == "first_second":
        prompt = (
            "You are comparing the first and second reasoning traces for the same problem. Exactly one trace contains a local process error. "
            "Choose the trace whose reasoning process is invalid. Answer only First or Second.\n"
            f"Problem:\n{problem}\n\nFirst trace:\n{trace_a}\n\nSecond trace:\n{trace_b}\n\nInvalid trace:"
        )
        return prompt, [" First", "First", " first", "first"], [" Second", "Second", " second", "second"], "First", "Second"
    if fmt == "trace1_trace2":
        prompt = (
            "You are comparing Trace 1 and Trace 2 for the same problem. Exactly one trace contains a local process error. "
            "Choose the trace whose reasoning process is invalid. Answer only Trace 1 or Trace 2.\n"
            f"Problem:\n{problem}\n\nTrace 1:\n{trace_a}\n\nTrace 2:\n{trace_b}\n\nInvalid trace:"
        )
        return prompt, [" Trace 1", "Trace 1", " 1", "1"], [" Trace 2", "Trace 2", " 2", "2"], "Trace 1", "Trace 2"
    raise ValueError(fmt)


def pointwise_prompt(problem: str, trace: str) -> str:
    return (
        "You are checking process validity, not answer correctness. Mentally cover the final-answer line before judging. "
        "If the visible derivation contains a wrong local step, wrong definition, wrong semantic interpretation, or wrong execution rule, answer No. "
        "If the visible reasoning process is valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\nIs the visible reasoning process valid? Answer:"
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


def first_token_score(model, tokenizer, prompt: str, options: list[str], device: torch.device, max_model_len: int, add_special_tokens: bool) -> tuple[float, str]:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)[-max_model_len:]
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0, -1].float()
    logp = F.log_softmax(logits, dim=-1)
    scored = []
    for opt in options:
        ids = tokenizer.encode(opt, add_special_tokens=False)
        if ids:
            scored.append((float(logp[ids[0]].item()), opt))
    del input_ids, attention_mask
    return max(scored, key=lambda x: x[0])


def group_keys(r: dict[str, Any]) -> list[tuple[str, str]]:
    keys = [("all", "all"), ("format", r["format"])]
    for k in ["family", "route_id"]:
        if r.get(k):
            keys.append((k, str(r[k])))
    return keys


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        for key in group_keys(r):
            groups[key].append(r)
    out = []
    for (st, sv), g in sorted(groups.items()):
        out.append({
            "slice_type": st,
            "slice": sv,
            "n": len(g),
            "accuracy": sum(r["correct"] for r in g) / len(g),
            "bad_first_rate": sum(r["order"] == "bad_first" for r in g) / len(g),
            "predict_first_rate": sum(r["pred_side"] == "first" for r in g) / len(g),
            "mean_target_margin": mean(r["target_margin"] for r in g),
        })
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E79_glm_label_free_sibling"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--formats", default=",".join(FORMATS))
    p.add_argument("--score-mode", choices=["first_token", "full_option"], default="first_token")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    formats = [x.strip() for x in args.formats.split(",") if x.strip()]
    pairs = load_pairs()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E79 pairs={len(pairs)} formats={formats}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    rows = []
    yes_opts = [" Yes", "Yes", " yes", "yes"]
    no_opts = [" No", "No", " no", "no"]
    scorer = first_token_score if args.score_mode == "first_token" else best_score
    total = len(pairs) * 2 * len(formats)
    done = 0
    for pair in pairs:
        for order in ["bad_first", "bad_second"]:
            if order == "bad_first":
                trace_first, trace_second, target_side = pair["bad_trace"], pair["valid_trace"], "first"
            else:
                trace_first, trace_second, target_side = pair["valid_trace"], pair["bad_trace"], "second"
            for fmt in formats:
                if fmt == "label_free_two_pass":
                    p1, add1 = render_prompt(tok, pointwise_prompt(pair["problem"], trace_first), use_chat)
                    p2, add2 = render_prompt(tok, pointwise_prompt(pair["problem"], trace_second), use_chat)
                    y1, _ = scorer(model, tok, p1, yes_opts, device, args.max_model_len, add1)
                    n1, _ = scorer(model, tok, p1, no_opts, device, args.max_model_len, add1)
                    y2, _ = scorer(model, tok, p2, yes_opts, device, args.max_model_len, add2)
                    n2, _ = scorer(model, tok, p2, no_opts, device, args.max_model_len, add2)
                    invalid_score_first = n1 - y1
                    invalid_score_second = n2 - y2
                    pred_side = "first" if invalid_score_first >= invalid_score_second else "second"
                    margin = invalid_score_first - invalid_score_second if target_side == "first" else invalid_score_second - invalid_score_first
                    row = {
                        "format": fmt,
                        "score_first": invalid_score_first,
                        "score_second": invalid_score_second,
                        "option_first": "two_pass_no_minus_yes",
                        "option_second": "two_pass_no_minus_yes",
                    }
                else:
                    prompt_raw, first_opts, second_opts, first_label, second_label = contrastive_prompt(pair["problem"], trace_first, trace_second, fmt)
                    prompt, add = render_prompt(tok, prompt_raw, use_chat)
                    s1, opt1 = scorer(model, tok, prompt, first_opts, device, args.max_model_len, add)
                    s2, opt2 = scorer(model, tok, prompt, second_opts, device, args.max_model_len, add)
                    pred_side = "first" if s1 >= s2 else "second"
                    margin = s1 - s2 if target_side == "first" else s2 - s1
                    row = {"format": fmt, "score_first": s1, "score_second": s2, "option_first": opt1, "option_second": opt2}
                rows.append({
                    **row,
                    "pair_id": pair["pair_id"],
                    "task_id": pair["task_id"],
                    "family": pair.get("family"),
                    "route_id": pair.get("route_id"),
                    "order": order,
                    "target_side": target_side,
                    "pred_side": pred_side,
                    "correct": pred_side == target_side,
                    "target_margin": margin,
                    "used_chat_template": use_chat,
                })
                done += 1
                if done % 50 == 0 or done == total:
                    print(f"scored {done}/{total}", flush=True)
    result = {
        "experiment": "E79_glm_label_free_sibling",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "formats": formats,
        "used_chat_template": use_chat,
        "args": vars(args),
        "rows": rows,
        "summary": summarize(rows),
        "leakage_audit": {"manual_labels_in_prompt_rows": 0, "error_spans_in_prompt_rows": 0, "note_zh": "E79 prompt 只含题目与两条 trace；pair 的 valid/invalid 标签只用于离线评分。"},
        "scope_note_zh": "E79 检查 GLM/其他模型的 sibling 失败是否由 A/B 标签、位置或直接 contrastive 格式导致；label_free_two_pass 不要求模型输出 A/B。",
    }
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e79_label_free_sibling_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] in {"all", "format"}:
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
