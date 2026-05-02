#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def zh_chars(text: str) -> int:
    return sum('\u4e00' <= ch <= '\u9fff' for ch in text)


def latin_letters(text: str) -> int:
    return sum(('a' <= ch.lower() <= 'z') for ch in text)


def contains_gold(text: str, gold: str) -> bool:
    compact = re.sub(r"\s+", "", text.lower())
    compact = compact.replace("\\frac", "frac")
    g = gold.lower().replace(" ", "")
    variants = {g}
    if g in {"4", "11", "40", "60", "2"}:
        variants |= {f"={g}", f"answer:{g}", f"答案是{g}", f"答案：{g}"}
    if g == "20":
        variants |= {"area=20", "面积是20", "答案是20", "答案：20"}
    if g == "3/5":
        variants |= {"0.6", "60%", "五分之三", "3/5", "frac{3}{5}"}
    if g == "2x+3":
        variants |= {"2x+3", "2*x+3", "2x + 3"}
    return any(v.replace(" ", "") in compact for v in variants)


def repetition_flag(prompt: str, completion: str) -> bool:
    c = completion.lower()
    return c.count("problem:") >= 2 or c.count("题目：") >= 2 or prompt[:40].lower() in c.lower()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", default="/home/Awei/P02_multilingual_process_lens/data/raw/trace_pool_smoke")
    p.add_argument("--out", default="/home/Awei/P02_multilingual_process_lens/data/processed/trace_pool_smoke_audit.json")
    args = p.parse_args()
    rows = []
    for path in sorted(Path(args.in_dir).glob("*trace_pool_smoke*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data["rows"]:
            text = r.get("completion", r.get("raw_completion", ""))
            raw_text = r.get("raw_completion", text)
            z = zh_chars(text)
            l = latin_letters(text)
            total = max(1, z + l)
            reason_lang = r["reason_lang"]
            if reason_lang == "zh":
                route_adherence = z / total
            else:
                route_adherence = l / total
            rows.append(
                {
                    **{k: r[k] for k in ["model_key", "task_id", "input_lang", "reason_lang", "sample_idx", "gold_answer"]},
                    "used_chat_template": bool(r.get("used_chat_template", False)),
                    "trim_flags": r.get("trim_flags", {}),
                    "completion_chars": len(text),
                    "zh_chars": z,
                    "latin_letters": l,
                    "route_adherence_ratio": route_adherence,
                    "likely_final_correct": contains_gold(text, r["gold_answer"]),
                    "repetition_flag": repetition_flag(r["prompt"], raw_text),
                }
            )
    by = {}
    for r in rows:
        key = (r["model_key"], r["reason_lang"])
        by.setdefault(key, []).append(r)
    summary_rows = []
    for (model, reason_lang), group in sorted(by.items()):
        n = len(group)
        summary_rows.append(
            {
                "model_key": model,
                "reason_lang": reason_lang,
                "n": n,
                "likely_final_correct_rate": sum(g["likely_final_correct"] for g in group) / n,
                "mean_route_adherence_ratio": sum(g["route_adherence_ratio"] for g in group) / n,
                "repetition_rate": sum(g["repetition_flag"] for g in group) / n,
                "mean_completion_chars": sum(g["completion_chars"] for g in group) / n,
            }
        )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows, "summary": summary_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}; rows={len(rows)}")
    for s in summary_rows:
        print(s)


if __name__ == "__main__":
    main()
