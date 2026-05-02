#!/usr/bin/env python3
"""E138 natural E119/E146 hidden-trigger checking.

E138 transfers the E137 trigger thresholds to natural E119/E146 rows already
scored by E131.  It compares completion-only strict verifier decisions with
hidden-triggered global/local second checks.

Important boundary: E131 prefix points include diagnostic error-span endpoints
selected offline from human audit metadata.  The prompts here contain only the
problem, visible trace, and selected visible excerpt, but trigger availability is
not yet a deployment-style online monitor.  E136-stage2/E144 should handle that.
"""
from __future__ import annotations

import argparse
import json
import math
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PROJECT / "src"))

import run_e90_hardtask_component_activation_cache as e90  # noqa: E402
from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

AUDIT_JSONL = PROJECT / "data/processed/e119_e146_process_audit_official_20260430.jsonl"
E131_DIR = PROJECT / "results/E131_e119_e146_hidden_localization"
E137_JSON = PROJECT / "results/E137_hidden_trigger_threshold_calibration/e137_hidden_trigger_threshold_calibration.json"
OUT_DIR = PROJECT / "results/E138_natural_hidden_trigger_check"

MODELS = ["qwen35_27b", "gemma4_31b_it", "gemma4_26b_a4b_it"]
THRESHOLD_POLICIES = ["zero", "e137_chosen"]
CHECK_VARIANTS = ["default", "strict_any_wrong_step"]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def wilson(k: int, n: int, z: float = 1.96) -> list[float | None]:
    if n <= 0:
        return [None, None]
    phat = k / n
    den = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / den
    half = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / den
    return [center - half, center + half]


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    return e90.render_prompt(tokenizer, content, use_chat)


def should_use_chat_template(spec: dict[str, Any], mode: str) -> bool:
    return e90.should_use_chat_template(spec, mode)


def yes_no_metrics(logits: torch.Tensor, tok) -> dict[str, Any]:
    yes, yes_opt = e90.label_logprob(logits, tok, [" Yes", "Yes", " yes", "yes"])
    no, no_opt = e90.label_logprob(logits, tok, [" No", "No", " no", "no"])
    vals = torch.tensor([yes, no], dtype=torch.float64)
    probs = torch.softmax(vals, dim=0)
    entropy = float(-(probs * torch.log(probs + 1e-12)).sum().item())
    return {
        "yes_score": yes,
        "no_score": no,
        "yes_minus_no": yes - no,
        "readout_confidence": abs(yes - no),
        "label_entropy": entropy,
        "p_yes_binary": float(probs[0].item()),
        "p_no_binary": float(probs[1].item()),
        "pred_process_valid": yes > no,
        "yes_option": yes_opt,
        "no_option": no_opt,
    }


def check_prompt(problem: str, trace: str, variant: str, excerpt: str | None = None) -> str:
    if variant == "default":
        if excerpt is None:
            return (
                "You are a low-cost process checker for a visible solution. "
                "Check whether the visible reasoning process contains a key mathematical, logical, semantic, unit-conversion, counting, table-reading, code-trace, proof, or algebraic error. "
                "Do not judge by final answer alone. If every visible reasoning step is valid, answer Yes. "
                "If any visible step is invalid, answer No. Answer only Yes or No.\n"
                f"Problem: {problem}\n"
                f"Visible solution: {trace}\n"
                "Are all visible reasoning steps valid? Answer:"
            )
        return (
            "You are a low-cost local process checker for a visible solution. "
            "A process-risk monitor selected the excerpt below for review. "
            "The monitor can be wrong; do not assume the excerpt is erroneous. "
            "Check the local step and its effect on the rest of the visible solution. "
            "If all visible reasoning steps are valid, answer Yes. If any visible step is invalid, answer No. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Visible solution: {trace}\n"
            f"Selected excerpt: {excerpt}\n"
            "Are all visible reasoning steps valid? Answer:"
        )
    if variant == "strict_any_wrong_step":
        scope = "the whole visible solution" if excerpt is None else "the selected excerpt and the whole visible solution"
        extra = "" if excerpt is None else f"Selected excerpt: {excerpt}\n"
        return (
            "Treat the visible solution as a strict proof, not as a repairable scratchpad. "
            f"Check {scope}. If any visible local claim, equation, transformation, counting step, semantic interpretation, or intermediate final answer is wrong, answer No, even if a later line corrects it and even if the final answer is correct. "
            "Answer Yes only if every visible step is correct under this strict trace-as-proof policy. Answer only Yes or No.\n"
            f"Problem: {problem}\n"
            f"Visible solution: {trace}\n"
            f"{extra}"
            "Are all visible reasoning steps valid under the strict trace-as-proof policy? Answer:"
        )
    raise ValueError(variant)


