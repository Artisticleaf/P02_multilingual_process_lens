# E171 Main-Claim Pipeline Audit / E171 主 claim pipeline 审计

- Passed / 通过：`True`
- Tasks / 题目数：59
- Errors / 错误：`[]`
- Warnings / 警告：`[]`

## Definitions / 定义

- Hidden signal / 隐藏层信号：teacher-forced causal prefill 后读取的 residual、MLP、token-mixer/attention、norm component 状态，以及沿 E61 validity direction 计算出的风险分数。
- `hidden_generic_warning` / hidden 泛泛提醒：hidden monitor 触发后转成文字，只告诉模型“prefix 某处风险高”，不告诉具体位置。
- `hidden_localized_warning` / hidden 局部提醒：hidden monitor 在自动边界上选出一个可见 span，再把这个 span 作为文字提醒给模型。
- E171 的主 claim 入口：只用模型原题 non-thinking 自己做错的题，检验 hidden-derived 提醒能否救回，并统计 completion-token cost per success。

## Guards / 防错点

- Baseline prompts use only the original problem and a generic non-thinking solve template.
- Rescue cases are built only from same-model original-problem baseline failures.
- Hidden trigger selection uses the E166 calibrated component key and threshold on the model's own wrong trace.
- No oracle/manual span is included in E171 repair variants.
- The .pt cache stores component vectors, directions, centers, and prefix metadata for later residual/MLP/attention/norm analysis.
