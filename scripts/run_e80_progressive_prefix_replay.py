#!/usr/bin/env python3
"""E80 progressive-prefix verifier replay for hard-task ACPI traces.

Unlike E76/E77, this keeps the verifier prompt fixed and progressively reveals
longer prefixes of the saved trace. It trains an E61 residual validity direction
under the same verifier prompt, then records hidden projection and Yes/No margin
at each prefix. Manual spans are used only offline to choose truncation points.
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
E65_DIR = PROJECT / "results/E65_mechanistic_layer_sweep"

REPAIR_RE = re.compile(
    r"\b(wait|re-?read|double[- ]?check|check|but|however|actually|correct(?:ed|ly)?|using the actual|using the correct)\b|可是|但是|实际|正确|应当|应为|才是",
    re.IGNORECASE,
)
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


def verifier_prompt(problem: str, trace: str) -> str:
    return (
        "You are a strict trace-selection auditor. Judge the visible reasoning trace step by step. "
        "If any visible local step, definition, arithmetic operation, counting rule, unit conversion, semantic interpretation, or proof implication is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
        "Only answer Yes if every visible reasoning step is valid. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {trace}\n"
        "Under this strict any-wrong-step rule, are all visible reasoning steps valid? Answer:"
    )


def get_best_layer(model_key: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    path = E65_DIR / f"{model_key}_e65_e61_layer_sweep.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return int(data["best_all_layer"]["layer"])


def build_e61_items() -> list[dict[str, Any]]:
    return [
        {"problem": r["problem"], "completion": r["completion"], "label": bool(r["manual_process_valid"])}
        for r in load_jsonl(E61_DATA)
    ]


def collect_direction_features(model, tok, items: list[dict[str, Any]], use_chat: bool, device: torch.device, layer: int, max_model_len: int) -> torch.Tensor:
    feats = []
    for i, item in enumerate(items, start=1):
        text, add = render_prompt(tok, verifier_prompt(item["problem"], item["completion"]), use_chat)
        ids = tok.encode(text, add_special_tokens=add)[-max_model_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
        feats.append(out.hidden_states[layer][0, -1, :].detach().float().cpu())
        del out, input_ids, attn
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if i % 24 == 0 or i == len(items):
            print(f"direction hidden {i}/{len(items)}", flush=True)
    return torch.stack(feats)


def train_direction(X: torch.Tensor, labels: list[bool]) -> tuple[torch.Tensor, torch.Tensor]:
    y = torch.tensor(labels, dtype=torch.bool)
    pos = X[y].mean(dim=0)
    neg = X[~y].mean(dim=0)
    d = pos - neg
    d = d / (d.norm() + 1e-8)
    c = X.mean(dim=0)
    return d, c


def target_rows(model_key: str, mode: str) -> list[dict[str, Any]]:
    rows = [r for r in load_jsonl(E57_AUDIT) if r["model_key"] == model_key]
    if mode == "auto":
        if model_key == "gemma4_31b_it":
            return [r for r in rows if r.get("manual_acpi_strict") and r.get("manual_repair_present")]
        if model_key == "gemma4_26b_a4b_it":
            return [r for r in rows if r.get("manual_acpi_unrepaired")]
        return [r for r in rows if r.get("manual_acpi_strict")]
    if mode == "repaired_acpi":
        return [r for r in rows if r.get("manual_acpi_strict") and r.get("manual_repair_present")]
    if mode == "unrepaired_acpi":
        return [r for r in rows if r.get("manual_acpi_unrepaired")]
    if mode == "strict_acpi":
        return [r for r in rows if r.get("manual_acpi_strict")]
    raise ValueError(mode)


def prefix_points(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row["completion"]
    points: list[dict[str, Any]] = []
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


def label_logprob(logits: torch.Tensor, tok, options: list[str]) -> tuple[float, str]:
    logp = F.log_softmax(logits.float(), dim=-1)
    scored = []
    for opt in options:
        ids = tok.encode(opt, add_special_tokens=False)
        if ids:
            scored.append((float(logp[int(ids[0])].item()), opt))
    return max(scored, key=lambda x: x[0])


def score_prefix(model, tok, problem: str, prefix: str, use_chat: bool, device: torch.device, layer: int, direction: torch.Tensor, center: torch.Tensor, max_model_len: int) -> dict[str, Any]:
    text, add = render_prompt(tok, verifier_prompt(problem, prefix), use_chat)
    ids = tok.encode(text, add_special_tokens=add)
    truncated_left = max(0, len(ids) - max_model_len)
    ids = ids[-max_model_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
    last_logits = out.logits[0, -1]
    yes_score, yes_opt = label_logprob(last_logits, tok, [" Yes", "Yes", " yes", "yes"])
    no_score, no_opt = label_logprob(last_logits, tok, [" No", "No", " no", "no"])
    h = out.hidden_states[layer][0, -1, :].detach().float().cpu()
    validity_score = float((h - center) @ direction)
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {
        "input_tokens": len(ids),
        "truncated_left_tokens": truncated_left,
        "yes_score": yes_score,
        "no_score": no_score,
        "yes_minus_no": yes_score - no_score,
        "pred_process_valid": yes_score > no_score,
        "yes_option": yes_opt,
        "no_option": no_opt,
        "hidden_validity_score": validity_score,
    }


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[("all", "all")].append(r)
        groups[("stage", r["stage"])].append(r)
        groups[("trace_class", r["trace_class"])].append(r)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        out.append({
            "slice_type": typ,
            "slice": key,
            "n": len(vals),
            "accept_rate": sum(v["pred_process_valid"] for v in vals) / len(vals),
            "mean_yes_minus_no": mean(v["yes_minus_no"] for v in vals),
            "mean_hidden_validity_score": mean(v["hidden_validity_score"] for v in vals),
        })
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E80_progressive_prefix_replay"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--layer", type=int, default=None)
    p.add_argument("--target-mode", choices=["auto", "repaired_acpi", "unrepaired_acpi", "strict_acpi"], default="auto")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    layer = get_best_layer(args.model_key, args.layer)
    rows = target_rows(args.model_key, args.target_mode)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E80 layer={layer} target_rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    e61 = build_e61_items()
    X = collect_direction_features(model, tok, e61, use_chat, device, layer, args.max_model_len)
    direction, center = train_direction(X, [x["label"] for x in e61])
    out_rows = []
    for row in rows:
        cls = "unrepaired_acpi" if row.get("manual_acpi_unrepaired") else ("repaired_acpi" if row.get("manual_acpi_strict") else "valid")
        pts = prefix_points(row)
        print(f"row audit_idx={row['manual_audit_idx']} prefixes={len(pts)}", flush=True)
        for pt in pts:
            prefix = row["completion"][: pt["char_end"]]
            scored = score_prefix(model, tok, row["problem"], prefix, use_chat, device, layer, direction, center, args.max_model_len)
            out_rows.append({
                "source_model": row["model_key"],
                "verifier_model": args.model_key,
                "manual_audit_idx": row["manual_audit_idx"],
                "task_id": row["task_id"],
                "prompt_variant": row["prompt_variant"],
                "trace_class": cls,
                "manual_error_type": row.get("manual_error_type"),
                "manual_error_span": row.get("manual_error_span"),
                "manual_process_valid_strict": bool(row.get("manual_process_valid_strict")),
                "manual_process_valid_repaired": bool(row.get("manual_process_valid_repaired")),
                "stage": pt["stage"],
                "char_end": pt["char_end"],
                "prefix_chars": len(prefix),
                "span_text": pt["span_text"],
                **scored,
            })
    result = {
        "experiment": "E80_progressive_prefix_replay",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "layer": layer,
        "target_mode": args.target_mode,
        "used_chat_template": use_chat,
        "args": vars(args),
        "direction_source": "E61 strict verifier prompt, valid_mean_minus_invalid_mean at E65 best layer",
        "rows": out_rows,
        "summary": summarize(out_rows),
        "leakage_audit": {"labels_in_prompt_rows": 0, "error_spans_in_prompt_rows": 0, "gold_answer_in_prompt_rows": 0, "note_zh": "人工标签/span 只用于离线选择 prefix；模型 prompt 只含 problem 与已截断 visible trace。"},
        "scope_note_zh": "E80 是同一 verifier prompt 下的 prefix replay；它比 E76/E77 更适合解释 repair 过程中 hidden/logit 如何变化，但仍是 teacher-forced 已保存 trace。",
    }
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e80_prefix_replay_{args.target_mode}_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] in {"all", "stage"}:
            print("SUMMARY", s, flush=True)


if __name__ == "__main__":
    main()
