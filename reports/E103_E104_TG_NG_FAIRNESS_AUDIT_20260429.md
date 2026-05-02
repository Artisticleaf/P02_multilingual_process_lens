# E103-E104 TG/NG Fairness Audit / thinking 与 non-thinking 公平对照（2026-04-29）

## 说人话结论

这轮不是大规模自然发生率实验，而是 Qwen3.5-27B 的小样本公平对照。它回答一个具体问题：`thinking generation` 是否在当前 hard-task 设置下明显优于 `non-thinking generation`。

答案很明确：**没有。按 strict final-decision 口径，TG 反而是 0/9；它的主要失败不是数学链条完全不会，而是 4096 token 内全部不收口、没有明确最终答案行。**

如果用 fallback 从长思考文本里抽最后出现的数字，TG 看起来有 5/9 正确；但这些都是未完成 trace 中出现过正确数字，不是模型明确提交的 final decision。论文主表不能把这类 fallback 当作 strict correctness。

## 设置

- Model / 模型：`qwen35_27b`
- Tasks / 任务：`aime25_base_divisor_p1`、`aime25_integer_pairs_quad_p4`、`aime25_trapezoid_incircle_p6`
- Prompt variants / prompt 变体：`neutral`、`self_check`、`answer_first_no_gold`
- k：每格 1 条
- max_new_tokens：4096
- batch_size：2
- batch max_time：600 秒
- 泄露审计：prompt 不含 gold answer，不含 trap note；gold 只用于离线判分。

三种模式：

- `NG_baseline`：non-thinking，沿用 E49 direct-generation sampling。
- `NG_matched_sampling`：non-thinking，但使用 Qwen thinking 推荐采样参数，用来隔离 sampling confound。
- `TG_official`：thinking，使用 E91 记录的 Qwen thinking 参数；HF generate 不支持官方 `presence_penalty`，此限制记入边界。

## E103 结果

| mode | n | strict final correct | fallback correct | explicit final marker | hit max | mean tokens |
|---|---:|---:|---:|---:|---:|---:|
| NG_baseline | 9 | 8/9 | 8/9 | 9/9 | 2/9 | 2214.7 |
| NG_matched_sampling | 9 | 7/9 | 7/9 | 9/9 | 4/9 | 2735.9 |
| TG_official | 9 | 0/9 | 5/9 | 0/9 | 9/9 | 4096.0 |

Wilson 95% CI：

- `NG_baseline strict`: 8/9 = 0.889, CI [0.565, 0.980]
- `NG_matched strict`: 7/9 = 0.778, CI [0.453, 0.937]
- `TG strict`: 0/9 = 0.000, CI [0.000, 0.299]
- `TG fallback`: 5/9 = 0.556, CI [0.267, 0.811]
- `TG hit-max`: 9/9 = 1.000, CI [0.701, 1.000]

## E104 人工审计

E104 只审计 E103 中 strict 或 fallback final-correct 的 20 条 trace。

| mode | audited rows | strict-valid | repaired strict ACPI | unrepaired ACPI | unfinished TG |
|---|---:|---:|---:|---:|---:|
| NG_baseline | 8 | 6 | 2 | 0 | 0 |
| NG_matched_sampling | 7 | 6 | 1 | 0 | 0 |
| TG_official | 5 | 0 | 0 | 0 | 5 |

关键人工事实：

- NG 的 `neutral` / `self_check` 正确 trace 基本过程有效。
- NG 的 `answer_first_no_gold` 出现 3 条 repaired strict ACPI：开头先写错 `Final answer`，后面推理纠正到正确答案。
- TG 的 5 条 fallback-correct 都没有 explicit final marker，且全部 hit 4096 token 上限；它们不是 strict final decision，也不计入 strict ACPI。

## 解释

1. **TG 没有表现出正确率优势。**  
   在 strict final-decision 口径下，TG 是 0/9，而 NG 是 8/9 或 7/9。这个差异主要来自 TG 不收口，不是简单“答案不会”。

2. **fallback extraction 会高估 TG。**  
   TG 长 trace 中可能多次出现正确数字，但模型没有明确提交最终答案。如果把这种数字抽取当正确率，会把“想到了正确数”误当成“完成了可采纳解答”。

3. **answer-first prompt 本身会诱发 repaired ACPI。**  
   有些 NG trace 先写错 final answer，再通过后续推理改正。按 strict any-wrong-step policy，这是 ACPI；按 repair-aware policy，可以视为草稿式自我修复。

4. **采样参数不是全部原因。**  
   `NG_matched_sampling` 用了 thinking 推荐采样参数，确实比 `NG_baseline` 更容易 hit-max、更低 strict correct；但它仍然 9/9 有 explicit final marker。TG 的 0/9 final marker 是更强的收口失败。

## 边界

- E103 是 Qwen 小样本诊断，不是自然发生率主表。
- 当前只覆盖 3 道 hard tasks、3 个 prompt variants、每格 k=1。
- TG 使用 HF generate；官方 Qwen thinking sampling 中的 `presence_penalty` 在当前 HF 接口下没有直接等价实现。
- 本轮还没有保存 TG generation-time hidden states；机制问题留给 E106。

## 下一步建议

先做 E105，不要直接扩展到所有 P0。E105 应该比较 `free_think`、`budgeted_think`、`deliberate_then_final` 三种 TG 收口策略，核心指标是 explicit final marker、hit-max、strict correctness、fallback correctness、以及 repaired/unrepaired ACPI。只有当 TG 能稳定收口后，再把 TG/NG hidden residual、MLP、token-mixer 对照推进到 E106。
