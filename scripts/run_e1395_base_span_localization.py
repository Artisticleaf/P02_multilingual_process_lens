#!/usr/bin/env python3
"""E139.5 base/no-check wrong-step localization audit.

E139 showed that failure rows can still contain an identifiable wrong step,
but its prompts explicitly asked for strict and repair-aware decisions.  E139.5
removes the global acceptance decision: it asks whether the same model can
directly locate the wrong step under base and strengthened locate-only prompts.

Manual labels and error spans are used only for row selection/evaluation.
Prompts contain only the problem and visible candidate solution.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import socket
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from transformers import StoppingCriteria, StoppingCriteriaList

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402

E132_DATA = PROJECT / "data/processed/e132_suspicious_valid_controls_20260430.jsonl"
E136_DIR = PROJECT / "results/E136_suspicious_confidence_adaptive_check"
OUT_DIR = PROJECT / "results/E1395_base_span_localization"

PROMPT_VARIANTS = ["base_span_only", "strong_span_only", "direct_json_final_only"]
CONTROL_VARIANTS = ["clean_valid", "suspicious_valid_marker", "low_conf_valid"]

FAILURE_POLICY_KEYS = [
    "plain_base_no_check_accept",
    "plain_always_global_check_accept",
    "plain_hidden_global_check_accept",
    "plain_hidden_local_check_accept",
    "strict_base_no_check_accept",
    "strict_always_global_check_accept",
    "strict_hidden_global_check_accept",
    "strict_hidden_local_check_accept",
]

BLOCK_RE = re.compile(r"<SPAN_AUDIT>\s*(.*?)\s*</SPAN_AUDIT>", re.IGNORECASE | re.DOTALL)
HAS_RE = re.compile(r"^\s*Has error\s*[:：]\s*(Yes|No|True|False)\b", re.IGNORECASE | re.MULTILINE)
FIRST_RE = re.compile(r"^\s*First wrong step\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE)
ALL_RE = re.compile(r"^\s*All wrong steps\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE)
TYPE_RE = re.compile(r"^\s*Error type\s*[:：]\s*(.*)$", re.IGNORECASE | re.MULTILINE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def e136_path(model_key: str) -> Path:
    path = E136_DIR / f"{model_key}_e136_suspicious_confidence_adaptive_check_rowspervariant12.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def failure_policy_names(row: dict[str, Any]) -> list[str]:
    return [key for key in FAILURE_POLICY_KEYS if bool(row.get(key))]


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content + "\nAnswer:", True
    messages = [{"role": "user", "content": content}]
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(messages, enable_thinking=False, **kwargs), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs), False


def should_use_chat(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def locate_prompt(problem: str, trace: str, variant: str) -> str:
    if variant == "base_span_only":
        return (
            "You are checking a candidate solution. Find whether it contains a wrong reasoning step. "
            "If a wrong step exists, quote the first wrong step from the candidate solution. "
            "If no wrong step exists, write NONE. Do not judge whether the final answer is correct. "
            "Do not continue or repair the solution. Do not write any explanation before or after the block. "
            "Finish exactly with:\n"
            "<SPAN_AUDIT>\n"
            "Has error: <Yes/No>\n"
            "First wrong step: <quote or NONE>\n"
            "Error type: <short type or NONE>\n"
            "</SPAN_AUDIT>\n\n"
            "Return exactly one <SPAN_AUDIT> block. The first generated token should be '<'. Stop immediately after </SPAN_AUDIT>.\n\n"
            f"Problem: {problem}\n"
            f"Candidate solution: {trace}\n"
        )
    if variant == "strong_span_only":
        return (
            "The first text is the task problem. The second text is a candidate solution written by another system; it is not your chain-of-thought. "
            "Your only job is error localization. Do not solve the task, do not rewrite the solution, and do not decide whether the solution should be accepted. "
            "A later correct calculation does not erase an earlier wrong visible step. Quote only text that appears in the candidate solution. "
            "Do not write any explanation before or after the block. "
            "Finish exactly with:\n"
            "<SPAN_AUDIT>\n"
            "Has error: <Yes/No>\n"
            "First wrong step: <quote or NONE>\n"
            "All wrong steps: <semicolon-separated quotes or NONE>\n"
            "Error type: <short type or NONE>\n"
            "</SPAN_AUDIT>\n\n"
            "Return exactly one <SPAN_AUDIT> block. The first generated token should be '<'. Stop immediately after </SPAN_AUDIT>.\n\n"
            f"Problem: {problem}\n"
            f"Candidate solution: {trace}\n"
        )
    if variant == "direct_json_final_only":
        return (
            "Inspect the candidate solution for wrong reasoning steps. Output only one JSON object and no reasoning text. "
            "The candidate solution is not your chain-of-thought. Do not solve or repair it. "
            "Do not use Markdown fences. Do not repeat. Stop immediately after the closing brace. "
            "Use this schema exactly: {\"has_error\": true/false, \"first_wrong_step\": \"quote or NONE\", \"error_type\": \"short type or NONE\"}.\n"
            f"Problem: {problem}\n"
            f"Candidate solution: {trace}\n"
        )
    raise ValueError(f"unknown prompt variant {variant}")


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Return the first balanced JSON object in text.

    Some Gemma generations repeat a valid fenced JSON object several times.
    Taking the first "{" and last "}" then falsely turns a valid answer into
    an invalid multi-object string, so we scan balanced objects in order.
    """
    starts = [m.start() for m in re.finditer(r"\{", text)]
    for start in starts:
        depth = 0
        in_string = False
        escape = False
        for pos in range(start, len(text)):
            ch = text[pos]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start : pos + 1])
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError:
                        break
    return None


