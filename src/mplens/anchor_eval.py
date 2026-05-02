from __future__ import annotations

import math
from typing import Any

import torch
import torch.nn.functional as F

from .modeling import candidate_first_token_id, get_transformer_layers, model_device
from .text_cases import term_prompts, verifier_prompt


def _overlap_positions(offsets, start: int, end: int) -> list[int]:
    positions: list[int] = []
    for i, (a, b) in enumerate(offsets):
        if a == b == 0:
            continue
        if max(a, start) < min(b, end):
            positions.append(i)
    return positions


def encode_with_target_span(tokenizer, text: str, target: str) -> tuple[dict[str, torch.Tensor], list[int]]:
    start = text.index(target)
    end = start + len(target)
    encoded = tokenizer(text, return_tensors="pt", return_offsets_mapping=True, add_special_tokens=True)
    offsets = encoded.pop("offset_mapping")[0].tolist()
    positions = _overlap_positions(offsets, start, end)
    if not positions:
        target_ids = tokenizer.encode(target, add_special_tokens=False)
        input_ids = encoded["input_ids"][0].tolist()
        for i in range(max(0, len(input_ids) - len(target_ids) + 1)):
            if input_ids[i : i + len(target_ids)] == target_ids:
                positions = list(range(i, i + len(target_ids)))
                break
    if not positions:
        positions = [int(encoded["attention_mask"].sum().item()) - 1]
    return encoded, positions


