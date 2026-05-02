#!/usr/bin/env python3
"""Build a human-readable audit sheet for generated trace pools.

The labels here are triage labels, not ground truth. They are designed to
separate "final answer is present" from "process is probably clean" and to
surface answer-correct/process-invalid candidates for manual reading.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TASK_SPECS: dict[str, dict[str, Any]] = {
    "lin_001": {
        "answer_variants": ["4", "x=4", "x = 4"],
        "required_any": [r"11\s*[-−]\s*3", r"2x\s*=\s*8", r"divide.*by\s*2|除以\s*2"],
        "invalid_any": [r"2x\s*=\s*9", r"11\s*\+\s*3", r"x\s*=\s*7"],
    },
    "area_001": {
        "answer_variants": ["20", "20 square", "20平方", "20 平方"],
        "required_any": [r"1/2|one[- ]half|half|二分之一|一半|0\.5", r"8\s*[×x*]\s*5|5\s*[×x*]\s*8|base.*height|底.*高"],
        "invalid_any": [r"area\s*=\s*8\s*[×x*]\s*5\s*=\s*40|面积\s*=\s*8\s*[×x*]\s*5\s*=\s*40"],
    },
    "prob_001": {
        "answer_variants": ["3/5", "0.6", "60%", "frac{3}{5}", "五分之三"],
        "required_any": [r"3\s*\+\s*2\s*=\s*5|total.*5|总.*5|一共.*5", r"3/5|0\.6|60%|五分之三"],
        "invalid_any": [r"3/2|2/3|red.*blue.*3/2|红.*蓝.*3/2"],
    },
    "avg_001": {
        "answer_variants": ["11", "x=11", "x = 11"],
        "required_any": [r"3\s*[×x*]\s*9\s*=\s*27|9\s*[×x*]\s*3\s*=\s*27|总和.*27|sum.*27", r"27\s*[-−]\s*16"],
        "invalid_any": [r"9\s*\+\s*3\s*=\s*12", r"sum.*12|总和.*12"],
    },
    "percent_001": {
        "answer_variants": ["60", "$60", "60美元"],
        "required_any": [r"25%.*80.*20|0\.25\s*[×x*]\s*80\s*=\s*20|折扣.*20", r"80\s*[-−]\s*20\s*=\s*60|75%.*80.*60|0\.75\s*[×x*]\s*80\s*=\s*60"],
        "invalid_any": [r"discount means multiply by 0\.25 to get 20|打折.*乘以\s*0\.25.*20", r"sale price (?:is|=)\s*20|售价(?:是|=)\s*20"],
    },
    "ratio_001": {
        "answer_variants": ["40", "40 girls", "女生40", "40名女生"],
        "required_any": [r"24\s*/\s*3\s*=\s*8|24\s*÷\s*3\s*=\s*8|scale.*8|比例因子.*8|每份.*8", r"5\s*[×x*]\s*8\s*=\s*40|8\s*[×x*]\s*5\s*=\s*40"],
        "invalid_any": [r"add\s+3\s+and\s+5\s+to\s+get\s+8,\s*then\s+multiply\s+5|把.*3.*5.*相加.*8.*然后.*5"],
    },
    "rem_001": {
        "answer_variants": ["2", "remainder 2", "余数是2", "余数 2"],
        "required_any": [r"9\s*[×x*]\s*15\s*=\s*135|15\s*[×x*]\s*9\s*=\s*135|137\s*[-−]\s*135\s*=\s*2", r"remainder.*2|余数.*2"],
        "invalid_any": [r"137\s*/\s*9\s*=\s*15\.2", r"round.*15\.2|四舍五入"],
    },
    "deriv_001": {
        "answer_variants": ["2x+3", "2*x+3", "2x + 3"],
        "required_any": [r"derivative of x\^2 is 2x|d/dx.*x\^2.*2x|x\^2.*导数.*2x", r"derivative of 3x is 3|3x.*导数.*3"],
        "invalid_any": [r"derivative of x\^2 is x|x\^2.*导数.*是\s*x", r"derivative of 3x is 2|3x.*导数.*是\s*2"],
    },
    "disc_en_25_off": {
        "answer_variants": ["60", "$60", "60美元"],
        "required_any": [r"25%.*80.*20|0\.25\s*[×x*]\s*80\s*=\s*20|折扣.*20", r"80\s*[-−]\s*20\s*=\s*60|75%.*80.*60|0\.75\s*[×x*]\s*80\s*=\s*60"],
        "invalid_any": [r"打八折.*75%|八折.*75%|25%\s*off.*pay\s*25%|discounted by 25%.*0\.25.*sale price|售价.*20"],
    },
    "disc_zh_75_price": {
        "answer_variants": ["60", "$60", "60美元"],
        "required_any": [r"七五折.*75%|75%.*原价|0\.75\s*[×x*]\s*80|80\s*[×x*]\s*0\.75", r"60"],
        "invalid_any": [r"七五折.*75%\s*off|75%\s*off|pay\s*25%|0\.25\s*[×x*]\s*80|售价.*20"],
    },
    "disc_en_75_off": {
        "answer_variants": ["20", "$20", "20美元"],
        "required_any": [r"75%.*80.*60|0\.75\s*[×x*]\s*80\s*=\s*60|折扣.*60", r"80\s*[-−]\s*60\s*=\s*20|25%.*80.*20|0\.25\s*[×x*]\s*80\s*=\s*20"],
        "invalid_any": [r"75%\s*off.*pay\s*75%|discounted by 75%.*0\.75.*sale price|打七五折|售价.*60"],
    },
    "ratio_boys_total": {
        "answer_variants": ["40", "40 girls", "女生40", "40名女生"],
        "required_any": [r"24\s*/\s*\(?3/8\)?|24\s*÷\s*\(?3/8\)?|total.*64|全班.*64|总人数.*64", r"64\s*[-−]\s*24\s*=\s*40"],
        "invalid_any": [r"3:5|boys\s*:\s*girls|24\s*/\s*3\s*=\s*8.*5\s*[×x*]\s*8|女生.*64"],
    },
    "deriv_sum": {
        "answer_variants": ["2x+3", "2*x+3", "2x + 3"],
        "required_any": [r"x\^2.*(?:derivative|导数).*2x|2x", r"3x.*(?:derivative|导数).*3|\(3x\)'\s*=\s*3"],
        "invalid_any": [r"3\s*(?:is|是).*constant.*(?:derivative|导数).*0|3\s*是常数.*导数.*0|3x.*constant term|3x.*常数项.*导数.*0"],
    },
    "percent_then_discount": {
        "answer_variants": ["80", "$80", "80美元"],
        "required_any": [r"80\s*[×x*]\s*1\.25|increase.*25%.*100|上涨25%.*100", r"100\s*[×x*]\s*0\.8|打八折.*0\.8|80%.*100.*80"],
        "invalid_any": [r"80%\s*discount|discount(?:ed)? by 80%|20%.*of.*100|100\s*[×x*]\s*0\.2|最终.*20"],
    },
}


def zh_chars(text: str) -> int:
    return sum("\u4e00" <= ch <= "\u9fff" for ch in text)


def latin_letters(text: str) -> int:
    return sum("a" <= ch.lower() <= "z" for ch in text)


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("\\frac", "frac")
    text = text.replace("\\boxed", "")
    text = re.sub(r"[\s`$。．.,，；;：:!！?？]", "", text)
    text = re.sub(r"[{}()\\[\\]]", "", text)
    text = text.replace("答案是", "").replace("答案", "")
    text = text.replace("finalanswer", "")
    return text


def extract_final_answer(text: str) -> tuple[str, bool]:
    patterns = [
        r"final\s*answer\s*[:：]\s*([^\n\r]+)",
        r"最终答案\s*[:：]\s*([^\n\r]+)",
        r"答案\s*[:：]\s*([^\n\r]+)",
    ]
    matches: list[str] = []
    for pat in patterns:
        matches.extend(re.findall(pat, text, flags=re.IGNORECASE))
    if matches:
        usable = []
        for candidate in matches:
            low = candidate.lower()
            if "<answer" in low or "<答案" in low or "答案>`" in candidate or "answer>`" in low:
                continue
            usable.append(candidate)
        if usable:
            ans = usable[-1].strip()
            ans = re.split(r"(?i)\b(?:problem|question|reasoning)\b|题目|推理", ans)[0].strip()
            return ans, True
    boxed = re.findall(r"\\boxed\{([^{}]+)\}", text)
    if boxed:
        return boxed[-1].strip(), False
    answer_is = re.findall(r"(?:answer|答案|therefore|因此|所以)[^\\n\\r]{0,30}(?:is|是|为|=)\s*([^\\n\\r。；;]+)", text, flags=re.IGNORECASE)
    if answer_is:
        ans = answer_is[-1].strip()
        ans = re.split(r"(?i)\b(?:problem|question|reasoning)\b|题目|推理", ans)[0].strip()
        return ans, False
    # Fallback is intentionally weak and is marked as marker_missing.
    tail = text.strip().splitlines()[-1] if text.strip() else ""
    return tail[-120:].strip(), False


def answer_matches(answer: str, variants: list[str]) -> bool:
    norm = normalize(answer)
    return any(normalize(v) in norm or norm in normalize(v) for v in variants if normalize(v))


def loose_answer_matches(text: str, extracted_answer: str, variants: list[str]) -> bool:
    if answer_matches(extracted_answer, variants):
        return True
    tail = text[-600:]
    return answer_matches(tail, variants)


def cue_hits(text: str, patterns: list[str]) -> list[str]:
    hits = []
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE | re.DOTALL):
            hits.append(pat)
    return hits


def route_adherence(text: str, reason_lang: str) -> float:
    z = zh_chars(text)
    l = latin_letters(text)
    total = max(1, z + l)
    return (z / total) if reason_lang == "zh" else (l / total)


def audit_row(row: dict[str, Any], source_file: str) -> dict[str, Any]:
    text = row.get("completion", row.get("raw_completion", ""))
    spec = TASK_SPECS.get(row["task_id"], {})
    final_answer, final_marker_present = extract_final_answer(text)
    variants = spec.get("answer_variants", [row.get("gold_answer", "")])
    final_correct_strict = final_marker_present and answer_matches(final_answer, variants)
    final_correct_loose = loose_answer_matches(text, final_answer, variants)
    invalid_hits = cue_hits(text, spec.get("invalid_any", []))
    required_hits = cue_hits(text, spec.get("required_any", []))
    required_total = len(spec.get("required_any", []))
    required_ok = len(required_hits) >= required_total if required_total else False
    adherence = route_adherence(text, row["reason_lang"])
    mixed_language_flag = adherence < (0.68 if row["reason_lang"] == "zh" else 0.80)

    if invalid_hits and final_correct_loose:
        process_triage = "red_invalid_cue_final_correct"
    elif final_correct_loose and required_ok:
        process_triage = "green_cues_final_correct"
    elif final_correct_loose:
        process_triage = "review_final_correct_missing_cues"
    elif final_marker_present:
        process_triage = "final_wrong_or_unparsed"
    else:
        process_triage = "review_no_final_marker"

    return {
        "source_file": source_file,
        "model_key": row["model_key"],
        "task_id": row["task_id"],
        "input_lang": row["input_lang"],
        "reason_lang": row["reason_lang"],
        "sample_idx": row["sample_idx"],
        "gold_answer": row["gold_answer"],
        "final_answer_extracted": final_answer,
        "final_marker_present": final_marker_present,
        "final_correct_strict": final_correct_strict,
        "final_correct_loose": final_correct_loose,
        "process_triage": process_triage,
        "required_cue_hits": len(required_hits),
        "required_cue_total": required_total,
        "invalid_cue_hits": len(invalid_hits),
        "required_patterns_hit": required_hits,
        "invalid_patterns_hit": invalid_hits,
        "route_adherence_ratio": adherence,
        "mixed_language_flag": mixed_language_flag,
        "completion_chars": len(text),
        "completion": text,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--in-dirs", nargs="+", required=True)
    p.add_argument("--out-jsonl", default="/home/Awei/P02_multilingual_process_lens/data/processed/trace_process_audit_sheet.jsonl")
    p.add_argument("--out-tsv", default="/home/Awei/P02_multilingual_process_lens/data/processed/trace_process_audit_sheet.tsv")
    p.add_argument("--out-summary", default="/home/Awei/P02_multilingual_process_lens/reports/E02_trace_process_audit_summary.md")
    args = p.parse_args()

    audited = []
    for in_dir in args.in_dirs:
        for path in sorted(Path(in_dir).glob("*trace_pool_smoke*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for row in data["rows"]:
                audited.append(audit_row(row, str(path)))

    out_jsonl = Path(args.out_jsonl)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for row in audited:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    out_tsv = Path(args.out_tsv)
    fields = [
        "model_key",
        "task_id",
        "input_lang",
        "reason_lang",
        "sample_idx",
        "gold_answer",
        "final_answer_extracted",
        "final_marker_present",
        "final_correct_strict",
        "final_correct_loose",
        "process_triage",
        "required_cue_hits",
        "required_cue_total",
        "invalid_cue_hits",
        "route_adherence_ratio",
        "mixed_language_flag",
        "completion_chars",
        "completion",
        "source_file",
    ]
    with out_tsv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(audited)

    by = defaultdict(list)
    for row in audited:
        by[(row["model_key"], row["reason_lang"])].append(row)

    lines = [
        "# E02 Trace Process Audit Summary",
        "",
        "These are triage labels for manual audit, not ground-truth process labels.",
        "",
        "| model | reason lang | n | final correct loose | green cues | red IFC cue | review final-correct | mixed lang |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for (model, lang), rows in sorted(by.items()):
        n = len(rows)
        counts = Counter(r["process_triage"] for r in rows)
        lines.append(
            "| {model} | {lang} | {n} | {fc:.3f} | {green:.3f} | {red:.3f} | {review:.3f} | {mixed:.3f} |".format(
                model=model,
                lang=lang,
                n=n,
                fc=sum(r["final_correct_loose"] for r in rows) / n,
                green=counts["green_cues_final_correct"] / n,
                red=counts["red_invalid_cue_final_correct"] / n,
                review=counts["review_final_correct_missing_cues"] / n,
                mixed=sum(r["mixed_language_flag"] for r in rows) / n,
            )
        )
    lines += [
        "",
        "## High-Priority Manual Reads",
        "",
        "| model | task | in->reason | sample | triage | final | chars |",
        "|---|---|---|---:|---|---|---:|",
    ]
    priority = [
        r
        for r in audited
        if r["process_triage"] in {"red_invalid_cue_final_correct", "review_final_correct_missing_cues"}
        or r["mixed_language_flag"]
    ]
    for r in priority[:80]:
        lines.append(
            f"| {r['model_key']} | {r['task_id']} | {r['input_lang']}->{r['reason_lang']} | "
            f"{r['sample_idx']} | {r['process_triage']} | {r['final_answer_extracted'][:40]} | {r['completion_chars']} |"
        )

    out_summary = Path(args.out_summary)
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_jsonl}; rows={len(audited)}")
    print(f"wrote {out_tsv}")
    print(f"wrote {out_summary}")


if __name__ == "__main__":
    main()
