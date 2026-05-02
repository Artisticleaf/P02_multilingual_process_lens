# E162 Completed and Checkpoint Audit / E162 完成结果与 checkpoint 审计

Created / 生成时间：2026-05-01T15:25:43

## Scope / 范围

- Completed final evidence / 完成 final 证据：Gemma dense first-sample smoke JSON only. / 目前只有 Gemma dense 首样本 smoke JSON 是完整 final 文件。
- Provisional evidence / 临时证据：current Qwen checkpoint JSONL snapshot. / 当前 Qwen checkpoint 快照，只用于临时行为审计。
- Running full E162 queue is not yet complete. / E162 全量队列尚未完成。

## Summary / 汇总

```json
{
  "by_evidence_level": {
    "completed_final_file": {
      "error_mentioned": 1,
      "final_correct": 2,
      "final_marker_found": 6,
      "hit_max": 0,
      "label::answer_repaired_from_wrong_source": 2,
      "label::final_wrong": 4,
      "n": 6,
      "source_answer_repeated": 4
    },
    "provisional_checkpoint": {
      "error_mentioned": 44,
      "final_correct": 57,
      "final_marker_found": 57,
      "hit_max": 4,
      "label::final_correct_process_repair_not_visible": 15,
      "label::incomplete_generation": 4,
      "label::process_error_identified_or_repaired_final_correct": 42,
      "n": 61,
      "source_answer_repeated": 57
    }
  },
  "by_evidence_level_and_family": {
    "completed_final_file::multilingual_semantic": {
      "error_mentioned": 1,
      "final_correct": 2,
      "hit_max": 0,
      "n": 6
    },
    "provisional_checkpoint::algebra_sign_symmetry": {
      "error_mentioned": 15,
      "final_correct": 21,
      "hit_max": 3,
      "n": 24
    },
    "provisional_checkpoint::code_boundary_zero": {
      "error_mentioned": 20,
      "final_correct": 24,
      "hit_max": 0,
      "n": 24
    },
    "provisional_checkpoint::counting_complement": {
      "error_mentioned": 9,
      "final_correct": 12,
      "hit_max": 1,
      "n": 13
    }
  },
  "by_evidence_level_and_variant": {
    "completed_final_file::baseline_regenerate": {
      "error_mentioned": 0,
      "final_correct": 0,
      "hit_max": 0,
      "label::final_wrong": 1,
      "n": 1
    },
    "completed_final_file::generic_error_prompt": {
      "error_mentioned": 0,
      "final_correct": 0,
      "hit_max": 0,
      "label::final_wrong": 1,
      "n": 1
    },
    "completed_final_file::localized_error_prompt": {
      "error_mentioned": 1,
      "final_correct": 1,
      "hit_max": 0,
      "label::answer_repaired_from_wrong_source": 1,
      "n": 1
    },
    "completed_final_file::oracle_error_prompt": {
      "error_mentioned": 0,
      "final_correct": 1,
      "hit_max": 0,
      "label::answer_repaired_from_wrong_source": 1,
      "n": 1
    },
    "completed_final_file::prefix_continue": {
      "error_mentioned": 0,
      "final_correct": 0,
      "hit_max": 0,
      "label::final_wrong": 1,
      "n": 1
    },
    "completed_final_file::random_location_prompt": {
      "error_mentioned": 0,
      "final_correct": 0,
      "hit_max": 0,
      "label::final_wrong": 1,
      "n": 1
    },
    "provisional_checkpoint::baseline_regenerate": {
      "error_mentioned": 0,
      "final_correct": 9,
      "hit_max": 2,
      "label::final_correct_process_repair_not_visible": 9,
      "label::incomplete_generation": 2,
      "n": 11
    },
    "provisional_checkpoint::generic_error_prompt": {
      "error_mentioned": 9,
      "final_correct": 9,
      "hit_max": 1,
      "label::final_correct_process_repair_not_visible": 1,
      "label::incomplete_generation": 1,
      "label::process_error_identified_or_repaired_final_correct": 8,
      "n": 10
    },
    "provisional_checkpoint::localized_error_prompt": {
      "error_mentioned": 10,
      "final_correct": 9,
      "hit_max": 1,
      "label::incomplete_generation": 1,
      "label::process_error_identified_or_repaired_final_correct": 9,
      "n": 10
    },
    "provisional_checkpoint::oracle_error_prompt": {
      "error_mentioned": 10,
      "final_correct": 10,
      "hit_max": 0,
      "label::process_error_identified_or_repaired_final_correct": 10,
      "n": 10
    },
    "provisional_checkpoint::prefix_continue": {
      "error_mentioned": 7,
      "final_correct": 10,
      "hit_max": 0,
      "label::final_correct_process_repair_not_visible": 3,
      "label::process_error_identified_or_repaired_final_correct": 7,
      "n": 10
    },
    "provisional_checkpoint::random_location_prompt": {
      "error_mentioned": 8,
      "final_correct": 10,
      "hit_max": 0,
      "label::final_correct_process_repair_not_visible": 2,
      "label::process_error_identified_or_repaired_final_correct": 8,
      "n": 10
    }
  }
}
```

