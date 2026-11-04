# 独立复核：RTX draft ubatch受限协议

状态：REVIEWED_AS_DESIGN_ONLY / NOT_READY_FOR_GPU。

已复核PROTOCOL.md、SHORT_PROMPT_CN.md、BENCHMARK_PLAN.json与SOURCE_SCOPE.json。经本轮修订，未发现新的实质性文档自洽阻断：G0仅静态预检，G1-R独立承担尚未完成的旧R/native observer/峰值桥接；heavy先资格、预算内light完成比对后才纳入性能结论；控制proposal内部oracle与H均计费。304/150/2204个setup上界算术正确。G2收缩为单prompt、5 heavy与10 provisional light，适合作为有限范围淘汰筛选，不能作总体性能结论；G3仍需单独授权、预算与新scope资格。

尚存的执行阻断必须保留：Windows/GPU adapter与Qwen/Smol extractor未验证，旧R reserve1/cap128/resident历史桥接未建立，实际设备路径、模型/数值模块身份、H recipe、RSS/VRAM/timeout及最坏payload预算未绑定。CPU tiny fixture的有限匹配不构成GPU、旧R或未观测light KV的证明。本复核不批准GPU运行，不认证runner可执行，不构成发布、合并或部署许可。

最终增量复核：已确认新参考族诊断必须另命名、另定预算并明确授权，不再构成绕过G1-R的自动降级。G3改为Cwinner、B_default、B_QB最多三个arm，保留真实默认参照，不使用pilot单一baseline或逐prompt oracle baseline；对两个合格baseline分别作非劣/加速判定且要求均通过，不合strict合同的default仍单列报告。C1优化证据仅限G2，若需G3确认必须另核定第四arm预算。两项修改自洽，不改变304/150/2204的既有setup上界，没有新增实质性文档阻断。

复核仅使用现有本地材料并检查计划计数；没有运行模型、使用GPU/用户设备、修改协议或仓库、发布内容。所审文件摘要另附reviewed-files.json，后续改动需以新摘要识别。
