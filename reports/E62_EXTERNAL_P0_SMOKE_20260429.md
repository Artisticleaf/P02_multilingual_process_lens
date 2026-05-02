# E62 External P0 Candidate Smoke / E62 外部 P0 候选准入测试（2026-04-29）

- JSON audit / 机器可读审计：`reports/E62_EXTERNAL_P0_SMOKE_AUDIT_20260429.json`
- Purpose / 目的：决定 Nemotron、GLM、EXAONE 是否能从 candidate 进入 expanded P0 official evidence。
- Plain language / 说人话：下载完成不等于能进主证据；必须能在本机可靠加载、按官方/本地 chat template 打分，并能拿 hidden states 做机制实验。

## Promotion Table / 准入表

| candidate | license | model type | tokenizer | AutoConfig | HF hidden/logprob | vLLM static | promote? | reason |
|---|---|---|---|---|---|---|---|---|
| `nemotron_cascade2_30b_a3b_candidate` | `nvidia_open_model_license` | `nemotron_h` | PASS | PASS | FAIL | PASS | FAIL | HF dynamic option-logprob/hidden-state/layer smoke failed or skipped |
| `glm47_flash_candidate` | `mit` | `glm4_moe_lite` | PASS | PASS | PASS | PASS | PASS | all promotion-gate checks passed |
| `exaone45_33b_candidate` | `exaone_1_2_nc` | `exaone4_5` | PASS | FAIL | FAIL | PASS | FAIL | AutoConfig/backend unsupported; HF dynamic option-logprob/hidden-state/layer smoke failed or skipped |

## Interpretation / 解释

- Passing static license/config checks is not enough for official evidence; E63 requires HF hidden-state and deterministic option-logprob support. / 只通过静态许可/配置不够；E63 需要 HF hidden-state 和确定性 option-logprob 支持。
- If a candidate fails because the local backend lacks architecture support, the scientific conclusion is not that the model lacks the phenomenon; it is only not admitted into official evidence under the current environment. / 如果候选失败原因是本地后端缺少架构支持，科学含义不是模型没有该现象，而是当前环境不能把它纳入官方证据。
- EXAONE is non-commercial research/education only under the local license text; any future publication should cite and respect that boundary. / EXAONE 本地许可为非商业研究/教育用途；后续论文应标注并遵守该边界。

## Audit Checks / 审计检查

| status | check | detail |
|---|---|---|
| PASS | result exists for nemotron_cascade2_30b_a3b_candidate | results/E62_external_p0_smoke/nemotron_cascade2_30b_a3b_candidate_e62_external_p0_smoke.json |
| PASS | nemotron_cascade2_30b_a3b_candidate license probe | ok |
| PASS | nemotron_cascade2_30b_a3b_candidate static probe | ok |
| PASS | nemotron_cascade2_30b_a3b_candidate tokenizer probe | ok |
| PASS | nemotron_cascade2_30b_a3b_candidate auto config probe | ok |
| FAIL | nemotron_cascade2_30b_a3b_candidate HF dynamic probe | ImportError: mamba-ssm is required by the Mamba model but cannot be imported |
| PASS | result exists for glm47_flash_candidate | results/E62_external_p0_smoke/glm47_flash_candidate_e62_external_p0_smoke.json |
| PASS | glm47_flash_candidate license probe | ok |
| PASS | glm47_flash_candidate static probe | ok |
| PASS | glm47_flash_candidate tokenizer probe | ok |
| PASS | glm47_flash_candidate auto config probe | ok |
| PASS | glm47_flash_candidate HF dynamic probe | ok |
| PASS | result exists for exaone45_33b_candidate | results/E62_external_p0_smoke/exaone45_33b_candidate_e62_external_p0_smoke.json |
| PASS | exaone45_33b_candidate license probe | ok |
| PASS | exaone45_33b_candidate static probe | ok |
| PASS | exaone45_33b_candidate tokenizer probe | ok |
| FAIL | exaone45_33b_candidate auto config probe | ValueError: The checkpoint you are trying to load has model type `exaone4_5` but Transformers does not recognize this architecture. This could be because of an issue with the checkpoint, or be |
| FAIL | exaone45_33b_candidate HF dynamic probe | not attempted in this environment |

## Boundary / 边界

- E62 is a technical admission gate, not a verifier-risk experiment. / E62 是技术准入，不是 verifier 风险实验。
- Candidates that do not pass E62 must remain `pending_smoke` or be demoted; they must not enter main claim synthesis. / 未通过 E62 的候选必须保持 pending 或降级，不能进入主 claim 综合。
