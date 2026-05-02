#!/usr/bin/env python3
"""Run order-balanced E42 contrastive sibling verification on E39 pairs."""
from __future__ import annotations

import argparse
import json
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def option_score(model, tokenizer, prompt_ids: list[int], option: str, device: torch.device, max_model_len: int) -> dict[str, Any]:
    forms = [option, " " + option, option + ".", " " + option + "."]
    scored = []
    for form in forms:
        option_ids = tokenizer.encode(form, add_special_tokens=False)
        if not option_ids:
            continue
        keep_prompt = max(1, max_model_len - len(option_ids))
        kept_prompt_ids = prompt_ids[-keep_prompt:]
        ids = kept_prompt_ids + option_ids
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attention_mask = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
        start = len(kept_prompt_ids)
        total = 0.0
        for j, tok_id in enumerate(option_ids):
            total += float(F.log_softmax(logits[start + j - 1], dim=-1)[tok_id].item())
        scored.append({"form": form, "sum_logprob": total, "avg_logprob": total / len(option_ids), "num_tokens": len(option_ids)})
    if not scored:
        raise ValueError(f"No tokenization for option {option!r}")
    return max(scored, key=lambda x: x["avg_logprob"])


def prompt_en(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "You are comparing two reasoning traces for the same math problem. "
        "Exactly one trace has a local mathematical or language-semantic process error, although both may end with the same final answer. "
        "Ignore style and verbosity. Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
        f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
    )


def prompt_zh(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "你正在比较同一道数学题的两段推理。恰好有一段包含局部数学错误或语言语义过程错误，虽然两段可能给出相同最终答案。"
        "请忽略风格和啰嗦程度，只选择推理过程无效的一段。只回答 A 或 B。\n"
        f"题目：\n{problem}\n\n推理 A：\n{trace_a}\n\n推理 B：\n{trace_b}\n\n无效推理："
    )


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        for key in [("all", "all"), ("prompt_lang", r["prompt_lang"]), ("order", r["order"]), ("task", r["task_id"]), ("pred", r["pred"])]:
            groups.setdefault(key, []).append(r)
    out = []
    for (slice_type, slice_name), g in sorted(groups.items()):
        out.append(
            {
                "slice_type": slice_type,
                "slice": slice_name,
                "n": len(g),
                "accuracy": sum(x["correct"] for x in g) / len(g),
                "mean_target_margin": sum(x["margin_target_minus_other"] for x in g) / len(g),
                "pred_A_rate": sum(x["pred"] == "A" for x in g) / len(g),
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl"))
    p.add_argument("--pairs-yaml", default=str(PROJECT / "configs/e42_e39_objective_pairs.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E42_e39_objective_matrix_contrastive"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--prompt-langs", default="en,zh")
    p.add_argument("--max-model-len", type=int, default=6144)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    manual = {r["audit_idx"]: r for r in load_jsonl(Path(args.manual_jsonl))}
    pairs = read_yaml(args.pairs_yaml)["pairs"]
    prompt_langs = [x.strip() for x in args.prompt_langs.split(",") if x.strip()]

    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading verifier={args.model_key} device={args.device} pairs={len(pairs)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    rows = []
    for pair in pairs:
        valid = manual[int(pair["valid_idx"])]
        bad = manual[int(pair["bad_idx"])]
        problem = bad["problem"]
        for prompt_lang in prompt_langs:
            for order in ["bad_A", "bad_B"]:
                if order == "bad_A":
                    trace_a, trace_b, target = bad["completion"], valid["completion"], "A"
                else:
                    trace_a, trace_b, target = valid["completion"], bad["completion"], "B"
                prompt = prompt_en(problem, trace_a, trace_b) if prompt_lang == "en" else prompt_zh(problem, trace_a, trace_b)
                prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
                a_score = option_score(model, tokenizer, prompt_ids, "A", device, args.max_model_len)
                b_score = option_score(model, tokenizer, prompt_ids, "B", device, args.max_model_len)
                pred = "A" if a_score["avg_logprob"] >= b_score["avg_logprob"] else "B"
                margin = (a_score["avg_logprob"] - b_score["avg_logprob"]) if target == "A" else (b_score["avg_logprob"] - a_score["avg_logprob"])
                row = {
                    "verifier_model_key": args.model_key,
                    "pair_id": pair["id"],
                    "task_id": pair["task_id"],
                    "prompt_lang": prompt_lang,
                    "order": order,
                    "target": target,
                    "pred": pred,
                    "correct": pred == target,
                    "margin_target_minus_other": margin,
                    "a_avg_logprob": a_score["avg_logprob"],
                    "b_avg_logprob": b_score["avg_logprob"],
                    "bad_idx": bad["audit_idx"],
                    "valid_idx": valid["audit_idx"],
                    "bad_error_span": pair.get("error_span"),
                    "valid_support_span": pair.get("support_span"),
                }
                rows.append(row)
                print(
                    f"task={pair['task_id']} prompt={prompt_lang} order={order} target={target} pred={pred} margin={margin:.3f}",
                    flush=True,
                )

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "verifier_model_key": args.model_key,
        "backend": "hf",
        "model_spec": spec,
        "args": vars(args),
        "rows": rows,
        "summary": summarize(rows),
    }
    out = Path(args.out_dir) / f"{args.model_key}_e42_contrastive_objective.json"
    write_json(out, result)
    overall = next(s for s in result["summary"] if s["slice_type"] == "all")
    print(f"wrote {out}; rows={len(rows)} acc={overall['accuracy']:.3f} mean_margin={overall['mean_target_margin']:.3f}", flush=True)


if __name__ == "__main__":
    main()
