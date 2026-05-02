# E16 Manual Sibling Audit Notes

Date: 2026-04-27 CST
Auditor: Codex as human auditor
Source labels: `data/processed/manual_e05_audit_combined_20260427.jsonl`
Pair bank: `data/processed/e13_same_route_pair_bank_20260427.json`

本轮人工审计目标不是重新统计频率，而是围绕主线因果链筛出下一轮最有信息增益的 sibling pairs：同题/同模型/同 route 下，一条 trace 出现过程错误，另一条 trace 给出有效过程。审计时严格区分：

- `process validity`: 可见数学/语言语义步骤是否有错。
- `final correctness`: 最终答案是否正确。
- `format/training validity`: 是否有截断、答案后续写、think tag、prompt spill。
- `paper-grade ACPI`: 未显式纠错、格式较干净、适合作为论文核心例子的 answer-correct/process-invalid。

## Pair-Level Human Audit

| pair | verdict | why it matters | sentence-level reading | use |
|---|---|---|---|---|
| `402 bad / 403 valid` Qwen3-14B `deriv_sum zh->zh` | strong same-route paper-grade ACPI | 同模型同题同输入同输出语言；答案都正确且格式干净；唯一核心差别是 3x 求导理由 | `402`: 前 4 步正确；第 5 步说“3 是常数，常数导数为0，所以 (3x)'=3”，理由错误但答案 2x+3 正确。`403`: 明确使用常数乘法法则 `(c*g)'=c*g'`，过程正确 | primary causal + verifier pair |
| `234 bad / 235 valid` Qwen3.5 `disc_en_25_off zh->zh` | same-route paper-grade ACPI, but valid side format-broken | 同模型同题同 route；bad 格式干净且答案正确；valid 过程正确但存在 raw/format 风险 | `234`: “优惠25%”应为 pay75%，但写“打八折，即原价75%”；八折=80%，语义错误。`235`: 先算 25% 折扣额 20，再 80-20=60，过程正确 | primary contrastive; span patch需注明 valid format confound |
| `358 bad / 359 valid` Qwen3-14B `disc_en_75_off en->zh` | strongest same-route semantic drift, final wrong | 同模型同题同 route；bad 把英文 75% off 中文化为打七五折/pay75%，valid 正确算 pay25% | `358`: “discounted by 75%” 应付 25%，但写“打七五折，就是原价75%”，最终 60 错。`359`: 计算折扣额 60，再 80-60=20，最终正确 | primary semantic-drift control; not ACPI because final wrong |
| `445 bad / 442 valid` Qwen3-14B `percent_then_discount` | paper-grade lexicalization ACPI but cross-route | bad 是 zh->en；valid 是 zh->zh，同题同输入但输出语言不同；存在 route confound | `445`: 公式乘 0.80 正确，但文字 “apply an 80% discount” 在英文中表示减 80%/pay20%，与公式冲突；最终表达式等价 80。`442`: 中文“打八折”直接乘 0.8，过程正确 | important example; avoid overclaim causal patch |
| `261 bad / 260 valid` Qwen3.5 `ratio_boys_total zh->en` | same-route self-corrected arithmetic ACPI | 同模型同题同 route；bad 明确写错一步并括号纠正；valid 干净 | `261`: total=64 正确；写 `64 - 2 = 62` 错，随后括号纠正为 `64 - 24 = 40`，最终 40。`260`: total=64、girls=64-24=40，过程正确 | data-cleaning risk; weaker paper claim due self-correction |
| `229 bad / 225 valid` Qwen3.5 `disc_zh_75_price` | semantic drift but not same input route | bad 是中文七五折 -> 英文 reasoning；valid 是英文 pay75 problem -> 英文 reasoning；共享 reason_lang 但输入不同 | `229`: 把七五折解释为 75% off，pay25%，最终 20 错。`225`: 75% original price -> 60，过程正确 | semantic-drift evidence; not clean same-route causal pair |
| `296 bad / 297 valid` Qwen3.5 `deriv_product_equiv en->en` | same-route final-wrong negative control | bad 最终答案错且 answer-after-template spill；valid 过程正确但答案后截断 | `296`: 只说先展开，却直接给 `3x^2+6x`，错且格式泄漏。`297`: 展开为 `x^2+3x`，导数 `2x+3` 正确，但 final 后继续 spill | negative control: final wrong + format confound |
| `183 bad / 182 valid` Phi `deriv_sum en->zh` | same-route late contradiction but truncation-heavy | bad 前面算对，后面又把 3x 当常数项；valid 可见过程正确但无干净 final | `183`: 定义法得到 2x+3 后，又说“如果函数中有一个常数项，比如3x，它的导数就是0”，截断前未完成纠错。`182`: 定义法过程正确，给出 2x+3，但正式输出截断 | mechanism anchor only; not clean paper-grade |
| `208 bad / 209 valid` Phi `frac_simplify en->en` | format/nonsense negative control | bad 开始化简正确后出现文件名/重复垃圾；valid 过程正确但格式截断 | `208`: GCD=2 正确，但接着出现 `615-02-1208...` 和重复句，不是数学 ACPI。`209`: 化简到 3/4 正确，最终有答案但格式不干净 | format confound control |

## Audit Corrections / No-Change Notes

- 本轮未发现需要推翻的既有人工标签；现有 `manual_process_valid`, `manual_final_correct`, `manual_format_valid`, `paper_grade_acpi` 与逐句审计一致。
- 需要在后续报告中调整措辞：`261` 是 strict ACPI/data-cleaning risk，但因它显式自我纠错，不应作为 paper-grade unmarked ACPI 主例。
- `178/183/208/209` 对机制和格式 confound 很有用，但不能作为干净训练样本或核心 paper-grade 例子。
- `445` 仍是非常强的语言 lexicalization ACPI，但当前最自然的 valid sibling 是 cross-route；需要继续采样 zh->en same-route valid sibling。
- `358/359` 是目前最干净的 same-route 语义漂移 pair，虽然 bad final wrong；它适合验证“语言表层语义陷阱”与 verifier false accept，而不是 answer-correct ACPI。

## Next Audit Targets

1. 为 `445` 继续采样 Qwen3-14B `percent_then_discount zh->en`，寻找同 route valid sibling。
2. 为 `234` 继续采样 Qwen3.5 `disc_en_25_off zh->zh`，寻找 format-clean valid sibling。
3. 对 `358/359`、`402/403`、`234/235` 做 expanded contrastive + non-verdict span patch；如果站住，再进入 head/MLP decomposition。
4. 对 `296/297`、`208/209` 保留为 negative controls，防止把 final wrong/format nonsense 误解释为 process-validity mechanism。
