#!/usr/bin/env python3
"""E85 full-layer hidden cache for hard-task repaired/unrepaired ACPI cases.

This is a cache-oriented follow-up to E80. It keeps the same strict verifier
prompt, reveals key trace prefixes, saves final-token hidden states across all
layers to a .pt file, and reports all-layer validity-direction projections.
Manual labels/spans are used only to select rows/prefix positions offline.
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

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E57_AUDIT = PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl"
E61_DATA = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"

REPAIR_RE = re.compile(r"\b(wait|re-?read|double[- ]?check|check|but|however|actually|correct(?:ed|ly)?|using the actual|using the correct)\b|可是|但是|实际|正确|应当|应为|才是", re.IGNORECASE)
FINAL_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*[^\n]+", re.IGNORECASE | re.MULTILINE)


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
        "If any visible local step, definition, arithmetic operation, counting rule, unit conversion, semantic interpretation, or proof implication is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
        "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    )


def label_logprob(logits: torch.Tensor, tok, options: list[str]) -> tuple[float, str]:
    logp = F.log_softmax(logits.float(), dim=-1)
    scored = []
    for opt in options:
        ids = tok.encode(opt, add_special_tokens=False)
        if ids:
            scored.append((float(logp[int(ids[0])].item()), opt))
    return max(scored, key=lambda x: x[0])


def target_rows(model_key: str, mode: str) -> list[dict[str, Any]]:
    rows = [r for r in load_jsonl(E57_AUDIT) if r["model_key"] == model_key]
    if mode == "auto":
        if model_key == "gemma4_31b_it":
            mode = "repaired_acpi"
        elif model_key == "gemma4_26b_a4b_it":
            mode = "unrepaired_acpi"
        else:
            mode = "strict_acpi"
    if mode == "repaired_acpi":
        return [r for r in rows if r.get("manual_acpi_strict") and r.get("manual_repair_present")]
    if mode == "unrepaired_acpi":
        return [r for r in rows if r.get("manual_acpi_unrepaired")]
    if mode == "strict_acpi":
        return [r for r in rows if r.get("manual_acpi_strict")]
    raise ValueError(mode)


def prefix_points(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row["completion"]
    points = []
    err = row.get("manual_error_span") or ""
    if err and err in comp:
        s = comp.find(err)
        points.append({"stage": "error_span_end", "char_end": s + len(err), "span_text": err})
    first_final = next(FINAL_RE.finditer(comp), None)
    if first_final:
        points.append({"stage": "first_final_answer_end", "char_end": first_final.end(), "span_text": first_final.group(0)})
    err_pos = comp.find(err) if err else -1
    repair = None
    for m in REPAIR_RE.finditer(comp):
        if err_pos < 0 or m.start() > err_pos:
            repair = m
            break
    if repair:
        points.append({"stage": "repair_trigger_end", "char_end": repair.end(), "span_text": repair.group(0)})
        points.append({"stage": "post_repair_240chars", "char_end": min(len(comp), repair.end() + 240), "span_text": comp[repair.start(): min(len(comp), repair.end() + 240)]})
    last_final = None
    for m in FINAL_RE.finditer(comp):
        last_final = m
    if last_final:
        points.append({"stage": "last_final_answer_end", "char_end": last_final.end(), "span_text": last_final.group(0)})
    points.append({"stage": "completion_end", "char_end": len(comp), "span_text": comp[-120:]})
    seen = set(); out = []
    for p in sorted(points, key=lambda x: (x["char_end"], x["stage"])):
        key = (p["stage"], p["char_end"])
        if key not in seen:
            out.append(p); seen.add(key)
    return out


def all_layer_final_hidden(model, tok, prompt: str, add: bool, device: torch.device, max_len: int) -> tuple[torch.Tensor, dict[str, Any]]:
    ids = tok.encode(prompt, add_special_tokens=add)
    truncated_left = max(0, len(ids) - max_len)
    ids = ids[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
    hs = torch.stack([h[0, -1, :].detach().float().cpu() for h in out.hidden_states])
    yes, yes_opt = label_logprob(out.logits[0, -1], tok, [" Yes", "Yes", " yes", "yes"])
    no, no_opt = label_logprob(out.logits[0, -1], tok, [" No", "No", " no", "no"])
    meta = {"input_tokens": len(ids), "truncated_left_tokens": truncated_left, "yes_score": yes, "no_score": no, "yes_minus_no": yes - no, "pred_process_valid": yes > no, "yes_option": yes_opt, "no_option": no_opt}
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return hs, meta


def train_all_layer_directions(model, tok, use_chat: bool, device: torch.device, max_len: int) -> tuple[torch.Tensor, torch.Tensor]:
    rows = load_jsonl(E61_DATA)
    labels = torch.tensor([bool(r["manual_process_valid"]) for r in rows], dtype=torch.bool)
    feats = []
    for i, r in enumerate(rows, start=1):
        prompt, add = render_prompt(tok, strict_prompt(r["problem"], r["completion"]), use_chat)
        hs, _ = all_layer_final_hidden(model, tok, prompt, add, device, max_len)
        feats.append(hs)
        if i % 24 == 0 or i == len(rows):
            print(f"e61 all-layer hidden {i}/{len(rows)}", flush=True)
    X = torch.stack(feats)  # [n, layers, dim]
    pos = X[labels].mean(dim=0)
    neg = X[~labels].mean(dim=0)
    direction = pos - neg
    direction = direction / (direction.norm(dim=1, keepdim=True) + 1e-8)
    center = X.mean(dim=0)
    return direction, center


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for r in rows:
        groups[("all", "all")].append(r)
        groups[("stage", r["stage"])].append(r)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        out.append({
            "slice_type": typ,
            "slice": key,
            "n": len(vals),
            "accept_rate": sum(v["pred_process_valid"] for v in vals) / len(vals),
            "mean_yes_minus_no": mean(v["yes_minus_no"] for v in vals),
            "mean_best_layer_score": mean(v["best_layer_validity_score"] for v in vals),
            "mean_max_layer_score": mean(max(v["all_layer_validity_scores"]) for v in vals),
            "mean_min_layer_score": mean(min(v["all_layer_validity_scores"]) for v in vals),
        })
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E85_hardtask_full_hidden_cache"))
    p.add_argument("--target-mode", choices=["auto", "repaired_acpi", "unrepaired_acpi", "strict_acpi"], default="auto")
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = target_rows(args.model_key, args.target_mode)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E85 target_rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    direction, center = train_all_layer_directions(model, tok, use_chat, device, args.max_model_len)
    best_layer = args.best_layer if args.best_layer is not None else int(torch.argmax(torch.abs(direction).norm(dim=1)).item())
    cache_hs = []
    out_rows = []
    prefix_meta = []
    for row in rows:
        trace_class = "unrepaired_acpi" if row.get("manual_acpi_unrepaired") else ("repaired_acpi" if row.get("manual_acpi_strict") else "valid")
        for pt in prefix_points(row):
            prefix = row["completion"][: pt["char_end"]]
            prompt, add = render_prompt(tok, strict_prompt(row["problem"], prefix), use_chat)
            hs, meta = all_layer_final_hidden(model, tok, prompt, add, device, args.max_model_len)
            scores = ((hs - center) * direction).sum(dim=1)
            cache_hs.append(hs.to(torch.float16))
            cache_idx = len(cache_hs) - 1
            rec = {
                "cache_index": cache_idx,
                "source_model": row["model_key"],
                "verifier_model": args.model_key,
                "manual_audit_idx": row["manual_audit_idx"],
                "task_id": row["task_id"],
                "prompt_variant": row["prompt_variant"],
                "trace_class": trace_class,
                "manual_error_type": row.get("manual_error_type"),
                "manual_error_span": row.get("manual_error_span"),
                "stage": pt["stage"],
                "char_end": pt["char_end"],
                "span_text": pt["span_text"],
                "all_layer_validity_scores": [float(x) for x in scores.tolist()],
                "best_layer": best_layer,
                "best_layer_validity_score": float(scores[best_layer].item()),
                **meta,
            }
            out_rows.append(rec)
            prefix_meta.append({k: rec[k] for k in ["cache_index", "manual_audit_idx", "task_id", "stage", "trace_class"]})
            print(f"cached audit_idx={row['manual_audit_idx']} stage={pt['stage']}", flush=True)
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    pt_path = out_dir / f"{args.model_key}_e85_hidden_cache_{args.target_mode}_{suffix}.pt"
    hidden_tensor = torch.stack(cache_hs) if cache_hs else torch.empty(0)
    torch.save({"hidden_final_tokens": hidden_tensor, "prefix_meta": prefix_meta, "note": "shape [prefix, hidden_state_index, hidden_dim]; hidden_state_index includes embedding at 0"}, pt_path)
    result = {
        "experiment": "E85_hardtask_full_hidden_cache",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "target_mode": args.target_mode,
        "hidden_cache_pt": str(pt_path.relative_to(PROJECT)),
        "hidden_cache_shape": list(hidden_tensor.shape),
        "args": vars(args),
        "rows": out_rows,
        "summary": summarize(out_rows),
        "leakage_audit": {"labels_in_prompt_rows": 0, "error_spans_in_prompt_rows": 0, "gold_answer_in_prompt_rows": 0, "note_zh": "人工标签/span 只用于离线选择 prefix；prompt 只含 problem 与 visible trace prefix。"},
        "scope_note_zh": "E85 保存 key prefix 的全层 final-token hidden cache；不是全 token 全序列 cache。",
    }
    out = out_dir / f"{args.model_key}_e85_hidden_cache_{args.target_mode}_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print(f"wrote {pt_path}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] in {"all", "stage"}:
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
