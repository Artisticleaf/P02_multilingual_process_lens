# S6 Integrated Scientific Analysis And Next Plan / S6 综合科学分析与后续计划

Date / 日期: 2026-04-27 CST  
Main artifacts / 主要产物: `reports/S6_lexical_paraphrase_grid_audit.md`, `reports/S6_lexical_grid_span_patch_summary.md`, `reports/S6_lexical_grid_layerwise_lens_summary.md`, `results/S6_integrated_analysis/s6_integrated_metrics.json`, `docs/LITERATURE_S6_POST_GRID_COLLISION_REVIEW_20260427.md`.

## 0. Plain-Language Takeaway / 人话结论

The new S6 experiments made the claim more causal and more concrete. / S6 让主张更接近因果链，也更具体。

We did not only observe “some answers are wrong.” We controlled the surface wording of the same small arithmetic family and saw that the model can keep the final number correct while flipping the process meaning: `sold for 75%` becomes `75% discount`, or `打八折/pay 80%` becomes `80% discount/pay 20%`. Absolute Yes/No verifiers then usually accept these traces as process-valid. / 我们不是只观察到“答案错”。我们控制同一类小算术题的表层说法，看到模型可能保留最终数字正确，却把过程语义翻转：`按原价 75% 出售` 变成 `75% discount`，或 `打八折/支付 80%` 变成 `80% discount/支付 20%`。绝对式 Yes/No verifier 随后通常仍把这些 trace 接受为过程有效。

The hidden-state evidence is now stronger for one S6 Qwen14 pair: swapping the valid sibling's support span into the bad trace increased the process-valid margin by `+2.750`, while swapping the bad error span into the valid trace decreased it by `-1.000`. / 隐藏状态证据在一个 S6 Qwen14 pair 上更强：把正确 sibling 的支持 span 换进错误 trace，会把“过程有效”margin 提高 `+2.750`；把错误 span 换进正确 trace，会把 margin 降低 `-1.000`。

## 1. What Was Newly Run / 本轮新增实验

| Component / 组件 | File / 文件 | What changed / 新增内容 |
|---|---|---|
| Lexical grid generation / 词汇改写网格生成 | `configs/s6_lexical_paraphrase_grid.yaml`, `scripts/launch_s6_lexical_grid_4gpu_tmux.sh` | 12 paraphrase/control tasks, 4 models, 2 routes, k=2, total 192 rows. / 12 个改写/控制任务、4 个模型、2 条 route、每格 2 条，共 192 行。 |
| Manual-style audit / 人工式审计 | `scripts/audit_s6_lexical_grid.py`, `data/processed/s6_lexical_grid_manual_audit_20260427.jsonl` | Sentence-level labels for final answer, process validity, route validity, semantic drift, and ACPI. / 逐句标注最终答案、过程有效性、route 有效性、语义漂移和 ACPI。 |
| Verifier objective test / verifier 目标测试 | `configs/s6_lexical_grid_verifier_pairs.yaml` | 3 paper-grade ACPI rows paired with 3 valid siblings. / 3 条论文级 ACPI 与 3 条正确 sibling 配对。 |
| Qwen3.5-27B transfer verifier / Qwen3.5-27B 迁移验证器 | `scripts/launch_s6_qwen27_verifier_auto_tmux.sh` | Four-GPU `device_map=auto` run on S6 selected pairs. / 四卡自动切分，在 S6 选择 pair 上复跑。 |
| Hidden span patch / hidden span patch | `configs/s6_lexical_grid_span_patch_pairs.yaml`, `scripts/launch_s6_mechanism_probes_2gpu_tmux.sh` | Residual patching for support/error span, trace span, and final-answer span. / 对 support/error span、trace span、final-answer span 做残差 patch。 |
| Layerwise verifier lens / 分层 verifier lens | `reports/S6_lexical_grid_layerwise_lens_summary.md` | Diagnostic logit lens on absolute and contrastive verifier decision tokens. / 在绝对式和对比式 verifier 决策 token 上做诊断 logit lens。 |

## 2. Generator-Side Facts / 生成侧科学事实

### 2.1 Aggregate / 汇总

