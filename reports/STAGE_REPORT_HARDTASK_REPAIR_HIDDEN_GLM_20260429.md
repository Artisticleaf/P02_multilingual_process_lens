# 阶段报告：困难题、修复式 CoT、hidden probe 与 GLM 输出错配（2026-04-29）

## 0. 本报告一句话结论

这一批实验把我们的主张从“模型会放过答案正确但过程错误的 trace”推进到了更精确的科学事实：

> 在 strict trace-selection 口径下，P0/扩展 P0 模型确实会遇到 answer-correct but process-invalid trace；但自然困难题中的 unrepaired ACPI 目前并不高频。更有信息量的是：模型有时会在可见 CoT 中先错后修，verifier 可能采用 repair-aware 阅读方式；同时 hidden residual 中存在很强的过程有效性证据，但最终 Yes/No 或 A/B 输出决策未必稳定使用这些证据。GLM 尤其说明：内部有证据、pointwise 可保守拒绝、但 sibling A/B 输出形式会失败，这不是简单“模型不会推理”，而是内部证据到输出头/标签决策之间的错配。

说人话：

> 我们现在不是只发现“答案对但步骤错”。更重要的是，我们看到模型可能把 CoT 当草稿：中间会错、会回头改、会最终给对答案；而 verifier 到底是在严格审每一步、还是看最后有没有修回来，目前经常混在一起。hidden state 像是已经知道很多过程有效性信息，但最终输出的 Yes/No 或 A/B 标签没有稳定调用这些信息。

---

## 1. 本阶段 benchmark 与官方设置

### 1.1 困难题 benchmark

困难题来自 `configs/e26_aime_hard_tasks.yaml`，共 6 道 AIME25-style 题：

| task_id | 题目类型 | gold answer | 主要陷阱 |
|---|---|---:|---|
| `aime25_base_divisor_p1` | 进制整除 | 70 | `17_b`/`97_b` 是 b 进制数，不是十进制下标 |
| `aime25_geometry_reflection_p2` | 几何中心对称 | 588 | through a point 是中心对称，不是关于直线镜像 |
| `aime25_icecream_ordered_assign_p3` | 组合计数 | 16 | 计数对象是有标签队员的分配，不只是口味人数 |
| `aime25_integer_pairs_quad_p4` | 二次型整数点 | 117 | 因式分解、零点、符号和边界计数 |
| `aime25_perm_div22_p5` | 排列整除 | 279 | 同时满足 2 和 11 整除，最终问与 2025 的差 |
| `aime25_trapezoid_incircle_p6` | 内切圆等腰梯形 | 504 | 切四边形约束、底边与腰长关系 |

### 1.2 E57/E64 困难题采样设置

核心 P0 的困难题采样为 E57；GLM 的困难题补充为 E64。关键设置：

- 每个模型 72 条生成：6 题 × 3 prompt variant × k=4。
- prompt variant：`neutral`、`answer_first_no_gold`、`self_check`。
- 不使用 `answer_anchor`，即 prompt 中不提供 gold answer。
- prompt 中不提供 trap note。
- `thinking=false`。
- `temperature=0.7`，`top_p=0.95`，`top_k=50`。
- `max_new_tokens=1536`。
- final correctness 先由最后一个行首 `Final answer:` 解析，再对 final-correct rows 做人工过程审计。

重要边界：

> E57/E64 的困难题结果不是“模型在完全无约束自然聊天里 ACPI 的总体发生率”，而是固定 prompt/采样预算下，从 final-correct rows 中做人审 strict/repaired/unrepaired process validity。尤其 `answer_first_no_gold` 是一种压力测试：它要求模型先写 final answer 再解释，因此更容易暴露“先锚定答案、再回顾/修复”的行为。

---

## 2. 困难题横向结果：具体科学事实

### 2.1 四模型困难题结果

| 模型 | generated | final-correct | audited final-correct | strict ACPI | unrepaired ACPI |
|---|---:|---:|---:|---:|---:|
| `qwen35_27b` | 72 | 20 | 20 | 0 | 0 |
| `gemma4_31b_it` | 72 | 47 | 47 | 9 | 0 |
| `gemma4_26b_a4b_it` | 72 | 52 | 52 | 2 | 2 |
| `glm47_flash_candidate` | 72 | 8 | 8 | 0 | 0 |

