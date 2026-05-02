#!/usr/bin/env python3
"""E86 algebra-equivalence adversarial ACPI set.

Constructs no-leak valid/invalid trace siblings where a wrong algebraic step can
still lead to the same final answer because the downstream answer is invariant
to a sign/root-set mistake. Runs strict pointwise Yes/No, raw A/B sibling, and
label-free two-pass scoring across a verifier model.
"""
from __future__ import annotations

import argparse
import json
import math
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


def strict_prompt(problem: str, trace: str) -> str:
    return (
        "You are a strict trace-selection auditor. Judge the visible reasoning trace step by step. "
        "If any visible local step, algebraic factorization, root implication, arithmetic operation, counting rule, semantic interpretation, or proof implication is wrong, answer No, even if the final answer is correct. "
        "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    )


def sibling_prompt(problem: str, trace_a: str, trace_b: str) -> str:
    return (
        "You are comparing two reasoning traces for the same problem. Exactly one trace contains a local process error. "
        "Both traces may have the same final answer. Choose the trace whose reasoning process is invalid. Answer only A or B.\n"
        f"Problem:\n{problem}\n\nTrace A:\n{trace_a}\n\nTrace B:\n{trace_b}\n\nInvalid trace:"
    )


def pointwise_prompt(problem: str, trace: str) -> str:
    return (
        "You are checking process validity, not answer correctness. If the visible derivation contains a wrong local algebraic step, wrong root implication, or wrong counting rule, answer No. "
        "If the visible reasoning process is valid, answer Yes. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\nIs the visible reasoning process valid? Answer:"
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
    del input_ids, attention_mask, logits
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return total


def best_score(model, tokenizer, prompt: str, options: list[str], device: torch.device, max_model_len: int, add_special_tokens: bool) -> tuple[float, str]:
    scored = [(option_logprob(model, tokenizer, prompt, opt, device, max_model_len, add_special_tokens), opt) for opt in options]
    return max(scored, key=lambda x: x[0])


def factor_count(a: int, b: int, c: int, d: int, n: int) -> tuple[int, int, int]:
    g1 = math.gcd(a, b)
    k1 = min(n // (b // g1), n // (a // g1))
    g2 = math.gcd(c, d)
    k2 = min(n // (d // g2), n // (c // g2))
    return 2 * k1 + 1, 2 * k2 + 1, (2 * k1 + 1) + (2 * k2 + 1) - 1


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    params = [
        (3, 2, 4, 3, 100),
        (2, 5, 3, 4, 60),
        (5, 3, 2, 7, 80),
        (4, 1, 5, 6, 90),
        (7, 2, 3, 5, 70),
        (5, 4, 6, 1, 120),
    ]
    for i, (a, b, c, d, n) in enumerate(params, start=1):
        coef_x2 = a * c
        coef_xy = b * c - a * d
        coef_y2 = -b * d
        eq = f"{coef_x2}x^2"
        eq += f" {'+' if coef_xy >= 0 else '-'} {abs(coef_xy)}xy"
        eq += f" {'+' if coef_y2 >= 0 else '-'} {abs(coef_y2)}y^2"
        n1, n2, ans = factor_count(a, b, c, d, n)
        problem = f"Find the number of ordered integer pairs (x,y) with -{n} <= x <= {n} and -{n} <= y <= {n} satisfying {eq} = 0."
        valid_factor = f"({a}x + {b}y)({c}x - {d}y) = 0"
        invalid_factor = f"({a}x - {b}y)({c}x + {d}y) = 0"
        valid_trace = (
            f"The quadratic factors as {valid_factor}, since the xy coefficient is {b*c}-{a*d}={coef_xy}. "
            f"The first line {a}x+{b}y=0 gives {n1} integer pairs in the box, and the second line {c}x-{d}y=0 gives {n2} pairs. "
            f"The origin is counted twice, so the total is {n1}+{n2}-1={ans}.\nFinal answer: {ans}"
        )
        invalid_trace = (
            f"The quadratic factors as {invalid_factor}. Then {a}x-{b}y=0 gives {n1} integer pairs in the symmetric box, and {c}x+{d}y=0 gives {n2} pairs. "
            f"The origin is counted twice, so the total is {n1}+{n2}-1={ans}.\nFinal answer: {ans}"
        )
        cases.append({
            "case_id": f"factor_sign_{i}",
            "family": "factorization_sign_symmetry",
            "problem": problem,
            "gold_answer": str(ans),
            "valid_trace": valid_trace,
            "invalid_trace": invalid_trace,
            "invalid_error_span": invalid_factor,
            "plain_risk_zh": "错误地把两个一次因子的符号同时反过来；在对称整数区间计数时，最终数量可能不变，所以答案正确会掩盖错误分解。",
        })
    root_params = [(2, 3), (3, 4), (3, 5), (4, 5), (2, 7), (5, 6)]
    for i, (r, s) in enumerate(root_params, start=1):
        sm, prod = r + s, r * s
        problem = f"The roots of x^2 - {sm}x + {prod} = 0 are r and s. Find r*s."
        valid_factor = f"(x - {r})(x - {s})"
        invalid_factor = f"(x + {r})(x + {s})"
        valid_trace = f"We factor x^2 - {sm}x + {prod} as {valid_factor}, so the roots are {r} and {s}. Their product is {r}*{s}={prod}.\nFinal answer: {prod}"
        invalid_trace = f"We factor x^2 - {sm}x + {prod} as {invalid_factor}, so the roots are -{r} and -{s}. Their product is (-{r})*(-{s})={prod}.\nFinal answer: {prod}"
        cases.append({
            "case_id": f"root_product_{i}",
            "family": "root_sign_product_invariance",
            "problem": problem,
            "gold_answer": str(prod),
            "valid_trace": valid_trace,
            "invalid_trace": invalid_trace,
            "invalid_error_span": invalid_factor,
            "plain_risk_zh": "把二次式的根号符号整体弄反；题目只问根的乘积时，错误根集仍可能给出正确乘积。",
        })
    return cases



def label_logprob(model, tokenizer, prompt: str, options: list[str], device: torch.device, max_model_len: int, add_special_tokens: bool) -> tuple[float, str]:
    ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)[-max_model_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0, -1].float()
    logp = F.log_softmax(logits, dim=-1)
    scored = []
    for opt in options:
        opt_ids = tokenizer.encode(opt, add_special_tokens=False)
        if opt_ids:
            scored.append((float(logp[int(opt_ids[0])].item()), opt))
    del input_ids, attention_mask, logits
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return max(scored, key=lambda x: x[0])

def score_yes_no(model, tok, prompt: str, add: bool, device: torch.device, max_len: int) -> dict[str, Any]:
    yes, yes_opt = label_logprob(model, tok, prompt, [" Yes", "Yes", " yes", "yes"], device, max_len, add)
    no, no_opt = label_logprob(model, tok, prompt, [" No", "No", " no", "no"], device, max_len, add)
    return {"yes_score": yes, "no_score": no, "yes_minus_no": yes - no, "pred_process_valid": yes > no, "yes_option": yes_opt, "no_option": no_opt}


def score_ab(model, tok, prompt: str, add: bool, device: torch.device, max_len: int) -> dict[str, Any]:
    a, a_opt = label_logprob(model, tok, prompt, [" A", "A", " A.", "A."], device, max_len, add)
    b, b_opt = label_logprob(model, tok, prompt, [" B", "B", " B.", "B."], device, max_len, add)
    return {"a_score": a, "b_score": b, "a_minus_b": a - b, "pred_side": "A" if a >= b else "B", "a_option": a_opt, "b_option": b_opt}


def summarize(pointwise: list[dict[str, Any]], sibling: list[dict[str, Any]], label_free: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rows, name in [(pointwise, "pointwise_strict"), (sibling, "raw_ab_sibling"), (label_free, "label_free_two_pass")]:
        groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for r in rows:
            groups[("all", "all")].append(r)
            groups[("family", r["family"])].append(r)
        for (typ, key), vals in sorted(groups.items()):
            if name == "pointwise_strict":
                invalid = [v for v in vals if not v["gold_process_valid"]]
                valid = [v for v in vals if v["gold_process_valid"]]
                out.append({
                    "objective": name,
                    "slice_type": typ,
                    "slice": key,
                    "n": len(vals),
                    "accuracy": sum(v["pred_process_valid"] == v["gold_process_valid"] for v in vals) / len(vals),
                    "invalid_accept_rate": sum(v["pred_process_valid"] for v in invalid) / len(invalid) if invalid else None,
                    "valid_accept_rate": sum(v["pred_process_valid"] for v in valid) / len(valid) if valid else None,
                    "mean_margin": mean(v["yes_minus_no"] for v in vals),
                })
            else:
                out.append({
                    "objective": name,
                    "slice_type": typ,
                    "slice": key,
                    "n": len(vals),
                    "accuracy": sum(v["correct"] for v in vals) / len(vals),
                    "mean_target_margin": mean(v["target_margin"] for v in vals),
                    "predict_first_rate": sum(v["pred_side"] == "first" for v in vals) / len(vals),
                })
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E86_algebra_equivalence_adversarial"))
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
    cases = build_cases()
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E86 cases={len(cases)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    pointwise_rows: list[dict[str, Any]] = []
    sibling_rows: list[dict[str, Any]] = []
    label_free_rows: list[dict[str, Any]] = []
    for ci, case in enumerate(cases, start=1):
        for variant, trace, gold_valid in [("valid", case["valid_trace"], True), ("invalid_acpi", case["invalid_trace"], False)]:
            prompt, add = render_prompt(tok, strict_prompt(case["problem"], trace), use_chat)
            scored = score_yes_no(model, tok, prompt, add, device, args.max_model_len)
            pointwise_rows.append({
                **scored,
                "case_id": case["case_id"],
                "family": case["family"],
                "variant": variant,
                "gold_process_valid": gold_valid,
                "final_answer_correct_by_construction": True,
                "invalid_error_span_offline": case["invalid_error_span"] if not gold_valid else "",
            })
        for order in ["bad_first", "bad_second"]:
            if order == "bad_first":
                first, second, target = case["invalid_trace"], case["valid_trace"], "first"
            else:
                first, second, target = case["valid_trace"], case["invalid_trace"], "second"
            prompt, add = render_prompt(tok, sibling_prompt(case["problem"], first, second), use_chat)
            ab = score_ab(model, tok, prompt, add, device, args.max_model_len)
            pred = "first" if ab["pred_side"] == "A" else "second"
            target_margin = ab["a_minus_b"] if target == "first" else -ab["a_minus_b"]
            sibling_rows.append({
                **ab,
                "case_id": case["case_id"],
                "family": case["family"],
                "order": order,
                "target_side": target,
                "pred_side": pred,
                "correct": pred == target,
                "target_margin": target_margin,
            })
            p1, add1 = render_prompt(tok, pointwise_prompt(case["problem"], first), use_chat)
            p2, add2 = render_prompt(tok, pointwise_prompt(case["problem"], second), use_chat)
            s1 = score_yes_no(model, tok, p1, add1, device, args.max_model_len)
            s2 = score_yes_no(model, tok, p2, add2, device, args.max_model_len)
            inv1 = s1["no_score"] - s1["yes_score"]
            inv2 = s2["no_score"] - s2["yes_score"]
            pred_lf = "first" if inv1 >= inv2 else "second"
            margin = inv1 - inv2 if target == "first" else inv2 - inv1
            label_free_rows.append({
                "case_id": case["case_id"],
                "family": case["family"],
                "order": order,
                "target_side": target,
                "pred_side": pred_lf,
                "correct": pred_lf == target,
                "target_margin": margin,
                "invalid_score_first": inv1,
                "invalid_score_second": inv2,
                "first_yes_minus_no": s1["yes_minus_no"],
                "second_yes_minus_no": s2["yes_minus_no"],
            })
        print(f"case {ci}/{len(cases)}", flush=True)

    result = {
        "experiment": "E86_algebra_equivalence_adversarial",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "args": vars(args),
        "cases": cases,
        "pointwise_rows": pointwise_rows,
        "sibling_rows": sibling_rows,
        "label_free_rows": label_free_rows,
        "summary": summarize(pointwise_rows, sibling_rows, label_free_rows),
        "leakage_audit": {
            "gold_answer_in_problem_rows": 0,
            "manual_label_in_prompt_rows": 0,
            "error_span_annotation_in_prompt_rows": 0,
            "note_zh": "prompt 只含题目与可见 trace；valid/invalid 标签和错误 span 只用于离线评分。trace 中可见 final answer 是 trace-selection 场景本身，不是标签泄露。",
        },
        "scope_note_zh": "E86 专门考察代数等价/符号不变性陷阱：局部代数步骤错了，但最终答案因为符号对称或乘积不变仍正确。",
    }
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e86_algebra_equivalence_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] == "all":
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