## Completed Smoke Audit / 已完成 smoke 审计

- `baseline_regenerate`: final `5` vs gold `7`, correct=False, label=`final_wrong`. Excerpt / 摘要：To solve the problem, we need to find the number of integers $x$ that satisfy two conditions: 1. $-8 \le x \le 8$ 2. $|x|$ is a multiple of 3 (zhi duo wei 3). **Step 1: Identify the range of $x$.** The integers $x$ in the range $-8 \le x...
- `prefix_continue`: final `5` vs gold `7`, correct=False, label=`final_wrong`. Excerpt / 摘要：Based on the conditions provided: 1. The range of $x$ is $-8 \le x \le 8$. 2. The absolute value $|x|$ must be a multiple of 3. We list the possible values for $|x|$ that are multiples of 3 and fall within the range $[0, 8]$: - $|x| = 0$...
- `generic_error_prompt`: final `5` vs gold `7`, correct=False, label=`final_wrong`. Excerpt / 摘要：The problem asks for the number of integers $x$ such that $-8 \le x \le 8$ and $|x|$ is a multiple of 3. 1. **Identify the range of $x$**: The integers $x$ are in the set $\{-8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8\}$. 2...
- `localized_error_prompt`: final `7` vs gold `7`, correct=True, label=`answer_repaired_from_wrong_source`. Excerpt / 摘要：The phrase "zhi duo wei 3" in the context of the problem " $|x|$ zhi duo wei 3" is a transcription of " $|x|$ 之多为 3" or more likely a misinterpretation of " $|x|$ 为 3 的倍数" (multiple of 3) or " $|x| \le 3$". However, looking at the standa...
- `oracle_error_prompt`: final `7` vs gold `7`, correct=True, label=`answer_repaired_from_wrong_source`. Excerpt / 摘要：The problem asks for the number of integers $x$ such that $-8 \le x \le 8$ and $|x|$ "zhi duo wei 3". According to the audit note, "zhi duo wei 3" (至多为 3) means "at most 3", which translates to the inequality $|x| \le 3$. 1. **Condition ...
- `random_location_prompt`: final `5` vs gold `7`, correct=False, label=`final_wrong`. Excerpt / 摘要：The phrase "Qiu zhengshu x de geshu" is a transliteration of the Chinese "求整数 $x$ 的个数", which translates to "Find the number of integers $x$". This is a standard mathematical request and is not abnormal. Continuing from the partial solut...

Smoke interpretation / smoke 解释：baseline, prefix, generic warning, and random-location control repeated the source wrong answer; localized and oracle prompts repaired the answer. / baseline、续写、泛泛提示、随机位置都重复源错误答案；局部提示和 oracle 提示修复答案。

## Qwen Checkpoint Provisional Audit / Qwen checkpoint 临时审计