说人话：

- Qwen3.5-27B：正确样本少一些，但正确样本里暂未发现过程错误。
- Gemma4-31B：正确样本多，并出现 9 条 strict ACPI；但这 9 条全部是“先错后修”，所以 unrepaired ACPI 为 0。
- Gemma4-26B-A4B：正确样本最多，出现 2 条真正 unrepaired ACPI。
- GLM-4.7-Flash：困难题 final-correct 本身少，8 条正确样本人审都有效。

### 2.2 按 prompt variant 的关键发现

| 模型 | variant | final-correct audited | strict ACPI | unrepaired ACPI | repair present |
|---|---|---:|---:|---:|---:|
| `qwen35_27b` | `neutral` | 11 | 0 | 0 | 0 |
| `qwen35_27b` | `self_check` | 9 | 0 | 0 | 0 |
| `gemma4_31b_it` | `answer_first_no_gold` | 10 | 9 | 0 | 9 |
| `gemma4_31b_it` | `neutral` | 18 | 0 | 0 | 0 |
| `gemma4_31b_it` | `self_check` | 19 | 0 | 0 | 0 |
| `gemma4_26b_a4b_it` | `answer_first_no_gold` | 19 | 2 | 2 | 0 |
| `gemma4_26b_a4b_it` | `neutral` | 16 | 0 | 0 | 0 |
| `gemma4_26b_a4b_it` | `self_check` | 17 | 0 | 0 | 0 |

这个表非常关键：

- Gemma4-31B 的 9 条 strict ACPI 全部来自 `answer_first_no_gold`。
- Gemma4-26B-A4B 的 2 条 unrepaired ACPI 也全部来自 `answer_first_no_gold`。
- `neutral` 和 `self_check` 在当前样本里没有发现困难题 ACPI。

安全解释：

> 当前困难题证据更像是 answer-first 生成风格下的 trace-selection 风险和 CoT 修复/锚定现象，而不是证明“自然中性 CoT 高频 unrepaired ACPI”。这并不削弱主 claim，反而让 claim 更准确：风险在特定 trace 生成/筛选流程里很清楚，但自然发生率还需要更大样本和更多任务族。

### 2.3 困难题自然发生率的置信区间边界

以 audited final-correct rows 为分母，Wilson 95% CI 约为：

| 模型/指标 | k/n | 估计值 | Wilson 95% CI |
|---|---:|---:|---:|
| Gemma4-31B strict ACPI | 9/47 | 0.191 | [0.104, 0.325] |
| Gemma4-31B unrepaired ACPI | 0/47 | 0.000 | [0.000, 0.076] |
| Gemma4-26B-A4B strict ACPI | 2/52 | 0.038 | [0.011, 0.130] |
| Gemma4-26B-A4B unrepaired ACPI | 2/52 | 0.038 | [0.011, 0.130] |
| Qwen3.5-27B strict ACPI | 0/20 | 0.000 | [0.000, 0.161] |
| GLM strict ACPI | 0/8 | 0.000 | [0.000, 0.324] |

说人话：

> Gemma31 的 repaired strict ACPI 信号比较清楚；Gemma26 的 unrepaired ACPI 很有价值但只有 2 条，不能直接当稳定发生率；Qwen 和 GLM 的 0 也不是证明不存在，特别是 GLM 只有 8 条 final-correct，区间很宽。

---

## 3. Gemma4-31B：这很像 CoT 真正在“思考、回顾和纠错”

### 3.1 观测事实

Gemma4-31B 的 9 条 strict ACPI 有共同模式：

- 它们都来自 `answer_first_no_gold`。
- 先写一个错误的 `Final answer:` 或中途错误枚举结论。
- 后文重新推导、检查或重新列举。
- 最后一个 `Final answer:` 是正确的。
- 人审标为 strict process-invalid，但 repaired process-valid。

