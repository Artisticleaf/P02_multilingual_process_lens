# E162 Gemma31 Localized / Oracle / Random Triad Audit

Date / 日期：2026-05-01T23:17:00

## Core Finding / 核心结论

- After removing pinyin/romanized cases, Gemma31 gets localized, oracle, and random all correct on 38/38 cases. / 去掉拼音/罗马化样本后，Gemma31 在 localized、oracle、random 三组都是 38/38。
- Oracle and random have very close completion length: oracle mean 207.4, random mean 202.1. / oracle 和 random 的 completion 长度非常接近：oracle 均值 207.4，random 均值 202.1。
- This does indicate the current non-pinyin bank is too easy for measuring localized-vs-random differential advantage. / 这说明当前去拼音题库对衡量 localized 相对 random 的差分优势来说过于简单。
- It does not mean localized is useless; it means random broad-problem reread is a strong baseline on these short cases. / 这不说明 localized 没用，而说明在这些短题上，random 宽泛题干重读是强基线。

## Token Statistics / token 统计

| variant | correct | mean tokens | median tokens | min | max | p90 |
|---|---:|---:|---:|---:|---:|---:|
| `localized` | 38/38 | 264.6 | 237.5 | 121 | 646 | 364 |
| `oracle` | 38/38 | 207.4 | 172.5 | 42 | 640 | 365 |
| `random` | 38/38 | 202.1 | 169.5 | 68 | 609 | 323 |

Deltas / 差值：

- localized - oracle: mean 57.2, median 35.0.
- localized - random: mean 62.5, median 67.5.
- oracle - random: mean 5.3, median 19.0.

## Why Localized Is Longer / 为什么 localized 更长

Localized usually explains the exact bad step before recomputing; oracle gives a direct correction; random often says the broad problem span is fine and simply recomputes from the problem. / localized 通常先解释具体错步为什么错，再重算；oracle 直接给修正；random 往往说宽泛题干片段没错，然后从题目重算。

Representative examples / 代表样本：

### `e159_algebra_sign_symmetry_03` / `algebra_sign_symmetry`

- localized: 188 tokens, span `roots of t^2-6t+5 are -1 and -5`. Excerpt: The provided partial solution contains an error in identifying the roots of the quadratic equation $f(t) = t^2 - 6t + 5$.  To find the roots of $t^2 - 6t + 5 = 0$, we can factor the quadratic: $(t - 1)(t - 5) = 0$ Setting each factor to zero gives $t = 1$ and $t = 5$. Thus, the roots are $1$ and $5$, not $-1$ and $-5$.  Since $1$ and $5$ are the roots of $f(t)$, by definition: $f(1) = 0$ $f(5) = 0$  Therefore: $f(1) + f(5) = 0 + 0 = 0$  Final answer: 0
- oracle: 158 tokens, span `roots of t^2-6t+5 are -1 and -5`. Excerpt: To find the roots of $f(t) = t^2 - 6t + 5$, we can factor the quadratic equation: $t^2 - 6t + 5 = (t - 1)(t - 5)$. Setting $f(t) = 0$, we find the roots are $t = 1$ and $t = 5$.  Since 1 and 5 are the roots of the function $f(t)$, by definition: $f(1) = 0$ $f(5) = 0$  Therefore, the sum is: $f(1) + f(5) = 0 + 0 = 0$.  Final answer: 0
- random: 274 tokens, span `Let f`. Excerpt: The partial solution contains an error in identifying the roots of the quadratic equation $f(t) = t^2 - 6t + 5$.  1.  **Recheck the flagged location and roots:**     The roots of $t^2 - 6t + 5 = 0$ are found by factoring:     $(t - 1)(t - 5) = 0$.     Thus, the roots are $t = 1$ and $t = 5$.     (The partial solution incorrectly stated the roots were $-1$ and $-5$).  2.  **Calculate $f(1)$ and $f(5)$:**     Since $1$ and $5$ are the roots of the function $f(t)$, by definition:     $f(1) = 1^2 - 6(1) + 5 = 1 - 6 + 5 = 0$.     $f(5) = 5^2 - 6(5) + 5 = 25 - 30 + 5 = 0$.  3.  **Find the sum:**     $f(1) + f(5) = 0 + 0 = 0$.  Final answer: 0

### `e159_code_boundary_zero_04` / `code_boundary_zero`