| model | rows | usable traces | final correct | process invalid | ACPI | paper-grade ACPI | semantic-drift final-wrong |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemma4 E4B-it | 48 | 48 | 42 | 8 | 2 | 2 | 6 |
| Qwen3-14B-Base | 48 | 48 | 42 | 7 | 1 | 1 | 5 |
| Qwen3.5-9B | 48 | 0 | 0 | 0 | 0 | 0 | 0 |
| DeepSeek-R1-Qwen3-8B | 48 | 0 | 0 | 0 | 0 | 0 | 0 |

Important caveat / 重要说明：Qwen3.5-9B and DeepSeek-R1-Qwen3-8B failed as generators under this prompt template: Qwen3.5-9B mostly wrote meta-planning `Thinking Process`, while DeepSeek produced prompt-corruption/tokenizer artifacts. This is a prompt/template boundary, not evidence that these models lack the phenomenon. / Qwen3.5-9B 和 DeepSeek-R1-Qwen3-8B 在此提示模板下不是可用生成器：前者主要写元规划 `Thinking Process`，后者出现提示损坏/tokenizer artifact。这是提示/模板边界，不是“这些模型没有现象”的证据。

### 2.2 Three paper-grade ACPI rows / 三条论文级 ACPI

| row | model | problem meaning / 题意 | wrong process sentence / 错误过程句 | final answer / 最终答案 | why ACPI / 为什么是 ACPI |
|---:|---|---|---|---|---|
| 600049 | Gemma4 | 25% off means pay 75%. / 优惠 25% 即支付 75%。 | “如果打八折（即支付 75% 的价格）” | 60 | Final number is right, but `打八折` means pay 80%, not pay 75%. / 数字对，但“打八折”是支付 80%，不是 75%。 |
| 600070 | Gemma4 | Increase 25%, then `打八折` means multiply by 0.8. / 先涨 25%，再打八折即乘 0.8。 | “apply an 80% discount (or multiply by 0.8)” | 80 | `80% discount` normally means pay 20%, while multiplying by 0.8 means pay 80%. / `80% discount` 通常是支付 20%，而乘 0.8 是支付 80%。 |
| 600150 | Qwen14 | Sold for 75% of original price. / 按原价 75% 出售。 | “sold at a 75% discount of its original price” | 60 | `75% discount` means pay 25%, but the trace multiplies by 0.75 and gets the correct final answer. / `75% discount` 是支付 25%，但 trace 乘了 0.75 并得到正确答案。 |

These are not random arithmetic mistakes. They are process-semantics flips caused by surface lexicalization. / 这些不是随机算术错，而是表层词汇化导致的过程语义翻转。

### 2.3 Controls matter / 控制组很关键

The derivative and ratio controls produced no ACPI in this S6 grid. The failures concentrated in pay/off discount wording: `七五折/pay75`, `pay25`, `75% off`, `80% discount`, and `打八折/pay80`. / 导数和比例控制题在 S6 网格中没有产生 ACPI。错误集中在折扣的 pay/off 表述：`七五折/pay75`、`pay25`、`75% off`、`80% discount`、`打八折/pay80`。

This supports a causal lexical story: changing surface wording changes the process semantics the trace verbalizes. / 这支持一个词汇层面的因果故事：改变表层说法会改变 trace 口头化出的过程语义。

## 3. Verifier Objective Facts / verifier 目标错配事实

The verifier subset contains 6 rows: 3 paper-grade ACPI rows and 3 valid siblings. / verifier 子集有 6 行：3 条论文级 ACPI 与 3 条正确 sibling。

### 3.1 Absolute Yes/No process verifier / 绝对式 Yes/No 过程 verifier

| verifier | English prompt ACPI false accept | Chinese prompt ACPI false accept | plain meaning / 人话解释 |
|---|---:|---:|---|
| Gemma4 E4B-it | 1.000 | 1.000 | Accepts all selected bad traces as process-valid. / 把所有选择后的错误过程都接收为有效。 |
| Qwen3-14B-Base | 1.000 | 1.000 | Same over-acceptance. / 同样过度接受。 |
| Qwen3.5-27B | 1.000 | 1.000 | Larger Qwen transfer model also over-accepts absolutely. / 更大的 Qwen 迁移模型也绝对式过度接受。 |
| Qwen3.5-9B | 0.667 | 1.000 | English prompt rejects one ACPI row; Chinese prompt accepts all. / 英文提示拒掉一条 ACPI，中文提示全接受。 |

