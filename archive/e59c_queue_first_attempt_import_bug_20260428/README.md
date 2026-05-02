# E59c Queue First Attempt Import Bug / E59c 队列首次尝试导入错误

The first E59c tmux queue successfully generated raw style rewrites, but the audit step failed because `scripts/audit_e59c_style_rewrite.py` imported non-existent helpers `write_jsonl` and `write_yaml` from `mplens.io_utils`. The downstream verifier steps in that queue produced zero-row files before the bug was fixed.

首次 E59c tmux 队列成功生成 raw style rewrites，但 audit 步骤因从 `mplens.io_utils` 导入不存在的 `write_jsonl`/`write_yaml` 而失败。该队列后续 verifier 步骤在修复前生成过 zero-row 文件。

Fix / 修复：the audit script now defines local JSONL/YAML writers, the launch script now stops on failure, and verifier outputs were overwritten by successful reruns after audited data were rebuilt. / audit 脚本已改为本地 writer，启动脚本已改为失败即停；verifier 输出已在重建 audited data 后成功重跑并覆盖。