Important boundary / 重要边界：these rows are still checkpoint rows. Hit-max or no-final rows should not be counted as model failure until full rerun/longer-token handling is decided. / 这些仍是 checkpoint；达到 token 上限或缺 final marker 的行，不应在未处理截断前当作最终模型失败。

- `e159_algebra_sign_symmetry_01` / `baseline_regenerate`: final `1` vs gold `127`, correct=False, hit_max=True, label=`incomplete_generation`. Excerpt / 摘要：To find the number of ordered integer pairs $(x, y)$ satisfying the equation $10x^2 - xy - 2y^2 = 0$ with the constraints $-90 \le x, y \le 90$, we proceed as follows: ### Step 1: Factor the quadratic equation The given equation is a hom...
- `e159_algebra_sign_symmetry_01` / `prefix_continue`: final `127` vs gold `127`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：The equation is given by $10x^2 - xy - 2y^2 = 0$. As factored in the partial solution, this becomes: $(2x + y)(5x - 2y) = 0$. For the product of two terms to be zero, at least one of the terms must be zero. This gives us two cases: Case ...
- `e159_algebra_sign_symmetry_01` / `generic_error_prompt`: final `10` vs gold `127`, correct=False, hit_max=True, label=`incomplete_generation`. Excerpt / 摘要：The partial solution correctly identifies the factorization of the quadratic expression. Let's verify and complete the solution. **1. Verify the Factorization** The given equation is $10x^2 - xy - 2y^2 = 0$. The proposed factorization is...
- `e159_algebra_sign_symmetry_01` / `localized_error_prompt`: final `4.5` vs gold `127`, correct=False, hit_max=True, label=`incomplete_generation`. Excerpt / 摘要：The factorization step provided in the partial solution is incorrect. Let's re-evaluate the factorization of the quadratic expression $10x^2 - xy - 2y^2$. We are looking for factors of the form $(ax + by)(cx + dy)$ such that: 1. $ac = 10...
- `e159_algebra_sign_symmetry_01` / `oracle_error_prompt`: final `127` vs gold `127`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains a factorization error. Let's verify the expansion of the given factors: $(2x+y)(5x-2y) = 10x^2 - 4xy + 5xy - 2y^2 = 10x^2 + xy - 2y^2$. The original equation is $10x^2 - xy - 2y^2 = 0$. The middle term sign ...
- `e159_algebra_sign_symmetry_01` / `random_location_prompt`: final `127` vs gold `127`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：The flagged span `Count ordered integer pairs` is a description of the problem's goal, not a mathematical step or a value to be calculated. It is not abnormal; it is the correct instruction for the task. The actual mathematical work begi...
- `e159_algebra_sign_symmetry_02` / `baseline_regenerate`: final `2,20` vs gold `2,20`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：To solve the problem, we need to find the integer values of $x$ within the interval $[-30, 30]$ that satisfy the equation $(x-12)(x+8)=0$, count how many such values exist, and calculate the sum of their absolute values. **Step 1: Solve ...
- `e159_algebra_sign_symmetry_02` / `prefix_continue`: final `2,20` vs gold `2,20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains an error in identifying the roots. Let's re-evaluate the equation $(x-12)(x+8)=0$. 1. **Find the roots**: The product of two factors is zero if and only if at least one of the factors is zero. - $x - 12 = 0 ...
- `e159_algebra_sign_symmetry_02` / `generic_error_prompt`: final `2,20` vs gold `2,20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains an error in identifying the roots of the equation. **Step 1: Solve the equation $(x-12)(x+8)=0$.** For the product of two factors to be zero, at least one of the factors must be zero. 1. $x - 12 = 0 \implies...
- `e159_algebra_sign_symmetry_02` / `localized_error_prompt`: final `2,20` vs gold `2,20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The step identifying the roots is actually correct. Let's verify: The equation is $(x-12)(x+8)=0$. Setting each factor to zero: 1. $x - 12 = 0 \implies x = 12$ 2. $x + 8 = 0 \implies x = -8$ The partial solution stated the roots are $x=-...
- `e159_algebra_sign_symmetry_02` / `oracle_error_prompt`: final `2,20` vs gold `2,20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The equation given is $(x-12)(x+8)=0$. To find the roots, we set each factor to zero: 1. $x - 12 = 0 \implies x = 12$ 2. $x + 8 = 0 \implies x = -8$ The flagged span stated the roots were $x=-12$ and $x=8$. This corresponds to the error ...
- `e159_algebra_sign_symmetry_02` / `random_location_prompt`: final `2,20` vs gold `2,20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The flagged span `How many integer x in` is part of the original problem statement and is not abnormal; it correctly introduces the query about the count of integers. The partial solution provided contains an error in identifying the roo...
- `e159_algebra_sign_symmetry_03` / `baseline_regenerate`: final `0` vs gold `0`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：To solve the problem, we need to evaluate the function $f(t) = t^2 - 6t + 5$ at two specific values, $t=1$ and $t=5$, and then sum the results. **Step 1: Evaluate $f(1)$** Substitute $t = 1$ into the function: $$f(1) = (1)^2 - 6(1) + 5$$...
- `e159_algebra_sign_symmetry_03` / `prefix_continue`: final `0` vs gold `0`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains a significant error in identifying the roots of the quadratic equation. Let's correct the calculation step by step. The function is given by $f(t) = t^2 - 6t + 5$. First, let's find the roots of $f(t) = 0$ t...
- `e159_algebra_sign_symmetry_03` / `generic_error_prompt`: final `0` vs gold `0`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains a significant error in identifying the roots of the quadratic equation. **Step 1: Analyze the function and the error.** The function is given by $f(t) = t^2 - 6t + 5$. The partial solution claims the roots a...
- `e159_algebra_sign_symmetry_03` / `localized_error_prompt`: final `0` vs gold `0`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The statement "roots of $t^2-6t+5$ are $-1$ and $-5$" is incorrect. To find the roots of the quadratic equation $t^2 - 6t + 5 = 0$, we can factor the expression: We look for two numbers that multiply to $5$ and add to $-6$. These numbers...
- `e159_algebra_sign_symmetry_03` / `oracle_error_prompt`: final `0` vs gold `0`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The statement "The roots of $t^2-6t+5$ are -1 and -5" is incorrect. To find the roots, we solve $t^2-6t+5=0$. Factoring the quadratic gives $(t-1)(t-5)=0$, so the roots are $t=1$ and $t=5$. Since $1$ and $5$ are the roots of the function...
- `e159_algebra_sign_symmetry_03` / `random_location_prompt`: final `0` vs gold `0`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The statement "The roots of t^2-6t+5 are -1 and -5" is incorrect. To find the roots of $t^2 - 6t + 5 = 0$, we factor the quadratic: $(t - 1)(t - 5) = 0$. The roots are $t = 1$ and $t = 5$, not $-1$ and $-5$. However, the question asks fo...
- `e159_algebra_sign_symmetry_04` / `baseline_regenerate`: final `2` vs gold `2`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：To solve the problem, we need to find the number of integers $n$ within the range $-20 \le n \le 20$ that satisfy the equation $n^2 = 49$. **Step 1: Solve the equation $n^2 = 49$.** To find the values of $n$, we take the square root of b...
- `e159_algebra_sign_symmetry_04` / `prefix_continue`: final `2` vs gold `2`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：The equation $n^2 = 49$ implies that $n = \sqrt{49}$ or $n = -\sqrt{49}$. Calculating the square roots, we get $n = 7$ and $n = -7$. We must check if these solutions fall within the given range $-20 \le n \le 20$. 1. For $n = 7$: $-20 \l...
- `e159_algebra_sign_symmetry_04` / `generic_error_prompt`: final `2` vs gold `2`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：The partial solution correctly identifies that the equation $n^2 = 49$ has two integer solutions: $n = 7$ and $n = -7$. Let's verify the steps: 1. **Solve the equation**: $n^2 = 49$ implies $n = \pm\sqrt{49}$, so $n = 7$ or $n = -7$. 2. ...
- `e159_algebra_sign_symmetry_04` / `localized_error_prompt`: final `2` vs gold `2`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The step "Taking square roots gives n=7 only" is incorrect because the equation $n^2 = 49$ has two real solutions: $n = 7$ and $n = -7$. Both satisfy the condition $-20 \le n \le 20$. Correcting the step: Taking the square root of both s...
- `e159_algebra_sign_symmetry_04` / `oracle_error_prompt`: final `2` vs gold `2`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The equation $n^2 = 49$ implies that $n$ can be either the positive or negative square root of 49. Taking the square root of both sides yields: $n = \pm\sqrt{49}$ $n = \pm 7$ So the possible integer values for $n$ are $7$ and $-7$. We mu...
- `e159_algebra_sign_symmetry_04` / `random_location_prompt`: final `2` vs gold `2`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：The flagged span `For integer n with -20` is part of the problem statement defining the domain for $n$. The condition is $-20 \le n \le 20$. Let's re-evaluate the solution steps based on this domain: 1. **Equation**: $n^2 = 49$. 2. **Sol...
- `e159_code_boundary_zero_01` / `baseline_regenerate`: final `-20` vs gold `-20`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：To determine what the Python code prints, let's trace the execution step by step. The code initializes a variable `s` to 0. Then, it enters a `for` loop where `i` takes values from `range(0, 6)`. The `range(0, 6)` function generates inte...
- `e159_code_boundary_zero_01` / `prefix_continue`: final `-20` vs gold `-20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains an error in the description of the `range` function. `range(0, 6)` generates integers starting from 0 up to, but not including, 6. Therefore, the values of `i` are 0, 1, 2, 3, 4, and 5, not just 1, 2, 3, 4. ...
- `e159_code_boundary_zero_01` / `generic_error_prompt`: final `-20` vs gold `-20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains an error in the description of the `range(0, 6)` function. **Correction:** The function `range(0, 6)` generates integers starting from 0 up to, but not including, 6. Therefore, the values of `i` are **0, 1, ...
- `e159_code_boundary_zero_01` / `localized_error_prompt`: final `-20` vs gold `-20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The step `range(0,6) gives i=1,2,3,4` is incorrect. In Python, `range(start, stop)` generates numbers starting from `start` up to, but not including, `stop`. Therefore, `range(0, 6)` generates the sequence `0, 1, 2, 3, 4, 5`. Let's re-ca...
- `e159_code_boundary_zero_01` / `oracle_error_prompt`: final `-20` vs gold `-20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The flagged span `range(0,6) gives i=1,2,3,4` is incorrect. The Python function `range(0, 6)` generates integers starting from 0 up to, but not including, 6. Therefore, the correct sequence of values for `i` is `0, 1, 2, 3, 4, 5`. Let's ...
- `e159_code_boundary_zero_01` / `random_location_prompt`: final `-20` vs gold `-20`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The previous step contains an error in the range evaluation. The function `range(0, 6)` generates integers starting from 0 up to, but not including, 6. Therefore, the sequence of values for `i` is `0, 1, 2, 3, 4, 5`, not `1, 2, 3, 4`. Le...
- `e159_code_boundary_zero_02` / `baseline_regenerate`: final `-4` vs gold `-4`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：To determine what the Python code prints, let's trace the execution step by step. 1. **Initialization**: The list `out` is initialized as an empty list: `out = []`. 2. **The Loop**: The loop iterates over `j` in `range(4)`. This means `j...
- `e159_code_boundary_zero_02` / `prefix_continue`: final `-4` vs gold `-4`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains an error: `range(4)` generates the sequence `0, 1, 2, 3`, not just `1, 2`. Let's re-evaluate the code step by step. 1. **Initialize**: `out = []`. 2. **Loop**: `for j in range(4)`: * **Iteration 1**: `j = 0`...
- `e159_code_boundary_zero_02` / `generic_error_prompt`: final `-4` vs gold `-4`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains an error in the description of the `range(4)` function. **Correction:** In Python, `range(4)` generates a sequence of integers starting from 0 up to (but not including) 4. Therefore, the values of `j` are **...
- `e159_code_boundary_zero_02` / `localized_error_prompt`: final `-4` vs gold `-4`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The step `range(4) gives j=1,2 only` is incorrect. In Python, `range(4)` generates a sequence of integers starting from 0 up to (but not including) 4. Therefore, the values of `j` are 0, 1, 2, and 3. Let's re-evaluate the code with the c...
- `e159_code_boundary_zero_02` / `oracle_error_prompt`: final `-4` vs gold `-4`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The statement `range(4) gives j=1,2 only` is incorrect. In Python, `range(4)` generates the sequence of integers starting from 0 up to (but not including) 4. Therefore, the values of `j` are `0, 1, 2, 3`. Let's re-evaluate the code with ...
- `e159_code_boundary_zero_02` / `random_location_prompt`: final `-4` vs gold `-4`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The previous step contains an error: `range(4)` generates the sequence `0, 1, 2, 3`, not just `1, 2`. Let's re-evaluate the loop correctly: 1. **`j = 0`**: `0 * (0 - 3) = 0 * -3 = 0`. `out` becomes `[0]`. 2. **`j = 1`**: `1 * (1 - 3) = 1...
- `e159_code_boundary_zero_03` / `baseline_regenerate`: final `-10` vs gold `-10`, correct=True, hit_max=False, label=`final_correct_process_repair_not_visible`. Excerpt / 摘要：To solve the problem `sum(k*(k-4) for k in range(5))` in Python, we need to evaluate the generator expression inside the `sum()` function step by step. 1. **Understand the range**: The function `range(5)` generates a sequence of integers...
- `e159_code_boundary_zero_03` / `prefix_continue`: final `-10` vs gold `-10`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains an error: `range(5)` in Python generates the sequence `0, 1, 2, 3, 4`, not `1, 2, 3`. Let's recalculate the sum correctly using the sequence `0, 1, 2, 3, 4`: The expression is `sum(k*(k-4) for k in range(5))...
- `e159_code_boundary_zero_03` / `generic_error_prompt`: final `-10` vs gold `-10`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The partial solution contains a factual error regarding the output of `range(5)`. **Correction:** In Python, `range(5)` generates a sequence of integers starting from 0 up to (but not including) 5. Therefore, the sequence is `0, 1, 2, 3,...
- `e159_code_boundary_zero_03` / `localized_error_prompt`: final `-10` vs gold `-10`, correct=True, hit_max=False, label=`process_error_identified_or_repaired_final_correct`. Excerpt / 摘要：The step `range(5) is 1,2,3` is incorrect. In Python, `range(5)` generates a sequence of integers starting from 0 up to (but not including) 5. Therefore, the correct sequence is `0, 1, 2, 3, 4`. Let's recalculate the sum using the correc...

## Current Reading / 当前解读

1. Localized prompt is useful but not identical to hidden-layer correction. / 局部提示有效，但它仍不是隐藏层纠错本身。
2. Qwen often repairs process errors even under prefix, generic, or random-location prompts, suggesting a generic re-solve/re-audit tendency. / Qwen 经常在续写、泛泛提示或随机位置提示下也修复过程，说明存在泛化重解/重审倾向。
3. Hit-max rows cluster in long baseline or localized algebra/counting generations under max_new_tokens=1024; these need token-budget handling before final scoring. / 截断主要出现在 1024 token 下的长代数/计数生成，最终评分前需要处理 token budget。
4. The smoke result remains the cleanest positive evidence so far: localized semantic span fixes Gemma dense where generic warning does not. / 目前最干净的正证据仍是 smoke：局部语义 span 能修复 Gemma dense，而泛泛提示不能。
