#!/usr/bin/env python3
"""E100 batch-size invariance audit for fixed-token hidden/component replay.

This is not a generation experiment.  It replays already generated
prompt+completion sequences with batch sizes 1/2/4 and checks whether residual,
MLP, token-mixer, and selected norm activations change.  Manual labels are not
used in prompts.
"""
from __future__ import annotations

import argparse
import json
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
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(SCRIPT_DIR))

from mplens.io_utils import read_json, read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402
from run_e49_hard_task_conditioning_official import render_prompt as render_e49_prompt  # noqa: E402
from run_e90_hardtask_component_activation_cache import build_component_plan, extract_output, selected_hidden_layers  # noqa: E402


E57_QWEN = PROJECT / "results/E57_p0_hard_task_final_correct_harvesting/qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json"
E88_QWEN = PROJECT / "results/E88_answer_first_natural_sample/qwen35_27b_e49_answer_first_no_gold_hard_task_conditioning.json"
E92_QWEN = PROJECT / "results/E92_thinking_hard_task_natural/qwen35_27b_e49_neutral_answer_first_no_gold_self_check_hard_task_conditioning.json"
E92_BOXED_QWEN = PROJECT / "results/E92_thinking_hard_task_natural/e92_qwen35_27b_thinking_boxed_k2_max8192_checkpoint.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return load_jsonl(path)
    data = read_json(path)
    return list(data.get("rows", []))


def select_source_rows(max_per_source: int) -> list[dict[str, Any]]:
    sources = [
        ("TG_E92_qwen", E92_QWEN),
        ("NG_E57_qwen", E57_QWEN),
        ("NG_E88_qwen_answer_first", E88_QWEN),
        ("TG_E92_boxed_truncated_qwen", E92_BOXED_QWEN),
    ]
    out: list[dict[str, Any]] = []
    for source, path in sources:
        rows = load_rows(path)
        keep = [r for r in rows if r.get("model_key") == "qwen35_27b" and (r.get("manual_final_correct") or source.startswith("TG_E92_boxed"))]
        for i, row in enumerate(keep[:max_per_source]):
            rec = dict(row)
            rec["e100_source"] = source
            rec["e100_source_path"] = str(path.relative_to(PROJECT))
            rec["e100_source_index"] = i
            out.append(rec)
    return out


def render_source_text(tokenizer: Any, spec: dict[str, Any], row: dict[str, Any]) -> tuple[str, bool]:
    task = {"en": row["problem"], "answer": row.get("gold_answer", "")}
    thinking = bool(row.get("thinking"))
    prompt, _used_chat, add_special, _gold = render_e49_prompt(tokenizer, spec, task, row["prompt_variant"], thinking)
    return prompt + row.get("completion", ""), add_special


def encode_left_padded(tokenizer: Any, texts: list[str], add_special: bool, max_len: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor, list[dict[str, int]]]:
    ids_list = []
    meta = []
    for text in texts:
        ids = tokenizer.encode(text, add_special_tokens=add_special)
        full_len = len(ids)
        trunc = max(0, full_len - max_len)
        ids = ids[-max_len:]
        ids_list.append(ids)
        meta.append({"full_tokens": full_len, "input_tokens": len(ids), "truncated_left_tokens": trunc})
    width = max(len(ids) for ids in ids_list)
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    input_ids = []
    attention = []
    for ids in ids_list:
        pad = [pad_id] * (width - len(ids))
        input_ids.append(pad + ids)
        attention.append([0] * len(pad) + [1] * len(ids))
    return (
        torch.tensor(input_ids, dtype=torch.long, device=device),
        torch.tensor(attention, dtype=torch.long, device=device),
        meta,
    )


def collect_batch_features(
    model: Any,
    tokenizer: Any,
    texts: list[str],
    add_special: bool,
    device: torch.device,
    max_len: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
) -> tuple[dict[str, torch.Tensor], torch.Tensor, list[dict[str, int]]]:
    captured: dict[tuple[int, str], torch.Tensor] = {}
    handles = []
    for key, module in component_plan.items():
        def make_hook(k: tuple[int, str]):
            def hook(_module, _inputs, output):
                hidden = extract_output(output)
                if torch.is_tensor(hidden) and hidden.ndim >= 3:
                    captured[k] = hidden[:, -1, :].detach().float().cpu()
                return output
            return hook

        handles.append(module.register_forward_hook(make_hook(key)))
    try:
        input_ids, attention, meta = encode_left_padded(tokenizer, texts, add_special, max_len, device)
        with torch.no_grad():
            try:
                out = model(input_ids=input_ids, attention_mask=attention, output_hidden_states=True, use_cache=False, logits_to_keep=1)
            except TypeError:
                out = model(input_ids=input_ids, attention_mask=attention, output_hidden_states=True, use_cache=False)
        feats: dict[str, torch.Tensor] = {}
        for hidden_idx in hidden_layers:
            feats[f"{hidden_idx}:residual_hidden_state"] = out.hidden_states[hidden_idx][:, -1, :].detach().float().cpu()
        for key, value in captured.items():
            feats[f"{key[0]}:{key[1]}"] = value
        logits = out.logits[:, -1, :].detach().float().cpu()
        del out, input_ids, attention
    finally:
        for handle in handles:
            handle.remove()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return feats, logits, meta