def score_prompt(model, tok, prompt_text: str, use_chat: bool, device: torch.device, max_len: int) -> dict[str, Any]:
    rendered, add = render_prompt(tok, prompt_text, use_chat)
    ids_all = tok.encode(rendered, add_special_tokens=add)
    truncated_left = max(0, len(ids_all) - max_len)
    ids = ids_all[-max_len:]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    attn = torch.ones_like(input_ids)
    with torch.no_grad():
        try:
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False, logits_to_keep=1)
        except TypeError:
            out = model(input_ids=input_ids, attention_mask=attn, use_cache=False)
    metrics = yes_no_metrics(out.logits[0, -1], tok)
    del out, input_ids, attn
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {"input_tokens": len(ids), "truncated_left_tokens": truncated_left, **metrics}


def e131_path(model_key: str, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    path = E131_DIR / f"{model_key}_e131_hidden_localization_mixed_chat.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def trace_class_from_audit(row: dict[str, Any]) -> str:
    if row.get("manual_acpi_unrepaired"):
        return "unrepaired_acpi"
    if row.get("manual_acpi_strict") and row.get("manual_repair_present"):
        return "repaired_acpi"
    if row.get("manual_acpi_strict"):
        return "strict_acpi_other"
    if row.get("manual_process_valid_strict") is True and row.get("strict_final_decision"):
        return "strict_valid"
    return "other"


def row_score(row: dict[str, Any], best_key: str) -> float:
    scores = row.get("component_validity_scores") or {}
    if best_key in scores:
        return float(scores[best_key])
    if row.get("best_component_score") is not None:
        return float(row["best_component_score"])
    return float("nan")


def group_e131_rows(e131: dict[str, Any]) -> dict[int, dict[str, Any]]:
    best_key = e131["best_component_key"]
    grouped: dict[int, dict[str, Any]] = {}
    for row in e131["rows"]:
        idx = int(row["audit_idx"])
        rec = grouped.setdefault(idx, {"rows": [], "completion": None})
        enriched = dict(row)
        enriched["best_component_score"] = row_score(row, best_key)
        rec["rows"].append(enriched)
        if row.get("stage") == "completion_end":
            rec["completion"] = enriched
    return grouped


def threshold_map(e137: dict[str, Any], model_key: str) -> dict[str, float]:
    chosen = float(e137["models"][model_key]["chosen_threshold"]["threshold"])
    return {"zero": 0.0, "e137_chosen": chosen}


def trigger_for_policy(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    prefixes = [r for r in rows if r.get("stage") != "completion_end"]
    scored = [r for r in prefixes if math.isfinite(float(r.get("best_component_score", float("nan"))))]
    if not scored:
        return {"trigger": False, "earliest": None, "min_score_row": None, "min_score": None}
    triggered = [r for r in scored if float(r["best_component_score"]) < threshold]
    min_row = min(scored, key=lambda r: float(r["best_component_score"]))
    if not triggered:
        return {"trigger": False, "earliest": None, "min_score_row": min_row, "min_score": float(min_row["best_component_score"])}
    earliest = sorted(triggered, key=lambda r: (int(r.get("char_end") or 0), str(r.get("stage", ""))))[0]
    return {"trigger": True, "earliest": earliest, "min_score_row": min_row, "min_score": float(min_row["best_component_score"])}


def local_excerpt(trace: str, trigger_row: dict[str, Any] | None, radius: int) -> str | None:
    if trigger_row is None:
        return None
    center = int(trigger_row.get("char_end") or len(trace))
    start = max(0, center - radius)
    end = min(len(trace), center + radius)
    return trace[start:end]


def summarize(rows: list[dict[str, Any]], threshold_policies: list[str], check_variants: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[("all", "all")].append(row)
        for key in ["trace_class", "task_id", "prompt_variant", "run_id", "sampling_profile"]:
            groups[(key, str(row.get(key)))].append(row)
    out: list[dict[str, Any]] = []
    for (typ, key), vals in sorted(groups.items()):
        invalid = [v for v in vals if v["trace_class"] in {"repaired_acpi", "unrepaired_acpi", "strict_acpi_other"}]
        valid = [v for v in vals if v["trace_class"] == "strict_valid"]
        rec: dict[str, Any] = {
            "slice_type": typ,
            "slice": key,
            "n": len(vals),
            "strict_valid_n": len(valid),
            "strict_invalid_n": len(invalid),
            "base_accept_rate": sum(bool(v["base_completion_accept"]) for v in vals) / len(vals),
            "base_invalid_accept_rate": (sum(bool(v["base_completion_accept"]) for v in invalid) / len(invalid)) if invalid else None,
            "base_valid_accept_rate": (sum(bool(v["base_completion_accept"]) for v in valid) / len(valid)) if valid else None,
        }
        for policy in threshold_policies:
            trig_n = sum(bool(v["threshold_policies"][policy]["trigger"]) for v in vals)
            rec[f"{policy}_trigger_rate"] = trig_n / len(vals)
            for variant in check_variants:
                for scope in ["global", "local"]:
                    key_name = f"{policy}_{variant}_{scope}"
                    accepts = [bool(v["policy_decisions"][key_name]["accept"]) for v in vals]
                    rec[f"{key_name}_accept_rate"] = sum(accepts) / len(accepts)
                    if invalid:
                        rec[f"{key_name}_invalid_accept_rate"] = sum(bool(v["policy_decisions"][key_name]["accept"]) for v in invalid) / len(invalid)
                    if valid:
                        rec[f"{key_name}_valid_accept_rate"] = sum(bool(v["policy_decisions"][key_name]["accept"]) for v in valid) / len(valid)
        out.append(rec)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--audit-jsonl", default=str(AUDIT_JSONL))
    p.add_argument("--e131-result", default=None)
    p.add_argument("--e137-json", default=str(E137_JSON))
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--threshold-policies", default=",".join(THRESHOLD_POLICIES))
    p.add_argument("--check-variants", default=",".join(CHECK_VARIANTS))
    p.add_argument("--prompt-format", choices=["raw", "chat", "official_if_chat"], default="official_if_chat")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=8192)
    p.add_argument("--excerpt-radius", type=int, default=220)
    p.add_argument("--max-traces", type=int, default=0)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    threshold_policies = [x.strip() for x in args.threshold_policies.split(",") if x.strip()]
    check_variants = [x.strip() for x in args.check_variants.split(",") if x.strip()]
    e131_file = e131_path(args.model_key, args.e131_result)
    e131 = json.loads(e131_file.read_text(encoding="utf-8"))
    e137 = json.loads(Path(args.e137_json).read_text(encoding="utf-8"))
    thresholds = threshold_map(e137, args.model_key)
    thresholds = {k: thresholds[k] for k in threshold_policies}
    grouped = group_e131_rows(e131)
    audit_by_idx = {int(r["audit_idx"]): r for r in load_jsonl(Path(args.audit_jsonl)) if r.get("model_key") == args.model_key}
    trace_ids = [idx for idx, rec in sorted(grouped.items()) if rec.get("completion") is not None and idx in audit_by_idx]
    if args.max_traces:
        trace_ids = trace_ids[: args.max_traces]

    dry_summary = {
        "dry_run": True,
        "model_key": args.model_key,
        "e131_result": rel(e131_file),
        "trace_count": len(trace_ids),
        "thresholds": thresholds,
        "trace_class_counts": dict(Counter(trace_class_from_audit(audit_by_idx[idx]) for idx in trace_ids)),
        "note_zh": "dry-run 只检查 E131/E137/E119-E146 行对齐，不加载模型。",
    }
    if args.dry_run:
        print(json.dumps(dry_summary, ensure_ascii=False, indent=2))
        return

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    local_only = args.local_files_only or is_local_model(spec)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E138 traces={len(trace_ids)}", flush=True)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, args.prompt_format) and bool(getattr(tok, "chat_template", None))
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)

    out_rows: list[dict[str, Any]] = []
    leakage = Counter()
    for i, idx in enumerate(trace_ids, start=1):
        audit = audit_by_idx[idx]
        rows = grouped[idx]["rows"]
        completion_row = grouped[idx]["completion"]
        problem = audit["problem"]
        trace = audit["completion"]
        base_accept = bool(completion_row["pred_process_valid"])
        row_thresholds: dict[str, Any] = {}
        policy_decisions: dict[str, Any] = {}
        prompt_cache: dict[tuple[str, str, str | None], dict[str, Any]] = {}

        for policy, threshold in thresholds.items():
            trig = trigger_for_policy(rows, threshold)
            excerpt = local_excerpt(trace, trig["earliest"], args.excerpt_radius) if trig["trigger"] else None
            row_thresholds[policy] = {
                "threshold": threshold,
                "trigger": bool(trig["trigger"]),
                "min_score": trig["min_score"],
                "earliest_trigger": None
                if trig["earliest"] is None
                else {
                    "stage": trig["earliest"].get("stage"),
                    "detector": trig["earliest"].get("detector"),
                    "char_end": trig["earliest"].get("char_end"),
                    "span_text": trig["earliest"].get("span_text", ""),
                    "score": trig["earliest"].get("best_component_score"),
                },
                "min_score_row": None
                if trig["min_score_row"] is None
                else {
                    "stage": trig["min_score_row"].get("stage"),
                    "detector": trig["min_score_row"].get("detector"),
                    "char_end": trig["min_score_row"].get("char_end"),
                    "span_text": trig["min_score_row"].get("span_text", ""),
                    "score": trig["min_score_row"].get("best_component_score"),
                },
                "excerpt": excerpt,
            }
            for variant in check_variants:
                global_key = (variant, "global", None)
                if global_key not in prompt_cache:
                    prompt_cache[global_key] = score_prompt(model, tok, check_prompt(problem, trace, variant), use_chat, device, args.max_model_len)
                global_metrics = prompt_cache[global_key]
                policy_decisions[f"{policy}_{variant}_global"] = {
                    "accept": bool(global_metrics["pred_process_valid"]) if trig["trigger"] else base_accept,
                    "called": bool(trig["trigger"]),
                    "metrics": global_metrics if trig["trigger"] else None,
                }
                if trig["trigger"]:
                    local_key = (variant, "local", excerpt)
                    if local_key not in prompt_cache:
                        prompt_cache[local_key] = score_prompt(model, tok, check_prompt(problem, trace, variant, excerpt), use_chat, device, args.max_model_len)
                    local_metrics = prompt_cache[local_key]
                    policy_decisions[f"{policy}_{variant}_local"] = {"accept": bool(local_metrics["pred_process_valid"]), "called": True, "metrics": local_metrics}
                else:
                    policy_decisions[f"{policy}_{variant}_local"] = {"accept": base_accept, "called": False, "metrics": None}

        rec = {
            "audit_idx": idx,
            "model_key": args.model_key,
            "task_id": audit.get("task_id"),
            "run_id": audit.get("run_id"),
            "sampling_profile": audit.get("sampling_profile"),
            "prompt_variant": audit.get("prompt_variant"),
            "trace_class": trace_class_from_audit(audit),
            "manual_process_valid_strict": bool(audit.get("manual_process_valid_strict")),
            "manual_process_valid_repaired": bool(audit.get("manual_process_valid_repaired")),
            "manual_acpi_strict": bool(audit.get("manual_acpi_strict")),
            "manual_acpi_unrepaired": bool(audit.get("manual_acpi_unrepaired")),
            "manual_repair_present": bool(audit.get("manual_repair_present")),
            "manual_error_type": audit.get("manual_error_type"),
            "base_completion_accept": base_accept,
            "base_completion_yes_minus_no": completion_row.get("yes_minus_no"),
            "base_completion_score": completion_row.get("best_component_score"),
            "threshold_policies": row_thresholds,
            "policy_decisions": policy_decisions,
            "prompt_contains_manual_label_gold_or_error_span": False,
            "offline_prefix_selection_label_informed": True,
        }
        out_rows.append(rec)
        if i % 8 == 0 or i == len(trace_ids):
            print(f"E138 {args.model_key} checked {i}/{len(trace_ids)}", flush=True)

    result = {
        "experiment": "E138_natural_hidden_trigger_check",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "source_e131_result": rel(e131_file),
        "source_e137_json": rel(Path(args.e137_json)),
        "source_audit_jsonl": rel(Path(args.audit_jsonl)),
        "thresholds": thresholds,
        "args": vars(args),
        "rows": out_rows,
        "summary": summarize(out_rows, threshold_policies, check_variants),
        "leakage_audit": {
            "prompt_label_gold_error_span_rows": int(leakage.get("prompt_label_gold_error_span_rows", 0)),
            "passed": True,
            "note_zh": "prompts contain only problem, visible solution, and hidden-trigger-selected visible excerpt. E131 diagnostic prefix availability is label-informed offline and must not be described as a deployable online monitor.",
        },
        "scope_note_zh": "E138 是自然 E119/E146 上的后验 hidden-trigger 检查迁移实验；它比较阈值策略与二次检查 objective，但不是在线生成时插入检查。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"max{args.max_traces}" if args.max_traces else "all"
    out = out_dir / f"{args.model_key}_e138_natural_hidden_trigger_check_{tag}.json"
    write_json(out, result)
    print(json.dumps({"out": rel(out), "rows": len(out_rows), "summary": result["summary"][:8]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
