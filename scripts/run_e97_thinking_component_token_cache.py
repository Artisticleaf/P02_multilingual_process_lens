#!/usr/bin/env python3
"""E97 thinking-mode token/component activation cache.

This script replays thinking-generation outputs with the same source model and
stores selected token activations.  It is post-hoc mechanism capture, not a
blind verifier run: manual labels/spans are used only offline to select rows and
token positions; they are never inserted into the model prompt.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402
from run_e49_hard_task_conditioning_official import PROMPT_VARIANTS, render_prompt as render_e49_prompt  # noqa: E402
from run_e90_hardtask_component_activation_cache import (  # noqa: E402
    REPAIR_RE,
    best_hidden_layer,
    build_component_plan,
    extract_output,
    selected_hidden_layers,
    train_component_directions,
)


ANSWER_LINE_RE = re.compile(
    r"^\s*.*\b(final\s+answer|answer|sum|result)\b\s*(?:is|=|:)?\s*.*$",
    re.IGNORECASE | re.MULTILINE,
)
FINAL_LINE_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*[^\n]+", re.IGNORECASE | re.MULTILINE)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    audit = Path(args.audit_jsonl) if args.audit_jsonl else None
    if audit and audit.exists() and audit.stat().st_size:
        rows = read_jsonl(audit)
        for i, row in enumerate(rows):
            row.setdefault("e97_row_source", str(audit.relative_to(PROJECT)))
            row.setdefault("e97_source_index", i)
        return rows
    rows: list[dict[str, Any]] = []
    for p in sorted(PROJECT.glob(args.input_json_glob)):
        data = read_json(p)
        if not isinstance(data, dict) or "rows" not in data:
            continue
        for i, row in enumerate(data["rows"]):
            rec = dict(row)
            rec.setdefault("e97_row_source", str(p.relative_to(PROJECT)))
            rec.setdefault("e97_source_index", i)
            rows.append(rec)
    return rows


def truthy(row: dict[str, Any], *keys: str) -> bool:
    return any(bool(row.get(k)) for k in keys)


def row_class(row: dict[str, Any]) -> str:
    if truthy(row, "manual_acpi_unrepaired"):
        return "unrepaired_acpi"
    if truthy(row, "manual_acpi_strict") and truthy(row, "manual_repair_present"):
        return "repaired_acpi"
    if truthy(row, "manual_acpi_strict"):
        return "strict_acpi"
    if truthy(row, "manual_process_valid", "manual_process_valid_strict"):
        return "strict_valid"
    if truthy(row, "manual_final_correct"):
        return "final_correct_unlabeled"
    return "not_final_correct_or_unlabeled"


def keep_row(row: dict[str, Any], model_key: str, row_filter: str) -> bool:
    if row.get("model_key") != model_key:
        return False
    cls = row_class(row)
    if row_filter == "all":
        return True
    if row_filter == "final_correct":
        return bool(row.get("manual_final_correct"))
    if row_filter == "repair_marker":
        return bool(REPAIR_RE.search(row.get("completion", "")))
    return cls == row_filter


def completion_points(row: dict[str, Any]) -> list[dict[str, Any]]:
    comp = row.get("completion", "")
    points: list[dict[str, Any]] = []
    if not comp:
        return points
    points.append({"stage": "completion_start_prompt_last_token", "char_end": 0, "span_text": ""})
    points.append({"stage": "early_thought_240chars", "char_end": min(len(comp), 240), "span_text": comp[:240]})
    if len(comp) > 640:
        mid = len(comp) // 2
        points.append({"stage": "completion_midpoint", "char_end": mid, "span_text": comp[max(0, mid - 80) : min(len(comp), mid + 80)]})
    err = row.get("manual_error_span") or ""
    err_pos = comp.find(err) if err else -1
    if err_pos >= 0:
        points.append({"stage": "error_span_end", "char_end": err_pos + len(err), "span_text": err})
    repair = None
    for m in REPAIR_RE.finditer(comp):
        if err_pos < 0 or m.start() > err_pos:
            repair = m
            break
    if repair:
        points.append({"stage": "repair_marker_end", "char_end": repair.end(), "span_text": repair.group(0)})
        points.append(
            {
                "stage": "post_repair_240chars",
                "char_end": min(len(comp), repair.end() + 240),
                "span_text": comp[repair.start() : min(len(comp), repair.end() + 240)],
            }
        )
    first_final = next(FINAL_LINE_RE.finditer(comp), None)
    if first_final:
        points.append({"stage": "first_final_answer_line_end", "char_end": first_final.end(), "span_text": first_final.group(0)})
    last_final = None
    for m in FINAL_LINE_RE.finditer(comp):
        last_final = m
    if last_final:
        points.append({"stage": "last_final_answer_line_end", "char_end": last_final.end(), "span_text": last_final.group(0)})
    answer_line = None
    for m in ANSWER_LINE_RE.finditer(comp):
        answer_line = m
    if answer_line:
        points.append({"stage": "last_answer_phrase_line_end", "char_end": answer_line.end(), "span_text": answer_line.group(0)})
    points.append({"stage": "completion_end", "char_end": len(comp), "span_text": comp[-240:]})
    seen: set[tuple[str, int]] = set()
    out = []
    for p in sorted(points, key=lambda x: (x["char_end"], x["stage"])):
        key = (p["stage"], int(p["char_end"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def render_source_prompt(tokenizer: Any, spec: dict[str, Any], row: dict[str, Any]) -> tuple[str, bool, bool]:
    variant = row.get("prompt_variant", "neutral")
    if variant not in PROMPT_VARIANTS:
        raise ValueError(f"Unknown prompt_variant={variant}")
    task = {"en": row["problem"], "answer": row.get("gold_answer", "")}
    prompt, used_chat, add_special, _gold = render_e49_prompt(tokenizer, spec, task, variant, thinking=True)
    return prompt, used_chat, add_special


def point_token_positions(tokenizer: Any, prompt: str, completion: str, add_special: bool, points: list[dict[str, Any]], max_len: int) -> tuple[list[int], list[dict[str, Any]], int, int]:
    full = prompt + completion
    ids = tokenizer.encode(full, add_special_tokens=add_special)
    truncated_left = max(0, len(ids) - max_len)
    kept_len = len(ids[-max_len:])
    usable_points: list[dict[str, Any]] = []
    positions: list[int] = []
    for pt in points:
        char_end = int(pt["char_end"])
        if char_end <= 0:
            pos = len(tokenizer.encode(prompt, add_special_tokens=add_special)) - 1
        else:
            prefix = full[: len(prompt) + char_end]
            pos = len(tokenizer.encode(prefix, add_special_tokens=add_special)) - 1
        adj = pos - truncated_left
        rec = dict(pt)
        rec.update({"original_token_pos": pos, "truncated_token_pos": adj, "truncated_away": not (0 <= adj < kept_len)})
        if 0 <= adj < kept_len:
            positions.append(adj)
            usable_points.append(rec)
    return positions, usable_points, len(ids), truncated_left


def collect_position_activations(
    model: Any,
    tokenizer: Any,
    prompt: str,
    completion: str,
    add_special: bool,
    device: torch.device,
    max_len: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
    points: list[dict[str, Any]],
) -> tuple[dict[tuple[int, str], torch.Tensor], list[dict[str, Any]], dict[str, Any]]:
    positions, usable_points, full_tokens, truncated_left = point_token_positions(tokenizer, prompt, completion, add_special, points, max_len)
    if not positions:
        return {}, usable_points, {"input_tokens": 0, "full_tokens": full_tokens, "truncated_left_tokens": truncated_left}
    pos_by_device: dict[torch.device, torch.Tensor] = {}
    captured: dict[tuple[int, str], torch.Tensor] = {}
    handles = []
    for key, module in component_plan.items():
        def make_hook(k: tuple[int, str]):
            def hook(_module, _inputs, output):
                hidden = extract_output(output)
                if torch.is_tensor(hidden) and hidden.ndim >= 3:
                    dev = hidden.device
                    if dev not in pos_by_device:
                        pos_by_device[dev] = torch.tensor(positions, dtype=torch.long, device=dev)
                    captured[k] = hidden[0, pos_by_device[dev], :].detach().float().cpu()
                return output
            return hook

        handles.append(module.register_forward_hook(make_hook(key)))
    try:
        ids = tokenizer.encode(prompt + completion, add_special_tokens=add_special)
        ids = ids[-max_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
        feats: dict[tuple[int, str], torch.Tensor] = {}
        for hidden_idx in hidden_layers:
            feats[(hidden_idx, "residual_hidden_state")] = out.hidden_states[hidden_idx][0, positions, :].detach().float().cpu()
        feats.update(captured)
        meta = {"input_tokens": len(ids), "full_tokens": full_tokens, "truncated_left_tokens": truncated_left}
        del out, input_ids, attn
    finally:
        for handle in handles:
            handle.remove()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return feats, usable_points, meta


def summarize(rows: list[dict[str, Any]], component_keys: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all")].append(row)
        groups[("stage", row["stage"])].append(row)
        groups[("trace_class", row["trace_class"])].append(row)
        groups[("prompt_variant", row.get("prompt_variant", "unknown"))].append(row)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        rec: dict[str, Any] = {"slice_type": typ, "slice": key, "n": len(vals)}
        for comp_key in component_keys:
            scores = [v["component_validity_scores"].get(comp_key) for v in vals if comp_key in v["component_validity_scores"]]
            norms = [v["component_norms"].get(comp_key) for v in vals if comp_key in v["component_norms"]]
            if scores:
                rec[f"mean_score_{comp_key}"] = mean(scores)
            if norms:
                rec[f"mean_norm_{comp_key}"] = mean(norms)
        out.append(rec)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--input-json-glob", default="results/E92_thinking_hard_task_natural/*_hard_task_conditioning.json")
    p.add_argument("--audit-jsonl", default="")
    p.add_argument("--out-dir", default=str(PROJECT / "results/E97_thinking_component_token_cache"))
    p.add_argument("--row-filter", choices=["all", "final_correct", "repair_marker", "strict_valid", "strict_acpi", "repaired_acpi", "unrepaired_acpi"], default="final_correct")
    p.add_argument("--max-rows", type=int, default=24)
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--layer-window", type=int, default=2)
    p.add_argument("--hidden-layers", nargs="+", type=int, default=None)
    p.add_argument("--all-layers", action="store_true")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    started = datetime.now().isoformat(timespec="seconds")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = [r for r in load_rows(args) if keep_row(r, args.model_key, args.row_filter)]
    rows = rows[: args.max_rows]
    print(f"[{started}] E97 loading {args.model_key}; selected_rows={len(rows)} filter={args.row_filter}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    best = best_hidden_layer(args.model_key, args.best_layer)
    hidden_layers = selected_hidden_layers(best, len(layers), args.all_layers, args.layer_window, args.hidden_layers)
    component_plan = build_component_plan(layers, hidden_layers)
    print(f"hidden_layers={hidden_layers}", flush=True)
    print(f"component_keys={[f'{k[0]}:{k[1]}' for k in sorted(component_plan)]}", flush=True)
    directions, centers, direction_keys = train_component_directions(model, tok, True, device, args.max_model_len, hidden_layers, component_plan)
    component_keys = sorted([f"{k[0]}:{k[1]}" for k in directions], key=lambda s: (int(s.split(":", 1)[0]), s.split(":", 1)[1]))
    component_key_tuples = [(int(s.split(":", 1)[0]), s.split(":", 1)[1]) for s in component_keys]

    cache_vectors: list[torch.Tensor] = []
    cache_meta: list[dict[str, Any]] = []
    out_rows: list[dict[str, Any]] = []
    skipped = Counter()
    for row_idx, row in enumerate(rows, start=1):
        points = completion_points(row)
        if not points:
            skipped["no_points"] += 1
            continue
        prompt, used_chat, add_special = render_source_prompt(tok, spec, row)
        feats, usable_points, meta = collect_position_activations(
            model,
            tok,
            prompt,
            row.get("completion", ""),
            add_special,
            device,
            args.max_model_len,
            hidden_layers,
            component_plan,
            points,
        )
        if not usable_points:
            skipped["all_points_truncated"] += 1
            continue
        for pos_i, pt in enumerate(usable_points):
            scores = {}
            norms = {}
            vecs = []
            used_component_keys = []
            for key in component_key_tuples:
                if key not in feats or pos_i >= feats[key].shape[0]:
                    continue
                vec = feats[key][pos_i]
                score = float(((vec - centers[key]) * directions[key]).sum().item())
                label = f"{key[0]}:{key[1]}"
                scores[label] = score
                norms[label] = float(vec.norm().item())
                vecs.append(vec.to(torch.float16))
                used_component_keys.append(label)
            cache_index = len(cache_vectors)
            cache_vectors.append(torch.stack(vecs) if vecs else torch.empty(0))
            rec = {
                "cache_index": cache_index,
                "model_key": args.model_key,
                "row_source": row.get("e97_row_source"),
                "row_source_index": row.get("e97_source_index"),
                "task_id": row.get("task_id"),
                "prompt_variant": row.get("prompt_variant"),
                "sample_idx": row.get("sample_idx"),
                "trace_class": row_class(row),
                "stage": pt["stage"],
                "char_end": pt["char_end"],
                "span_text": pt.get("span_text", ""),
                "original_token_pos": pt["original_token_pos"],
                "truncated_token_pos": pt["truncated_token_pos"],
                "used_chat_template": used_chat,
                "add_special_tokens": add_special,
                "manual_final_correct": row.get("manual_final_correct"),
                "manual_error_type": row.get("manual_error_type"),
                "manual_error_span_present": bool(row.get("manual_error_span")),
                "manual_repair_present": row.get("manual_repair_present"),
                "manual_acpi_strict": row.get("manual_acpi_strict"),
                "manual_acpi_unrepaired": row.get("manual_acpi_unrepaired"),
                "extraction_method": row.get("extraction_method"),
                "final_marker_found": row.get("final_marker_found"),
                "best_hidden_layer": best,
                "selected_hidden_layers": hidden_layers,
                "component_keys_used": used_component_keys,
                "component_validity_scores": scores,
                "component_norms": norms,
                **meta,
            }
            out_rows.append(rec)
            cache_meta.append({k: rec[k] for k in ["cache_index", "task_id", "prompt_variant", "sample_idx", "trace_class", "stage"]})
        print(f"E97 replayed row {row_idx}/{len(rows)} points={len(usable_points)}", flush=True)

    if cache_vectors:
        width = max(v.shape[0] for v in cache_vectors)
        dim = max(v.shape[-1] for v in cache_vectors if v.numel())
        padded = []
        for v in cache_vectors:
            if v.numel() == 0:
                padded.append(torch.zeros((width, dim), dtype=torch.float16))
            elif v.shape[0] < width:
                pad = torch.zeros((width - v.shape[0], v.shape[1]), dtype=torch.float16)
                padded.append(torch.cat([v.cpu(), pad], dim=0))
            else:
                padded.append(v.cpu())
        cache_tensor = torch.stack(padded)
    else:
        cache_tensor = torch.empty(0)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"{args.row_filter}_n{len(rows)}"
    pt_path = out_dir / f"{args.model_key}_e97_thinking_component_tokens_{suffix}.pt"
    torch.save(
        {
            "component_token_vectors": cache_tensor,
            "component_keys": component_keys,
            "point_meta": cache_meta,
            "note": "shape [point, component_key, hidden_dim]; post-hoc replay of prompt+completion, not generation-time cache",
        },
        pt_path,
    )
    result = {
        "experiment": "E97_thinking_component_token_cache",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "row_filter": args.row_filter,
        "selected_rows": len(rows),
        "skipped": dict(skipped),
        "best_hidden_layer": best,
        "selected_hidden_layers": hidden_layers,
        "component_keys": component_keys,
        "direction_keys": direction_keys,
        "component_cache_pt": str(pt_path.relative_to(PROJECT)),
        "component_cache_shape": list(cache_tensor.shape),
        "rows": out_rows,
        "summary": summarize(out_rows, component_keys),
        "leakage_audit": {
            "manual_labels_in_prompt_rows": 0,
            "manual_error_spans_in_prompt_rows": 0,
            "gold_answer_in_prompt_rows": sum(bool(r.get("gold_answer_in_prompt")) for r in rows),
            "note_zh": "人工标签和 error span 只用于离线选行/定位 token；模型输入仍是原始 problem prompt 与模型自己的 completion。",
        },
        "scope_note_zh": "E97 是 thinking 输出的 post-hoc 激活复放缓存；它能比较 thought/repair/final token 上的 residual、MLP、token-mixer 信号，但不能单独证明生成时因果路径。",
    }
    out_json = out_dir / f"{args.model_key}_e97_thinking_component_tokens_{suffix}.json"
    write_json(out_json, result)
    print(f"wrote {out_json}", flush=True)
    print(f"wrote {pt_path}", flush=True)
    print("SUMMARY", {"rows": len(rows), "points": len(out_rows), "skipped": dict(skipped)}, flush=True)


if __name__ == "__main__":
    main()