- localized: 341 tokens, span ``[0:5]` excludes both endpoints`. Excerpt: The partial solution provided is incorrect. Let's re-evaluate the Python slicing expressions.  1.  **Analyze `'abcde'[0:5]`**:     *   In Python, the slice `[start:stop]` includes the character at the `start` index and excludes the character at the `stop` index.     *   For `'abcde'[0:5]`, the indices are 0, 1, 2, 3, and 4.     *   The characters are `'a'`, `'b'`, `'c'`, `'d'`, and `'e'`.     *   The resulting string is `'abcde'`, and its length is `5`.  2.  **Analyze `'abcde'[1:4]`**:     *   The slice `[1:4]` includes indices 1, 2, and 3.     *   The characters are `'b'`, `'c'`, and `'d'`.     *   The resulting string is `'bcd'`, and its length is `3`.  3.  **Calculate the difference**:     *   `len('abcde'[0:5]) - len('abcde'[1:4])`     *   `5 - 3 = 2`  Wait, while the partial solution's logic about endpoints was wrong (it claimed `[0:5]` excludes both endpoints and has length 3), the final subtraction result it reached happened to be 2. However, the correct lengths are 5 and 3.  Calculation: $5 - 3 = 2$.  Final answer: 2
- oracle: 221 tokens, span ``[0:5]` excludes both endpoints`. Excerpt: The partial solution contains an error regarding how Python slicing works. In Python, a slice `[start:stop]` includes the character at the `start` index and excludes the character at the `stop` index.  1.  Evaluate `'abcde'[0:5]`: This slice starts at index 0 ('a') and goes up to, but does not include, index 5. Since the string has indices 0 through 4, this captures the entire string `'abcde'`. The length is 5. 2.  Evaluate `'abcde'[1:4]`: This slice starts at index 1 ('b') and goes up to, but does not include, index 4 ('e'). It captures characters at indices 1, 2, and 3, which are `'bcd'`. The length is 3. 3.  Calculate the difference: `len('abcde'[0:5]) - len('abcde'[1:4])` = `5 - 3 = 2`.  Final answer: 2
- random: 201 tokens, span `What does this Python expression evaluate`. Excerpt: The partial solution contains errors regarding how Python slicing works.  1.  **Rechecking the flagged span:** The expression `len('abcde'[0:5])` evaluates the slice from index 0 up to (but not including) index 5. For the string `'abcde'`, this includes indices 0, 1, 2, 3, and 4. Thus, `'abcde'[0:5]` is `'abcde'`, and its length is 5. 2.  **Evaluating the second part:** The expression `len('abcde'[1:4])` evaluates the slice from index 1 up to (but not including) index 4. This includes indices 1, 2, and 3. Thus, `'abcde'[1:4]` is `'bcd'`, and its length is 3. 3.  **Calculating the difference:** `5 - 3 = 2`.  Final answer: 2

### `e159_probability_conditioning_03` / `probability_conditioning`