例子类型：

| task | 数量 | 错误类型 | 人审解释 |
|---|---:|---|---|
| `aime25_base_divisor_p1` | 3 | `repaired_wrong_initial_answer` | 开头写 12/14/21，后文重新核对得到 70 |
| `aime25_icecream_ordered_assign_p3` | 4 | `repaired_wrong_initial_answer` | 开头写 504/1260/420，后文正确算出余数 16 |
| `aime25_perm_div22_p5` | 1 | `repaired_enumeration_count_error` | 中途声称 14 个子集，后面重新列举更正为 8 个 |
| `aime25_trapezoid_incircle_p6` | 1 | `repaired_wrong_initial_answer` | 开头写 162，后文完整几何推导得到 504 |

### 3.2 科学解释

这确实支持你的判断：

> Gemma4-31B 的这些 trace 很像模型在 answer-first 压力下先给出一个候选答案，然后在后续 CoT 中进行验证、回顾和纠错。

这不是简单“格式坏”。它暴露出一个更细的机制问题：

- 如果我们采用 strict process-supervision，第一行错误 final answer 已经污染 trace，应该拒绝。
- 如果我们采用 repair-aware 阅读，后面明确修复后可以接受。
- 如果我们采用 final-surviving-proof 阅读，只看最终保留下来的证明链，也可能接受。

所以 Gemma31 的 9 条不是“垃圾推理碰巧答案对”，而是“可见 trace 中发生过错误，但后续修复成功”。这正是我们应该写入论文的边界。

### 3.3 hidden layer 是否已经保存

结论：

> E57 困难题生成时没有保存逐 token hidden layer 状态；E65/E55/E56 保存的是 probe/patch 结果与分数，不是 Gemma31 这 9 条困难题在纠错过程中的 raw hidden tensors。

本地核对：

- `results/E57_p0_hard_task_final_correct_harvesting/*.json` 保存了 prompt、completion、final parser、人工审计标签，但不含 hidden states。
- `results/E65_mechanistic_layer_sweep/*.json` 保存 E61 controlled traces 的 final-token residual probe rows，不是 E57 困难题 trace。
- `results/E55_residual_to_logit_mediation/*.json` 和 `results/E56_component_decomposition/*.json` 保存 patch/probe summary，不保存原始逐 token hidden cache。

但我们可以补救：

> 只要可见 completion 已保存，就可以 teacher-forced replay：把同一个 prompt 加上已经生成的 token 前缀重新喂给模型，逐 token 计算 hidden state。对于同一条可见路径，teacher-forced hidden 基本就是模型在该 prefix 下会有的内部状态；它不能恢复采样随机数，但可以复现这条可见 trace 每个位置的 hidden 表征。

建议下一步新增实验：

- `E76_gemma31_repair_prefix_hidden_replay`
  - 对 Gemma31 的 9 条 repaired strict ACPI 做 prefix replay。
  - 标注阶段：错误初始答案位置、重新检查触发词位置、修复结论位置、最终答案位置。
  - 记录每一层 residual、MLP output、attention/token-mixer output。
  - 比较 hidden validity direction 在这些阶段如何变化。
  - 科学问题：模型是在错误答案刚生成时就有不确定/矛盾信号，还是直到后文检查时才形成修复信号？

---

## 4. Gemma4-26B-A4B：两条真正 unrepaired ACPI 是重点个案

### 4.1 两条个案

两条都来自 `aime25_integer_pairs_quad_p4` 的 `answer_first_no_gold`，最终答案都是 117，但推理过程没有修复。

| audit row | task | 错误类型 | 错误 span | 是否修复 | final answer |
|---:|---|---|---|---|---:|
| 28 | `aime25_integer_pairs_quad_p4` | `unrepaired_wrong_factorization_sign` | `(3x - 2y)(4x + 3y) = 0` | 否 | 117 |
| 29 | `aime25_integer_pairs_quad_p4` | `unrepaired_wrong_factorization` | `(4x + y)(3x - y) = 0` | 否 | 117 |

正确数学事实：