Scientific fact / 科学事实：the absolute verifier objective is too permissive for this selected ACPI family. It is not merely an “answer wrong” filter, and it often maps process-semantic contradictions to `Yes`. / 绝对式 verifier 目标对这个选择后的 ACPI 族过于宽松。它不只是“答案错”过滤器，而且常把过程语义矛盾映射成 `Yes`。

### 3.2 Contrastive sibling verifier / 对比式 sibling verifier

| verifier | overall accuracy | mean target margin | position behavior / 位置行为 | plain meaning / 人话解释 |
|---|---:|---:|---|---|
| Qwen3-14B-Base | 0.750 | 0.343 | correct on all `bad_B`, weaker on `bad_A` | Helps, especially on the Qwen14 pay75 pair, but not universal. / 有帮助，尤其 Qwen14 pay75 pair，但不万能。 |
| Qwen3.5-9B | 0.667 | 0.417 | mixed | Detects the Qwen14 pair, mixed on Gemma-generated ACPI. / 能抓 Qwen14 pair，对 Gemma ACPI 混合。 |
| Qwen3.5-27B | 0.667 | 0.874 | predicts A in 10/12 rows | Larger model gets the Qwen14 pair right but shows A-position bias on Gemma pairs. / 大模型抓住 Qwen14 pair，但在 Gemma pair 上有 A 位置偏差。 |
| Gemma4 E4B-it | 0.500 | -0.055 | predicts A in 12/12 rows | Confirms strong position bias; contrastive cannot be treated as an oracle. / 强位置偏差；对比式不能当神谕。 |

Scientific fact / 科学事实：pairwise comparison changes the objective and can expose process errors, but it also introduces order bias. The safe method must order-balance `bad_A` and `bad_B` and use conservative rejection thresholds. / 对比式改变了目标，能暴露一部分过程错误，但也引入顺序偏差。安全做法必须平衡 `bad_A` 与 `bad_B`，并使用保守拒绝阈值。

## 4. Hidden-State And Mechanism Facts / 隐藏状态与机制事实

### 4.1 Residual span patch / 残差 span patch

Clean direction / 干净方向：`valid->bad` should increase the verifier's process-valid margin on the bad trace; `bad->valid` should decrease it on the valid trace. / 把正确 span 换进错误 trace 应提高“过程有效”margin；把错误 span 换进正确 trace 应降低正确 trace 的 margin。

| pair | model | best span | layer | valid->bad effect | bad->valid effect | interpretation / 解释 |
|---|---|---|---:|---:|---:|---|
| Qwen14 `sold for 75%` vs `75% discount` | Qwen3-14B-Base | support/error span | 14 | +2.750 | -1.000 | Strong causal evidence that the support/error phrase carries process-validity signal. / 强因果证据：support/error 短语携带过程有效性信号。 |
| Gemma4 `80% discount` vs `pay 80%` | Gemma4 E4B-it | support/error span | 8 | +0.250 | -0.125 | Direction is clean but weak. / 方向干净但很弱。 |
| Gemma4 `打八折=75%` optional step | Gemma4 E4B-it | support/error span | 14 | +0.125 | -0.125 | Direction is clean but weak. / 方向干净但很弱。 |

This is the strongest new causal result in S6. It does not prove a complete circuit; it proves that, for selected sibling pairs, replacing the hidden representation of the local support/error span causally moves the verifier margin in the expected direction. / 这是 S6 最强的新因果结果。它不证明完整 circuit；它证明在选择后的 sibling pair 上，替换局部 support/error span 的隐藏表征会按预期方向因果移动 verifier margin。

### 4.2 Layerwise verifier lens / 分层 verifier lens

The S6 lens is diagnostic only: it projects hidden states through the final LM head and uses first-token margins, so it is not numerically identical to the whole-option verifier log-probability used in the main verifier experiment. / S6 lens 只是诊断工具：它把 hidden state 通过最终 LM head 投影，并使用首 token margin，因此数值上不等同于主 verifier 实验中的完整选项 log-probability。