def parse_output(text: str, variant: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {
        "parse_ok": False,
        "has_error": None,
        "first_wrong_step": "",
        "all_wrong_steps": "",
        "error_type": "",
        "final_block_found": False,
        "json_found": False,
    }
    if variant == "direct_json_final_only":
        obj = extract_json_object(text)
        if obj is not None:
            parsed["json_found"] = True
            parsed["has_error"] = bool(obj.get("has_error")) if isinstance(obj.get("has_error"), bool) else str(obj.get("has_error", "")).strip().lower() in {"yes", "true", "1"}
            parsed["first_wrong_step"] = str(obj.get("first_wrong_step", "")).strip()
            parsed["error_type"] = str(obj.get("error_type", "")).strip()
            parsed["parse_ok"] = True
            return parsed
    block = BLOCK_RE.search(text)
    parse_text = block.group(1) if block else text
    parsed["final_block_found"] = bool(block)
    has = HAS_RE.search(parse_text)
    first = FIRST_RE.search(parse_text)
    all_steps = ALL_RE.search(parse_text)
    typ = TYPE_RE.search(parse_text)
    if has:
        parsed["has_error"] = has.group(1).strip().lower() in {"yes", "true"}
    if first:
        parsed["first_wrong_step"] = first.group(1).strip()
    if all_steps:
        parsed["all_wrong_steps"] = all_steps.group(1).strip()
    if typ:
        parsed["error_type"] = typ.group(1).strip()
    parsed["parse_ok"] = has is not None and first is not None
    return parsed


def norm_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\s\"'`“”‘’.,;:!?，。；：！？()（）\\[\\]{}<>]", "", text)
    return text


def span_hit(predicted: str, expected: str | None) -> bool:
    if not expected:
        return False
    pred = norm_text(predicted)
    exp = norm_text(expected)
    if not pred or not exp:
        return False
    if len(pred) >= 6 and (pred in exp or exp in pred):
        return True
    return difflib.SequenceMatcher(None, pred, exp).ratio() >= 0.58


def no_error_claim(parsed: dict[str, Any]) -> bool:
    step = norm_text(str(parsed.get("first_wrong_step", "")))
    return parsed.get("has_error") is False or step in {"", "none", "na", "n/a", "no"}


def eos_token_ids(tok) -> set[int]:
    ids: set[int] = set()
    eos = tok.eos_token_id
    if isinstance(eos, list):
        ids.update(int(x) for x in eos)
    elif eos is not None:
        ids.add(int(eos))
    return ids