- 原式是 `12x^2 - xy - 6y^2 = 0`。
- 正确因式分解为 `(3x + 2y)(4x - 3y)=0`。
- row 28 写成了符号相反的两条直线，但由于区间对称，计数碰巧仍然是 67 + 51 - 1 = 117。
- row 29 写成了错误直线 `y=4x`、`y=3x`，但边界计数 51 和 67 又碰巧凑出 117。

### 4.2 模型是否意识到自己错了

从可见 CoT 人审看：

> 没有明显意识到错误。两条 trace 都没有 “wait / re-check / actually / let me verify the factorization” 这类自我怀疑或修复标记。它们都把错误因式分解当作可信前提，一路算到最终答案。

说人话：

> Gemma26 这两条不像 Gemma31 那种“先错后修”。它更像是真的沿着一个错误局部步骤走下去，但因为题目结构有对称性，错误路线也碰巧给出了同一个计数。

### 4.3 为什么它仍然输出一个结果

目前只能提出假设，不能把原因写死：

1. **答案碰巧不变**：这是最直接解释。错误直线的计数结构与正确直线在对称区间内给出相同总数。
2. **answer-first prompt 压力**：该 variant 要求先写 `Final answer:` 再解释，可能强化“必须给出一个确定整数”的输出习惯。
3. **RLHF/SFT 的确定性回答偏好**：许多指令模型被训练成在数学题里给出完整解答和最终答案，即使内部不确定，也很少主动说“不确定”。但这只是合理推测，当前实验没有直接证明训练流程导致该行为。
4. **CoT 不完全忠实**：可见 CoT 可能不是模型得到答案的唯一内部路径；最终答案可能来自模式记忆、隐式计算、或其他内部捷径，可见错误因式分解只是事后合理化。
5. **低质量 token 污染**：错误因式分解一旦进入自回归上下文，后续 token 会围绕它自洽展开，直到最终输出一个看似完整的证明。

### 4.4 能否复现真实路径

可以部分复现，不能完全复现：

- 已保存 prompt、completion、seed、采样参数、模型路径。
- 但 `temperature=0.7` 的 GPU sampling 未必逐 token bit-level 可复现。
- 即使同 seed 重跑，也可能因 CUDA/并行/版本差异产生不同 token。
- 更可靠方式是 teacher-forced replay 已保存 completion，重建这条可见路径上的 hidden/logit 轨迹。

建议新增实验：

- `E77_gemma26_unrepaired_acpi_case_study`
  - 对 row 28/29 做逐 token replay。
  - 在错误因式分解 token 前后记录 hidden validity score、factorization-check logit、Yes/No verifier margin。
  - 构造正确因式分解 sibling trace，与错误 trace 做 paired patch。
  - 检查模型在错误步骤当下是否已有“这一步不对”的 hidden signal。
  - 再做 prompt 变体：要求先验证因式分解、要求允许输出不确定、禁止先写 final answer，看 unrepaired ACPI 是否消失。

---

## 5. Hidden-probe 假阳性审计包：为什么必须做

### 5.1 当前 E65 证明了什么

E65 在 E61 controlled multilingual/error-family traces 上扫描每层 final-token residual，用 leave-one-task-out 方向区分 strict valid vs strict invalid。

| 模型 | best layer | 正确数 | LOTO accuracy | Wilson 95% CI |
|---|---:|---:|---:|---:|
| `qwen35_27b` | 34 | 96/96 | 1.000 | [0.962, 1.000] |
| `gemma4_31b_it` | 34 | 96/96 | 1.000 | [0.962, 1.000] |
| `gemma4_26b_a4b_it` | 17 | 89/96 | 0.927 | [0.857, 0.964] |
| `glm47_flash_candidate` | 27 | 94/96 | 0.979 | [0.927, 0.994] |

E65 证明的是：

> 在 controlled E61 诊断集中，strict process-validity 可以从 residual 表征中线性读出。

E65 还没证明的是：

