from __future__ import annotations

from typing import Any


def term_prompts(term: str, lang: str) -> str:
    if lang == "zh":
        return f"在数学推理中，当前概念是：{term}。请理解这个概念。"
    return f"In mathematical reasoning, the current concept is: {term}. Understand this concept."


def verifier_prompt(problem: str, trace: str, lang: str = "en") -> str:
    if lang == "zh":
        return (
            "请判断下面的数学推理过程每一步是否都有效。只回答 是 或 否。\n"
            f"题目：{problem}\n"
            f"推理过程：{trace}\n"
            "每一步是否都数学有效？答案："
        )
    return (
        "Judge whether every step in the following mathematical reasoning is valid. "
        "Answer only Yes or No.\n"
        f"Problem: {problem}\n"
        f"Reasoning: {trace}\n"
        "Is every step mathematically valid? Answer:"
    )


def group_process_pairs(cases: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    by_problem: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        by_problem.setdefault(case["problem"], []).append(case)
    pairs = []
    for group in by_problem.values():
        valids = [c for c in group if c.get("process_valid") is True]
        invalids = [c for c in group if c.get("process_valid") is False and c.get("final_correct") is True]
        for v in valids:
            for b in invalids:
                pairs.append((v, b))
    return pairs