class StopOnDecodedString(StoppingCriteria):
    def __init__(self, tokenizer, prompt_len: int, stop_strings: list[str]):
        self.tokenizer = tokenizer
        self.prompt_len = prompt_len
        self.stop_strings = [s for s in stop_strings if s]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        if not self.stop_strings:
            return False
        tail = input_ids[0, self.prompt_len :]
        if tail.numel() == 0:
            return False
        text = self.tokenizer.decode(tail.detach().cpu(), skip_special_tokens=True)
        return any(stop in text for stop in self.stop_strings)


def stop_strings_for_variant(variant: str) -> list[str]:
    if variant in {"base_span_only", "strong_span_only"}:
        return ["</SPAN_AUDIT>"]
    if variant == "direct_json_final_only":
        return ["}"]
    return []


def trim_after_first_stop(text: str, stop_strings: list[str]) -> tuple[str, bool, str]:
    hits = [(text.find(stop), stop) for stop in stop_strings if stop and text.find(stop) >= 0]
    if not hits:
        return text, False, ""
    idx, stop = min(hits, key=lambda x: x[0])
    return text[: idx + len(stop)].strip(), True, stop


def generate_one(
    model,
    tok,
    prompt: str,
    add_special: bool,
    device: torch.device,
    max_input_tokens: int,
    max_new_tokens: int,
    max_time: float,
    stop_strings: list[str] | None = None,
) -> dict[str, Any]:
    enc = tok(prompt, return_tensors="pt", add_special_tokens=add_special, truncation=True, max_length=max_input_tokens).to(device)
    stop_strings = stop_strings or []
    kwargs: dict[str, Any] = {
        **enc,
        "do_sample": False,
        "max_new_tokens": max_new_tokens,
        "pad_token_id": tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id,
    }
    if tok.eos_token_id is not None:
        kwargs["eos_token_id"] = tok.eos_token_id
    if max_time > 0:
        kwargs["max_time"] = max_time
    if stop_strings:
        kwargs["stopping_criteria"] = StoppingCriteriaList([StopOnDecodedString(tok, enc["input_ids"].shape[1], stop_strings)])
    with torch.no_grad():
        out = model.generate(**kwargs)
    prompt_len = enc["input_ids"].shape[1]
    gen_ids = out[0, prompt_len:]
    raw_completion = tok.decode(gen_ids, skip_special_tokens=True).strip()
    completion, stopped_with_stop_string, matched_stop_string = trim_after_first_stop(raw_completion, stop_strings)
    eos_ids = eos_token_ids(tok)
    stopped_with_eos = bool(gen_ids.numel() and int(gen_ids[-1].item()) in eos_ids)
    return {
        "completion": completion,
        "raw_completion": raw_completion,
        "input_tokens": int(prompt_len),
        "generated_tokens": int(gen_ids.numel()),
        "hit_max_new_tokens": bool(gen_ids.numel() >= max_new_tokens and not stopped_with_stop_string),
        "stopped_with_eos": stopped_with_eos,
        "stopped_with_stop_string": stopped_with_stop_string,
        "matched_stop_string": matched_stop_string,
        "may_have_hit_max_time": bool(max_time > 0 and not stopped_with_eos and gen_ids.numel() < max_new_tokens),
        "truncated_input": bool(enc["input_ids"].shape[1] >= max_input_tokens),
    }