Still, it reveals a useful pattern. / 但它仍显示一个有用模式。

- Gemma4 absolute lens has positive Yes margins for both valid and ACPI rows. / Gemma4 绝对式 lens 对正确行和 ACPI 行都给正的 Yes margin。
- Qwen14 contrastive lens often has middle-layer target-positive signal even when final A/B margin fails, which is an output-head/objective re-entanglement candidate. / Qwen14 对比式 lens 中，很多行中层已有 target-positive 信号，但最终 A/B margin 失败，这是输出头/目标再纠缠候选。
- For Gemma4 contrastive rows, target-positive signal is often lost when the bad trace is placed in B, matching the observed A-position bias. / 对 Gemma4 对比行，当错误 trace 放在 B 时，target-positive 信号常在输出端丢失，这与 A 位置偏差一致。

Mechanistic hypothesis after S6 / S6 后的机制假设：middle layers can contain local process/error evidence, but the final verifier objective can reweight it toward final-answer correctness, fluency, language prior, or position bias. / 中层可能含有局部过程/错误证据，但最终 verifier 目标会把它与最终答案正确性、流畅度、语言先验或位置偏差重新加权。

## 5. What Is New Compared With Published Work / 相比已发表工作的创新点

The project should not claim that “correct answers can hide wrong reasoning” as if this were new. Recent work already makes that broad point, including `Right Is Not Enough`, PRIME process-outcome alignment, CoT faithfulness papers, and PRM literature. / 本项目不应声称“正确答案会掩盖错误推理”本身是新发现。近期工作已经广泛指出这一点，包括 `Right Is Not Enough`、PRIME 过程-结果一致性、CoT 忠实性论文和 PRM 文献。

P02's novelty is the combination below. / P02 的创新点在以下组合。

1. **Multilingual lexical ACPI family / 多语言词汇 ACPI 族**: the key failure is not generic flawed math; it is a surface-semantic flip such as `打八折/pay80` versus `80% discount/pay20`. / 关键失败不是一般数学错，而是表层语义翻转。
2. **Trace-selection risk / 轨迹选择风险**: the bad trace can be final-correct and format-valid, so answer-based filtering keeps it. / 错误 trace 可以答案正确、格式正确，因此按答案筛选会保留它。
3. **Objective/threshold mismatch / 目标与阈值错配**: the same evidence is over-accepted by absolute Yes/No prompts but partly exposed by sibling comparison. / 同一证据在绝对式提示下被过度接受，在 sibling 对比中部分暴露。
4. **Hidden support/error-span causality / 隐藏 support/error span 因果性**: S6 adds a strong Qwen14 support/error span patch effect and weaker Gemma effects. / S6 加入强 Qwen14 support/error span patch 效应与较弱 Gemma 效应。
5. **Explicit boundaries / 明确边界**: contrastive comparison fails under position bias, AIME-style hard tasks currently lack final-correct traces, and generator prompt templates can fail. / 对比式会受位置偏差影响，AIME 难题当前缺 final-correct trace，生成提示模板也会失败。

## 6. Research Boundary / 科研边界

What we can say now / 现在可以说：

- Controlled lexical paraphrases produced 3 paper-grade ACPI traces in Gemma4/Qwen14 and multiple semantic-drift final-wrong traces. / 受控词汇改写在 Gemma4/Qwen14 中产生 3 条论文级 ACPI 和多条语义漂移答案错 trace。
- Absolute process verifiers over-accepted the S6 selected ACPI rows across Gemma4, Qwen14, Qwen3.5-27B, and mostly Qwen3.5-9B. / 绝对式过程 verifier 在 Gemma4、Qwen14、Qwen3.5-27B 上全接受 S6 选择 ACPI，在 Qwen3.5-9B 上大部分接受。
- Contrastive sibling comparison helps Qwen-family verifiers on some pairs, especially the Qwen14 pay75 pair. / 对比式 sibling 对 Qwen 系 verifier 的部分 pair 有帮助，尤其 Qwen14 pay75 pair。
- Hidden support/error spans causally move verifier margins in selected pairs, with one strong Qwen14 effect. / 在选择后的 pair 上，隐藏 support/error span 会因果移动 verifier margin，其中 Qwen14 有强效应。

