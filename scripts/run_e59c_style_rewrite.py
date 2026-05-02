#!/usr/bin/env python3
"""E59c style-controlled rewriting for mutual-verifier proxy.

Each source model rewrites audited controlled traces in its own surface style while
being instructed not to solve or repair the reasoning. The resulting rows are
human/heuristic-audited before entering verifier matrices.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def should_use_chat_template(spec: dict[str, Any], tokenizer) -> bool:
    cls = str(spec.get("class", "")).lower()
    fam = str(spec.get("family", "")).lower()
    if "base" in cls and "post" not in cls and "instruct" not in cls:
        return False
    return bool(getattr(tokenizer, "chat_template", None)) and (fam in {"qwen35", "gemma", "mistral", "phi", "glm"} or "instruct" in cls or "post" in cls)


def render_prompt(tokenizer, content: str, use_chat: bool) -> tuple[str, bool]:
    if not use_chat:
        return content + "\nRewritten trace:", True
    messages = [{"role": "user", "content": content}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), False


def rewrite_prompt(row: dict[str, Any]) -> str:
    return (
        "You are doing a style-transfer task, not a math-solving task. Rewrite the reasoning trace below in your own natural style.\n"
        "Rules:\n"
        "1. Preserve every mathematical claim and every local reasoning step, even if a claim is wrong.\n"
        "2. Do not correct mistakes, do not add a new solution, and do not remove the final answer.\n"
        "3. Keep the same final answer line.\n"
        "4. Output only the rewritten trace, with no commentary about the rewrite.\n\n"
        f"Problem:\n{row['problem']}\n\n"
        f"Trace to rewrite:\n{row['completion']}\n\n"
        "Rewritten trace:"
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--manual-jsonl", default=str(PROJECT / "data/processed/e42_e39_objective_focus_20260428.jsonl"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E59_style_rewrite_raw"))
    p.add_argument("--max-new-tokens", type=int, default=220)
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    rows = load_jsonl(Path(args.manual_jsonl))
    if args.limit > 0:
        rows = rows[: args.limit]
    started = datetime.now().isoformat(timespec="seconds")
    print(f"[{started}] loading source model {args.model_key} rows={len(rows)}", flush=True)
    local_only = args.local_files_only or is_local_model(spec)
    tok = load_tokenizer(spec["path"], local_files_only=local_only)
    use_chat = should_use_chat_template(spec, tok)
    model = load_causal_lm(spec["path"], dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    out_rows = []
    for row in rows:
        prompt_text, add_special = render_prompt(tok, rewrite_prompt(row), use_chat)
        enc = tok(prompt_text, return_tensors="pt", add_special_tokens=add_special).to(device)
        with torch.no_grad():
            generated = model.generate(
                **enc,
                do_sample=False,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tok.eos_token_id,
                eos_token_id=tok.eos_token_id,
                use_cache=True,
            )
        completion = tok.decode(generated[0, enc["input_ids"].shape[1] :], skip_special_tokens=True).strip()
        out_rows.append(
            {
                "source_model_key": args.model_key,
                "original_audit_idx": row["audit_idx"],
                "task_id": row["task_id"],
                "problem": row["problem"],
                "original_completion": row["completion"],
                "rewritten_completion": completion,
                "gold_answer": row["gold_answer"],
                "e39_variant": row["e39_variant"],
                "manual_process_valid": bool(row["manual_process_valid"]),
                "manual_final_correct": bool(row["manual_final_correct"]),
                "support_span": row.get("support_span", ""),
                "error_span": row.get("error_span", ""),
                "used_chat_template": use_chat,
                "add_special_tokens": add_special,
            }
        )
        print(f"rewrote {args.model_key} audit_idx={row['audit_idx']} task={row['task_id']}", flush=True)
    result = {
        "experiment": "E59c_style_controlled_rewrite_raw",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "source_model_key": args.model_key,
        "model_spec": spec,
        "used_chat_template": use_chat,
        "args": vars(args),
        "rows": out_rows,
    }
    out = Path(args.out_dir) / f"{args.model_key}_e59c_style_rewrite_raw.json"
    write_json(out, result)
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