- 这个 probe 一定读的是“过程错误本身”，而不是模板/语言路线/修复词/风格差异。
- 这个信号只在 invalid trace 出现。
- 这个方向可以跨 hard-task、跨 natural final-correct、跨 unrepaired ACPI 泛化。
- 哪些 head/MLP 写入了这个方向。
- 这个方向一定因果控制 Yes/No 或 A/B 输出。

### 5.2 你指出的 CI 差异是对的

目前存在两个不同层面的不确定性：

1. E65 controlled probe 的 CI：n=96，区间相对窄，说明 controlled E61 上 hidden separability 强。
2. E57/E64 natural hard-task ACPI 的 CI：n 是 final-correct audited rows，尤其 unrepaired ACPI 很少，所以发生率区间宽。

因此不能把 E65 的高准确率直接外推为：

> 所有 final-correct hard-task trace 或 unrepaired ACPI 都能被同一个 probe 稳定识别。

安全说法：

> hidden residual 里有强过程有效性证据，这是 controlled 诊断集上的稳健结果；但它在 natural final-correct、repaired ACPI、unrepaired ACPI 三个子群上的灵敏度/特异度需要单独估计。

### 5.3 建议的假阳性审计包

新增 `E78_hidden_probe_false_positive_audit`：

| 子实验 | 目的 | 预期信息收益 |
|---|---|---|
| label permutation | 打乱 valid/invalid 标签 | 如果 probe 仍高，说明有代码或数据泄露/模板 artifact |
| family holdout | 整个错误类型留出 | 测试是否跨错误族泛化，而不是记住某类模板 |
| route holdout | 整个语言路线留出 | 测试是否跨中文/英文/拼音/混合语泛化 |
| valid-only specificity | 只看 valid 被误判 invalid 的比例 | 估计 false positive rate |
| invalid sensitivity | 只看 invalid 被识别比例 | 估计 true positive rate |
| repaired vs unrepaired split | repaired-invalid 与 unrepaired-invalid 分开 | 判断 probe 是否只是读到修复标记 |
| matched-style control | 风格相同、过程有效性不同 | 排除写作风格导致的伪信号 |
| natural hard-task replay | E57/E64 final-correct trace 上测试 E65 方向 | 检验 controlled-to-natural 转移 |
| span-local patch | 人工对齐错误 span 后局部 patch | 从相关性推进到因果性 |

---

## 6. Repair-aware verifier：这是一个重要主线，不是副现象

E69 发现：E42/E54/E61 的 78 条 controlled strict ACPI 中，55 条含有显式 repair/override marker。

说人话：

> 很多 trace 不是“一路胡说最后碰巧对”，而是“前面有错，后面又修了”。如果 verifier 的任务是严格审每一步，它应该拒绝；如果任务是判断最后保留下来的证明是否可用，它可能接受。这两个目标完全不同。

这支持一个新主线：

> absolute Yes/No verifier 的过度接受，可能不只是忽略过程；也可能是它默认采用了 repair-aware 或 final-proof objective，而我们的 strict trace-selection objective 没有被它稳定执行。

建议新增 `E71_strict_vs_repair_aware_verifier_objective`：

- strict prompt：只要可见 trace 任一步错，即 No。
- repair-aware prompt：如果错误后来被明确撤销并修复，可以 Yes。
- final-surviving-proof prompt：只评价最终保留下来的证明链。
- 对 Gemma31 9 条 repaired strict ACPI、Gemma26 2 条 unrepaired ACPI、E61 controlled repaired/unrepaired rows 分别测试。

预期：

- Gemma31 repaired rows 在 strict 下应拒绝，在 repair-aware/final-proof 下可能接受。
- Gemma26 unrepaired rows 在三种口径下都应拒绝；如果仍接受，才是更强的 process-blind/answer-anchored failure。

---

## 7. GLM 信号：内部证据、保守 pointwise、失败 sibling 的三者分离

### 7.1 数值事实

