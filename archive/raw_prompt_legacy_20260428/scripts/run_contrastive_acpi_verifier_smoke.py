#!/usr/bin/env python3
"""Contrastive verifier smoke on manually paired valid vs ACPI traces."""
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


def option_score(model, tokenizer, prompt_ids: list[int], option: str, device: torch.device) -> dict[str, Any]:
    forms = [option, " " + option, option + ".", " " + option + "."]
    scored = []
    for form in forms:
        option_ids = tokenizer.encode(form, add_special_tokens=False)
        if not option_ids:
            continue
        max_len = 6144
        keep_prompt = max(1, max_len - len(option_ids))
        ids = prompt_ids[-keep_prompt:] + option_ids
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attention_mask = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
        start = len(prompt_ids[-keep_prompt:])
        total = 0.0
        for j, tok_id in enumerate(option_ids):
            total += float(F.log_softmax(logits[start + j - 1], dim=-1)[tok_id].item())
        scored.append({"form": form, "sum_logprob": total, "avg_logprob": total / len(option_ids), "num_tokens": len(option_ids)})
    return max(scored, key=lambda x: x["avg_logprob"])


def en_prompt(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "You are comparing two mathematical reasoning traces for the same problem. "
        "Exactly one trace contains a mathematical or language-semantic process error. "
        "Ignore style, verbosity, truncation, and final-answer formatting. "
        "Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
        f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
    )


def zh_prompt(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "你正在比较同一道题的两段数学推理。恰好有一段包含数学或语言语义过程错误。"
        "请忽略风格、啰嗦程度、截断和最终答案格式，只判断推理过程是否有效。"
        "请选择推理过程无效的一段。只回答 A 或 B。\n"
        f"题目：\n{problem}\n\n推理 A：\n{trace_a}\n\n推理 B：\n{trace_b}\n\n无效推理："
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True, help="Verifier model key.")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/manual_e05_audit_combined_20260427.jsonl"))
    p.add_argument("--pairs-yaml", default=str(PROJECT / "configs/e11_real_acpi_pairs_extended.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E12_contrastive_acpi_verifier"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    manual = {json.loads(line)["e05_idx"]: json.loads(line) for line in Path(args.manual_jsonl).read_text(encoding="utf-8").splitlines() if line.strip()}
    pairs = read_yaml(args.pairs_yaml)["pairs"]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading verifier={args.model_key} on {args.device}; pairs={len(pairs)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    rows = []
    for pair in pairs:
        valid = manual[pair["valid_idx"]]
        bad = manual[pair["bad_idx"]]
        problem = bad["problem"]
        for prompt_lang in ["en", "zh"]:
            for order in ["bad_A", "bad_B"]:
                if order == "bad_A":
                    trace_a, trace_b, target = bad["completion"], valid["completion"], "A"
                else:
                    trace_a, trace_b, target = valid["completion"], bad["completion"], "B"
                prompt = en_prompt(problem, trace_a, trace_b) if prompt_lang == "en" else zh_prompt(problem, trace_a, trace_b)
                prompt_ids = tokenizer.encode(prompt, add_special_tokens=True)
                a_score = option_score(model, tokenizer, prompt_ids, "A", device)
                b_score = option_score(model, tokenizer, prompt_ids, "B", device)
                pred = "A" if a_score["avg_logprob"] >= b_score["avg_logprob"] else "B"
                rows.append(
                    {
                        "verifier_model_key": args.model_key,
                        "pair_id": pair["id"],
                        "trace_model_key": pair["model_key"],
                        "prompt_lang": prompt_lang,
                        "order": order,
                        "target": target,
                        "pred": pred,
                        "correct": pred == target,
                        "margin_target_minus_other": (a_score["avg_logprob"] - b_score["avg_logprob"]) if target == "A" else (b_score["avg_logprob"] - a_score["avg_logprob"]),
                        "a_avg_logprob": a_score["avg_logprob"],
                        "b_avg_logprob": b_score["avg_logprob"],
                        "bad_idx": pair["bad_idx"],
                        "valid_idx": pair["valid_idx"],
                        "bad_risk": bad["manual_risk"],
                        "valid_risk": valid["manual_risk"],
                    }
                )
                print(
                    f"pair={pair['id']} prompt={prompt_lang} order={order} target={target} pred={pred} "
                    f"margin={rows[-1]['margin_target_minus_other']:.3f}",
                    flush=True,
                )
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        for key in [("all", "all"), ("prompt_lang", r["prompt_lang"]), ("trace_model", r["trace_model_key"]), ("pair", r["pair_id"])]:
            groups.setdefault(key, []).append(r)
    summary = []
    for (slice_type, slice_name), g in sorted(groups.items()):
        summary.append(
            {
                "slice_type": slice_type,
                "slice": slice_name,
                "n": len(g),
                "acc": sum(x["correct"] for x in g) / len(g),
                "mean_margin": sum(x["margin_target_minus_other"] for x in g) / len(g),
            }
        )
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "verifier_model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "rows": rows,
        "summary": summary,
    }
    out = Path(args.out_dir) / f"{args.model_key}_contrastive_acpi_verifier.json"
    write_json(out, result)
    overall = next(x for x in summary if x["slice_type"] == "all")
    print(f"wrote {out}; rows={len(rows)} acc={overall['acc']:.3f} mean_margin={overall['mean_margin']:.3f}", flush=True)


if __name__ == "__main__":
    main()
