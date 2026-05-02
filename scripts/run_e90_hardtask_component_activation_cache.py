#!/usr/bin/env python3
"""E90 component activation cache for hard-task ACPI prefixes.

E85 stores full-layer residual hidden states for key prefixes.  E90 adds
component-level signals at selected layers: residual hidden states, token-mixer
/ attention outputs, MLP outputs, and available norm outputs.  It learns
component validity directions from E61 controlled valid/invalid rows and scores
hard-task prefixes without inserting labels or error spans into prompts.
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
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

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


def strict_prompt(problem: str, trace: str) -> str:
    return (
        "You are a strict trace-selection auditor. Judge the visible reasoning trace step by step. "
        "If any visible local step, definition, arithmetic operation, counting rule, unit conversion, semantic interpretation, algebraic transformation, or proof implication is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
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


def target_rows(model_key: str, mode: str, audit_jsonl: Path) -> list[dict[str, Any]]:
    rows = [r for r in load_jsonl(audit_jsonl) if r["model_key"] == model_key]
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
        points.append({"stage": "post_repair_240chars", "char_end": min(len(comp), repair.end() + 240), "span_text": comp[repair.start() : min(len(comp), repair.end() + 240)]})
    last_final = None
    for m in FINAL_RE.finditer(comp):
        last_final = m
    if last_final:
        points.append({"stage": "last_final_answer_end", "char_end": last_final.end(), "span_text": last_final.group(0)})
    points.append({"stage": "completion_end", "char_end": len(comp), "span_text": comp[-120:]})
    seen = set()
    out = []
    for p in sorted(points, key=lambda x: (x["char_end"], x["stage"])):
        key = (p["stage"], p["char_end"])
        if key not in seen:
            out.append(p)
            seen.add(key)
    return out


def best_hidden_layer(model_key: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    p = E65_DIR / f"{model_key}_e65_e61_layer_sweep.json"
    if p.exists():
        return int(read_json(p)["best_all_layer"]["layer"])
    return 16


def selected_hidden_layers(best_layer: int, n_model_layers: int, all_layers: bool, window: int, explicit: list[int] | None) -> list[int]:
    # Hidden-state index 0 is embeddings; layer module i maps to hidden index i+1.
    if explicit:
        vals = explicit
    elif all_layers:
        vals = list(range(1, n_model_layers + 1))
    else:
        vals = list(range(best_layer - window, best_layer + window + 1))
    return sorted({x for x in vals if 1 <= x <= n_model_layers})


def module_for_first_attr(layer_module, names: list[str]):
    for name in names:
        if hasattr(layer_module, name):
            return getattr(layer_module, name)
    return None


def component_modules_for_layer(layer_module) -> dict[str, Any]:
    mods: dict[str, Any] = {}
    token_mixer = module_for_first_attr(layer_module, ["self_attn", "linear_attn", "attention", "attn", "token_mixer"])
    if token_mixer is not None:
        mods["token_mixer_output"] = token_mixer
    mlp = module_for_first_attr(layer_module, ["mlp", "feed_forward", "ffn"])
    if mlp is not None:
        mods["mlp_output"] = mlp
    for label, names in [
        ("input_norm_output", ["input_layernorm", "input_norm", "ln1"]),
        ("post_attention_norm_output", ["post_attention_layernorm", "post_attention_norm", "ln2"]),
        ("pre_mlp_norm_output", ["pre_feedforward_layernorm", "pre_mlp_layernorm"]),
        ("post_feedforward_norm_output", ["post_feedforward_layernorm", "post_mlp_layernorm"]),
    ]:
        mod = module_for_first_attr(layer_module, names)
        if mod is not None:
            mods[label] = mod
    return mods


def extract_output(output):
    return output[0] if isinstance(output, tuple) else output


def build_component_plan(layers, hidden_layers: list[int]) -> dict[tuple[int, str], Any]:
    plan: dict[tuple[int, str], Any] = {}
    for hidden_idx in hidden_layers:
        layer_idx = hidden_idx - 1
        for comp, module in component_modules_for_layer(layers[layer_idx]).items():
            plan[(hidden_idx, comp)] = module
    return plan


def collect_activation(
    model,
    tok,
    prompt: str,
    add: bool,
    device: torch.device,
    max_len: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
) -> tuple[dict[tuple[int, str], torch.Tensor], dict[str, Any]]:
    captured: dict[tuple[int, str], torch.Tensor] = {}
    handles = []
    for key, module in component_plan.items():
        def make_hook(k):
            def hook(_module, _inputs, output):
                hidden = extract_output(output)
                if torch.is_tensor(hidden) and hidden.ndim >= 3:
                    captured[k] = hidden[0, -1, :].detach().float().cpu()
                return output
            return hook

        handles.append(module.register_forward_hook(make_hook(key)))
    try:
        ids = tok.encode(prompt, add_special_tokens=add)
        truncated_left = max(0, len(ids) - max_len)
        ids = ids[-max_len:]
        input_ids = torch.tensor([ids], dtype=torch.long, device=device)
        attn = torch.ones_like(input_ids, device=device)
        with torch.no_grad():
            try:
                out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False, logits_to_keep=1)
            except TypeError:
                out = model(input_ids=input_ids, attention_mask=attn, output_hidden_states=True, use_cache=False)
        feats: dict[tuple[int, str], torch.Tensor] = {}
        for hidden_idx in hidden_layers:
            feats[(hidden_idx, "residual_hidden_state")] = out.hidden_states[hidden_idx][0, -1, :].detach().float().cpu()
        feats.update(captured)
        yes, yes_opt = label_logprob(out.logits[0, -1], tok, [" Yes", "Yes", " yes", "yes"])
        no, no_opt = label_logprob(out.logits[0, -1], tok, [" No", "No", " no", "no"])
        meta = {
            "input_tokens": len(ids),
            "truncated_left_tokens": truncated_left,
            "yes_score": yes,
            "no_score": no,
            "yes_minus_no": yes - no,
            "pred_process_valid": yes > no,
            "yes_option": yes_opt,
            "no_option": no_opt,
        }
        del out, input_ids, attn
    finally:
        for h in handles:
            h.remove()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return feats, meta


def train_component_directions(
    model,
    tok,
    use_chat: bool,
    device: torch.device,
    max_len: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
) -> tuple[dict[tuple[int, str], torch.Tensor], dict[tuple[int, str], torch.Tensor], list[str]]:
    rows = load_jsonl(E61_DATA)
    labels = [bool(r["manual_process_valid"]) for r in rows]
    by_key: dict[tuple[int, str], list[torch.Tensor]] = defaultdict(list)
    for i, r in enumerate(rows, start=1):
        prompt, add = render_prompt(tok, strict_prompt(r["problem"], r["completion"]), use_chat)
        feats, _meta = collect_activation(model, tok, prompt, add, device, max_len, hidden_layers, component_plan)
        for key, vec in feats.items():
            by_key[key].append(vec)
        if i % 24 == 0 or i == len(rows):
            print(f"E61 component activations {i}/{len(rows)}", flush=True)
    directions: dict[tuple[int, str], torch.Tensor] = {}
    centers: dict[tuple[int, str], torch.Tensor] = {}
    keys = sorted(by_key, key=lambda x: (x[0], x[1]))
    y = torch.tensor(labels, dtype=torch.bool)
    for key in keys:
        X = torch.stack(by_key[key])
        if len(X) != len(labels):
            continue
        pos = X[y].mean(dim=0)
        neg = X[~y].mean(dim=0)
        d = pos - neg
        d = d / (d.norm() + 1e-8)
        directions[key] = d
        centers[key] = X.mean(dim=0)
    return directions, centers, [f"{k[0]}:{k[1]}" for k in keys if k in directions]


def trace_class(row: dict[str, Any]) -> str:
    if row.get("manual_acpi_unrepaired"):
        return "unrepaired_acpi"
    if row.get("manual_acpi_strict") and row.get("manual_repair_present"):
        return "repaired_acpi"
    if row.get("manual_acpi_strict"):
        return "strict_acpi"
    return "valid"


def summarize(rows: list[dict[str, Any]], component_keys: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[("all", "all")].append(r)
        groups[("stage", r["stage"])].append(r)
        groups[("trace_class", r["trace_class"])].append(r)
    out = []
    for (typ, key), vals in sorted(groups.items()):
        rec: dict[str, Any] = {
            "slice_type": typ,
            "slice": key,
            "n": len(vals),
            "accept_rate": sum(v["pred_process_valid"] for v in vals) / len(vals),
            "mean_yes_minus_no": mean(v["yes_minus_no"] for v in vals),
        }
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
    p.add_argument("--audit-jsonl", default=str(E57_AUDIT))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E90_hardtask_component_activation_cache"))
    p.add_argument("--target-mode", choices=["auto", "repaired_acpi", "unrepaired_acpi", "strict_acpi"], default="auto")
    p.add_argument("--best-layer", type=int, default=None, help="E65 hidden-state index; layer module is best_layer-1")
    p.add_argument("--layer-window", type=int, default=2)
    p.add_argument("--hidden-layers", nargs="+", type=int, default=None, help="Explicit hidden-state indices; 0 embedding is not valid for components")
    p.add_argument("--all-layers", action="store_true")
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
    rows = target_rows(args.model_key, args.target_mode, Path(args.audit_jsonl))
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E90 target_rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    layers = get_transformer_layers(model)
    best = best_hidden_layer(args.model_key, args.best_layer)
    hidden_layers = selected_hidden_layers(best, len(layers), args.all_layers, args.layer_window, args.hidden_layers)
    component_plan = build_component_plan(layers, hidden_layers)
    print(f"hidden_layers={hidden_layers}", flush=True)
    print(f"component_keys={[f'{k[0]}:{k[1]}' for k in sorted(component_plan)]}", flush=True)
    directions, centers, direction_keys = train_component_directions(model, tok, use_chat, device, args.max_model_len, hidden_layers, component_plan)

    cache_vectors: list[torch.Tensor] = []
    cache_meta: list[dict[str, Any]] = []
    out_rows: list[dict[str, Any]] = []
    component_keys = sorted([f"{k[0]}:{k[1]}" for k in directions], key=lambda s: (int(s.split(":", 1)[0]), s.split(":", 1)[1]))
    component_key_tuples = [(int(s.split(":", 1)[0]), s.split(":", 1)[1]) for s in component_keys]
    for row in rows:
        for pt in prefix_points(row):
            prefix = row["completion"][: pt["char_end"]]
            prompt, add = render_prompt(tok, strict_prompt(row["problem"], prefix), use_chat)
            feats, meta = collect_activation(model, tok, prompt, add, device, args.max_model_len, hidden_layers, component_plan)
            scores = {}
            vecs = []
            for key in component_key_tuples:
                if key not in feats:
                    continue
                score = float(((feats[key] - centers[key]) * directions[key]).sum().item())
                label = f"{key[0]}:{key[1]}"
                scores[label] = score
                vecs.append(feats[key].to(torch.float16))
            cache_index = len(cache_vectors)
            cache_vectors.append(torch.stack(vecs) if vecs else torch.empty(0))
            rec = {
                "cache_index": cache_index,
                "source_model": row["model_key"],
                "verifier_model": args.model_key,
                "manual_audit_idx": row.get("manual_audit_idx", row.get("e88_audit_idx", row.get("audit_idx"))),
                "task_id": row["task_id"],
                "prompt_variant": row["prompt_variant"],
                "trace_class": trace_class(row),
                "manual_error_type": row.get("manual_error_type"),
                "manual_error_span": row.get("manual_error_span"),
                "stage": pt["stage"],
                "char_end": pt["char_end"],
                "span_text": pt["span_text"],
                "best_hidden_layer": best,
                "selected_hidden_layers": hidden_layers,
                "component_validity_scores": scores,
                **meta,
            }
            out_rows.append(rec)
            cache_meta.append({k: rec[k] for k in ["cache_index", "manual_audit_idx", "task_id", "stage", "trace_class"]})
            print(f"cached components audit_idx={rec['manual_audit_idx']} stage={pt['stage']}", flush=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "chat" if use_chat else "raw"
    pt_path = out_dir / f"{args.model_key}_e90_component_cache_{args.target_mode}_{suffix}.pt"
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
            "prefix_meta": cache_meta,
            "note": "shape [prefix, component_key, hidden_dim]; component keys are hidden_state_index:component_name",
        },
        pt_path,
    )
    result = {
        "experiment": "E90_hardtask_component_activation_cache",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "target_mode": args.target_mode,
        "best_hidden_layer": best,
        "selected_hidden_layers": hidden_layers,
        "component_keys": component_keys,
        "component_cache_pt": str(pt_path.relative_to(PROJECT)),
        "component_cache_shape": list(hidden_tensor.shape),
        "args": vars(args),
        "rows": out_rows,
        "summary": summarize(out_rows, component_keys),
        "leakage_audit": {
            "labels_in_prompt_rows": 0,
            "error_spans_in_prompt_rows": 0,
            "gold_answer_in_prompt_rows": 0,
            "note_zh": "E61 标签只用于离线训练 component validity direction；E57 人工标签/span 只用于离线选择 prefix。prompt 只含 problem 与 visible trace prefix。",
        },
        "scope_note_zh": "E90 捕捉 selected layers 的 residual hidden state、token-mixer/attention output、MLP output 与可用 norm output；它是机制诊断，不是 blind verifier 性能评估。",
    }
    out = out_dir / f"{args.model_key}_e90_component_cache_{args.target_mode}_{suffix}.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)
    print(f"wrote {pt_path}", flush=True)
    for s in result["summary"]:
        if s["slice_type"] in {"all", "stage"}:
            compact = {k: v for k, v in s.items() if k in {"slice_type", "slice", "n", "accept_rate", "mean_yes_minus_no"}}
            print("SUMMARY", compact, flush=True)


if __name__ == "__main__":
    main()
