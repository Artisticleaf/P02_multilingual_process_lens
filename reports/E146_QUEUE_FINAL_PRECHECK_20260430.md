# E146 Queue Final Precheck / E146 队列最后检查

Date / 日期：2026-04-30  
Scope / 范围：Qwen/Gemma-only `NG_model_card_hf_profile` rerun after E119.

## Current Runtime Status / 当前运行状态

- Active tmux / 活跃 tmux：`p02_e146_qg_20260430` only.
- Upstream dependency / 上游依赖：E119 completed with `all_done` at `2026-04-30T04:06:05+08:00`.
- E146 status / E146 状态：preflight passed; `wait_for_e119` observed E119 `all_done`; current step is `e146_qwen35_27b_ng_model_card_hf_profile`.
- Current checkpoint / 当前 checkpoint：Qwen has written 8/36 rows at check time.
- Current process / 当前进程：one `run_e49_hard_task_conditioning_official.py` process under `/home/Awei/miniconda3/envs/passage_prep_py312/bin/python3.12`.
- GPU status / GPU 状态：one model process is sharded across four RTX 5090 GPUs; no duplicate model queue is active.

## Parameter Check / 参数核对

E146 is intentionally labeled `NG_model_card_hf_profile`, not exact Qwen model-card replication.

- Qwen3.5-27B / Qwen3.5-27B：`temperature=1.0`, `top_p=0.95`, `top_k=20`, `max_new_tokens=8192`, `batch_size=2`, `thinking=false`.
- Gemma4-31B-it / Gemma4-31B-it：`temperature=1.0`, `top_p=0.95`, `top_k=64`, `max_new_tokens=8192`, `batch_size=2`, `thinking=false`.
- Gemma4-26B-A4B-it / Gemma4-26B-A4B-it：`temperature=1.0`, `top_p=0.95`, `top_k=64`, `max_new_tokens=8192`, `batch_size=2`, `thinking=false`.
- Qwen caveat / Qwen 边界：current HF generate does not apply Qwen `presence_penalty`; this is recorded as a backend limitation.
- Pad token / pad token：generation code now uses `tokenizer.pad_token_id` when available, otherwise `eos_token_id`. This avoids forcing Gemma pad to EOS.

## Safety Check / 防呆检查

- Serial execution / 串行执行：one large model at a time.
- Dependency guard / 依赖保护：launcher waits for E119 `all_done` or GPU release before E146 model loading.
- Step markers / 步骤标记：each step writes `_DONE.json` or `_FAILED.json` under `results/E146_qwen_gemma_ng_model_card_hf_profile/_status/`.
- Failure continuation / 失败续跑：failed model steps write a failure marker, save a GPU snapshot, and continue to the next step.
- Checkpointing / checkpoint：each generation step writes per-row JSONL checkpoints.
- Static checks / 静态检查：`py_compile`, queue `bash -n`, no-GPU smoke, and official workspace audit passed.
- Leakage check / 泄露检查：current Qwen checkpoint rows have `gold_answer_in_prompt=0`, `known_trap_note_in_prompt=0`, and `thinking=false`.

## Current Observation / 当前观察

At 8/36 Qwen rows, 6 rows are final-correct and 2 rows hit `max_new_tokens=8192`. The hit-max rows are long geometry traces without final markers. This is not a queue error; it is a scientific signal about non-thinking generation closure under the model-card HF profile.

## Decision / 当前决策

Do not change E146 mid-run. Changing `max_new_tokens`, prompt contract, or sampling parameters now would break comparability across Qwen/Gemma and make the run harder to interpret.

After E146 finishes, decide based on the completed hit-max and final-correct summary:

- If Qwen hit-max remains high, add `E147_Qwen_NG_16k_final_contract` as a follow-up, not as a replacement for E146.
- Use E146 final-correct rows to drive token-level localization and activation capture experiments: residual / MLP / attention component signals should be collected around local error spans, repair markers, final answer spans, and hit-max/stop failure regions.
- Keep E146 separate from hidden-mechanism claims until process audit is complete. The current run only establishes generation behavior under corrected HF-profile settings.