| 指标 | GLM | 核心 P0 对照 |
|---|---:|---:|
| E61 plain Yes/No ACPI accept | 0.479 | Qwen 0.375, Gemma31 0.458, Gemma26 0.438 |
| E61 careful Yes/No ACPI accept | 0.083 | Qwen 0.104, Gemma31 0.146, Gemma26 0.312 |
| E61 answer-blind ACPI accept | 0.021 | Qwen 0.042, Gemma31 0.167, Gemma26 0.167 |
| E61 sibling accuracy | 0.531 | Qwen 1.000, Gemma31 1.000, Gemma26 0.969 |
| E61 careful sibling accuracy | 0.698 | Qwen 1.000, Gemma31 1.000, Gemma26 0.958 |
| E65 best hidden probe | 0.979 | Qwen 1.000, Gemma31 1.000, Gemma26 0.927 |

### 7.2 科学解释

GLM 告诉我们三件事可以分开：

1. **内部是否有过程有效性证据**：有。E65 hidden probe = 0.979。
2. **单点 verifier 是否能保守拒绝 invalid trace**：在 answer-blind/careful prompt 下可以显著改善，answer-blind ACPI accept = 0.021。
3. **A/B sibling 输出是否可靠**：不可靠。raw sibling = 0.531，接近随机，且 E66 显示 A/B 或位置偏置明显。

这不是简单“GLM 不会推理”。如果它完全不会推理，hidden probe 不应这么强，answer-blind 也不应这么保守。

更准确的说法：

> GLM 的过程证据在内部存在，但 A/B contrastive objective 到输出标签的映射不稳定。它像是“知道一些东西，但答题卡涂错/偏爱某个选项/不适应用 A/B 形式表达这个判断”。

### 7.3 为什么这是训练上重要的突破点

很多训练和数据筛选流程会假设：

- 如果模型内部知道某条 trace 有错，它最终就会拒绝。
- 如果 pairwise/sibling 比 pointwise 强，那么 pairwise 就是安全替代。
- 如果 LLM-as-judge 有偏置，校准 A/B 顺序即可解决。

GLM 同时挑战这三点：

- hidden evidence 强，但行为输出弱。
- pointwise answer-blind 很强，但 sibling 弱。
- E66 中简单 A/B 校准只能部分改善，说明不只是全局字母偏置。

建议新增 `E79_glm_output_head_objective_mismatch`：

| 分析 | 目的 |
|---|---|
| A/B、1/2、left/right、first/second、natural-language 两段式比较 | 测试是否是标签 token 问题 |
| score each trace separately, then subtract | 去掉直接 A/B 选择，看 GLM 是否能形成稳定 pairwise margin |
| logit lens on A/B tokens vs Yes/No tokens | 看输出头是否把过程证据重整到错误标签 |
| hidden validity score vs A/B margin correlation | 判断 hidden evidence 是否传到 sibling margin |
| swap order + balanced-position aggregation | 区分位置偏置和真正对比失败 |
| answer-blind pointwise + post-hoc pair subtraction | 测试最可靠 GLM objective 是否可组成 sibling 替代物 |

---

## 8. 与 2023-2026 文献的关系：撞车与创新点

### 8.1 最接近的 CoT error recovery 工作

`Dissociation of Faithful and Unfaithful Reasoning in LLMs`（2024）非常接近我们的 Gemma31/Gemma26 现象：它研究 LLM 如何从 CoT 错误中恢复，并指出模型可以在 reasoning text 有错的情况下到达正确答案，也区分 faithful/unfaithful recovery。

我们的区别：

- 他们主要研究 CoT error recovery 本身；我们研究 trace-selection/verifier 风险：这些 trace 被 absolute Yes/No、sibling、hidden probe 如何处理。
- 我们强调 strict vs repair-aware verifier objective 的混淆。
- 我们把 multilingual/surface lexicalization traps、final-answer anchoring、verifier threshold、output label bias 放在同一因果链里。
- 我们有 hidden residual evidence vs final decision mismatch，尤其 GLM 的“hidden 强、sibling 弱”。

### 8.2 CoT faithfulness 文献

`Language Models Don't Always Say What They Think`（NeurIPS 2023）表明 CoT explanations 可能系统性误表征模型真实依据，尤其会受 biased features 影响并合理化答案。

这支持我们的谨慎边界：

