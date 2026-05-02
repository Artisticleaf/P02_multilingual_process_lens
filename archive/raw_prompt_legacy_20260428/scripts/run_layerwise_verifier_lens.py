#!/usr/bin/env python3
"""Layerwise logit-lens probe for verifier decisions on ACPI sibling pairs."""
from __future__ import annotations

import argparse
import json
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, visible_device_label  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prompt_for(row: dict[str, Any], prompt_lang: str) -> str:
    trace = row["completion"]
    problem = row["problem"]
    if prompt_lang == "zh":
        return (
            "你是数学推理过程审计员。只判断推理过程中的数学步骤是否有效；"
            "不要因为最终答案格式缺失、截断或额外文本而判错。"
            "如果存在任何数学步骤错误，回答 否；如果可见推理步骤都数学有效，回答 是。只回答 是 或 否。\n"
            f"题目：{problem}\n"
            f"推理过程：{trace}\n"
            "可见推理步骤是否数学有效？答案："
        )
    return (
        "You are auditing a mathematical reasoning trace. Judge only whether the mathematical "
        "reasoning steps are valid; do not penalize missing final-answer formatting, truncation, "
        "or extra text after the answer. If any mathematical step is wrong, answer No. If the "
        "visible reasoning steps are mathematically valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {problem}\n"
        f"Reasoning trace: {trace}\n"
        "Are the visible reasoning steps mathematically valid? Answer:"
    )


def en_pair_prompt(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "You are comparing two mathematical reasoning traces for the same problem. "
        "Exactly one trace contains a mathematical or language-semantic process error. "
        "Ignore style, verbosity, truncation, and final-answer formatting. "
        "Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
        f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
    )


def zh_pair_prompt(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "你正在比较同一道题的两段数学推理。恰好有一段包含数学或语言语义过程错误。"
        "请忽略风格、啰嗦程度、截断和最终答案格式，只判断推理过程是否有效。"
        "请选择推理过程无效的一段。只回答 A 或 B。\n"
        f"题目：\n{problem}\n\n推理 A：\n{trace_a}\n\n推理 B：\n{trace_b}\n\n无效推理："
    )


