#!/usr/bin/env python3
"""Run E172 hidden-gate realtime observation on AIME 2026.

The script generates in small non-thinking chunks, teacher-forces the current
visible prefix through the E166 component monitor, and writes an observation
row immediately.  If the calibrated risk threshold is crossed, it stops the
first branch and starts a non-thinking controlled-check branch.
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
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(PROJECT / "src"))

import run_e49_hard_task_conditioning_official as e49  # noqa: E402
import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
import run_e166_hardened_hidden_monitor_replay as e166  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

TASK_BANK = PROJECT / "data/processed/e172_aime2026_matharena_task_bank_20260502.jsonl"
OUT_DIR = PROJECT / "results/E172_aime2026_hidden_gate"
CALIBRATION = PROJECT / "reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.json"

BASELINE_TEMPLATE = (
    "Solve the following AIME 2026 problem carefully in non-thinking mode. "
    "Show only the reasoning needed to justify the answer; do not give the final answer before the reasoning. "
    "End with exactly one line `Final answer: <integer>`.\n\n"
    "Problem: {problem}"
)

CONTROLLED_TEMPLATE = (
    "A hidden monitor flagged this visible span as potentially abnormal: `{localized_span}`. "
    "The signal came from hidden/component state while running non-thinking generation, not from a gold answer. "
    "Stay in non-thinking mode, do a short controlled check of the flagged span against the problem, correct it if needed, and continue. "
    "End with exactly one line `Final answer: <integer>`.\n\n"
    "Problem: {problem}\n\nPartial solution so far:\n{prefix}"
)

BOXED_RE = re.compile(r"\\boxed\s*\{\s*(-?\d+(?:\.\d+)?)\s*\}", re.IGNORECASE)
FINAL_RE = re.compile(r"^\s*final\s*answer\s*[:：]\s*[^\n]+", re.IGNORECASE | re.MULTILINE)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_extracted_answer(text: str) -> str:
    boxed = list(BOXED_RE.finditer(text))
    if boxed:
        return boxed[-1].group(1).strip()
    simple_box = re.fullmatch(r"\s*\\boxed\s*\{\s*([^}]+?)\s*\}\s*\.?\s*", text, flags=re.IGNORECASE)
    if simple_box:
        return simple_box.group(1).strip()
    return text.strip()


def select_tasks(tasks: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    task_ids = set(args.task_ids or [])
    out = [t for t in tasks if not task_ids or t["task_id"] in task_ids or str(t["problem_idx"]) in task_ids]
    out = sorted(out, key=lambda t: int(t["problem_idx"]))
    if args.max_tasks > 0:
        out = out[: args.max_tasks]
    return out


def render_generation_chat(tokenizer, spec: dict[str, Any], content: str) -> tuple[str, bool, bool]:
    use_chat = e49.should_use_chat(spec, tokenizer)
    if not use_chat:
        return content + "\nReasoning:", False, True
    messages = [{"role": "user", "content": content}]
    try:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return text, True, False


def render_monitor_prompt(tokenizer, spec: dict[str, Any], problem: str, prefix: str) -> tuple[str, bool, bool]:
    content = e166.render_prefill_content({"problem": problem, "prefix_text": prefix}, "generation_prefill")
    return e166.render_chat(tokenizer, spec, content, "official_if_chat")


def component_key_tuple(key: str) -> tuple[int, str]:
    hidden_idx, comp = key.split(":", 1)
    return int(hidden_idx), comp


def load_calibration(model_key: str, threshold_mode: str, threshold_override: float | None) -> dict[str, Any]:
    data = load_json(CALIBRATION)
    for row in data["models"]:
        if row["model_key"] == model_key:
            best = row["best_key_record"]
            eval_key = "budgeted_eval" if threshold_mode == "budgeted" else "high_precision_eval"
            threshold = float(threshold_override) if threshold_override is not None else float(best[eval_key]["threshold"])
            out = dict(row)
            out["threshold_mode"] = threshold_mode
            out["threshold"] = threshold
            out["threshold_source"] = "override" if threshold_override is not None else f"E166.{eval_key}.threshold"
            return out
    raise KeyError(f"No E166 calibration found for {model_key}")


def torch_load(path: Path) -> dict[str, Any]:
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def load_monitor_direction_center(
    calibration: dict[str, Any],
    best_key: str,
    model,
    tokenizer,
    spec: dict[str, Any],
    device: torch.device,
    max_model_len: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
) -> tuple[torch.Tensor, torch.Tensor, str]:
    cache_rel = calibration.get("component_cache_pt", "")
    if cache_rel:
        cache_path = PROJECT / cache_rel
        if cache_path.exists():
            cache = torch_load(cache_path)
            keys = list(cache.get("component_keys", []))
            if best_key in keys and "monitor_directions" in cache and "monitor_centers" in cache:
                idx = keys.index(best_key)
                return cache["monitor_directions"][idx].float().cpu(), cache["monitor_centers"][idx].float().cpu(), str(cache_path.relative_to(PROJECT))
    use_chat = e90.should_use_chat_template(spec, "official_if_chat") and bool(getattr(tokenizer, "chat_template", None))
    directions, centers, _ = e90.train_component_directions(model, tokenizer, use_chat, device, max_model_len, hidden_layers, component_plan)
    key = component_key_tuple(best_key)
    if key not in directions:
        raise RuntimeError(f"Monitor key {best_key} unavailable after training directions")
    return directions[key].float().cpu(), centers[key].float().cpu(), "trained_from_e61_this_run"


def score_risk(validity_score: float) -> float:
    return -float(validity_score)


def last_visible_span(text: str, max_chars: int) -> str:
    text = text.strip()
    if not text:
        return ""
    boundaries = [0]
    for m in re.finditer(r"\n+|(?<=[.!?。！？；;])\s+", text):
        boundaries.append(m.end())
    start = max(boundaries[-1], len(text) - max_chars)
    span = text[start:].strip()
    if len(span) > max_chars:
        span = span[-max_chars:].strip()
    return span or text[-max_chars:].strip()


def generate_more(
    model,
    tokenizer,
    prompt_text: str,
    add_special_tokens: bool,
    device: torch.device,
    pad_token_id: int,
    max_model_len: int,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    top_k: int,
) -> tuple[str, int, int]:
    ids = tokenizer.encode(prompt_text, add_special_tokens=add_special_tokens)
    truncated_left = max(0, len(ids) - max_model_len)
    ids = ids[-max_model_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids, device=device)
    gen_kwargs = dict(max_new_tokens=max_new_tokens, pad_token_id=pad_token_id)
    if temperature > 0:
        gen_kwargs.update(dict(do_sample=True, temperature=temperature, top_p=top_p, top_k=top_k))
    else:
        gen_kwargs.update(dict(do_sample=False))
    with torch.no_grad():
        seq = model.generate(input_ids=input_ids, attention_mask=attn, **gen_kwargs)[0]
    gen_ids = seq[input_ids.shape[1] :]
    text = tokenizer.decode(gen_ids, skip_special_tokens=True)
    del input_ids, attn, seq
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return text, int(gen_ids.numel()), int(truncated_left)


def observe_hidden(
    model,
    tokenizer,
    spec: dict[str, Any],
    task: dict[str, Any],
    completion: str,
    observation_index: int,
    device: torch.device,
    max_model_len: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
    monitor_key_tuple: tuple[int, str],
    monitor_key: str,
    direction: torch.Tensor,
    center: torch.Tensor,
    threshold: float,
    threshold_mode: str,
    visible_span_chars: int,
) -> dict[str, Any]:
    prompt, used_chat, add = render_monitor_prompt(tokenizer, spec, task["problem"], completion)
    feats, meta = e166.collect_prefill_activation(model, tokenizer, prompt, add, device, max_model_len, hidden_layers, component_plan)
    if monitor_key_tuple not in feats:
        raise RuntimeError(f"Monitor key {monitor_key} missing from captured features")
    validity_score = float(((feats[monitor_key_tuple] - center) * direction).sum().item())
    risk = score_risk(validity_score)
    rec = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E172_aime2026_hidden_gate_observation",
        "model_key": spec.get("_model_key", ""),
        "task_id": task["task_id"],
        "problem_idx": int(task["problem_idx"]),
        "observation_index": observation_index,
        "prefix_char_end": len(completion),
        "prefix_token_estimate": len(tokenizer.encode(completion, add_special_tokens=False)),
        "visible_span": last_visible_span(completion, visible_span_chars),
        "hidden_component_key": monitor_key,
        "hidden_validity_score": validity_score,
        "hidden_risk": risk,
        "hidden_threshold": threshold,
        "hidden_threshold_mode": threshold_mode,
        "hidden_threshold_crossed": bool(risk >= threshold),
        "monitor_prompt_used_chat_template": used_chat,
        "monitor_prompt_add_special_tokens": add,
        "selected_hidden_layers": hidden_layers,
        **meta,
    }
    return rec


def append_jsonl(path: Path | None, row: dict[str, Any]) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def first_final_seen(text: str) -> bool:
    return bool(FINAL_RE.search(text) or BOXED_RE.search(text))


def run_task(
    task: dict[str, Any],
    args: argparse.Namespace,
    model,
    tokenizer,
    spec: dict[str, Any],
    device: torch.device,
    pad_token_id: int,
    hidden_layers: list[int],
    component_plan: dict[tuple[int, str], Any],
    monitor_key_tuple: tuple[int, str],
    monitor_key: str,
    direction: torch.Tensor,
    center: torch.Tensor,
    calibration: dict[str, Any],
    observation_path: Path | None,
) -> dict[str, Any]:
    baseline_content = BASELINE_TEMPLATE.format(problem=task["problem"])
    baseline_prompt, used_chat, add_special = render_generation_chat(tokenizer, spec, baseline_content)
    completion = ""
    total_generated = 0
    total_truncated_left = 0
    last_observed_tokens = 0
    observations: list[dict[str, Any]] = []
    trigger: dict[str, Any] | None = None
    stop_reason = "max_first_pass_tokens"

    while total_generated < args.max_first_pass_tokens:
        chunk = min(args.chunk_tokens, args.max_first_pass_tokens - total_generated)
        new_text, new_tokens, truncated_left = generate_more(
            model,
            tokenizer,
            baseline_prompt + completion,
            add_special,
            device,
            pad_token_id,
            args.max_model_len,
            chunk,
            args.temperature,
            args.top_p,
            args.top_k,
        )
        completion += new_text
        total_generated += new_tokens
        total_truncated_left += truncated_left
        completion_tokens_est = len(tokenizer.encode(completion, add_special_tokens=False))
        if first_final_seen(completion):
            stop_reason = "final_marker_seen_before_gate"
            break
        enough_new_tokens = completion_tokens_est - last_observed_tokens >= args.observe_every_tokens
        enough_chars = len(completion.strip()) >= args.min_observe_chars
        if enough_chars and (enough_new_tokens or new_tokens == 0 or total_generated >= args.max_first_pass_tokens):
            obs = observe_hidden(
                model,
                tokenizer,
                spec,
                task,
                completion,
                len(observations),
                device,
                args.max_model_len,
                hidden_layers,
                component_plan,
                monitor_key_tuple,
                monitor_key,
                direction,
                center,
                float(calibration["threshold"]),
                str(calibration["threshold_mode"]),
                args.visible_span_chars,
            )
            observations.append(obs)
            append_jsonl(observation_path, obs)
            last_observed_tokens = completion_tokens_est
            print(
                f"E172 observe model={args.model_key} task={task['task_id']} obs={obs['observation_index']} risk={obs['hidden_risk']:.3f} threshold={obs['hidden_threshold']:.3f} crossed={obs['hidden_threshold_crossed']}",
                flush=True,
            )
            if obs["hidden_threshold_crossed"]:
                trigger = obs
                stop_reason = "hidden_gate_trigger"
                break
        if new_tokens == 0:
            stop_reason = "model_generated_no_tokens"
            break

    controlled_content = ""
    controlled_prompt_tokens = 0
    controlled_completion = ""
    controlled_tokens = 0
    controlled_hit_max = False
    controlled_used_chat = False
    controlled_truncated_left = 0
    if trigger is not None:
        controlled_content = CONTROLLED_TEMPLATE.format(
            problem=task["problem"],
            prefix=completion,
            localized_span=trigger.get("visible_span") or "the current partial solution",
        )
        controlled_prompt, controlled_used_chat, controlled_add_special = render_generation_chat(tokenizer, spec, controlled_content)
        controlled_prompt_tokens = len(tokenizer.encode(controlled_prompt, add_special_tokens=controlled_add_special))
        controlled_completion, controlled_tokens, controlled_truncated_left = generate_more(
            model,
            tokenizer,
            controlled_prompt,
            controlled_add_special,
            device,
            pad_token_id,
            args.max_model_len,
            args.max_controlled_tokens,
            args.temperature,
            args.top_p,
            args.top_k,
        )
        controlled_completion = controlled_completion.strip()
        controlled_hit_max = controlled_tokens >= args.max_controlled_tokens

    final_text = controlled_completion if trigger is not None else completion
    extracted_raw, marker, method = e49.extract_final_answer(final_text, allow_fallback=True)
    extracted = canonical_extracted_answer(extracted_raw)
    final_correct = e49.normalize_answer(extracted) == e49.normalize_answer(str(task["gold_answer"]))
    top_risk = max((float(o["hidden_risk"]) for o in observations), default=None)
    row = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "E172_aime2026_hidden_gate_realtime",
        "model_key": args.model_key,
        "task_id": task["task_id"],
        "source_task_id": task.get("source_task_id", ""),
        "problem_idx": int(task["problem_idx"]),
        "task_source": task["task_source"],
        "family": task["family"],
        "problem": task["problem"],
        "gold_answer": task["gold_answer"],
        "dataset_repo": task.get("dataset_repo", ""),
        "dataset_sha": task.get("dataset_sha", ""),
        "thinking": False,
        "prompt_variant": "hidden_gate_realtime_controlled_nonthinking",
        "used_chat_template_first_pass": used_chat,
        "chat_template_enable_thinking_false_requested": bool(used_chat),
        "gold_answer_in_prompt": False,
        "dataset_metadata_in_prompt": False,
        "hidden_component_key": monitor_key,
        "hidden_threshold": float(calibration["threshold"]),
        "hidden_threshold_mode": calibration["threshold_mode"],
        "hidden_threshold_source": calibration["threshold_source"],
        "hidden_gate_triggered": trigger is not None,
        "hidden_gate_stop_reason": stop_reason,
        "hidden_observations": len(observations),
        "hidden_top_risk": top_risk,
        "hidden_trigger_observation": trigger or {},
        "first_pass_prompt_content": baseline_content,
        "first_pass_completion_until_stop": completion.strip(),
        "first_pass_generated_tokens": total_generated,
        "first_pass_hit_max_tokens": bool(total_generated >= args.max_first_pass_tokens and trigger is None),
        "first_pass_total_truncated_left_tokens": total_truncated_left,
        "controlled_prompt_content": controlled_content,
        "controlled_prompt_tokens": controlled_prompt_tokens,
        "controlled_used_chat_template": controlled_used_chat,
        "controlled_completion": controlled_completion,
        "controlled_generated_tokens": controlled_tokens,
        "controlled_hit_max_new_tokens": controlled_hit_max,
        "controlled_truncated_left_tokens": controlled_truncated_left,
        "completion_for_scoring": final_text.strip(),
        "extracted_final": extracted,
        "extracted_final_raw": extracted_raw,
        "extraction_method": method,
        "final_marker_found": marker,
        "manual_final_correct": final_correct,
        "generated_tokens_total": total_generated + controlled_tokens,
        "hit_max_new_tokens": bool((trigger is None and total_generated >= args.max_first_pass_tokens) or controlled_hit_max),
        "observations": observations if args.include_observations_in_result else [],
    }
    return row


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_gate: dict[str, Counter[str]] = defaultdict(Counter)
    by_task: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for bucket in (by_gate[str(bool(row["hidden_gate_triggered"]))], by_task[row["task_id"]]):
            bucket["n"] += 1
            bucket["manual_final_correct"] += int(row["manual_final_correct"])
            bucket["final_marker_found"] += int(row["final_marker_found"])
            bucket["hit_max"] += int(row["hit_max_new_tokens"])
            bucket["generated_tokens_total"] += int(row["generated_tokens_total"])
    risks = [float(r["hidden_top_risk"]) for r in rows if r.get("hidden_top_risk") is not None]
    return {
        "jobs": len(rows),
        "manual_final_correct": sum(int(r["manual_final_correct"]) for r in rows),
        "accuracy": sum(int(r["manual_final_correct"]) for r in rows) / len(rows) if rows else None,
        "hidden_gate_triggered": sum(int(r["hidden_gate_triggered"]) for r in rows),
        "hidden_gate_not_triggered": sum(int(not r["hidden_gate_triggered"]) for r in rows),
        "final_marker_found": sum(int(r["final_marker_found"]) for r in rows),
        "hit_max": sum(int(r["hit_max_new_tokens"]) for r in rows),
        "generated_tokens_total": sum(int(r["generated_tokens_total"]) for r in rows),
        "hidden_observations": sum(int(r["hidden_observations"]) for r in rows),
        "mean_hidden_top_risk": mean(risks) if risks else None,
        "leakage_audit": {
            "gold_answer_in_prompt_rows": sum(int(r["gold_answer_in_prompt"]) for r in rows),
            "dataset_metadata_in_prompt_rows": sum(int(r["dataset_metadata_in_prompt"]) for r in rows),
        },
        "by_gate_triggered": {k: dict(v) for k, v in sorted(by_gate.items())},
        "by_task": {k: dict(v) for k, v in sorted(by_task.items())},
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--task-bank", default=str(TASK_BANK))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--task-ids", nargs="*", default=[])
    p.add_argument("--max-tasks", type=int, default=0)
    p.add_argument("--max-first-pass-tokens", type=int, default=16384)
    p.add_argument("--max-controlled-tokens", type=int, default=4096)
    p.add_argument("--chunk-tokens", type=int, default=96)
    p.add_argument("--observe-every-tokens", type=int, default=96)
    p.add_argument("--min-observe-chars", type=int, default=160)
    p.add_argument("--visible-span-chars", type=int, default=420)
    p.add_argument("--threshold-mode", choices=["high_precision", "budgeted"], default="high_precision")
    p.add_argument("--threshold-override", type=float, default=None)
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--top-k", type=int, default=0)
    p.add_argument("--checkpoint-jsonl", default="")
    p.add_argument("--observation-jsonl", default="")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--include-observations-in-result", action="store_true")
    p.add_argument("--tag", default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    tasks = select_tasks(load_jsonl(Path(args.task_bank)), args)
    if not tasks:
        raise SystemExit("No E172 AIME2026 tasks selected")
    registry = read_yaml(args.registry)["models"]
    spec = dict(registry[args.model_key])
    spec["_model_key"] = args.model_key
    calibration = load_calibration(args.model_key, args.threshold_mode, args.threshold_override)
    best_key = calibration["best_key"]
    best_tuple = component_key_tuple(best_key)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E172 hidden-gate realtime tasks={len(tasks)} best_key={best_key}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    pad_token_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    layers = get_transformer_layers(model)
    hidden_layers = [best_tuple[0]]
    if not (1 <= hidden_layers[0] <= len(layers)):
        raise RuntimeError(f"Best hidden layer {hidden_layers[0]} is outside model layers={len(layers)}")
    component_plan = e90.build_component_plan(layers, hidden_layers)
    direction, center, direction_source = load_monitor_direction_center(
        calibration,
        best_key,
        model,
        tok,
        spec,
        device,
        args.max_model_len,
        hidden_layers,
        component_plan,
    )
    if best_tuple[1] != "residual_hidden_state" and best_tuple not in component_plan:
        raise RuntimeError(f"Best component {best_key} not in component plan")

    checkpoint = Path(args.checkpoint_jsonl) if args.checkpoint_jsonl else None
    observation_path = Path(args.observation_jsonl) if args.observation_jsonl else None
    if checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text("", encoding="utf-8")
    if observation_path:
        observation_path.parent.mkdir(parents=True, exist_ok=True)
        observation_path.write_text("", encoding="utf-8")

    rows: list[dict[str, Any]] = []
    for idx, task in enumerate(tasks, start=1):
        row = run_task(
            task,
            args,
            model,
            tok,
            spec,
            device,
            pad_token_id,
            hidden_layers,
            component_plan,
            best_tuple,
            best_key,
            direction,
            center,
            calibration,
            observation_path,
        )
        rows.append(row)
        append_jsonl(checkpoint, row)
        print(
            f"E172 hidden-gate {idx}/{len(tasks)} task={task['task_id']} triggered={row['hidden_gate_triggered']} correct={row['manual_final_correct']} tokens={row['generated_tokens_total']}",
            flush=True,
        )

    summary = summarize(rows)
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "args": vars(args),
        "calibration": {
            "best_key": best_key,
            "threshold": calibration["threshold"],
            "threshold_mode": calibration["threshold_mode"],
            "threshold_source": calibration["threshold_source"],
            "direction_source": direction_source,
            "selected_hidden_layers": hidden_layers,
        },
        "prompt_templates": {
            "baseline": BASELINE_TEMPLATE,
            "controlled": CONTROLLED_TEMPLATE,
        },
        "summary": summary,
        "rows": rows,
    }
    tag = f"_{args.tag}" if args.tag else ""
    out_path = Path(args.out_dir) / f"{args.model_key}_e172_aime2026_hidden_gate{tag}.json"
    write_json(out_path, result)
    print(f"wrote {out_path}", flush=True)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
