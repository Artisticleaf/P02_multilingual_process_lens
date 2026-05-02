#!/usr/bin/env python3
"""E62 external P0 candidate backend/license smoke test.

This is a prerequisite gate. A candidate is promoted to expanded P0 only if
license, tokenizer/chat-template, HF model loading, deterministic option
log-prob scoring, hidden states, and layer discovery pass.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from transformers import AutoConfig

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from mplens.io_utils import read_yaml, write_json  # noqa: E402
from mplens.modeling import get_transformer_layers, is_local_model, load_causal_lm, load_tokenizer, model_device, visible_device_label  # noqa: E402


def safe_call(name: str, fn) -> dict[str, Any]:
    started = time.time()
    try:
        value = fn()
        return {"name": name, "ok": True, "seconds": time.time() - started, "value": value}
    except Exception as exc:  # noqa: BLE001 - smoke tests should capture any backend failure.
        return {
            "name": name,
            "ok": False,
            "seconds": time.time() - started,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback_tail": traceback.format_exc(limit=5),
        }


def read_text_if_exists(path: Path, limit: int = 24000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:limit]


def license_probe(model_path: Path) -> dict[str, Any]:
    readme = read_text_if_exists(model_path / "README.md")
    license_text = read_text_if_exists(model_path / "LICENSE")
    lower = (readme + "\n" + license_text).lower()
    license_files = [p.name for p in model_path.iterdir() if p.is_file() and "license" in p.name.lower()]
    if "license: mit" in lower:
        license_class = "mit"
        usage_gate = "permissive_for_research"
    elif "exaone ai model license" in lower or "license_name: exaone" in lower:
        license_class = "exaone_1_2_nc"
        usage_gate = "research_education_only_noncommercial"
    elif "nvidia-open-model-license" in lower or "nvidia open model license" in lower:
        license_class = "nvidia_open_model_license"
        usage_gate = "custom_open_model_license_review_needed"
    elif "apache-2.0" in lower or "apache 2.0" in lower:
        license_class = "apache_2_0"
        usage_gate = "permissive_for_research"
    else:
        license_class = "unknown"
        usage_gate = "manual_review_needed"
    snippets = []
    for token in ["license:", "license_name", "license_link", "license grant", "commercial use", "research and educational", "non-commercial", "nvidia open model license"]:
        idx = lower.find(token)
        if idx >= 0:
            snippets.append((readme + "\n" + license_text)[max(0, idx - 120) : idx + 500].replace("\n", " "))
    return {
        "license_files": license_files,
        "license_class": license_class,
        "usage_gate": usage_gate,
        "readme_exists": (model_path / "README.md").exists(),
        "license_exists": (model_path / "LICENSE").exists(),
        "snippets": snippets[:5],
    }


def static_probe(model_path: Path) -> dict[str, Any]:
    cfg_path = model_path / "config.json"
    tok_cfg_path = model_path / "tokenizer_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    tok_cfg = json.loads(tok_cfg_path.read_text(encoding="utf-8")) if tok_cfg_path.exists() else {}
    weight_files = sorted(model_path.glob("*.safetensors"))
    size_gib = sum(p.stat().st_size for p in weight_files) / (1024**3)
    readme = read_text_if_exists(model_path / "README.md")
    return {
        "path_exists": model_path.exists(),
        "config_exists": cfg_path.exists(),
        "tokenizer_config_exists": tok_cfg_path.exists(),
        "chat_template_file_exists": (model_path / "chat_template.jinja").exists(),
        "safetensor_shards": len(weight_files),
        "safetensor_size_gib": size_gib,
        "model_type": cfg.get("model_type"),
        "architectures": cfg.get("architectures"),
        "auto_map": cfg.get("auto_map"),
        "transformers_version_in_config": cfg.get("transformers_version"),
        "tokenizer_chat_template_in_config": bool(tok_cfg.get("chat_template")),
        "readme_mentions_vllm": "vllm" in readme.lower(),
        "readme_mentions_transformers_fork": "transformers" in readme.lower() and "fork" in readme.lower(),
    }


def render_chat(tokenizer, text: str) -> tuple[str, bool]:
    if not getattr(tokenizer, "chat_template", None):
        return text, True
    messages = [{"role": "user", "content": text}]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False), False
    except TypeError:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True), False


def option_logprob(model, tokenizer, prompt: str, option: str, device: torch.device, max_model_len: int, add_special_tokens: bool) -> float:
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)
    option_ids = tokenizer.encode(option, add_special_tokens=False)
    if not option_ids:
        return float("-inf")
    keep_prompt = max(1, max_model_len - len(option_ids))
    prompt_ids = prompt_ids[-keep_prompt:]
    input_ids = torch.tensor([prompt_ids + option_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).logits[0].float()
    total = 0.0
    start = len(prompt_ids)
    for j, tok_id in enumerate(option_ids):
        total += float(F.log_softmax(logits[start + j - 1], dim=-1)[tok_id].item())
    return total


def hf_dynamic_probe(spec: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    model_path = spec["path"]
    local_only = args.local_files_only or is_local_model(spec)
    tokenizer = load_tokenizer(model_path, local_files_only=local_only)
    rendered, add_special = render_chat(tokenizer, "Answer only Yes or No: is 2+2=4?")
    model = load_causal_lm(model_path, dtype=args.dtype, device=args.device, local_files_only=local_only)
    device = model_device(model)
    encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=add_special).to(device)
    with torch.no_grad():
        out = model(**encoded, use_cache=False, output_hidden_states=True)
    logits_shape = list(out.logits.shape)
    hidden_count = len(out.hidden_states) if getattr(out, "hidden_states", None) is not None else 0
    hidden_last_shape = list(out.hidden_states[-1].shape) if hidden_count else None
    yes_score = max(option_logprob(model, tokenizer, rendered, opt, device, args.max_model_len, add_special) for opt in [" Yes", "Yes", " yes", "yes"])
    no_score = max(option_logprob(model, tokenizer, rendered, opt, device, args.max_model_len, add_special) for opt in [" No", "No", " no", "no"])
    try:
        layers = get_transformer_layers(model)
        layer_count = len(layers)
        layer_type = type(layers[0]).__name__ if layer_count else None
    except Exception as exc:  # noqa: BLE001
        layer_count = None
        layer_type = None
        layer_error = f"{type(exc).__name__}: {exc}"
    else:
        layer_error = None
    # Generation is a separate light check. Some custom models support logits but
    # have generate-cache issues; we record it without making hidden-state smoke depend on it.
    gen_text = None
    gen_error = None
    try:
        with torch.no_grad():
            gen_ids = model.generate(**encoded, max_new_tokens=args.max_new_tokens, do_sample=False, use_cache=True)
        gen_text = tokenizer.decode(gen_ids[0, encoded["input_ids"].shape[1] :], skip_special_tokens=True)
    except Exception as exc:  # noqa: BLE001
        gen_error = f"{type(exc).__name__}: {exc}"
    return {
        "tokenizer_class": type(tokenizer).__name__,
        "model_class": type(model).__name__,
        "device": str(device),
        "used_chat_template": bool(getattr(tokenizer, "chat_template", None)),
        "rendered_prompt_prefix": rendered[:500],
        "logits_shape": logits_shape,
        "hidden_states_count": hidden_count,
        "hidden_last_shape": hidden_last_shape,
        "yes_score": yes_score,
        "no_score": no_score,
        "yes_minus_no": yes_score - no_score,
        "option_logprob_ok": isinstance(yes_score, float) and isinstance(no_score, float),
        "layer_count": layer_count,
        "layer_type": layer_type,
        "layer_error": layer_error,
        "generate_text": gen_text,
        "generate_error": gen_error,
    }


def vllm_static_probe(model_path: Path) -> dict[str, Any]:
    try:
        import vllm  # noqa: PLC0415
        version = getattr(vllm, "__version__", "unknown")
    except Exception as exc:  # noqa: BLE001
        return {"vllm_import_ok": False, "error": f"{type(exc).__name__}: {exc}"}
    readme = read_text_if_exists(model_path / "README.md")
    lines = [line.strip() for line in readme.splitlines() if "vllm" in line.lower()][:20]
    return {"vllm_import_ok": True, "vllm_version": version, "readme_vllm_lines": lines}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-key", required=True)
    p.add_argument("--registry", default=str(PROJECT / "configs/model_registry.yaml"))
    p.add_argument("--out-dir", default=str(PROJECT / "results/E62_external_p0_smoke"))
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--device", default="auto")
    p.add_argument("--max-model-len", type=int, default=2048)
    p.add_argument("--max-new-tokens", type=int, default=8)
    p.add_argument("--local-files-only", action="store_true")
    p.add_argument("--skip-hf-dynamic", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    registry = read_yaml(args.registry)["models"]
    spec = registry[args.model_key]
    model_path = Path(spec["path"])
    started = datetime.now().isoformat(timespec="seconds")
    checks = []
    checks.append(safe_call("license_probe", lambda: license_probe(model_path)))
    checks.append(safe_call("static_probe", lambda: static_probe(model_path)))
    checks.append(safe_call("auto_config", lambda: {"class": type(AutoConfig.from_pretrained(str(model_path), trust_remote_code=True, local_files_only=True)).__name__}))
    checks.append(safe_call("tokenizer_chat", lambda: {"class": type(load_tokenizer(str(model_path), local_files_only=True)).__name__, "has_chat_template": bool(getattr(load_tokenizer(str(model_path), local_files_only=True), "chat_template", None))}))
    checks.append(safe_call("vllm_static", lambda: vllm_static_probe(model_path)))
    if not args.skip_hf_dynamic:
        checks.append(safe_call("hf_dynamic", lambda: hf_dynamic_probe(spec, args)))

    by_name = {c["name"]: c for c in checks}
    license_value = by_name.get("license_probe", {}).get("value", {})
    static_value = by_name.get("static_probe", {}).get("value", {})
    hf_value = by_name.get("hf_dynamic", {}).get("value", {})
    license_ok_for_research = license_value.get("usage_gate") in {
        "permissive_for_research",
        "research_education_only_noncommercial",
        "custom_open_model_license_review_needed",
    }
    dynamic_ok = bool(by_name.get("hf_dynamic", {}).get("ok")) and bool(hf_value.get("option_logprob_ok")) and bool(hf_value.get("hidden_states_count")) and hf_value.get("layer_count") is not None
    tokenizer_ok = bool(by_name.get("tokenizer_chat", {}).get("ok"))
    config_ok = bool(by_name.get("auto_config", {}).get("ok"))
    promote_to_expanded_p0 = bool(license_ok_for_research and tokenizer_ok and config_ok and dynamic_ok)
    result = {
        "experiment": "E62_external_p0_candidate_smoke",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "host": socket.gethostname(),
        "cuda_visible_devices": visible_device_label(),
        "model_key": args.model_key,
        "model_spec": spec,
        "args": vars(args),
        "checks": checks,
        "summary": {
            "license_ok_for_noncommercial_research": license_ok_for_research,
            "license_class": license_value.get("license_class"),
            "usage_gate": license_value.get("usage_gate"),
            "model_type": static_value.get("model_type"),
            "architectures": static_value.get("architectures"),
            "tokenizer_ok": tokenizer_ok,
            "auto_config_ok": config_ok,
            "hf_dynamic_ok": dynamic_ok,
            "vllm_static_ok": bool(by_name.get("vllm_static", {}).get("ok") and by_name.get("vllm_static", {}).get("value", {}).get("vllm_import_ok")),
            "promote_to_expanded_p0": promote_to_expanded_p0,
            "promotion_rule": "license permits noncommercial research, tokenizer/config load, HF dynamic option-logprob, hidden states, and layer discovery all pass",
        },
    }
    out = Path(args.out_dir) / f"{args.model_key}_e62_external_p0_smoke.json"
    write_json(out, result)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2), flush=True)
    print(f"wrote {out}", flush=True)
    # Non-zero exit for hard dynamic failure so launch logs reveal blockers, but
    # still writes the JSON above.
    if not promote_to_expanded_p0:
        sys.exit(2)


if __name__ == "__main__":
    main()
