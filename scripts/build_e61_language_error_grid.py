#!/usr/bin/env python3
"""Build E61 language-route x error-taxonomy controlled grid."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "data/processed/e61_language_error_grid_20260429.jsonl"
PAIRS = PROJECT / "configs/e61_language_error_grid_pairs.yaml"

ROUTES = [
    ("en_en", "en", "en", "en_problem_en_reason"),
    ("zh_zh", "zh", "zh", "zh_problem_zh_reason"),
    ("zh_en", "zh", "en", "zh_problem_en_reason"),
    ("en_zh", "en", "zh", "en_problem_zh_reason"),
    ("mixed", "mixed", "mixed", "mixed_zh_en_problem_reason"),
    ("romanized_zh", "romanized_zh", "romanized_zh", "pinyin_problem_reason"),
]

TASKS = [
    {
        "family": "unit_scale",
        "name": "meter_centimeter",
        "gold_answer": "320",
        "wrong_answer": "32",
        "support_span": "1 meter is 100 centimeters",
        "error_span": "1 meter is 10 centimeters",
        "en_problem": "How many centimeters are in 3.2 meters?",
        "zh_problem": "3.2米等于多少厘米？",
        "mixed_problem": "3.2 meters 等于多少厘米？",
        "pinyin_problem": "3.2 mi dengyu duoshao limi?",
        "en_valid": "1 meter is 100 centimeters, so 3.2 meters is 3.2*100 = 320 centimeters.",
        "en_invalid": "1 meter is 10 centimeters, so 3.2 meters looks like 32 centimeters. Using the centimeter scale for the requested unit gives 3.2*100 = 320 centimeters.",
        "zh_valid": "1米等于100厘米，所以3.2米等于3.2*100=320厘米。",
        "zh_invalid": "1米等于10厘米，所以3.2米看起来是32厘米。按题目要求的厘米尺度计算，3.2*100=320厘米。",
        "mix_valid": "1 meter = 100 厘米，所以 3.2 meters = 3.2*100 = 320 厘米。",
        "mix_invalid": "1 meter = 10 厘米，所以 3.2 meters 看起来是 32 厘米。按 centimeters 的实际换算，3.2*100 = 320。",
        "py_valid": "1 mi shi 100 limi, suoyi 3.2 mi shi 3.2*100 = 320 limi.",
        "py_invalid": "1 mi shi 10 limi, suoyi 3.2 mi kanqilai shi 32 limi. An zhengque limi huansuan, 3.2*100 = 320.",
    },
    {
        "family": "percentage_base",
        "name": "increase_base",
        "gold_answer": "100",
        "wrong_answer": "20",
        "support_span": "25% increase adds 25% of the original to 80",
        "error_span": "25% increase means the final price is 25% of the original",
        "en_problem": "A price of 80 increases by 25%. What is the new price?",
        "zh_problem": "价格80增加25%后，新价格是多少？",
        "mixed_problem": "价格 80 increases by 25%，new price 是多少？",
        "pinyin_problem": "jiage 80 zengjia 25% hou, xin jiage shi duoshao?",
        "en_valid": "A 25% increase adds 25% of 80, which is 20, so the new price is 80+20 = 100.",
        "en_invalid": "A 25% increase means the final price is 25% of the original, which would be 20. For an increase, add 25% of 80 to the original, so 80+20 = 100.",
        "zh_valid": "增加25%表示加上原价80的25%，也就是20，所以新价格是80+20=100。",
        "zh_invalid": "增加25%表示最终价格是原价的25%，也就是20。作为增加，应把80的25%加回原价，所以80+20=100。",
        "mix_valid": "25% increase means add 25% of 80，也就是20，所以 new price = 80+20 = 100。",
        "mix_invalid": "25% increase means final price is 25% of 80，也就是20。But increase 要加到原价上，所以 80+20 = 100。",
        "py_valid": "zengjia 25% shi jia shang 80 de 25%, yejiu shi 20, suoyi xin jiage 80+20=100.",
        "py_invalid": "zengjia 25% shi zuihou jiage dengyu yuanjia de 25%, yejiu shi 20. Danshi zengjia yao jia hui yuanjia, suoyi 80+20=100.",
    },
    {
        "family": "quantifier_inequality",
        "name": "strict_inclusive_mix",
        "gold_answer": "4",
        "wrong_answer": "5",
        "support_span": "greater than -1 excludes -1 and at most 3 includes 3",
        "error_span": "greater than -1 includes -1",
        "en_problem": "How many integers are greater than -1 and at most 3?",
        "zh_problem": "大于-1且不超过3的整数有多少个？",
        "mixed_problem": "整数 greater than -1 且 no more than 3，有多少个？",
        "pinyin_problem": "dayu -1 erqie bu chaoguo 3 de zhengshu you duoshao ge?",
        "en_valid": "Greater than -1 excludes -1, and at most 3 includes 3. The integers are 0, 1, 2, and 3, so there are 4.",
        "en_invalid": "Greater than -1 includes -1. Listing the integers that actually satisfy the strict lower bound gives 0, 1, 2, and 3, so there are 4.",
        "zh_valid": "大于-1不包含-1，不超过3包含3，所以整数是0、1、2、3，共4个。",
        "zh_invalid": "大于-1包含-1。按严格下界实际列出满足条件的整数是0、1、2、3，所以共有4个。",
        "mix_valid": "greater than -1 不包含 -1，no more than 3 包含 3，所以 values 是 0,1,2,3，共 4 个。",
        "mix_invalid": "greater than -1 includes -1。实际按 strict lower bound 列表是 0,1,2,3，所以 count = 4。",
        "py_valid": "dayu -1 bu baohan -1, bu chaoguo 3 baohan 3, suoyi zhengshu shi 0,1,2,3, gong 4 ge.",
        "py_invalid": "dayu -1 baohan -1. Danshi an yange xiajie liechu shi 0,1,2,3, suoyi gong 4 ge.",
    },
    {
        "family": "counting_order",
        "name": "roles_ordered",
        "gold_answer": "20",
        "wrong_answer": "10",
        "support_span": "president and secretary are different roles, so order matters",
        "error_span": "choosing president and secretary is unordered",
        "en_problem": "From 5 students, choose a president and a secretary. How many assignments are possible?",
        "zh_problem": "从5名学生中选一名主席和一名秘书，有多少种安排？",
        "mixed_problem": "From 5 students 选 president 和 secretary，有多少 assignments？",
        "pinyin_problem": "cong 5 ge xuesheng li xuan zhuxi he mishu, you duoshao zhong anpai?",
        "en_valid": "The two roles are different, so order matters: 5 choices for president and then 4 for secretary, giving 5*4 = 20.",
        "en_invalid": "Choosing a president and a secretary is unordered, so C(5,2)=10. Since the two titles are actually different roles, the assignment count is 5*4 = 20.",
        "zh_valid": "主席和秘书是不同职位，顺序有意义：主席5种选择，秘书剩4种，所以5*4=20。",
        "zh_invalid": "选主席和秘书是不区分顺序的，所以C(5,2)=10。因为两个职位其实不同，安排数应为5*4=20。",
        "mix_valid": "president 和 secretary 是不同 roles，order matters，所以 5 choices then 4 choices，5*4=20。",
        "mix_invalid": "president and secretary 是 unordered choice，所以 C(5,2)=10。But titles are different roles，所以 assignments = 5*4=20。",
        "py_valid": "zhuxi he mishu shi butong zhiwei, shunxu you yiyi: 5 ge zhuxi xuanze, ranhou 4 ge mishu, 5*4=20.",
        "py_invalid": "xuan zhuxi he mishu bu fen shunxu, suoyi C(5,2)=10. Danshi liangge zhiwei butong, suoyi anpai shu shi 5*4=20.",
    },
    {
        "family": "table_interpretation",
        "name": "sum_vs_max_table",
        "gold_answer": "20",
        "wrong_answer": "9",
        "support_span": "total means summing across rows",
        "error_span": "total means the largest entry",
        "en_problem": "A table lists apples sold: Mon 6, Tue 9, Wed 5. How many apples were sold in total?",
        "zh_problem": "表格显示苹果销量：周一6个，周二9个，周三5个。总共卖了多少个？",
        "mixed_problem": "表格 apples sold: Mon 6, Tue 9, Wed 5。total 是多少？",
        "pinyin_problem": "biaoge: zhouyi 6 ge pingguo, zhouer 9 ge, zhousan 5 ge. zonggong maile duoshao?",
        "en_valid": "Total means summing across the days: 6+9+5 = 20 apples.",
        "en_invalid": "Total means the largest single-day entry, which is 9. Summing across the days gives the total: 6+9+5 = 20.",
        "zh_valid": "总共表示把三天相加：6+9+5=20个。",
        "zh_invalid": "总共表示最大的单日销量，也就是9个。把三天相加才是总数：6+9+5=20。",
        "mix_valid": "total means sum across days，所以 6+9+5 = 20 apples。",
        "mix_invalid": "total means largest entry，也就是 9。But across days 的总量要 sum: 6+9+5=20。",
        "py_valid": "zonggong shi san tian xiangjia: 6+9+5=20 ge.",
        "py_invalid": "zonggong shi zui da de danri shuliang, yejiu shi 9. Danshi san tian xiangjia cai shi zongshu: 6+9+5=20.",
    },
    {
        "family": "code_execution",
        "name": "python_range_stop",
        "gold_answer": "14",
        "wrong_answer": "20",
        "support_span": "range(2,6) excludes 6",
        "error_span": "range(2,6) includes 6",
        "en_problem": "In Python, after s=0; for i in range(2,6): s += i, what is s?",
        "zh_problem": "在 Python 中，s=0; for i in range(2,6): s += i 运行后，s是多少？",
        "mixed_problem": "Python 里 s=0; for i in range(2,6): s += i，最后 s 是多少？",
        "pinyin_problem": "Python zhong, s=0; for i in range(2,6): s += i, zuihou s shi duoshao?",
        "en_valid": "range(2,6) includes 2, 3, 4, and 5, but excludes 6, so s = 2+3+4+5 = 14.",
        "en_invalid": "range(2,6) includes 6, so one might add 2+3+4+5+6. Python excludes the stop value, so the loop adds 2+3+4+5 = 14.",
        "zh_valid": "range(2,6) 包含2、3、4、5，不包含6，所以s=2+3+4+5=14。",
        "zh_invalid": "range(2,6) 包含6，所以可能会加2+3+4+5+6。Python 不包含 stop 值，因此实际加2+3+4+5=14。",
        "mix_valid": "range(2,6) includes 2,3,4,5 but excludes 6，所以 s=2+3+4+5=14。",
        "mix_invalid": "range(2,6) includes 6，所以会像 2+3+4+5+6。But Python excludes stop，所以 s=2+3+4+5=14。",
        "py_valid": "range(2,6) baohan 2,3,4,5, bu baohan 6, suoyi s=2+3+4+5=14.",
        "py_invalid": "range(2,6) baohan 6, suoyi keneng jia 2+3+4+5+6. Danshi Python bu baohan stop, suoyi s=2+3+4+5=14.",
    },
    {
        "family": "proof_validity",
        "name": "multiple_of_six_even",
        "gold_answer": "true",
        "wrong_answer": "false",
        "support_span": "n=6k=2(3k), so n is even",
        "error_span": "all even numbers are multiples of 6",
        "en_problem": "Is this statement true: if n is a multiple of 6, then n is even?",
        "zh_problem": "命题“如果n是6的倍数，那么n是偶数”是真的吗？",
        "mixed_problem": "Statement: 如果 n is multiple of 6, then n is even. True or false?",
        "pinyin_problem": "mingti: ruguo n shi 6 de beishu, name n shi oushu. zhen hai shi jia?",
        "en_valid": "If n is a multiple of 6, then n=6k=2(3k), so n is even. The statement is true.",
        "en_invalid": "All even numbers are multiples of 6, so the implication should hold. Directly, if n=6k then n=2(3k), so n is even; the statement is true.",
        "zh_valid": "如果n是6的倍数，则n=6k=2(3k)，所以n是偶数。命题为真。",
        "zh_invalid": "所有偶数都是6的倍数，所以这个蕴含成立。直接看，若n=6k，则n=2(3k)，所以n是偶数；命题为真。",
        "mix_valid": "If n is multiple of 6, then n=6k=2(3k)，所以 n is even，statement true。",
        "mix_invalid": "All even numbers are multiples of 6，所以 implication holds。Directly n=6k=2(3k)，所以 n is even，true。",
        "py_valid": "ruguo n shi 6 de beishu, n=6k=2(3k), suoyi n shi oushu, mingti wei zhen.",
        "py_invalid": "suoyou oushu dou shi 6 de beishu, suoyi yunhan chengli. Zhijie kan n=6k=2(3k), suoyi n shi oushu, wei zhen.",
    },
    {
        "family": "geometry_notation",
        "name": "rectangle_perimeter_area",
        "gold_answer": "22",
        "wrong_answer": "24",
        "support_span": "perimeter is 2(length+width)",
        "error_span": "perimeter means length times width",
        "en_problem": "A rectangle has length 8 and width 3. What is its perimeter?",
        "zh_problem": "一个长方形长8、宽3，它的周长是多少？",
        "mixed_problem": "一个 rectangle length 8, width 3，perimeter 是多少？",
        "pinyin_problem": "changfangxing chang 8, kuan 3, zhouchang shi duoshao?",
        "en_valid": "Perimeter is the boundary length, so 2*(8+3)=22.",
        "en_invalid": "Perimeter means length times width, which would be 8*3=24. The boundary length is 2*(8+3)=22.",
        "zh_valid": "周长是边界长度，所以2*(8+3)=22。",
        "zh_invalid": "周长表示长乘宽，也就是8*3=24。边界长度应为2*(8+3)=22。",
        "mix_valid": "perimeter 是 boundary length，所以 2*(8+3)=22。",
        "mix_invalid": "perimeter means length times width，所以 8*3=24。But boundary length 是 2*(8+3)=22。",
        "py_valid": "zhouchang shi bianjie changdu, suoyi 2*(8+3)=22.",
        "py_invalid": "zhouchang shi chang cheng kuan, yejiu shi 8*3=24. Danshi bianjie changdu shi 2*(8+3)=22.",
    },
]


def select_text(task: dict, route_id: str) -> tuple[str, str, str]:
    if route_id == "en_en":
        return task["en_problem"], task["en_valid"], task["en_invalid"]
    if route_id == "zh_zh":
        return task["zh_problem"], task["zh_valid"], task["zh_invalid"]
    if route_id == "zh_en":
        return task["zh_problem"], task["en_valid"], task["en_invalid"]
    if route_id == "en_zh":
        return task["en_problem"], task["zh_valid"], task["zh_invalid"]
    if route_id == "mixed":
        return task["mixed_problem"], task["mix_valid"], task["mix_invalid"]
    if route_id == "romanized_zh":
        return task["pinyin_problem"], task["py_valid"], task["py_invalid"]
    raise KeyError(route_id)


def with_final(body: str, answer: str) -> str:
    return f"{body}\nFinal answer: {answer}"


def main() -> None:
    rows = []
    pairs = []
    base = 610000
    case_i = 0
    for task in TASKS:
        for route_id, input_lang, reason_lang, route_desc in ROUTES:
            problem, valid_body, invalid_body = select_text(task, route_id)
            task_id = f"e61_{route_id}_{task['name']}"
            valid_idx = base + case_i * 10 + 1
            bad_idx = base + case_i * 10 + 2
            common = {
                "task_id": task_id,
                "source_family": task["name"],
                "family": task["family"],
                "route_id": route_id,
                "route": route_desc,
                "input_lang": input_lang,
                "reason_lang": reason_lang,
                "problem": problem,
                "gold_answer": task["gold_answer"],
                "wrong_answer": task["wrong_answer"],
                "manual_final_correct": True,
                "manual_format_valid": True,
                "support_span": task["support_span"],
                "error_span": task["error_span"],
                "gold_label_in_prompt": False,
                "known_error_span_in_prompt": False,
                "known_error_span_annotation_in_prompt": False,
                "manual_correction_in_prompt": False,
            }
            rows.append({**common, "audit_idx": valid_idx, "e61_variant": "valid_correct", "e39_variant": "valid_correct", "completion": with_final(valid_body, task["gold_answer"]), "manual_process_valid": True, "is_acpi": False})
            rows.append({**common, "audit_idx": bad_idx, "e61_variant": "invalid_correct", "e39_variant": "invalid_correct", "completion": with_final(invalid_body, task["gold_answer"]), "manual_process_valid": False, "is_acpi": True})
            pairs.append({
                "id": f"{task_id}_bad{bad_idx}_valid{valid_idx}",
                "task_id": task_id,
                "family": task["family"],
                "route_id": route_id,
                "model_key": "e61_controlled",
                "bad_idx": bad_idx,
                "valid_idx": valid_idx,
                "problem": problem,
            })
            case_i += 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    PAIRS.parent.mkdir(parents=True, exist_ok=True)
    PAIRS.write_text(yaml.safe_dump({"pairs": pairs}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "pairs": len(pairs), "out": str(OUT), "pairs_yaml": str(PAIRS)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
