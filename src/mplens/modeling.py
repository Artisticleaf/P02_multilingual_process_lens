from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoModelForImageTextToText, AutoTokenizer


def resolve_model_path(model_spec: dict[str, Any]) -> str:
    return str(model_spec["path"])


def is_local_model(model_spec: dict[str, Any]) -> bool:
    return str(model_spec.get("status", "")).startswith("local") or Path(str(model_spec.get("path", ""))).exists()


def load_tokenizer(model_path: str, *, local_files_only: bool = False):
    extra_kwargs: dict[str, Any] = {}
    if "mistral" in str(model_path).lower() or "ministral" in str(model_path).lower():
        extra_kwargs["fix_mistral_regex"] = True
    tok = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=local_files_only,
        use_fast=True,
        **extra_kwargs,
    )
    if tok.pad_token is None and tok.eos_token is not None:
        tok.pad_token = tok.eos_token
    return tok


def load_causal_lm(
    model_path: str,
    *,
    dtype: str = "bfloat16",
    device: str = "cuda",
    local_files_only: bool = False,
):
    torch_dtype = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }.get(dtype, torch.bfloat16)

    kwargs = dict(
        trust_remote_code=True,
        torch_dtype=torch_dtype,
        local_files_only=local_files_only,
        low_cpu_mem_usage=True,
    )
    if device == "auto":
        kwargs["device_map"] = "auto"
        max_memory = _parse_max_memory_env()
        if max_memory:
            kwargs["max_memory"] = max_memory
    try:
        model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    except ValueError as exc:
        # Some current small P0 releases are multimodal ConditionalGeneration
        # checkpoints while still exposing text logits/hidden states.
        if "AutoModelForCausalLM" not in str(exc) and "Unrecognized configuration class" not in str(exc):
            raise
        model = AutoModelForImageTextToText.from_pretrained(model_path, **kwargs)
        _patch_known_text_only_loader_issues(model)
    model.eval()
    if device != "auto":
        model.to(torch.device(device))
    return model


def _parse_max_memory_env() -> dict[int | str, str] | None:
    """Parse optional per-device memory hints for multi-GPU loading.

    Example: `MPLENS_MAX_MEMORY=0:30GiB,1:30GiB,2:30GiB,3:30GiB,cpu:120GiB`.
    """
    text = os.environ.get("MPLENS_MAX_MEMORY", "").strip()
    if not text:
        return None
    out: dict[int | str, str] = {}
    for item in text.split(","):
        if not item.strip():
            continue
        key, value = item.split(":", 1)
        key = key.strip()
        out[int(key) if key.isdigit() else key] = value.strip()
    return out or None


def _patch_known_text_only_loader_issues(model) -> None:
    """Patch known HF loader gaps for text-only probing of multimodal models."""
    cfg = getattr(model, "config", None)
    text_cfg = getattr(cfg, "text_config", None)
    model_type = getattr(cfg, "model_type", None)
    if model_type == "glm4v" and text_cfg is not None:
        rope = getattr(text_cfg, "rope_scaling", None) or getattr(text_cfg, "rope_parameters", None)
        if isinstance(rope, dict):
            rope = dict(rope)
            # transformers 4.57.1 expects the multimodal split to sum to the
            # full rotary dimension. The released config stores half sections.
            if rope.get("mrope_section") == [8, 12, 12]:
                rope["mrope_section"] = [16, 24, 24]
            for module in model.modules():
                if hasattr(module, "rope_scaling"):
                    module.rope_scaling = rope


def get_transformer_layers(model):
    candidates = [
        ("model", "layers"),
        ("model", "language_model", "layers"),
        ("model", "language_model", "model", "layers"),
        ("transformer", "h"),
        ("gpt_neox", "layers"),
        ("language_model", "model", "layers"),
    ]
    for path in candidates:
        obj = model
        ok = True
        for attr in path:
            if not hasattr(obj, attr):
                ok = False
                break
            obj = getattr(obj, attr)
        if ok:
            return obj
    raise AttributeError("Cannot locate transformer layers for activation patching")


def model_device(model) -> torch.device:
    return next(model.parameters()).device


def candidate_first_token_id(tokenizer, text_options: list[str]) -> int:
    for text in text_options:
        ids = tokenizer.encode(text, add_special_tokens=False)
        if ids:
            return int(ids[0])
    raise ValueError(f"No token id found for candidates: {text_options}")


def visible_device_label() -> str:
    return os.environ.get("CUDA_VISIBLE_DEVICES", "all")