def load_pairs(paths: list[Path]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    pairs: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        for pair in read_yaml(path)["pairs"]:
            if pair["id"] in seen:
                continue
            item = dict(pair)
            item["source_yaml"] = str(path)
            pairs.append(item)
            seen.add(item["id"])
    return pairs


def get_lm_head(model):
    for path in [
        ("lm_head",),
        ("language_model", "lm_head"),
        ("model", "lm_head"),
        ("model", "language_model", "lm_head"),
        ("model", "language_model", "model", "lm_head"),
    ]:
        obj = model
        ok = True
        for attr in path:
            if not hasattr(obj, attr):
                ok = False
                break
            obj = getattr(obj, attr)
        if ok:
            return obj
    emb = model.get_output_embeddings()
    if emb is None:
        raise AttributeError("Cannot locate LM head / output embeddings")
    return emb


def get_final_norm(model):
    for path in [
        ("model", "norm"),
        ("model", "language_model", "norm"),
        ("model", "language_model", "model", "norm"),
        ("language_model", "model", "norm"),
        ("transformer", "ln_f"),
        ("gpt_neox", "final_layer_norm"),
    ]:
        obj = model
        ok = True
        for attr in path:
            if not hasattr(obj, attr):
                ok = False
                break
            obj = getattr(obj, attr)
        if ok:
            return obj
    return None


def candidate_token_ids(tokenizer, forms: list[str]) -> list[int]:
    ids: list[int] = []
    for form in forms:
        toks = tokenizer.encode(form, add_special_tokens=False)
        if toks:
            ids.append(int(toks[0]))
    return sorted(set(ids))


def layerwise_margin(
    model,
    tokenizer,
    prompt: str,
    positive_token_ids: list[int],
    negative_token_ids: list[int],
    max_len: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    ids = tokenizer.encode(prompt, add_special_tokens=True)[-max_len:]
    input_device = next(model.parameters()).device
    input_ids = torch.tensor([ids], dtype=torch.long, device=input_device)
    attention_mask = torch.ones_like(input_ids, device=input_device)
    lm_head = get_lm_head(model)
    norm = get_final_norm(model)
    head_device = next(lm_head.parameters()).device
    norm_device = next(norm.parameters()).device if norm is not None and any(True for _ in norm.parameters()) else head_device
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False, output_hidden_states=True)
    hidden_states = out.hidden_states
    rows = []
    for layer_idx, hidden in enumerate(hidden_states):
        vec = hidden[0, -1, :]
        if norm is not None:
            vec = norm(vec.to(norm_device)).to(head_device)
        else:
            vec = vec.to(head_device)
        logits = lm_head(vec).float()
        pos = float(logits[positive_token_ids].max().item())
        neg = float(logits[negative_token_ids].max().item())
        rows.append({"layer": layer_idx - 1, "hidden_state_index": layer_idx, "positive_logit": pos, "negative_logit": neg, "margin": pos - neg})
    return rows, {"prompt_tokens": len(ids), "num_hidden_states": len(hidden_states)}


def compact_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    layers = [r["layer"] for r in rows]
    margins = [float(r["margin"]) for r in rows]
    final = margins[-1]
    max_i = max(range(len(rows)), key=lambda i: margins[i])
    min_i = min(range(len(rows)), key=lambda i: margins[i])
    real_layers = [r for r in rows if r["layer"] >= 0]
    if real_layers:
        lo = int(len(real_layers) * 0.25)
        hi = max(lo + 1, int(len(real_layers) * 0.75))
        middle = real_layers[lo:hi]
    else:
        middle = rows
    mid_best = max(float(r["margin"]) for r in middle)
    mid_best_layer = max(middle, key=lambda r: float(r["margin"]))["layer"]
    return {
        "final_margin": final,
        "max_margin": margins[max_i],
        "max_layer": layers[max_i],
        "min_margin": margins[min_i],
        "min_layer": layers[min_i],
        "middle_best_margin": mid_best,
        "middle_best_layer": mid_best_layer,
        "middle_to_final_drop": mid_best - final,
        "any_positive": any(m > 0 for m in margins),
        "final_positive": final > 0,
        "middle_positive": mid_best > 0,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/manual_e05_plus_e18_targeted_20260427.jsonl"))
    p.add_argument("--pairs-yaml", action="append", default=[], help="May be repeated.")
    p.add_argument("--out-dir", default=str(PROJECT / "results/E25_layerwise_verifier_lens"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="cuda")
    p.add_argument("--max-len", type=int, default=6144)
    p.add_argument("--prompt-langs", default="en,zh")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    pair_paths = [Path(p) for p in args.pairs_yaml] or [
        PROJECT / "configs/e11_real_acpi_pairs_extended.yaml",
        PROJECT / "configs/e18_manual_targeted_pairs.yaml",
        PROJECT / "configs/e22_e18_clean_sibling_pairs.yaml",
    ]
    pairs = load_pairs(pair_paths)
    manual = {int(row["audit_idx"]): row for row in read_jsonl(Path(args.manual_jsonl))}
    prompt_langs = [x.strip() for x in args.prompt_langs.split(",") if x.strip()]
    local_only = args.local_files_only or is_local_model(spec)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for layerwise lens on {args.device}", flush=True)
    tokenizer = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    yes_no = {
        "en": (
            candidate_token_ids(tokenizer, [" Yes", "Yes", " yes", "yes"]),
            candidate_token_ids(tokenizer, [" No", "No", " no", "no"]),
        ),
        "zh": (
            candidate_token_ids(tokenizer, [" 是", "是"]),
            candidate_token_ids(tokenizer, [" 否", "否", " 不", "不"]),
        ),
    }
    a_ids = candidate_token_ids(tokenizer, ["A", " A", "A.", " A."])
    b_ids = candidate_token_ids(tokenizer, ["B", " B", "B.", " B."])
    absolute_rows = []
    contrastive_rows = []
    unique_idxs = sorted({int(p["bad_idx"]) for p in pairs} | {int(p["valid_idx"]) for p in pairs})
    for idx in unique_idxs:
        if idx not in manual:
            continue
        row = manual[idx]
        target_valid = row.get("manual_process_valid") is True
        for prompt_lang in prompt_langs:
            pos, neg = yes_no[prompt_lang]
            lens_rows, meta = layerwise_margin(model, tokenizer, prompt_for(row, prompt_lang), pos, neg, args.max_len)
            stats = compact_stats(lens_rows)
            absolute_rows.append(
                {
                    "audit_idx": idx,
                    "trace_model_key": row["model_key"],
                    "task_id": row["task_id"],
                    "prompt_lang": prompt_lang,
                    "target_process_valid": target_valid,
                    "is_acpi": row.get("is_acpi"),
                    "manual_risk": row.get("manual_risk"),
                    "positive_label": "Yes/是",
                    "negative_label": "No/否",
                    "prompt_meta": meta,
                    "stats": stats,
                    "layers": lens_rows,
                }
            )
            print(f"absolute idx={idx} lang={prompt_lang} final={stats.get('final_margin'):.3f}", flush=True)
    for pair in pairs:
        bad = manual.get(int(pair["bad_idx"]))
        valid = manual.get(int(pair["valid_idx"]))
        if not bad or not valid:
            continue
        for prompt_lang in prompt_langs:
            for order in ["bad_A", "bad_B"]:
                if order == "bad_A":
                    trace_a, trace_b, target = bad["completion"], valid["completion"], "A"
                else:
                    trace_a, trace_b, target = valid["completion"], bad["completion"], "B"
                prompt = en_pair_prompt(bad["problem"], trace_a, trace_b) if prompt_lang == "en" else zh_pair_prompt(bad["problem"], trace_a, trace_b)
                pos, neg = (a_ids, b_ids) if target == "A" else (b_ids, a_ids)
                lens_rows, meta = layerwise_margin(model, tokenizer, prompt, pos, neg, args.max_len)
                stats = compact_stats(lens_rows)
                contrastive_rows.append(
                    {
                        "pair_id": pair["id"],
                        "trace_model_key": pair["model_key"],
                        "bad_idx": pair["bad_idx"],
                        "valid_idx": pair["valid_idx"],
                        "prompt_lang": prompt_lang,
                        "order": order,
                        "target": target,
                        "positive_label": target,
                        "negative_label": "B" if target == "A" else "A",
                        "bad_risk": bad.get("manual_risk"),
                        "prompt_meta": meta,
                        "stats": stats,
                        "layers": lens_rows,
                    }
                )
                print(f"contrastive pair={pair['id']} lang={prompt_lang} order={order} final={stats.get('final_margin'):.3f}", flush=True)
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "verifier_model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "absolute_rows": absolute_rows,
        "contrastive_rows": contrastive_rows,
    }
    out = Path(args.out_dir) / f"{args.model_key}_layerwise_verifier_lens.json"
    write_json(out, result)
    print(f"wrote {out}; absolute={len(absolute_rows)} contrastive={len(contrastive_rows)}", flush=True)


if __name__ == "__main__":
    main()
