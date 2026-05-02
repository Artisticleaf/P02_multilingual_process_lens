# E172 Qwen Parameter and Hidden-Gate Evaluation Audit / E172 Qwen 参数与 hidden-gate 评估审计

Created / 创建时间：`2026-05-02`.

Purpose / 目的：answer whether E172 used non-thinking, whether its parameters match Qwen3.5-27B official recommendations, how hidden_gate is set, whether the threshold is too sensitive, and whether hidden_gate changes the evaluation target.

## 1. Actual E172 Runtime Settings / 实际运行设置

E172 did request non-thinking:

- `scripts/run_e172_aime2026_nonthinking_baseline.py` renders chat with `enable_thinking=False` when the model uses a chat template.
- `scripts/run_e172_aime2026_hidden_gate_realtime.py` renders both the first-pass generation and the controlled branch with `enable_thinking=False`.
- Landed Qwen rows record `used_chat_template=true` and `chat_template_enable_thinking_false_requested=true`.

Actual Qwen E172 generation settings:

| run | thinking | temperature | top_p | top_k | sample mode | max output |
|---|---:|---:|---:|---:|---|---:|
| baseline smoke | false | 0.0 | 1.0 | 0 | deterministic `do_sample=False` | 4096 |
| baseline formal | false | 0.0 | 1.0 | 0 | deterministic `do_sample=False` | 16384 |
| hidden_gate smoke first pass | false | 0.0 | 1.0 | 0 | deterministic `do_sample=False` | 1024 |
| hidden_gate smoke controlled | false | 0.0 | 1.0 | 0 | deterministic `do_sample=False` | 512 |
| hidden_gate formal planned first pass | false | 0.0 | 1.0 | 0 | deterministic `do_sample=False` | 16384 |
| hidden_gate formal planned controlled | false | 0.0 | 1.0 | 0 | deterministic `do_sample=False` | 4096 |

Other runtime settings:

- `batch_size=1`, `dtype=bfloat16`, `device=auto`, `local_files_only=true`.
- Launcher uses `CUDA_VISIBLE_DEVICES=0,1,2,3` and `MPLENS_MAX_MEMORY='0:29GiB,1:29GiB,2:29GiB,3:29GiB,cpu:180GiB'`.
- hidden_gate uses `max_model_len=8192`, `chunk_tokens=96`, `observe_every_tokens=96`, `min_observe_chars=160`, `visible_span_chars=420`.

## 2. Qwen Official/Local Model-Card Requirements / Qwen 官方/本地模型卡要求

Local model card path / 本地模型卡：`/home/Awei/LLM/Model/base/qwen35_27b/README.md`.

Relevant facts:

- Qwen3.5 thinks by default and non-thinking direct response requires disabling thinking. The local README says the model operates in thinking mode by default and points to the non-thinking section for direct response. Lines 887-888.
- Context: default context length is 262,144 tokens; for complex tasks, the README advises maintaining at least 128K tokens to preserve thinking capabilities. Lines 904-907.
- API sampling recommendations, lines 1008-1015:
  - thinking/general: `temperature=1.0`, `top_p=0.95`, `top_k=20`, `presence_penalty=1.5`, `repetition_penalty=1.0`.
  - non-thinking/general: `temperature=0.7`, `top_p=0.8`, `top_k=20`, `presence_penalty=1.5`, `repetition_penalty=1.0`.
  - non-thinking/reasoning: `temperature=1.0`, `top_p=0.95`, `top_k=20`, `presence_penalty=1.5`, `repetition_penalty=1.0`.
- Non-thinking API example, lines 1129-1170: uses `chat_template_kwargs: {"enable_thinking": False}`, `max_tokens=32768`, `temperature=0.7`, `top_p=0.8`, `presence_penalty=1.5`, and `top_k=20`.
- Best Practices, lines 1306-1322, contain a different non-thinking/reasoning recommendation: `temperature=1.0`, `top_p=1.0`, `top_k=40`, `presence_penalty=2.0`, `repetition_penalty=1.0`; output length 32,768 for most queries and 81,920 for complex math/programming benchmarks.
- Local `generation_config.json` has `do_sample=true`, `temperature=0.6`, `top_p=0.95`, `top_k=20`, but this is not the task-specific non-thinking reasoning recommendation.

Conclusion / 结论：

- E172 is correctly non-thinking.
- E172 is not using Qwen official/model-card sampling for best performance. It is using deterministic project evaluation (`temperature=0`, `do_sample=False`), shorter output budget than Qwen benchmark advice, and no `presence_penalty`.
- This is acceptable only if reported as deterministic non-thinking evaluation, not as official Qwen benchmark-performance evaluation.