What we should not say yet / 现在不能说：

- Not a population prevalence estimate. / 不是总体发生率估计。
- Not a full circuit proof. / 不是完整 circuit 证明。
- Not proof that sibling comparison always solves ACPI. / 不能证明 sibling 对比总能解决 ACPI。
- Not proof that AIME hard tasks have the same ACPI rate. / 不能证明 AIME 难题有相同 ACPI 率。
- Not proof that Qwen3.5-9B or DeepSeek lack the phenomenon; their S6 generation failed under this prompt. / 不能证明 Qwen3.5-9B 或 DeepSeek 没有现象；只是本提示下生成失败。

## 7. Mainline Plan / 主线任务规划

The five mainlines remain enough, but they should be written as one causal chain rather than five independent smokes. / 五条主线仍然足够，但应写成一条因果链，而不是五个独立 smoke。

| Mainline / 主线 | Current evidence / 当前证据 | Next goal / 下一目标 | Expected result / 希望看到的结果 |
|---|---|---|---|
| A. Real ACPI existence / 真实 ACPI 存在 | E05/E18/S6 show selected real final-correct/process-invalid traces. / 已有选择集真实 ACPI。 | Expand clean pair bank to at least 20 paper-grade pairs across discount, ratio, derivative, and translation families. / 扩到至少 20 对论文级干净 pair。 | ACPI remains concentrated in surface-semantics traps, not random formatting. / ACPI 仍集中在表层语义陷阱。 |
| B. Verifier objective mismatch / verifier 目标错配 | S6 absolute false accept is 1.0 for Gemma4/Qwen14/Qwen27 on selected ACPI. / S6 选择 ACPI 上多个 verifier 全接受。 | Add objective ablations: absolute Yes/No, contrastive A/B, ask-for-error-span, conservative reject. / 增加目标消融。 | Error-span/explanation objectives should reject more ACPI than pointwise Yes/No. / 要求指出错误 span 应比绝对式更能拒绝 ACPI。 |
| C. Lexical causality / 词汇因果性 | S6 grid separates `pay X%` from `X% off` and controls ratio/derivative tasks. / S6 已区分 pay/off 并有控制题。 | Add minimal pairs with same answer but opposite lexical meaning, e.g. `pay 80%` vs `80% discount`. / 加最小对。 | ACPI and semantic drift track lexical form rather than arithmetic difficulty. / 错误跟随词汇形式而非算术难度。 |
| D. Hidden process/error signal / 隐藏过程/错误信号 | S6 Qwen14 support/error L14 patch is strong; Gemma effects are weak. / Qwen14 L14 强，Gemma 弱。 | Decompose robust spans into attention head, MLP block, and optional SAE/transcoder features. / 对稳健 span 做头、MLP、SAE/transcoder 分解。 | A small number of mid-layer components should carry most lexical-process contrast; output head may suppress it. / 少数中层组件承载词汇-过程对比，输出头可能压制。 |
| E. Sibling/triangulation mitigation / sibling 与三角测量缓解 | Qwen-family contrastive helps; Gemma and Qwen27 show A-position bias on some pairs. / Qwen 有帮助，Gemma/Qwen27 有 A 偏差。 | Use order-balanced contrastive plus abstention when orders disagree. / 使用顺序平衡与不一致拒绝。 | Risk drops without pretending contrastive is an oracle. / 风险下降，但不把对比式当万能。 |

## 8. Follow-Up Experiments To Run Next / 下一步实验设计

### Experiment N1: Larger clean lexical pair bank / 更大的干净词汇 pair bank

Purpose / 目的：test whether the S6 phenomenon repeats beyond three ACPI rows. / 检验 S6 现象是否能超出 3 条 ACPI 重复出现。  
Design / 设计：generate 20-40 minimal-pair tasks across `打八折`, `七五折`, `pay 75%`, `75% off`, `sold for 75%`, `80% discount`, plus ratio/derivative negative controls. / 生成 20-40 个最小对任务，并保留比例/导数负控。  
Expected result / 希望结果：discount lexical forms produce ACPI/semantic-drift rows; negative controls stay mostly clean. / 折扣词汇形式产生 ACPI/语义漂移，负控基本干净。

