# E91 Thinking-Mode Config Audit / thinking 模式配置审计（2026-04-29）

## Conclusion / 结论

中文：E91 是轻量配置审计，不是行为实验。四个 P0/扩展 P0 模型的官方 chat template 都能区分 thinking 与 non-thinking 渲染。thinking 模式下，assistant 起点会进入 thought/reasoning 区域，因此不能再使用首 token `Yes/No` 或 `A/B` logprob 作为 verifier 决策；后续 TV/TG 实验必须让模型生成完整 thinking 输出，再解析最后明确的 `Final decision` 或最终选项。

English: E91 is a lightweight configuration audit, not a behavioral experiment. The P0/expanded-P0 chat templates distinguish thinking and non-thinking rendering. In thinking mode the assistant begins with a thought/reasoning region, so first-token `Yes/No` or `A/B` option-logprob is not a valid thinking-verifier decision. TV/TG reruns must generate full thinking outputs and parse the final explicit decision.

## Checklist / 检查表

| model | thinking render | non-thinking render | first-token logprob safe in thinking | recommended thinking params from local model card |
|---|---:|---:|---:|---|
| qwen35_27b | OK | OK | No | {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 1.5, "repetition_penalty": 1.0} |
| gemma4_31b_it | OK | OK | No | {"temperature": 1.0, "top_p": 0.95, "top_k": 64} |
| gemma4_26b_a4b_it | OK | OK | No | {"temperature": 1.0, "top_p": 0.95, "top_k": 64} |
| glm47_flash_candidate | OK | OK | No | {"temperature": 1.0, "top_p": 0.95, "max_new_tokens": 131072} |

## Immediate Experimental Rule / 立即实验规则

1. `DV` results remain valid as direct-answer verifier evidence only. / `DV` 结果只作为直接回答 verifier 证据。
2. `TV` reruns must use generated final decisions, not first-token option logprob. / `TV` 重测必须解析生成后的最终判定，不能用首 token logprob。
3. `TG` natural generation must use official thinking sampling parameters and be audited separately from `NG`. / `TG` 自然生成必须用官方 thinking 采样参数，并与 `NG` 分开审计。
4. Hidden/mechanism reruns in thinking mode must record thought tokens, repair markers, and final decision tokens separately. / thinking 机制实验需分别记录思考 token、修复标记和最终决策 token。

## Model Details / 模型细节

### qwen35_27b

- Local path: `/home/Awei/LLM/Model/base/qwen35_27b`
- Official/model-card link: https://huggingface.co/Qwen/Qwen3.5-27B
- Tokenizer: `Qwen2Tokenizer`; chat template: `True`
- Thinking true tail:
```text
<|im_start|>user
Please inspect the trace and then output a final decision exactly as `Final decision: Yes` or `Final decision: No`.

Problem: Is 2 + 2 = 4?
Trace: 2 + 2 = 4.<|im_end|>
<|im_start|>assistant
<think>

```
- Thinking false tail:
```text
<|im_start|>user
Please inspect the trace and then output a final decision exactly as `Final decision: Yes` or `Final decision: No`.

Problem: Is 2 + 2 = 4?
Trace: 2 + 2 = 4.<|im_end|>
<|im_start|>assistant
<think>

</think>


```
- README snippets:
```text
59:     - LM Output: 248320 (Padded)
60:     - MTP: trained with multi-steps  
61: - Context Length: 262,144 natively and extensible up to 1,010,000 tokens.
62: 
63: ## Benchmark Results
```

```text
903: 
904: > [!Important]
905: > The model has a default context length of 262,144 tokens.
906: > If you encounter out-of-memory (OOM) errors, consider reducing the context window. 
907: > However, because Qwen3.5 leverages extended context for complex tasks, we advise maintaining a context length of at least 128K tokens to preserve thinking capabilities.
```

```text
918: The following will create API endpoints at `http://localhost:8000/v1`:
919: 
920: - **Standard Version**: The following command can be used to create an API endpoint with maximum context length 262,144 tokens using tensor parallel on 8 GPUs.
921:     
922:     ```shell
```

```text
927:     
928:     ```shell
929:     python -m sglang.launch_server --model-path Qwen/Qwen3.5-27B --port 8000 --tp-size 8 --mem-fraction-static 0.8 --context-length 262144 --reasoning-parser qwen3 --tool-call-parser qwen3_coder
930:     ```
931: 
```

```text
933:     
934:     ```shell
935:     python -m sglang.launch_server --model-path Qwen/Qwen3.5-27B --port 8000 --tp-size 8 --mem-fraction-static 0.8 --context-length 262144 --reasoning-parser qwen3 --speculative-algo NEXTN --speculative-num-steps 3 --speculative-eagle-topk 1 --speculative-num-draft-tokens 4
936:     ```
937: 
```

### gemma4_31b_it

- Local path: `/home/Awei/LLM/Model/base/gemma4_31b_it`
- Official/model-card link: https://huggingface.co/google/gemma-4-31B-it
- Tokenizer: `GemmaTokenizer`; chat template: `True`
- Thinking true tail:
```text
<bos><|turn>system
<|think|>
<turn|>
<|turn>user
Please inspect the trace and then output a final decision exactly as `Final decision: Yes` or `Final decision: No`.

Problem: Is 2 + 2 = 4?
Trace: 2 + 2 = 4.<turn|>
<|turn>model

```
- Thinking false tail:
```text
<bos><|turn>user
Please inspect the trace and then output a final decision exactly as `Final decision: Yes` or `Final decision: No`.

Problem: Is 2 + 2 = 4?
Trace: 2 + 2 = 4.<turn|>
<|turn>model
<|channel>thought
<channel|>
```
- README snippets:
```text
53: | **Layers** | 35 | 42 | 60 |
54: | **Sliding Window** | 512 tokens | 512 tokens | 1024 tokens |
55: | **Context Length** | 128K tokens | 128K tokens | 256K tokens  |
56: | **Vocabulary Size** | 262K | 262K | 262K |
57: | **Supported Modalities** | Text, Image, Audio | Text, Image, Audio | Text, Image |
```

