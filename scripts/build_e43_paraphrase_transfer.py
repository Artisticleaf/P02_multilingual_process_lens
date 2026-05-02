#!/usr/bin/env python3
"""Build E43 paraphrase-transfer diagnostic rows.

Rows are manually constructed valid/invalid sibling traces.  Each family has
two surface paraphrases with the same process semantics and same final answer.
The intended test is whether hidden support/error vectors transfer across
wording inside a family more than across mismatched families.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]


FAMILIES = [
    {
        "task_id": "each_vs_total",
        "problem": "Four students each read 6 pages. How many pages did they read in total?",
        "answer": "24",
        "paraphrases": [
            {
                "tag": "a",
                "valid": "Each of the 4 students read 6 pages, so the class total is 4*6 = 24 pages.\nFinal answer: 24",
                "invalid": "The word each means the whole group read 6 pages total, so the total is 6 pages. Since there are 4 students, I then report 24.\nFinal answer: 24",
                "support_span": "the class total is 4*6",
                "error_span": "each means the whole group read 6 pages total",
            },
            {
                "tag": "b",
                "valid": "Per student there are 6 pages. Across 4 students, multiply 6 by 4 to get 24 pages.\nFinal answer: 24",
                "invalid": "Per student means split 6 pages among the 4 students, so each share is 6/4 pages. I will still give the total as 24 pages.\nFinal answer: 24",
                "support_span": "Across 4 students, multiply 6 by 4",
                "error_span": "split 6 pages among the 4 students",
            },
        ],
    },
    {
        "task_id": "percent_increase_vs_percent_of",
        "problem": "A price is $50 and increases by 20%. What is the new price?",
        "answer": "60",
        "paraphrases": [
            {
                "tag": "a",
                "valid": "A 20% increase adds 20% of 50, which is 10, to the original price: 50+10=60.\nFinal answer: 60",
                "invalid": "A 20% increase means the new price is only 20% of the old price, which is 10. I will state the new price as 60.\nFinal answer: 60",
                "support_span": "adds 20% of 50",
                "error_span": "the new price is only 20% of the old price",
            },
            {
                "tag": "b",
                "valid": "Increase by 20% means multiply by 1.20, so 50*1.20 = 60.\nFinal answer: 60",
                "invalid": "Increase by 20% means multiply by 0.20, so the price part is 10; I will give 60 as the answer.\nFinal answer: 60",
                "support_span": "multiply by 1.20",
                "error_span": "multiply by 0.20",
            },
        ],
    },
    {
        "task_id": "prob_without_replacement",
        "problem": "A bag has 3 red balls and 2 blue balls. Two balls are drawn without replacement. What is the probability both are red?",
        "answer": "3/10",
        "paraphrases": [
            {
                "tag": "a",
                "valid": "The first red probability is 3/5. Without replacement, then 2 red balls remain out of 4, so multiply 3/5 by 2/4 = 3/10.\nFinal answer: 3/10",
                "invalid": "Without replacement means the first red ball is replaced before the second draw, so use 3/5 twice. I will report 3/10.\nFinal answer: 3/10",
                "support_span": "2 red balls remain out of 4",
                "error_span": "the first red ball is replaced before the second draw",
            },
            {
                "tag": "b",
                "valid": "After drawing a red ball and not putting it back, the bag has 2 red among 4 total. Thus (3/5)*(2/4)=3/10.\nFinal answer: 3/10",
                "invalid": "Not putting it back leaves the same 3 red among 5 total for the second draw. I will still output 3/10.\nFinal answer: 3/10",
                "support_span": "not putting it back, the bag has 2 red among 4 total",
                "error_span": "leaves the same 3 red among 5 total",
            },
        ],
    },
    {
        "task_id": "reciprocal_vs_additive_inverse",
        "problem": "What is the reciprocal of 4?",
        "answer": "1/4",
        "paraphrases": [
            {
                "tag": "a",
                "valid": "The reciprocal is the number that multiplies by 4 to make 1, so it is 1/4.\nFinal answer: 1/4",
                "invalid": "The reciprocal means the additive inverse, so for 4 it would be -4. I will answer 1/4.\nFinal answer: 1/4",
                "support_span": "multiplies by 4 to make 1",
                "error_span": "reciprocal means the additive inverse",
            },
            {
                "tag": "b",
                "valid": "To take a reciprocal, flip 4 to 1 divided by 4, giving 1/4.\nFinal answer: 1/4",
                "invalid": "To take a reciprocal, change the sign of 4, giving -4. I will give 1/4.\nFinal answer: 1/4",
                "support_span": "flip 4 to 1 divided by 4",
                "error_span": "change the sign of 4",
            },
        ],
    },
    {
        "task_id": "zh_exclusive_interval",
        "problem": "一个整数大于2且小于6。它有多少个可能取值？",
        "answer": "3",
        "paraphrases": [
            {
                "tag": "a",
                "valid": "大于2且小于6不包含端点2和6，因此整数只能是3、4、5，共3个。\nFinal answer: 3",
                "invalid": "大于2且小于6包含2和6，所以可以取2、3、4、5、6；我仍给出3个。\nFinal answer: 3",
                "support_span": "不包含端点2和6",
                "error_span": "包含2和6",
            },
            {
                "tag": "b",
                "valid": "严格在2和6之间的整数是3、4、5，所以可能取值数是3。\nFinal answer: 3",
                "invalid": "严格在2和6之间也把边界2、6算进去，所以有2到6这些数；最后写3。\nFinal answer: 3",
                "support_span": "严格在2和6之间的整数是3、4、5",
                "error_span": "把边界2、6算进去",
            },
        ],
    },
    {
        "task_id": "zh_perimeter_vs_area",
        "problem": "一个长方形长8厘米、宽3厘米。它的周长是多少厘米？",
        "answer": "22",
        "paraphrases": [
            {
                "tag": "a",
                "valid": "周长是四条边长度之和，所以是2*(8+3)=22厘米。\nFinal answer: 22",
                "invalid": "周长就是面积，所以先算8*3=24平方厘米；最后我写22厘米。\nFinal answer: 22",
                "support_span": "四条边长度之和",
                "error_span": "周长就是面积",
            },
            {
                "tag": "b",
                "valid": "矩形周长要把长和宽各算两次，即8+3+8+3=22厘米。\nFinal answer: 22",
                "invalid": "矩形周长要把长乘宽，得到24；但最终答案写22厘米。\nFinal answer: 22",
                "support_span": "把长和宽各算两次",
                "error_span": "把长乘宽",
            },
        ],
    },
]


def main() -> None:
    rows = []
    pairs = []
    idx = 430000
    for fam_i, fam in enumerate(FAMILIES):
        for p in fam["paraphrases"]:
            ids = {}
            for side, valid in [("valid", True), ("invalid", False)]:
                idx += 1
                row = {
                    "audit_idx": idx,
                    "e05_idx": idx,
                    "sample_idx": idx,
                    "model_key": "e43_controlled_manual",
                    "task_id": fam["task_id"],
                    "paraphrase_tag": p["tag"],
                    "problem": fam["problem"],
                    "completion": p[side],
                    "gold_answer": fam["answer"],
                    "input_lang": "zh" if fam["problem"][0] > "\u007f" else "en",
                    "reason_lang": "zh" if p[side][0] > "\u007f" else "en",
                    "route": "controlled",
                    "manual_process_valid": valid,
                    "manual_final_correct": True,
                    "manual_format_valid": True,
                    "manual_route_valid": True,
                    "is_acpi": not valid,
                    "paper_grade_acpi": not valid,
                    "manual_risk": "e43_valid" if valid else "e43_acpi",
                    "support_span": p["support_span"],
                    "error_span": p["error_span"],
                }
                rows.append(row)
                ids[side] = idx
            pairs.append(
                {
                    "id": f"e43_{fam['task_id']}_{p['tag']}",
                    "task_id": fam["task_id"],
                    "paraphrase_tag": p["tag"],
                    "valid_idx": ids["valid"],
                    "bad_idx": ids["invalid"],
                    "support_span": p["support_span"],
                    "error_span": p["error_span"],
                }
            )
    out_jsonl = PROJECT / "data/processed/e43_paraphrase_transfer_20260428.jsonl"
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_jsonl.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    out_yaml = PROJECT / "configs/e43_paraphrase_transfer_pairs.yaml"
    out_yaml.write_text(yaml.safe_dump({"pairs": pairs}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"wrote {out_jsonl} rows={len(rows)}")
    print(f"wrote {out_yaml} pairs={len(pairs)}")


if __name__ == "__main__":
    main()