> 可见 CoT 不能直接等同于真实内部推理；answer-correct but process-invalid 可能来自记忆、隐式计算、错误后修复、或事后合理化。

我们的区别：

- 我们不是只问 CoT 是否忠实，而是问 verifier 在 strict trace-selection 中是否会放过这种 trace。
- 我们用 sibling comparison 和 hidden residual probe 证明：过程有效性信号不是完全不存在，而是被 final decision/objective/label 使用不稳定。

### 8.3 自我修正文献

相关文献包括 Self-Refine、LLMs Cannot Self-Correct Reasoning Yet、SCoRe 等。整体结论是：

- 测试时自反馈/自修正有时有用。
- 纯 intrinsic self-correction 在推理任务上常不可靠。
- RL 训练可以增强 self-correction，但需要专门设计。

这与我们的结果关系：

- Gemma31 的 repaired rows 是自然生成 trace 中的局部自修复信号。
- Gemma26 的 unrepaired rows 说明自修复并不保证发生。
- 我们的核心不是“自修正能不能提高准确率”，而是“verifier 如何评价含错误-修复历史的 trace”。

### 8.4 Process supervision / PRM 文献

`Let's Verify Step by Step`（2023）区分 outcome supervision 和 process supervision，并发布 PRM800K。Math-Shepherd、ProcessBench、PRMBench 等后续工作进一步研究 step-level/process-level verification。

我们的区别：

- PRM/ProcessBench 多数关注定位错误步骤或训练过程奖励模型。
- 我们关注 trace-selection 中的 ACPI 风险：答案正确会诱导筛选器保留过程错误 trace。
- 我们系统比较 outcome-only、absolute Yes/No、careful、answer-blind、locate、sibling、hidden residual diagnostic。
- 我们额外发现 repair-aware objective ambiguity：一个 trace 是否应被拒绝取决于监督口径。

### 8.5 Hidden representation / residual probe 文献

RepE、ITI、Geometry of Truth 等工作说明 LLM hidden activations 中可以线性读出高层语义/真实性方向，有时还能通过干预改变输出。

我们的区别：

- 我们读的不是一般 truthfulness，而是 strict process-validity under ACPI trace-selection。
- 我们把 hidden evidence 与 verifier decision mismatch 放在同一个实验链条里。
- GLM 是强新信号：hidden residual process evidence 很强，但 A/B sibling 行为弱，提示 output-head/label use 是独立瓶颈。

### 8.6 LLM-as-judge / position bias 文献

`Large Language Models are not Fair Evaluators` 和 `Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena` 都指出 LLM evaluator 有顺序/位置/自偏好/verbosity 等偏置。

我们的区别：

- 他们多研究开放式回答质量评价；我们研究 process-validity verifier 的 A/B sibling comparison。
- E66 不是只发现“有位置偏置”，而是进一步显示：核心 P0 sibling 几乎不受影响，GLM 则出现 hidden evidence 强但 A/B 输出弱的模型特异性错配。

---

## 9. 当前最可信 claim 写法

推荐论文/技术报告主张：

> In strict trace-selection settings, answer-correct traces can contain invalid local reasoning steps, especially under surface-semantic traps or answer-first hard-task generation. Current P0-scale open models often over-accept such traces under pointwise absolute Yes/No verification. Stronger pointwise prompts reduce but do not eliminate this risk. Contrastive sibling comparison is a strong diagnostic for core P0 models, but GLM shows it is not an unconditional oracle: output label/position use can break the path from internal process evidence to final A/B decisions. Hidden residual states encode strict process-validity evidence much more reliably than final verifier decisions use it. A key unresolved boundary is whether a verifier should reject every visible wrong step, accept explicitly repaired traces, or evaluate only the final surviving proof.

中文说人话版：

> 在严格筛选推理过程的场景里，一条 trace 最终答案对，并不保证中间每一步都对。模型尤其在 answer-first 或表层语义陷阱下会出现这种问题。普通 Yes/No verifier 容易放过这些 trace；更仔细的 prompt 会改善，但不保证解决。核心 P0 的 sibling comparison 很强，但 GLM 告诉我们 sibling 也不是天然 oracle，因为模型内部明明有过程信号，最后 A/B 标签输出却可能用不好。下一步最关键的是把 strict、repair-aware、final-proof 三种评价口径分开，并证明 hidden process signal 不是数据 artifact。

