#!/usr/bin/env python3
"""E123 deep dive for E119/E146 unrepaired ACPI cases.

Builds visible-text variants of the two Gemma26 unrepaired integer-pairs cases
and scores them with a strict direct verifier plus a hidden process-validity
projection trained on E61. This asks whether the wrong factorization, final
answer anchor, and corrected factorization change readout and hidden evidence.
"""
from __future__ import annotations

import argparse
import json
import re
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

from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E61_DATA = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
E65_DIR = PROJECT / "results/E65_mechanistic_layer_sweep"
E119_E146_AUDIT = PROJECT / "data/processed/e119_e146_process_audit_official_20260430.jsonl"
FINAL_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*([^\n]+)", re.IGNORECASE | re.MULTILINE)


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


def strict_prompt(problem: str, trace: str) -> str:
    return (
        "You are a strict trace-selection auditor. Judge the visible reasoning trace step by step. "
        "If any visible local step, definition, arithmetic operation, counting rule, unit conversion, semantic interpretation, algebraic transformation, or proof implication is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
        "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    )


def yes_no_metrics(logits: torch.Tensor, tok) -> dict[str, Any]:
    logp = F.log_softmax(logits.float(), dim=-1)
    def best(options: list[str]) -> tuple[float, str]:
        vals = []
        for opt in options:
            ids = tok.encode(opt, add_special_tokens=False)
            if ids:
                vals.append((float(logp[int(ids[0])].item()), opt))
        return max(vals, key=lambda x: x[0])
    yes, yes_opt = best([" Yes", "Yes", " yes", "yes"])
    no, no_opt = best([" No", "No", " no", "no"])
    return {
        "yes_score": yes,
        "no_score": no,
        "yes_minus_no": yes - no,
        "pred_process_valid": yes > no,
        "readout_confidence": abs(yes - no),
        "yes_option": yes_opt,
        "no_option": no_opt,
    }


def best_layer_for(model_key: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    path = E65_DIR / f"{model_key}_e65_e61_layer_sweep.json"
    if path.exists():
        return int(read_json(path)["best_all_layer"]["layer"])
    return {"qwen35_27b": 34, "gemma4_31b_it": 34, "gemma4_26b_a4b_it": 17, "glm47_flash_candidate": 27}.get(model_key, 16)


def train_direction(model, tok, use_chat: bool, device: torch.device, best_layer: int, max_len: int, max_train: int) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    rows = load_jsonl(E61_DATA)
    if max_train:
        rows = sorted(rows, key=lambda r: (r["task_id"], bool(r["manual_process_valid"]), r["audit_idx"]))[:max_train]
    feats = []
    labels = []
    for i, row in enumerate(rows, start=1):
        prompt, add = render_prompt(tok, strict_prompt(row["problem"], row["completion"]), use_chat)
        ids = tok.encode(prompt, add_special_tokens=add)[-max_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids)
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
        feats.append(out.hidden_states[best_layer][0, -1, :].detach().float().cpu())
        labels.append(bool(row["manual_process_valid"]))
        del out, input_ids, attn
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if i % 24 == 0 or i == len(rows):
            print(f"E123 train direction {i}/{len(rows)}", flush=True)
    X = torch.stack(feats)
    y = torch.tensor(labels, dtype=torch.bool)
    direction = X[y].mean(0) - X[~y].mean(0)
    direction = direction / (direction.norm() + 1e-8)
    return direction, X.mean(0), {"train_rows": len(rows), "train_valid": int(y.sum()), "train_invalid": int((~y).sum())}


def replace_final(trace: str, replacement: str | None) -> str:
    matches = list(FINAL_RE.finditer(trace))
    if not matches:
        return trace
    m = matches[-1]
    if replacement is None:
        return trace[: m.start()] + trace[m.end():]
    return trace[: m.start()] + replacement + trace[m.end():]


def error_prefix(trace: str) -> str:
    patterns = [
        "(3x - 2y)(4x + 3y)",
        "(3x-2y)(4x+3y)",
        "(4x + 3y)(3x - 2y)",
    ]
    for pat in patterns:
        pos = trace.find(pat)
        if pos >= 0:
            return trace[: pos + len(pat)]
    return trace[: min(len(trace), 900)]


def corrected_solution_trace(row: dict[str, Any]) -> str:
    return (
        "We need solve 12x^2 - xy - 6y^2 = 0. "
        "The correct factorization is (3x + 2y)(4x - 3y)=0, since it expands to 12x^2 - 9xy + 8xy - 6y^2 = 12x^2 - xy - 6y^2. "
        "So either 3x + 2y=0 or 4x - 3y=0. "
        "In the first case x=2k and y=-3k, and the bounds give -33<=k<=33, so 67 pairs. "
        "In the second case x=3m and y=4m, and the bounds give -25<=m<=25, so 51 pairs. "
        "The only overlap is (0,0), so the total is 67+51-1=117.\n"
        "Final answer: 117"
    )


def explicit_repair_trace(row: dict[str, Any]) -> str:
    wrong = error_prefix(row["completion"])
    return (
        wrong
        + "\nWait, this factorization is wrong: (3x - 2y)(4x + 3y) expands to 12x^2 + xy - 6y^2, not 12x^2 - xy - 6y^2. "
        + corrected_solution_trace(row)
    )


def variants_for(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row["completion"]
    return [
        {"variant": "original_unrepaired", "trace": comp, "target_strict_valid": False, "note": "Original final-correct unrepaired ACPI."},
        {"variant": "error_prefix_only", "trace": error_prefix(comp), "target_strict_valid": False, "note": "Only through the wrong factorization."},
        {"variant": "final_removed", "trace": replace_final(comp, None), "target_strict_valid": False, "note": "Remove final answer line; wrong process remains."},
        {"variant": "final_wrong", "trace": replace_final(comp, "Final answer: 118"), "target_strict_valid": False, "note": "Wrong final answer control."},
        {"variant": "explicit_repair_inserted", "trace": explicit_repair_trace(row), "target_strict_valid": False, "note": "Wrong step appears, then explicit repair; strict invalid but repair-aware valid."},
        {"variant": "corrected_solution_only", "trace": corrected_solution_trace(row), "target_strict_valid": True, "note": "Clean corrected proof without the wrong factorization."},
    ]


def score(model, tok, prompt: str, add: bool, device: torch.device, max_len: int, best_layer: int, direction: torch.Tensor, center: torch.Tensor) -> dict[str, Any]:
    ids = tok.encode(prompt, add_special_tokens=add)[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
    metrics = yes_no_metrics(out.logits[0, -1], tok)
    vec = out.hidden_states[best_layer][0, -1, :].detach().float().cpu()
    metrics["hidden_process_score"] = float(((vec - center) @ direction).item())
    metrics["hidden_pred_process_valid"] = metrics["hidden_process_score"] > 0
    metrics["input_tokens"] = len(ids)
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return metrics


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups["all"].append(row)
        groups[row["variant"]].append(row)
    out = []
    for key, vals in sorted(groups.items()):
        out.append(
            {
                "slice": key,
                "n": len(vals),
                "strict_invalid_accept_rate": sum(v["pred_process_valid"] and not v["target_strict_valid"] for v in vals) / len(vals),
                "strict_valid_accept_rate": sum(v["pred_process_valid"] and v["target_strict_valid"] for v in vals) / max(1, sum(v["target_strict_valid"] for v in vals)),
                "mean_yes_minus_no": mean(v["yes_minus_no"] for v in vals),
                "mean_hidden_process_score": mean(v["hidden_process_score"] for v in vals),
            }
        )
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--verifier-model-key", default="gemma4_26b_a4b_it")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E123_unrepaired_case_deepdive"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--max-train-items", type=int, default=0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.verifier_model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.verifier_model_key} for E123", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    best = best_layer_for(args.verifier_model_key, args.best_layer)
    direction, center, train_meta = train_direction(model, tok, use_chat, device, best, args.max_model_len, args.max_train_items)

    source_rows = [r for r in load_jsonl(E119_E146_AUDIT) if r.get("manual_acpi_unrepaired")]
    rows_out = []
    for row in source_rows:
        for variant in variants_for(row):
            prompt, add = render_prompt(tok, strict_prompt(row["problem"], variant["trace"]), use_chat)
            metrics = score(model, tok, prompt, add, device, args.max_model_len, best, direction, center)
            rows_out.append(
                {
                    "audit_idx": row["audit_idx"],
                    "source_model": row["model_key"],
                    "run_id": row["run_id"],
                    "task_id": row["task_id"],
                    "variant": variant["variant"],
                    "variant_note": variant["note"],
                    "target_strict_valid": variant["target_strict_valid"],
                    **metrics,
                }
            )
            print(f"E123 scored audit_idx={row['audit_idx']} variant={variant['variant']}", flush=True)
    result = {
        "experiment": "E123_unrepaired_case_deepdive",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "verifier_model_key": args.verifier_model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "best_hidden_layer": best,
        "args": vars(args),
        "train_direction_meta": train_meta,
        "rows": rows_out,
        "summary": summarize(rows_out),
        "leakage_audit": {
            "gold_answer_in_prompt_rows": 0,
            "manual_labels_in_prompt_rows": 0,
            "error_span_annotation_in_prompt_rows": 0,
            "note_zh": "人工标签只用于离线选择两条 unrepaired case 和构造文本变体；strict verifier prompt 只含 problem 与 visible trace。",
        },
        "scope_note_zh": "E123 是两条自然 unrepaired ACPI 的 case-study，不估计自然发生率。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.verifier_model_key}_e123_unrepaired_case_deepdive_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print(json.dumps({"summary": result["summary"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
