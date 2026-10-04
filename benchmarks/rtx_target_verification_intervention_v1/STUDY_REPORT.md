# RTX 实验阻塞报告

状态：BLOCKED_QUALIFICATION。正式计划645条，已有效完成0条；其余未执行。

具体停止原因：AssertionError(('N sham witness mismatch', 'HumanEval/18', 2))。发生于G0阶段。原始尝试均保留，不修改历史expected数组。

GPU：NVIDIA GeForce RTX 5070 Ti Laptop GPU, 12227 MiB, 616.92, 00000000:02:00.0。固定base：6a3a7e2483d5b13a24518d27b8c1ff3eafaac08f。模型、数据和54个runtime文件身份已核验。G0及后续阶段仅以实际收据为准。

本轮无法作出合格干预或参考恢复结论；/15、/18恢复未建立。恢复前先读STOP_REASON.json、BUDGET.json和RESUME.md；不自动重置预算或开始新科学版本。