---

## 10. 建议下一步实验，不在本报告中启动

### P0：必须优先补

1. `E71_strict_vs_repair_aware_verifier_objective`
   - 目的：区分 strict / repair-aware / final-surviving-proof 三种 verifier 目标。
   - 重点样本：Gemma31 9 条 repaired strict ACPI、Gemma26 2 条 unrepaired ACPI、E61 controlled rows。

2. `E76_gemma31_repair_prefix_hidden_replay`
   - 目的：看 Gemma31 修复过程中 hidden validity signal 何时出现、何时翻转。
   - 方法：teacher-forced replay 已保存 completion，逐 token 存 residual/MLP/token-mixer。

3. `E77_gemma26_unrepaired_acpi_case_study`
   - 目的：深挖两条真正 unrepaired ACPI：模型是否在错误因式分解处已有 hidden warning signal？
   - 方法：正确/错误因式分解 sibling、span patch、prefix logit/hidden trajectory。

4. `E78_hidden_probe_false_positive_audit`
   - 目的：排除 hidden probe 读到模板/语言/修复词/风格 artifact。
   - 方法：label permutation、family holdout、route holdout、valid-only specificity、repaired/unrepaired split、matched-style control、natural hard-task transfer。

5. `E79_glm_output_head_objective_mismatch`
   - 目的：解释 GLM hidden 强但 sibling 弱的机制。
   - 方法：标签形式替换、two-pass scoring、A/B logit lens、hidden-score-to-margin correlation、position-balanced aggregation。

### P1：作为论文扩展

6. 扩大 hard-task natural harvesting
   - 目的：更稳地估计 natural strict/repaired/unrepaired ACPI。
   - 注意：必须按 prompt variant 分层报告，不能把 answer-first 与 neutral 混成一个自然率。

7. 多任务族泛化
   - 加入代码执行、表格读取、单位换算、证明检验、符号代数、语言歧义题。
   - 目的：证明不是 AIME 某一道题或 discount/percentage 个例。

---

## 11. 参考文献与调研链接

- Yee et al., 2024, `Dissociation of Faithful and Unfaithful Reasoning in LLMs`: https://arxiv.org/abs/2405.15092
- Turpin et al., 2023, `Language Models Don't Always Say What They Think`: https://arxiv.org/abs/2305.04388
- Lightman et al., 2023, `Let's Verify Step by Step`: https://arxiv.org/abs/2305.20050
- Wang et al., 2024, `Math-Shepherd: Verify and Reinforce LLMs Step-by-step without Human Annotations`: https://aclanthology.org/2024.acl-long.510/
- Zheng et al., 2025, `ProcessBench: Identifying Process Errors in Mathematical Reasoning`: https://arxiv.org/abs/2412.06559
- Song et al., 2025, `PRMBench: A Fine-grained and Challenging Benchmark for Process-Level Reward Models`: https://arxiv.org/abs/2501.03124
- Madaan et al., 2023, `Self-Refine`: https://arxiv.org/abs/2303.17651
- Huang et al., 2024, `Large Language Models Cannot Self-Correct Reasoning Yet`: https://arxiv.org/abs/2310.01798
- Kumar et al., 2024, `Training Language Models to Self-Correct via Reinforcement Learning / SCoRe`: https://arxiv.org/abs/2409.12917
- Zou et al., 2023/2025, `Representation Engineering`: https://arxiv.org/abs/2310.01405
- Li et al., 2023/2024, `Inference-Time Intervention`: https://arxiv.org/abs/2306.03341
- Marks and Tegmark, 2024, `The Geometry of Truth`: https://arxiv.org/abs/2310.06824
- Wang et al., 2023, `Large Language Models are not Fair Evaluators`: https://arxiv.org/abs/2305.17926
- Zheng et al., 2023, `Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena`: https://arxiv.org/abs/2306.05685