def select_source_rows(model_key: str, e136_rows: list[dict[str, Any]], data_by_idx: dict[int, dict[str, Any]], control_variants: list[str]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    rows_by_family_route_variant = {(r["family"], r["route_id"], r["variant"]): r for r in data_by_idx.values()}
    for row in sorted(e136_rows, key=lambda r: int(r["audit_idx"])):
        failures = failure_policy_names(row)
        if bool(row["manual_process_valid_strict"]) or not failures:
            continue
        src = data_by_idx[int(row["audit_idx"])]
        expected = (row.get("policy_trigger_meta") or {}).get("span_text") or src.get("manual_error_span") or ""
        rec = {
            "source_kind": "strict_invalid_failure",
            "selection_reason": "e136_base_or_check_failed_to_reject",
            "failure_policy_names": failures,
            "model_key_for_selection": model_key,
            "expected_error_span": expected,
            "e136_policy_trigger_meta": row.get("policy_trigger_meta"),
            **src,
        }
        selected.append(rec)
        seen.add((int(src["audit_idx"]), rec["source_kind"]))
        for variant in control_variants:
            ctrl = rows_by_family_route_variant.get((src["family"], src["route_id"], variant))
            if not ctrl:
                continue
            key = (int(ctrl["audit_idx"]), variant)
            if key in seen:
                continue
            selected.append({
                "source_kind": f"valid_control::{variant}",
                "selection_reason": "matched_family_route_valid_control",
                "failure_policy_names": [],
                "model_key_for_selection": model_key,
                "expected_error_span": "",
                "e136_policy_trigger_meta": None,
                **ctrl,
            })
            seen.add(key)
    selected.sort(key=lambda r: (str(r["source_kind"]), int(r["audit_idx"])))
    return selected


def build_jobs(rows: list[dict[str, Any]], variants: list[str], max_jobs: int) -> list[dict[str, Any]]:
    jobs = [{"row": row, "prompt_variant": variant} for row in rows for variant in variants]
    return jobs[:max_jobs] if max_jobs else jobs


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups["all"].append(row)
        groups[f"prompt={row['prompt_variant']}"].append(row)
        groups[f"source={row['source_kind']}"].append(row)
        groups[f"family={row['family']}"].append(row)
        groups[f"route={row['route_id']}"].append(row)
    by_slice = {}
    for key, vals in sorted(groups.items()):
        invalid = [r for r in vals if not r["manual_process_valid_strict"]]
        valid = [r for r in vals if r["manual_process_valid_strict"]]
        by_slice[key] = {
            "n": len(vals),
            "parse_ok_rate": sum(r["parsed"]["parse_ok"] for r in vals) / len(vals),
            "hit_max_rate": sum(r["generation"]["hit_max_new_tokens"] for r in vals) / len(vals),
            "invalid_n": len(invalid),
            "valid_n": len(valid),
            "invalid_has_error_rate": (sum(r["parsed"]["has_error"] is True for r in invalid) / len(invalid)) if invalid else None,
            "invalid_span_hit_rate": (sum(r["span_hit"] for r in invalid) / len(invalid)) if invalid else None,
            "valid_false_error_rate": (sum(r["parsed"]["has_error"] is True and not no_error_claim(r["parsed"]) for r in valid) / len(valid)) if valid else None,
            "valid_no_error_rate": (sum(no_error_claim(r["parsed"]) for r in valid) / len(valid)) if valid else None,
        }
    return {
        "by_slice": by_slice,
        "leakage_audit": {
            "labels_in_prompt_rows": 0,
            "gold_answer_in_prompt_rows": 0,
            "manual_error_span_annotation_in_prompt_rows": 0,
            "passed": True,
            "note_zh": "Prompts contain only problem and visible candidate solution. Manual labels/gold/error spans are used only offline.",
        },
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--data-jsonl", default=str(E132_DATA))
    p.add_argument("--e136-result", default="")
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--prompt-variants", default=",".join(PROMPT_VARIANTS))
    p.add_argument("--control-variants", default=",".join(CONTROL_VARIANTS))
    p.add_argument("--max-jobs", type=int, default=0)
    p.add_argument("--max-input-tokens", type=int, default=6144)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--max-time", type=float, default=30.0)
    p.add_argument("--no-stop-at-first-answer", action="store_true")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    variants = [x.strip() for x in args.prompt_variants.split(",") if x.strip()]
    controls = [x.strip() for x in args.control_variants.split(",") if x.strip()]
    e136_result = Path(args.e136_result) if args.e136_result else e136_path(args.model_key)
    e136 = json.loads(e136_result.read_text(encoding="utf-8"))
    data_by_idx = {int(r["audit_idx"]): r for r in load_jsonl(Path(args.data_jsonl))}
    source_rows = select_source_rows(args.model_key, list(e136["rows"]), data_by_idx, controls)
    jobs = build_jobs(source_rows, variants, args.max_jobs)
    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "model_key": args.model_key,
            "source_rows": len(source_rows),
            "jobs": len(jobs),
            "source_counts": dict(Counter(r["source_kind"] for r in source_rows)),
            "prompt_variants": variants,
        }, ensure_ascii=False, indent=2))
        return

    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    local_only = args.local_files_only or is_local_model(spec)
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading {args.model_key} for E139.5 jobs={len(jobs)} rows={len(source_rows)}", flush=True)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    tok.padding_side = "left"
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    use_chat = should_use_chat(spec, tok)

    out_rows: list[dict[str, Any]] = []
    for i, job in enumerate(jobs, start=1):
        row = job["row"]
        prompt_variant = job["prompt_variant"]
        content = locate_prompt(row["problem"], row["completion"], prompt_variant)
        rendered, add_special = render_prompt(tok, content, use_chat)
        stop_strings = [] if args.no_stop_at_first_answer else stop_strings_for_variant(prompt_variant)
        gen = generate_one(model, tok, rendered, add_special, device, args.max_input_tokens, args.max_new_tokens, args.max_time, stop_strings)
        parsed = parse_output(gen["completion"], prompt_variant)
        hit = span_hit(parsed.get("first_wrong_step", ""), row.get("expected_error_span"))
        rec = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "experiment": "E1395_base_span_localization",
            "model_key": args.model_key,
            "prompt_variant": prompt_variant,
            "thinking": False,
            "audit_idx": row["audit_idx"],
            "task_id": row["task_id"],
            "family": row["family"],
            "route_id": row["route_id"],
            "variant": row["variant"],
            "source_kind": row["source_kind"],
            "selection_reason": row["selection_reason"],
            "manual_process_valid_strict": row["manual_process_valid_strict"],
            "manual_process_valid_repaired": row["manual_process_valid_repaired"],
            "manual_acpi_strict": row["manual_acpi_strict"],
            "manual_acpi_unrepaired": row["manual_acpi_unrepaired"],
            "manual_repair_present": row["manual_repair_present"],
            "manual_error_type": row.get("manual_error_type"),
            "expected_error_span": row.get("expected_error_span", ""),
            "failure_policy_names": row.get("failure_policy_names", []),
            "problem": row["problem"],
            "visible_trace": row["completion"],
            "prompt_contains_gold_label_or_error_annotation": False,
            "generation": gen,
            "parsed": parsed,
            "span_hit": bool(hit),
        }
        out_rows.append(rec)
        print(
            f"E139.5 {args.model_key} {i}/{len(jobs)} variant={prompt_variant} idx={row['audit_idx']} "
            f"has_error={parsed.get('has_error')} hit={hit}",
            flush=True,
        )

    result = {
        "experiment": "E1395_base_span_localization",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "source_e136_result": rel(e136_result),
        "source_data_jsonl": rel(Path(args.data_jsonl)),
        "args": vars(args),
        "selected_rows": [
            {
                "audit_idx": r["audit_idx"],
                "family": r["family"],
                "route_id": r["route_id"],
                "variant": r["variant"],
                "source_kind": r["source_kind"],
                "manual_process_valid_strict": r["manual_process_valid_strict"],
                "expected_error_span": r.get("expected_error_span", ""),
                "failure_policy_names": r.get("failure_policy_names", []),
            }
            for r in source_rows
        ],
        "rows": out_rows,
        "summary": summarize(out_rows),
        "scope_note_zh": "E139.5 只测试 base/no-check 与 locate-only prompt 下能否直接定位错步；不要求整体接受/拒绝 trace。",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.model_key}_e1395_base_span_localization.json"
    write_json(out, result)
    print(json.dumps({"out": rel(out), "jobs": len(jobs), "summary": result["summary"]["by_slice"].get("all")}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
