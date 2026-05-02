#!/usr/bin/env python3
"""Run E166 teacher-forced hidden replay on hardened prefix points.

This script scores causal prefill prefixes using model hidden states. It is the
first step toward hidden-derived localized spans. Unlike E162/E165, the target
span is not inserted into the prompt; hidden replay prompts contain only the
problem and visible prefix.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch
import torch.nn.functional as F

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402
import run_e90_hardtask_component_activation_cache as e90  # noqa: E402

PREFIX_BANK = PROJECT / "data/processed/e166_hardened_monitor_prefix_points_20260502.jsonl"
OUT_DIR = PROJECT / "results/E166_hardened_hidden_monitor_replay"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render_prefill_content(row: dict[str, Any], mode: str) -> str:
    if mode == "generation_prefill":
        return (
            "Solve the following problem carefully. Continue from the partial reasoning prefix. "
            "Do not give the final answer before the reasoning.\n\n"
            f"Problem: {row['problem']}\n\nPartial reasoning prefix:\n{row['prefix_text']}"
        )
    if mode == "strict_verifier":
        return e90.strict_prompt(row["problem"], row["prefix_text"])
    raise ValueError(mode)


def render_chat(tokenizer, spec: dict[str, Any], content: str, mode: str) -> tuple[str, bool, bool]:
    use_chat = e90.should_use_chat_template(spec, mode) and bool(getattr(tokenizer, "chat_template", None))
    if not use_chat:
        return content, False, True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        text = tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, **kwargs)
    return text, True, False


def select_rows(rows: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    families = set(args.families or [])
    trace_classes = set(args.trace_classes or [])
    task_ids = set(args.task_ids or [])
    out = [
        r
        for r in rows
        if (not families or r["family"] in families)
        and (not trace_classes or r["trace_class"] in trace_classes)
        and (not task_ids or r["task_id"] in task_ids)
    ]
    out = sorted(out, key=lambda r: (r["family"], r["task_id"], r["candidate_variant"], r["prefix_char_end"], r["boundary_kind"]))
    if args.max_rows > 0:
        out = out[: args.max_rows]
    return out


def label_logprob(logits: torch.Tensor, tok, options: list[str]) -> float | None:
    scored = []
    logp = F.log_softmax(logits.float(), dim=-1)
    for opt in options:
        ids = tok.encode(opt, add_special_tokens=False)
        if ids:
            scored.append(float(logp[int(ids[0])].item()))
    return max(scored) if scored else None


def collect_prefill_activation(
    model,
    tok,
    prompt: str,
    add_special_tokens: bool,
    device: torch.device,
    max_len: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
) -> tuple[dict[tuple[int, str], torch.Tensor], dict[str, Any]]:
    feats, meta = e90.collect_activation(model, tok, prompt, add_special_tokens, device, max_len, hidden_layers, component_plan)
    # e90 meta has Yes/No verifier logprobs. For generation-prefill mode we also
    # record simple continuation confidence statistics at the final prefix token.
    ids = tok.encode(prompt, add_special_tokens=add_special_tokens)[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        try:
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=False, use_cache=False, logits_to_keep=1)
        except TypeError:
            out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=False, use_cache=False)
    logits = out.logits[0, -1].float()
    logp = F.log_softmax(logits, dim=-1)
    probs = torch.softmax(logits, dim=-1)
    top = torch.topk(logp, k=min(5, logp.numel()))
    meta.update(
        {
            "next_token_entropy": float(-(probs * logp).sum().item()),
            "next_token_top1_logprob": float(top.values[0].item()),
            "next_token_top5_logprobs": [float(x) for x in top.values.tolist()],
            "maybe_logprob": label_logprob(logits, tok, [" maybe", "maybe", " Maybe", "Maybe"]),
            "error_logprob": label_logprob(logits, tok, [" error", "error", " Error", "Error"]),
            "wait_logprob": label_logprob(logits, tok, [" Wait", "Wait", " wait", "wait"]),
        }
    )
    del out, input_ids, attn
    return feats, meta


def score_rows(
    rows: list[dict[str, Any]],
    component_keys: list[str],
) -> list[dict[str, Any]]:
    out = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[("all", "all")].append(r)
        groups[("family", r["family"])].append(r)
        groups[("trace_class", r["trace_class"])].append(r)
        groups[("boundary_kind", r["boundary_kind"])].append(r)
        groups[("monitor_target", str(bool(r["monitor_target_offline"])))].append(r)
    for (typ, key), vals in sorted(groups.items()):
        rec: dict[str, Any] = {"slice_type": typ, "slice": key, "n": len(vals)}
        if vals:
            rec["monitor_target_rate"] = sum(int(v["monitor_target_offline"]) for v in vals) / len(vals)
            rec["mean_yes_minus_no"] = mean(v["yes_minus_no"] for v in vals)
            rec["mean_next_token_entropy"] = mean(v["next_token_entropy"] for v in vals)
        for comp_key in component_keys:
            scores = [v["component_validity_scores"].get(comp_key) for v in vals if comp_key in v["component_validity_scores"]]
            if scores:
                rec[f"mean_score_{comp_key}"] = mean(scores)
        out.append(rec)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--prefix-bank", default=str(PREFIX_BANK))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--prompt-mode", choices=["generation_prefill", "strict_verifier"], default="generation_prefill")
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--families", nargs="*", default=[])
    p.add_argument("--trace-classes", nargs="*", default=[])
    p.add_argument("--task-ids", nargs="*", default=[])
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--best-layer", type=int, default=None)
    p.add_argument("--layer-window", type=int, default=1)
    p.add_argument("--hidden-layers", nargs="+", type=int, default=None)
    p.add_argument("--all-layers", action="store_true")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--tag", default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = select_rows(load_jsonl(Path(args.prefix_bank)), args)
    if not rows:
        raise SystemExit("No E166 prefix rows selected")
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E166 rows={len(rows)} prompt_mode={args.prompt_mode}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    best = e90.best_hidden_layer(args.model_key, args.best_layer)
    hidden_layers = e90.selected_hidden_layers(best, len(layers), args.all_layers, args.layer_window, args.hidden_layers)
    component_plan = e90.build_component_plan(layers, hidden_layers)
    use_chat_mode = args.prompt_format
    use_chat = e90.should_use_chat_template(spec, use_chat_mode) and bool(getattr(tok, "chat_template", None))
    directions, centers, _ = e90.train_component_directions(model, tok, use_chat, device, args.max_model_len, hidden_layers, component_plan)
    component_keys = sorted([f"{k[0]}:{k[1]}" for k in directions], key=lambda s: (int(s.split(":", 1)[0]), s.split(":", 1)[1]))
    component_key_tuples = [(int(s.split(":", 1)[0]), s.split(":", 1)[1]) for s in component_keys]

    cache_vectors: list[torch.Tensor] = []
    cache_meta: list[dict[str, Any]] = []
    out_rows: list[dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        content = render_prefill_content(row, args.prompt_mode)
        prompt, used_chat, add = render_chat(tok, spec, content, args.prompt_format)
        feats, meta = collect_prefill_activation(model, tok, prompt, add, device, args.max_model_len, hidden_layers, component_plan)
        scores: dict[str, float] = {}
        vecs: list[torch.Tensor] = []
        for key in component_key_tuples:
            if key in feats:
                scores[f"{key[0]}:{key[1]}"] = float(((feats[key] - centers[key]) * directions[key]).sum().item())
                vecs.append(feats[key].to(torch.float16))
        cache_index = len(cache_vectors)
        cache_vectors.append(torch.stack(vecs) if vecs else torch.empty(0))
        rec = {
            "cache_index": cache_index,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "experiment": "E166_hardened_hidden_monitor_replay",
            "model_key": args.model_key,
            "prefix_id": row["prefix_id"],
            "solution_id": row["solution_id"],
            "task_id": row["task_id"],
            "family": row["family"],
            "candidate_variant": row["candidate_variant"],
            "trace_class": row["trace_class"],
            "boundary_kind": row["boundary_kind"],
            "prefix_char_end": row["prefix_char_end"],
            "visible_span": row["visible_span"],
            "monitor_target_offline": bool(row["monitor_target"]),
            "manual_error_type_offline": row["manual_error_type_offline"],
            "exact_manual_error_span_end_offline": bool(row["exact_manual_error_span_end"]),
            "prompt_mode": args.prompt_mode,
            "used_chat_template": used_chat,
            "best_hidden_layer": best,
            "selected_hidden_layers": hidden_layers,
            "component_validity_scores": scores,
            **meta,
        }
        out_rows.append(rec)
        cache_meta.append(
            {
                "cache_index": cache_index,
                "prefix_id": rec["prefix_id"],
                "solution_id": rec["solution_id"],
                "task_id": rec["task_id"],
                "family": rec["family"],
                "trace_class": rec["trace_class"],
                "boundary_kind": rec["boundary_kind"],
                "monitor_target_offline": rec["monitor_target_offline"],
                "manual_error_type_offline": rec["manual_error_type_offline"],
            }
        )
        if i % 20 == 0 or i == len(rows):
            print(f"E166 replay {i}/{len(rows)}", flush=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"_{args.tag}" if args.tag else ""
    out_path = out_dir / f"{args.model_key}_e166_{args.prompt_mode}{tag}.json"
    pt_path = out_dir / f"{args.model_key}_e166_{args.prompt_mode}{tag}.pt"
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
        hidden_tensor = torch.stack(padded)
    else:
        hidden_tensor = torch.empty(0)
    torch.save(
        {
            "component_final_token_vectors": hidden_tensor,
            "component_keys": component_keys,
            "monitor_directions": torch.stack([directions[k].to(torch.float16) for k in component_key_tuples]).cpu(),
            "monitor_centers": torch.stack([centers[k].to(torch.float16) for k in component_key_tuples]).cpu(),
            "prefix_meta": cache_meta,
            "note": "component_final_token_vectors shape [prefix, component_key, hidden_dim]; vectors are teacher-forced final-prefix-token component states. monitor_directions and monitor_centers use the same component_key order.",
        },
        pt_path,
    )
    result = {
        "experiment": "E166_hardened_hidden_monitor_replay",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "prompt_mode": args.prompt_mode,
        "used_chat_template_possible": use_chat,
        "best_hidden_layer": best,
        "selected_hidden_layers": hidden_layers,
        "component_keys": component_keys,
        "component_cache_pt": str(pt_path.relative_to(PROJECT)),
        "component_cache_shape": list(hidden_tensor.shape),
        "args": vars(args),
        "rows": out_rows,
        "summary": score_rows(out_rows, component_keys),
        "leakage_audit": {
            "prompt_fields_used": ["problem", "prefix_text"],
            "gold_answer_in_prompt_rows": 0,
            "manual_error_span_in_prompt_rows": 0,
            "manual_label_in_prompt_rows": 0,
            "note_zh": "manual error spans and monitor_target labels are offline only; hidden replay prompt contains only problem and causal prefix.",
        },
    }
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print(f"wrote {pt_path}", flush=True)


if __name__ == "__main__":
    main()
