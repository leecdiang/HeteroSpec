# B570：独立零 GPU 监督修复

本 PR 只修复三个工程问题：跨槽位通知与封存时序、负例控制点证据、监督日志/辅助进程计账/实际代码审查。它不是 PR115 的第三轮，不重开 PR115，不执行其 S1–S3，不修改论文。

当前交付是**可执行验收判据、测试与原机实施协议**，尚无 Windows 修复实现或原机通过结果。`check_receipts.py` 检查规范化回执的语义，不能替代真实 Windows 注入、原始证据审计或实现审查。

- [协议与实施边界](PROTOCOL.md)
- [固定验收矩阵](ACCEPTANCE.json)
- [证据与验收要求](EVIDENCE.md)
- [预算](BUDGET.json)及[固定来源](SOURCE_LOCK.json)
- [完整 B570 执行 prompt](HOST_PROMPT_ZH.md)
- 本地检查：`python -m unittest discover -s benchmarks/b570_zero_gpu_repair_v1 -p 'test_*.py'`

原机交付位置：本目录下新增 `host/`、`results/`。开发失败、确认失败与缺失均保留。最终只有 `ENGINEERING_READY` 或 `ENGINEERING_BLOCKED`；前者也不授权 GPU/模型/原生科学任务。