def compare_vectors(a: torch.Tensor, b: torch.Tensor) -> dict[str, float]:
    diff = (a - b).float()
    return {
        "cosine": float(F.cosine_similarity(a.float(), b.float(), dim=0).item()),
        "l2": float(diff.norm().item()),
        "relative_l2": float((diff.norm() / (a.float().norm() + 1e-8)).item()),
        "max_abs": float(diff.abs().max().item()),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", default="qwen35_27b")
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E100_batch_invariance_audit"))
    p.add_argument("--max-per-source", type=int, default=6)
    p.add_argument("--batch-sizes", nargs="+", type=int, default=[1, 2, 4])
    p.add_argument("--best-layer", type=int, default=34)
    p.add_argument("--layer-window", type=int, default=1)
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    started = datetime.now().isoformat(timespec="seconds")
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = select_source_rows(args.max_per_source)
    print(f"[{started}] E100 loading {args.model_key}; rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    hidden_layers = selected_hidden_layers(args.best_layer, len(layers), False, args.layer_window, None)
    component_plan = build_component_plan(layers, hidden_layers)
    print(f"hidden_layers={hidden_layers}", flush=True)

    texts = []
    add_flags = []
    row_meta = []
    for i, row in enumerate(rows):
        text, add = render_source_text(tok, spec, row)
        texts.append(text)
        add_flags.append(add)
        row_meta.append(
            {
                "row_id": i,
                "source": row["e100_source"],
                "task_id": row.get("task_id"),
                "prompt_variant": row.get("prompt_variant"),
                "thinking": row.get("thinking"),
                "manual_final_correct": row.get("manual_final_correct"),
                "extraction_method": row.get("extraction_method"),
                "hit_max_new_tokens": row.get("hit_max_new_tokens"),
                "completion_chars": len(row.get("completion", "")),
            }
        )
    if len(set(add_flags)) != 1:
        raise RuntimeError("Mixed add_special settings are not supported in this E100 audit.")
    add_special = add_flags[0] if add_flags else False

    baseline_feats: dict[int, dict[str, torch.Tensor]] = {}
    baseline_logits: dict[int, torch.Tensor] = {}
    token_meta: dict[int, dict[str, int]] = {}
    for i, text in enumerate(texts):
        feats, logits, meta = collect_batch_features(model, tok, [text], add_special, device, args.max_model_len, hidden_layers, component_plan)
        baseline_feats[i] = {k: v[0].clone() for k, v in feats.items()}
        baseline_logits[i] = logits[0].clone()
        token_meta[i] = meta[0]
        print(f"E100 baseline {i + 1}/{len(texts)}", flush=True)

    comparisons = []
    for bs in args.batch_sizes:
        for start in range(0, len(texts), bs):
            batch_texts = texts[start : start + bs]
            feats, logits, meta = collect_batch_features(model, tok, batch_texts, add_special, device, args.max_model_len, hidden_layers, component_plan)
            for local_i, global_i in enumerate(range(start, start + len(batch_texts))):
                for key, mat in feats.items():
                    stats = compare_vectors(baseline_feats[global_i][key], mat[local_i])
                    comparisons.append({"batch_size": bs, "row_id": global_i, "component": key, **stats})
                logit_stats = compare_vectors(baseline_logits[global_i], logits[local_i])
                comparisons.append({"batch_size": bs, "row_id": global_i, "component": "logits", **logit_stats})
                token_meta[global_i] = meta[local_i]
        print(f"E100 checked batch_size={bs}", flush=True)

    groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for rec in comparisons:
        groups[(rec["batch_size"], rec["component"])].append(rec)
    summary = []
    for (bs, comp), vals in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1])):
        summary.append(
            {
                "batch_size": bs,
                "component": comp,
                "n": len(vals),
                "min_cosine": min(v["cosine"] for v in vals),
                "mean_cosine": mean(v["cosine"] for v in vals),
                "max_l2": max(v["l2"] for v in vals),
                "mean_l2": mean(v["l2"] for v in vals),
                "max_relative_l2": max(v["relative_l2"] for v in vals),
                "max_abs": max(v["max_abs"] for v in vals),
            }
        )

    result = {
        "experiment": "E100_batch_invariance_audit",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "args": vars(args),
        "row_meta": [{**m, **token_meta.get(m["row_id"], {})} for m in row_meta],
        "component_keys": sorted({c["component"] for c in comparisons}),
        "comparisons": comparisons,
        "summary": summary,
        "audit": {
            "generation_performed": False,
            "manual_labels_in_prompt_rows": 0,
            "note_zh": "E100 只复放固定 prompt+completion；batch size 变化不改变输入 token 序列。若有差异，应视为 padding/kernel/device-map 数值差异或 bug。",
        },
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.model_key}_e100_batch_invariance.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    for rec in summary[:12]:
        print("SUMMARY", rec, flush=True)


if __name__ == "__main__":
    main()