def tokenization_report(tokenizer, terms: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in terms:
        for lang in ("en", "zh"):
            text = row[lang]
            ids = tokenizer.encode(text, add_special_tokens=False)
            toks = tokenizer.convert_ids_to_tokens(ids)
            rows.append(
                {
                    "pair_en": row["en"],
                    "pair_zh": row["zh"],
                    "lang": lang,
                    "text": text,
                    "num_tokens": len(ids),
                    "token_ids": [int(x) for x in ids],
                    "tokens": toks,
                }
            )
    return rows


def contextual_bridge(model, tokenizer, terms: list[dict[str, str]], device: torch.device) -> dict[str, Any]:
    vectors: dict[int, dict[str, list[torch.Tensor]]] = {}
    term_rows = []
    with torch.no_grad():
        for idx, pair in enumerate(terms):
            for lang in ("en", "zh"):
                term = pair[lang]
                text = term_prompts(term, lang)
                encoded, positions = encode_with_target_span(tokenizer, text, term)
                encoded = {k: v.to(device) for k, v in encoded.items()}
                out = model(**encoded, output_hidden_states=True, use_cache=False)
                for layer_idx, hs in enumerate(out.hidden_states):
                    vec = hs[0, positions, :].mean(dim=0).detach().float().cpu()
                    vectors.setdefault(layer_idx, {}).setdefault(lang, []).append(F.normalize(vec, dim=0))
                term_rows.append(
                    {
                        "idx": idx,
                        "lang": lang,
                        "term": term,
                        "prompt": text,
                        "target_positions": positions,
                    }
                )
    layer_metrics = []
    n = len(terms)
    for layer_idx in sorted(vectors):
        en = torch.stack(vectors[layer_idx]["en"])
        zh = torch.stack(vectors[layer_idx]["zh"])
        sim = en @ zh.T
        ranks = []
        correct = []
        margins = []
        diag = torch.diag(sim)
        for i in range(n):
            order = torch.argsort(sim[i], descending=True).tolist()
            rank = order.index(i) + 1
            ranks.append(rank)
            correct.append(rank == 1)
            off_diag = torch.cat([sim[i, :i], sim[i, i + 1 :]]) if n > 1 else torch.tensor([], device=sim.device)
            hardest_mismatch = off_diag.max() if off_diag.numel() else torch.tensor(0.0, device=sim.device)
            margins.append(float((sim[i, i] - hardest_mismatch).item()))
        layer_metrics.append(
            {
                "layer": layer_idx,
                "top1": float(sum(correct) / n),
                "mean_rank": float(sum(ranks) / n),
                "mean_pair_cos": float(diag.mean().item()),
                "mean_mismatch_cos": float((sim.sum() - diag.sum()).item() / max(1, n * n - n)),
                "mean_hard_margin": float(sum(margins) / len(margins)),
                "min_hard_margin": float(min(margins)),
            }
        )
    best = max(layer_metrics, key=lambda x: (x["top1"], x["mean_hard_margin"], -x["mean_rank"], x["mean_pair_cos"]))
    early = None
    for m in layer_metrics:
        if m["top1"] >= 0.9 and m["mean_hard_margin"] > 0.02:
            early = m
            break
    return {"term_rows": term_rows, "layers": layer_metrics, "best_layer": best, "early_bridge_layer": early}


def process_margin(model, tokenizer, prompt: str, yes_id: int, no_id: int, device: torch.device) -> float:
    encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
    encoded = {k: v.to(device) for k, v in encoded.items()}
    with torch.no_grad():
        logits = model(**encoded, use_cache=False).logits[0, -1, :].float()
    log_probs = F.log_softmax(logits, dim=-1)
    return float((log_probs[yes_id] - log_probs[no_id]).item())


def process_verifier_margins(model, tokenizer, cases: list[dict[str, Any]], device: torch.device) -> dict[str, Any]:
    yes_id = candidate_first_token_id(tokenizer, [" Yes", "Yes", " yes", "yes"])
    no_id = candidate_first_token_id(tokenizer, [" No", "No", " no", "no"])
    zh_yes_id = candidate_first_token_id(tokenizer, [" 是", "是"])
    zh_no_id = candidate_first_token_id(tokenizer, [" 否", "否", " 不", "不"])
    rows = []
    for case in cases:
        for lang, yid, nid in (("en", yes_id, no_id), ("zh", zh_yes_id, zh_no_id)):
            prompt = verifier_prompt(case["problem"], case["trace"], lang=lang)
            margin = process_margin(model, tokenizer, prompt, yid, nid, device)
            pred_valid = margin > 0
            rows.append(
                {
                    "case_id": case["id"],
                    "prompt_lang": lang,
                    "process_valid_gold": bool(case["process_valid"]),
                    "final_correct_gold": bool(case.get("final_correct", False)),
                    "yes_token_id": int(yid),
                    "no_token_id": int(nid),
                    "yes_minus_no_logprob": margin,
                    "pred_process_valid": pred_valid,
                    "correct": pred_valid == bool(case["process_valid"]),
                    "risk_type": "invalid_final_correct" if (not case["process_valid"] and case.get("final_correct")) else "other",
                }
            )
    total = len(rows)
    invalid_fc = [r for r in rows if r["risk_type"] == "invalid_final_correct"]
    return {
        "yes_id": int(yes_id),
        "no_id": int(no_id),
        "zh_yes_id": int(zh_yes_id),
        "zh_no_id": int(zh_no_id),
        "rows": rows,
        "accuracy": float(sum(r["correct"] for r in rows) / total) if total else None,
        "invalid_final_correct_false_accept_rate": float(
            sum(r["pred_process_valid"] for r in invalid_fc) / len(invalid_fc)
        )
        if invalid_fc
        else None,
    }


def _extract_layer_output(output):
    if isinstance(output, tuple):
        return output[0]
    return output


def _replace_layer_output(output, patched_hidden):
    if isinstance(output, tuple):
        return (patched_hidden,) + tuple(output[1:])
    return patched_hidden


def residual_patch_effects(
    model,
    tokenizer,
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
    layers_to_patch: list[int],
    device: torch.device,
) -> dict[str, Any]:
    layers = get_transformer_layers(model)
    yes_id = candidate_first_token_id(tokenizer, [" Yes", "Yes", " yes", "yes"])
    no_id = candidate_first_token_id(tokenizer, [" No", "No", " no", "no"])

    def layer_vec(prompt: str, layer_idx: int) -> torch.Tensor:
        encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        encoded = {k: v.to(device) for k, v in encoded.items()}
        with torch.no_grad():
            out = model(**encoded, output_hidden_states=True, use_cache=False)
        # hidden_states[0] is embedding; layer_idx output is hidden_states[layer_idx + 1]
        return out.hidden_states[layer_idx + 1][0, -1, :].detach()

    def patched_margin(prompt: str, layer_idx: int, clean_vec: torch.Tensor) -> float:
        def hook(_module, _inputs, output):
            hidden = _extract_layer_output(output).clone()
            hidden[:, -1, :] = clean_vec.to(hidden.device, dtype=hidden.dtype)
            return _replace_layer_output(output, hidden)

        handle = layers[layer_idx].register_forward_hook(hook)
        try:
            return process_margin(model, tokenizer, prompt, yes_id, no_id, device)
        finally:
            handle.remove()

    rows = []
    for valid, bad in pairs:
        valid_prompt = verifier_prompt(valid["problem"], valid["trace"], lang="en")
        bad_prompt = verifier_prompt(bad["problem"], bad["trace"], lang="en")
        base_valid = process_margin(model, tokenizer, valid_prompt, yes_id, no_id, device)
        base_bad = process_margin(model, tokenizer, bad_prompt, yes_id, no_id, device)
        for layer_idx in layers_to_patch:
            if layer_idx < 0 or layer_idx >= len(layers):
                continue
            valid_vec = layer_vec(valid_prompt, layer_idx)
            bad_vec = layer_vec(bad_prompt, layer_idx)
            v_to_b = patched_margin(bad_prompt, layer_idx, valid_vec)
            b_to_v = patched_margin(valid_prompt, layer_idx, bad_vec)
            rows.append(
                {
                    "valid_case_id": valid["id"],
                    "bad_case_id": bad["id"],
                    "layer": int(layer_idx),
                    "base_valid_margin": base_valid,
                    "base_bad_margin": base_bad,
                    "valid_to_bad_margin": v_to_b,
                    "valid_to_bad_effect": v_to_b - base_bad,
                    "bad_to_valid_margin": b_to_v,
                    "bad_to_valid_effect": b_to_v - base_valid,
                }
            )
    if rows:
        by_layer = []
        for layer_idx in sorted({r["layer"] for r in rows}):
            sub = [r for r in rows if r["layer"] == layer_idx]
            by_layer.append(
                {
                    "layer": layer_idx,
                    "mean_valid_to_bad_effect": float(sum(r["valid_to_bad_effect"] for r in sub) / len(sub)),
                    "mean_bad_to_valid_effect": float(sum(r["bad_to_valid_effect"] for r in sub) / len(sub)),
                    "n": len(sub),
                }
            )
    else:
        by_layer = []
    return {"rows": rows, "by_layer": by_layer}


def auto_patch_layers(num_layers: int) -> list[int]:
    raw = [num_layers // 4, num_layers // 2, (3 * num_layers) // 4, num_layers - 1]
    return sorted({int(x) for x in raw if 0 <= x < num_layers})