```text
69: | **Layers** | 30 |
70: | **Sliding Window** | 1024 tokens |
71: | **Context Length** | 256K tokens |
72: | **Vocabulary Size** | 262K |
73: | **Expert Count** | 8 active / 128 total and 1 shared |
```

```text
154:     tokenize=False, 
155:     add_generation_prompt=True, 
156:     enable_thinking=False
157: )
158: inputs = processor(text=text, return_tensors="pt").to(model.device)
```

```text
167: ```
168: 
169: To enable reasoning, set `enable_thinking=True` and the `parse_response` function will take care of parsing the thinking output.
170: 
171: Below, you will also find snippets for processing audio (E2B and E4B only), images, and video alongside text:
```

```text
356: Use the following standardized sampling configuration across all use cases:
357: 
358: * `temperature=1.0`  
359: * `top_p=0.95`  
360: * `top_k=64`
```

### gemma4_26b_a4b_it

- Local path: `/home/Awei/LLM/Model/base/gemma4_26b_a4b_it`
- Official/model-card link: https://huggingface.co/google/gemma-4-26B-A4B-it
- Tokenizer: `GemmaTokenizer`; chat template: `True`
- Thinking true tail:
```text
<bos><|turn>system
<|think|>
<turn|>
<|turn>user
Please inspect the trace and then output a final decision exactly as `Final decision: Yes` or `Final decision: No`.

Problem: Is 2 + 2 = 4?
Trace: 2 + 2 = 4.<turn|>
<|turn>model

```
- Thinking false tail:
```text
<bos><|turn>user
Please inspect the trace and then output a final decision exactly as `Final decision: Yes` or `Final decision: No`.

Problem: Is 2 + 2 = 4?
Trace: 2 + 2 = 4.<turn|>
<|turn>model
<|channel>thought
<channel|>
```
- README snippets:
```text
53: | **Layers** | 35 | 42 | 60 |
54: | **Sliding Window** | 512 tokens | 512 tokens | 1024 tokens |
55: | **Context Length** | 128K tokens | 128K tokens | 256K tokens  |
56: | **Vocabulary Size** | 262K | 262K | 262K |
57: | **Supported Modalities** | Text, Image, Audio | Text, Image, Audio | Text, Image |
```

```text
69: | **Layers** | 30 |
70: | **Sliding Window** | 1024 tokens |
71: | **Context Length** | 256K tokens |
72: | **Vocabulary Size** | 262K |
73: | **Expert Count** | 8 active / 128 total and 1 shared |
```

```text
154:     tokenize=False, 
155:     add_generation_prompt=True, 
156:     enable_thinking=False
157: )
158: inputs = processor(text=text, return_tensors="pt").to(model.device)
```

```text
167: ```
168: 
169: To enable reasoning, set `enable_thinking=True` and the `parse_response` function will take care of parsing the thinking output.
170: 
171: Below, you will also find snippets for processing audio (E2B and E4B only), images, and video alongside text:
```

```text
356: Use the following standardized sampling configuration across all use cases:
357: 
358: * `temperature=1.0`  
359: * `top_p=0.95`  
360: * `top_k=64`
```

### glm47_flash_candidate

- Local path: `/home/Awei/LLM/Model/base/glm47_flash`
- Official/model-card link: https://huggingface.co/zai-org/GLM-4.7-Flash
- Tokenizer: `TokenizersBackend`; chat template: `True`
- Thinking true tail:
```text
[gMASK]<sop><|user|>Please inspect the trace and then output a final decision exactly as `Final decision: Yes` or `Final decision: No`.

Problem: Is 2 + 2 = 4?
Trace: 2 + 2 = 4.
<|assistant|><think>
```
- Thinking false tail:
```text
[gMASK]<sop><|user|>Please inspect the trace and then output a final decision exactly as `Final decision: Yes` or `Final decision: No`.

Problem: Is 2 + 2 = 4?
Trace: 2 + 2 = 4.
<|assistant|></think>
```
- README snippets:
```text
46: **Default Settings (Most Tasks)**
47: 
48: * temperature: `1.0`
49: * top-p: `0.95`
50: * max new tokens: `131072`
```

```text
54: **Terminal Bench, SWE Bench Verified**
55: 
56: * temperature: `0.7`
57: * top-p: `1.0`
58: * max new tokens: `16384`
```

```text
60: **τ^2-Bench**
61: 
62: * Temperature: `0`
63: * Max new tokens: `16384`
64: 
```

```text
133:      --speculative-config.num_speculative_tokens 1 \
134:      --tool-call-parser glm47 \
135:      --reasoning-parser glm45 \
136:      --enable-auto-tool-choice \
137:      --served-model-name glm-4.7-flash
```

```text
145:   --tp-size 4 \
146:   --tool-call-parser glm47  \
147:   --reasoning-parser glm45 \
148:   --speculative-algorithm EAGLE \
149:   --speculative-num-steps 3 \
```