## 3. hidden_gate Setup / hidden_gate 设置

E172 hidden_gate:

- First-pass non-thinking generation proceeds in chunks.
- After enough visible prefix is available, the script teacher-forces a monitor prompt over `problem + prefix`, captures the selected component state, computes a validity projection, and defines `hidden_risk = -hidden_validity_score`.
- If `hidden_risk >= threshold`, the first pass stops and a second non-thinking controlled-check prompt is rendered.
- Controlled prompt includes the hidden-derived visible span and the partial solution prefix. It does not include the gold answer.

Qwen E172 gate calibration:

- component key: `35:residual_hidden_state`.
- threshold mode: `high_precision`.
- threshold: `1.4118950366973877`.
- source: `reports/E166_HIDDEN_MONITOR_CALIBRATION_AUDIT_20260502.json`.

E166 Qwen threshold alternatives:

| mode | threshold | target recall | valid false trigger | overall trigger | invalid non-target trigger |
|---|---:|---:|---:|---:|---:|
| high_precision | 1.411895 | 0.952381 | 0.114754 | 0.568528 | 0.691489 |
| budgeted | 2.277721 | 0.595238 | 0.000000 | 0.324873 | 0.414894 |

The name `high_precision` is inherited from E166 calibration on the E164 prefix bank. For E172 AIME2026 online generation it should be treated as an imported threshold, not already validated for this distribution.

## 4. Is the Threshold Too Tight? / 阈值是否过紧？

For the E172 smoke row:

- visible span: `Let $t_P$ be`.
- hidden validity score: `-1.8095734119415283`.
- hidden risk: `1.8095734119415283`.
- high_precision threshold: `1.4118950366973877`, so it triggered.
- budgeted threshold: `2.2777209281921387`, so it would not have triggered.
- monitor visible prediction fields still look valid: `pred_process_valid=true`, `yes_minus_no=0.6875`, entropy `0.0632`.

Interpretation / 解释：

- If "too tight" means "too strict, hard to trigger", then no: it is not too tight.
- The observed issue is the opposite: high_precision is too sensitive for this E172 smoke case. It fired on an early variable-introduction span that appears process-valid.
- For AIME2026, the next calibration comparison should include at least `high_precision` vs `budgeted`, and probably a delayed trigger rule such as "do not trigger on the first observation unless risk exceeds the budgeted threshold."

## 5. Does hidden_gate Affect Evaluation? / hidden_gate 是否影响 evaluation？

Yes. hidden_gate is an intervention/treatment condition, not passive instrumentation.

Mechanically:

- Baseline score uses the ordinary non-thinking completion.
- In hidden_gate, if the gate triggers, the script stops the first pass and scores the controlled branch output instead.
- Therefore hidden_gate changes the prompt, changes the remaining generated text, changes token budget exposure, and changes final extraction.

The smoke row demonstrates this clearly:

- Baseline smoke on `e172_aime2026_p01`: correct `277`, final marker found.
- Hidden-gate smoke on the same task: triggered on `Let $t_P$ be`, controlled branch hit its 512-token cap, no final marker, fallback extracted `5`, incorrect.

So hidden_gate did not leak gold answers, but it did change the evaluation target. It must be reported as a paired intervention: `baseline_nonthinking` vs `hidden_gate_realtime_controlled_nonthinking`.

## 6. Required Reporting Boundary / 必须保留的报告边界

- Do not call E172 hidden_gate a pure evaluator-side monitor. It is a generation-time intervention.
- Do not compare hidden_gate accuracy to baseline unless paired by task and token budget/hit-max/final-marker are reported.
- Do not claim hidden_gate improvement from current E172 evidence. Current evidence shows a smoke false-positive/over-early trigger.
- Do not claim official Qwen benchmark settings for E172. Current E172 is deterministic non-thinking project evaluation.

Recommended next rerun matrix / 推荐下一轮：

| condition | sampling | gate threshold | controlled budget | purpose |
|---|---|---|---:|---|
| baseline deterministic | `temperature=0`, `do_sample=False` | none | none | preserve current comparability |
| baseline official non-thinking reasoning | official non-thinking reasoning sampling | none | none | estimate model-card-compatible performance |
| gate high_precision | deterministic | 1.411895 | 4096 or 8192 | replicate current gate with adequate branch budget |
| gate budgeted | deterministic | 2.277721 | 4096 or 8192 | test lower false-trigger policy |
| gate delayed/high-risk | deterministic | budgeted on first obs, high_precision later | 4096 or 8192 | reduce early variable-definition triggers |