### Experiment N2: Error-span extraction verifier / 错误 span 抽取 verifier

Purpose / 目的：distinguish “the verifier cannot see the error” from “the verifier sees weak evidence but the Yes/No threshold accepts.” / 区分“看不到错误”和“看到了弱证据但 Yes/No 阈值仍接受”。  
Design / 设计：on the same pairs, ask verifiers to quote or mark the first invalid phrase before Yes/No; compare with absolute and contrastive prompts. / 在同一 pair 上要求先标出第一处无效短语，再判断。  
Expected result / 希望结果：some ACPI rows that absolute Yes/No accepts will have identifiable error-span candidates under extraction prompts. / 部分绝对式接受的 ACPI 在抽取提示下会出现可定位错误 span。

### Experiment N3: Head/MLP/SAE mechanism on robust S6 Qwen14 L14 / 在稳健 S6 Qwen14 L14 上做头/MLP/SAE 机制

Purpose / 目的：turn residual span causality into a more specific mechanism claim. / 把残差 span 因果性推进到更具体机制。  
Design / 设计：patch attention outputs and MLP outputs separately at layers 9/14/20; if feasible, train or load small SAE/transcoder probes on the verifier decision context. / 分别 patch attention output 与 MLP output；可行时做 SAE/transcoder probe。  
Expected result / 希望结果：mid-layer MLP or a small set of heads will explain most of the support/error span margin movement. / 中层 MLP 或少数 head 解释大部分 span margin movement。

### Experiment N4: Hard-task final-correct conditioning / 难题 final-correct 条件化

Purpose / 目的：answer the “simple task” critique without pretending AIME rates are comparable. / 回应“任务太简单”的质疑，但不把 AIME 率硬外推。  
Design / 设计：use Qwen3.5-27B/Gemma4 and verifier-guided sampling on AIME24/25 until final-correct traces exist; only then manually audit process validity. / 用 Qwen3.5-27B/Gemma4 与 verifier-guided sampling 先得到 final-correct AIME trace，再人工审计过程。  
Expected result / 希望结果：final-correct hard traces are rarer; if ACPI appears, errors may be “miracle step / unsupported inference” rather than discount lexicalization. / 难题 final-correct 更少；若有 ACPI，可能是“神来一步/无依据推断”，不一定是折扣词汇化。

### Experiment N5: Transfer with fixed chat templates / 修复模板后的跨模型迁移

Purpose / 目的：separate model phenomenon from prompt-template failure. / 区分模型现象与提示模板失败。  
Design / 设计：fix Qwen3.5-9B and DeepSeek generator prompts; rerun only the S6 lexical grid first, not all experiments. / 先修复 Qwen3.5-9B 与 DeepSeek 的生成提示，只复跑 S6 网格。  
Expected result / 希望结果：if clean traces appear, we can test whether their lexical ACPI pattern matches Gemma/Qwen14; if not, record prompt/model boundary. / 若生成干净 trace，测试词汇 ACPI 是否匹配；否则记录提示/模型边界。

## 9. Reliability Audit / 可靠性审计

- No fine-tuning or training was performed. / 未进行微调或训练。
- Manual-style labels were produced after generation and used only for audit/evaluation. / 人工式标签在生成后产生，仅用于审计/评估。
- Verifier/patch/lens subset is selected: 3 ACPI + 3 valid siblings. Rates on this subset are not prevalence. / verifier/patch/lens 子集是选择集：3 条 ACPI + 3 条正确 sibling。比例不是总体发生率。
- Contrastive experiments include both `bad_A` and `bad_B`, revealing position bias rather than hiding it. / 对比实验包含 `bad_A` 和 `bad_B`，显式暴露位置偏差。
- Span patch results are causal interventions on hidden activations, but not full circuit explanations. / span patch 是隐藏激活的因果干预，但不是完整 circuit 解释。
- Layerwise lens is diagnostic and should not be equated with whole-option verifier log-probability. / 分层 lens 是诊断工具，不应等同于完整选项 log-probability verifier。
- Qwen3.5-27B was run with four-GPU `device_map=auto` and per-GPU memory caps. / Qwen3.5-27B 使用四卡 `device_map=auto` 与显存上限运行。