- localized: 278 tokens, span `the other child has probability 1/2`. Excerpt: To recheck the step: "the other child has probability 1/2", we must look at the sample space. The possible outcomes for two children are $\{BB, BG, GB, GG\}$, each with probability $1/4$. The condition is "at least one child is a boy". This restricts the sample space to $S' = \{BB, BG, GB\}$. The event "both are boys" is $E = \{BB\}$. The probability is $P(E|S') = \frac{|E|}{|S'|} = \frac{1}{3}$.  The statement "the other child has probability 1/2" is a common misconception that treats the children as independent events without accounting for the specific condition "at least one". If we knew a *specific* child (e.g., the elder) was a boy, the probability the other is a boy would be $1/2$. However, given that *at least one* is a boy, we are choosing from the set $\{BB, BG, GB\}$, making the probability $1/3$.  Correcting the step: Given that at least one child is a boy, the possible configurations are BB, BG, and GB. Only one of these three equally likely outcomes results in both being boys.  Final answer: 1/3
- oracle: 87 tokens, span `the other child has probability 1/2`. Excerpt: To solve the problem, we identify the sample space of two children: {BB, BG, GB, GG}. The condition "at least one child is a boy" restricts the sample space to {BB, BG, GB}. Out of these three equally likely outcomes, only one outcome (BB) consists of two boys. Therefore, the probability is 1/3.  Final answer: 1/3
- random: 119 tokens, span `A family has two children`. Excerpt: The flagged span `A family has two children` is a correct statement of the problem's premise and is not abnormal.  Continuing the solution: The sample space for two children is $S = \{BB, BG, GB, GG\}$. The condition "at least one child is a boy" restricts the sample space to $S' = \{BB, BG, GB\}$. Out of these 3 equally likely outcomes, only 1 outcome ($BB$) consists of two boys. The probability is therefore $1/3$.  Final answer: 1/3

### `e159_proof_invalid_lemma_04` / `proof_invalid_lemma`

- localized: 237 tokens, span `12 and 3 are both multiples of 3`. Excerpt: To evaluate the claim "Every multiple of 12 is a multiple of 3," we examine the relationship between 12 and 3.  1.  **Analyze the step:** The flagged span says "12 and 3 are both multiples of 3."     *   $12 = 3 \times 4$ (True)     *   $3 = 3 \times 1$ (True)     The step is mathematically correct.  2.  **Verify the logic:**     *   A multiple of 12 can be written as $12n$ for some integer $n$.     *   Since $12 = 3 \times 4$, we can substitute this into the expression: $12n = (3 \times 4)n = 3(4n)$.     *   Since $4n$ is an integer, $3(4n)$ is by definition a multiple of 3.     *   Therefore, every multiple of 12 is indeed a multiple of 3.  The claim is true.  Final answer: Yes
- oracle: 150 tokens, span `12 and 3 are both multiples of 3`. Excerpt: To evaluate the claim "Every multiple of 12 is a multiple of 3," we examine the relationship between 12 and 3.  A number is a multiple of 12 if it can be written in the form $12n$ for some integer $n$. Since $12 = 3 \times 4$, we can rewrite any multiple of 12 as: $12n = (3 \times 4)n = 3(4n)$.  Since $4n$ is an integer, $3(4n)$ is by definition a multiple of 3. Therefore, every multiple of 12 is necessarily a multiple of 3.  Final answer: Yes
- random: 115 tokens, span `Claim`. Excerpt: The claim is "Every multiple of 12 is a multiple of 3." A multiple of 12 can be written as $12n$ for some integer $n$. Since $12 = 3 \times 4$, we can rewrite $12n$ as $3(4n)$. Since $4n$ is an integer, $3(4n)$ is by definition a multiple of 3. Therefore, every multiple of 12 is indeed a multiple of 3.  Final answer: Yes

### `e159_unit_roundtrip_02` / `unit_roundtrip`

- localized: 268 tokens, span `one third of the original 60`. Excerpt: The problem states that the value starts at 60 and increases by 50%. 1.  **Increase by 50%**: $60 + (0.50 \times 60) = 60 + 30 = 90$. 2.  **Decrease by one third**: The problem specifies that the *new value* (which is 90) decreases by one third.     *   One third of the new value is $\frac{1}{3} \times 90 = 30$.     *   The final value is $90 - 30 = 60$.  The partial solution flagged the phrase "one third of the original 60". While the numerical result of the subtraction (30) happens to be the same as one third of the original 60, the logic should be based on the *new value* (90).   Correcting the step: Increasing by 50% adds 30, resulting in 90. Then decreasing by one third subtracts one third of the new value (one third of 90), which is 30. $90 - 30 = 60$.  Final answer: 60
- oracle: 249 tokens, span `one third of the original 60`. Excerpt: The problem asks for the final value after a value of 60 increases by 50% and then decreases by one third.  1.  **Initial value:** 60 2.  **Increase by 50%:** $60 + (0.50 \times 60) = 60 + 30 = 90$. 3.  **Decrease by one third:** The decrease is applied to the *new* value (90), not the original value.     One third of 90 is $\frac{1}{3} \times 90 = 30$. 4.  **Final value:** $90 - 30 = 60$.  The partial solution incorrectly stated that the decrease was "one third of the original 60" (which would be 20), but the correct calculation is one third of the current value (90). Although the final result in the partial solution happened to be 60, the logic used to get there was flawed. Correcting the step: decreasing by one third subtracts one third of the current value 90.  Final answer: 60
- random: 323 tokens, span `A value starts at 60`. Excerpt: The partial solution contains an error in the second step.  1.  **Rechecking the flagged location:** "A value starts at 60." This is correct based on the problem statement. 2.  **Evaluating the subsequent steps:**     *   Increase by 50%: $60 + (0.50 \times 60) = 60 + 30 = 90$. (Correct)     *   Decrease by one third: The problem states "the **new value** decreases by one third." The new value is 90.     *   Calculation: $90 - (\frac{1}{3} \times 90) = 90 - 30 = 60$.  Wait, let's re-verify the partial solution's logic: "decreasing by one third subtracts one third of the original 60". This logic is incorrect; it should subtract one third of the *new* value (90). However, in this specific case, one third of 90 is 30, and one half of 60 is also 30.  Calculation: Start: 60 Increase 50%: $60 \times 1.5 = 90$ Decrease by 1/3: $90 \times (1 - 1/3) = 90 \times 2/3 = 60$  The final value is 60.  Final answer: 60

## Next Step / 下一步

- Proceed to harder multi-family tasks. / 应进入更复杂的 multi-family 题目。
- Random controls must avoid broad problem restatements. / random control 必须避免宽泛题干重述。
- Harder cases should make full restart expensive: long tables, long code, multi-hop geometry, proof validity, graph definitions with hidden constraints, and multi-condition aggregation. / 更难样本应让从头重算代价高：长表格、长代码、多跳几何、证明有效性、带隐含条件的图定义、多条件聚合。
- Use budget curves such as 128/256/512/1024 completion tokens. / 使用 128/256/512/1024 completion-token 预算曲线。
