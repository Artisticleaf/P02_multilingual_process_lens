#!/usr/bin/env python3
"""E76/E77 hard-task hidden replay.

Teacher-forced replay of saved E57 hard-task traces. It trains a best-layer
process-validity direction on E61 controlled traces, then scores key spans in
hard-task repaired/unrepaired ACPI traces. No hard-task labels or spans enter the
model prompt; annotations are used only to choose offline analysis positions.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E57_AUDIT = PROJECT / "data/processed/e57_final_correct_manual_audit_20260428.jsonl"
E61_DATA = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
E65_DIR = PROJECT / "results/E65_mechanistic_layer_sweep"

PROMPT_VARIANTS = {
    "neutral": (
        "Solve the following AIME-style problem carefully. Show the reasoning needed to justify the result. "
        "End with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
    ),
    "answer_first_no_gold": (
        "Solve the following AIME-style problem yourself. First write one line `Final answer: <integer>`, "
        "then give a concise justification. No final answer is provided in the prompt.\n\nProblem: {problem}"
    ),
    "self_check": (
        "Solve the following AIME-style problem. After deriving an answer, do one brief self-check for the main trap, "
        "then end with exactly one line `Final answer: <integer>`.\n\nProblem: {problem}"
    ),
}

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


def render_chat(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content + "\nReasoning:", True
    messages = [{"role": "user", "content": content}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), False


def process_prompt(problem: str, completion: str) -> str:
    return (
        "You are auditing a reasoning trace. Judge only whether the reasoning steps are valid. "
        "If any mathematical, code-execution, table-reading, unit, language-semantic, or proof step is wrong, "
        "the process is invalid even if the final answer is correct. Answer only Yes or No.\n"
        f"Problem: {problem}\nReasoning trace: {completion}\nAre the visible reasoning steps valid? Answer:"
    )


def get_best_layer(model_key: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    path = E65_DIR / f"{model_key}_e65_e61_layer_sweep.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return int(data["best_all_layer"]["layer"])


def build_e61_items() -> list[dict[str, Any]]:
    return [{"problem": r["problem"], "completion": r["completion"], "label": bool(r["manual_process_valid"])} for r in load_jsonl(E61_DATA)]


def collect_final_features(model, tok, items: list[dict[str, Any]], use_chat: bool, device: torch.device, layer: int, max_model_len: int) -> torch.Tensor:
    feats = []
    for i, item in enumerate(items, start=1):
        prompt, add = render_chat(tok, process_prompt(item["problem"], item["completion"]), use_chat)
        ids = tok.encode(prompt, add_special_tokens=add)[-max_model_len:]
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


def target_rows(model_key: str, mode: str, max_rows: int | None) -> list[dict[str, Any]]:
    rows = [r for r in load_jsonl(E57_AUDIT) if r["model_key"] == model_key]
    if mode == "auto":
        if model_key == "gemma4_31b_it":
            rows = [r for r in rows if r.get("manual_acpi_strict") and r.get("manual_repair_present")]
        elif model_key == "gemma4_26b_a4b_it":
            rows = [r for r in rows if r.get("manual_acpi_unrepaired")]
        else:
            rows = [r for r in rows if r.get("manual_acpi_strict")]
    elif mode == "repaired_acpi":
        rows = [r for r in rows if r.get("manual_acpi_strict") and r.get("manual_repair_present")]
    elif mode == "unrepaired_acpi":
        rows = [r for r in rows if r.get("manual_acpi_unrepaired")]
    elif mode == "valid":
        rows = [r for r in rows if r.get("manual_process_valid_strict")]
    else:
        raise ValueError(mode)
    return rows[:max_rows] if max_rows else rows


def token_index_for_char(tok, full_text: str, add_special: bool, char_end: int) -> int | None:
    try:
        enc = tok(full_text, return_offsets_mapping=True, add_special_tokens=add_special)
        offsets = enc["offset_mapping"]
        candidates = [i for i, (s, e) in enumerate(offsets) if e and e <= char_end]
        if candidates:
            return candidates[-1]
    except Exception:
        pass
    try:
        return max(0, len(tok.encode(full_text[:char_end], add_special_tokens=add_special)) - 1)
    except Exception:
        return None


def stage_char_spans(row: dict[str, Any], prompt_len: int) -> list[dict[str, Any]]:
    comp = row["completion"]
    spans = []
    err = row.get("manual_error_span") or ""
    if err and err in comp:
        s = comp.find(err); spans.append({"stage": "error_span_end", "span_text": err, "char_end": prompt_len + s + len(err)})
    first_final = next(FINAL_RE.finditer(comp), None)
    if first_final:
        spans.append({"stage": "first_final_answer_end", "span_text": first_final.group(0), "char_end": prompt_len + first_final.end()})
    last_final = None
    for m in FINAL_RE.finditer(comp):
        last_final = m
    if last_final:
        spans.append({"stage": "last_final_answer_end", "span_text": last_final.group(0), "char_end": prompt_len + last_final.end()})
    err_pos = comp.find(err) if err else -1
    repair = None
    for m in REPAIR_RE.finditer(comp):
        if err_pos < 0 or m.start() > err_pos:
            repair = m; break
    if repair:
        spans.append({"stage": "repair_trigger_end", "span_text": repair.group(0), "char_end": prompt_len + repair.end()})
    spans.append({"stage": "completion_end", "span_text": comp[-80:], "char_end": prompt_len + len(comp)})
    # De-duplicate same stage/position while preserving order.
    seen = set(); out = []
    for sp in spans:
        key = (sp["stage"], sp["char_end"])
        if key not in seen:
            out.append(sp); seen.add(key)
    return out


def replay_row(model, tok, row: dict[str, Any], use_chat: bool, device: torch.device, layer: int, direction: torch.Tensor, center: torch.Tensor, max_model_len: int) -> dict[str, Any]:
    content = PROMPT_VARIANTS[row["prompt_variant"]].format(problem=row["problem"])
    prompt, add = render_chat(tok, content, use_chat)
    full_text = prompt + row["completion"]
    ids = tok.encode(full_text, add_special_tokens=add)
    truncated_left = 0
    if len(ids) > max_model_len:
        truncated_left = len(ids) - max_model_len
        ids = ids[-max_model_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
    H = out.hidden_states[layer][0].detach().float().cpu()
    stage_rows = []
    for sp in stage_char_spans(row, len(prompt)):
        pos = token_index_for_char(tok, full_text, add, sp["char_end"])
        if pos is None:
            continue
        pos_adj = pos - truncated_left
        if pos_adj < 0 or pos_adj >= H.shape[0]:
            continue
        score = float((H[pos_adj] - center) @ direction)
        stage_rows.append({**sp, "token_index_full": pos, "token_index_used": pos_adj, "validity_score": score})
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {
        "source_model": row["model_key"],
        "manual_audit_idx": row["manual_audit_idx"],
        "task_id": row["task_id"],
        "prompt_variant": row["prompt_variant"],
        "trace_class": "unrepaired_acpi" if row.get("manual_acpi_unrepaired") else ("repaired_acpi" if row.get("manual_acpi_strict") else "valid"),
        "manual_process_valid_strict": bool(row.get("manual_process_valid_strict")),
        "manual_process_valid_repaired": bool(row.get("manual_process_valid_repaired")),
        "manual_error_type": row.get("manual_error_type"),
        "manual_error_span": row.get("manual_error_span"),
        "input_tokens": len(ids),
        "truncated_left_tokens": truncated_left,
        "stage_scores": stage_rows,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E76_E77_hardtask_hidden_replay"))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--layer", type=int, default=None)
    p.add_argument("--target-mode", choices=["auto", "repaired_acpi", "unrepaired_acpi", "valid"], default="auto")
    p.add_argument("--max-rows", type=int, default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = target_rows(args.model_key, args.target_mode, args.max_rows)
    layer = get_best_layer(args.model_key, args.layer)
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E76/E77 layer={layer} target_rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    e61 = build_e61_items()
    X = collect_final_features(model, tok, e61, use_chat, device, layer, args.max_model_len)
    direction, center = train_direction(X, [x["label"] for x in e61])
    replay = []
    for i, row in enumerate(rows, start=1):
        print(f"replay {i}/{len(rows)} audit_idx={row['manual_audit_idx']}", flush=True)
        replay.append(replay_row(model, tok, row, use_chat, device, layer, direction, center, args.max_model_len))
    result = {
        "experiment": "E76_E77_hardtask_hidden_replay",
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
        "direction_source": "E61 all rows valid_mean_minus_invalid_mean at E65 best layer",
        "rows": replay,
        "summary": {
            "n_rows": len(replay),
            "stage_mean_scores": {
                stage: mean(vals) for stage, vals in _stage_values(replay).items() if vals
            },
        },
        "leakage_audit": {"hard_task_labels_in_prompt_rows": 0, "error_spans_in_prompt_rows": 0, "note_zh": "hard-task 人工标签和 span 只用于离线选择分析 token；模型输入为原始 problem prompt + saved completion。"},
        "scope_note_zh": "E76/E77 是 teacher-forced hidden replay；它复现已保存可见路径的 hidden 轨迹，不声称重采样随机路径 bit-level 可复现。",
    }
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    out = out_dir / f"{args.model_key}_e76_e77_hidden_replay_{args.target_mode}_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print("SUMMARY", result["summary"], flush=True)


def _stage_values(replay: list[dict[str, Any]]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for row in replay:
        for sp in row.get("stage_scores", []):
            out.setdefault(sp["stage"], []).append(float(sp["validity_score"]))
    return out


if __name__ == "__main__":
    main()
