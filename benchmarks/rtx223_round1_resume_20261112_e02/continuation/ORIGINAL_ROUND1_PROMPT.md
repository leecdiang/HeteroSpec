# Prompt 1｜5070 Ti：第一轮，原型、正确性与机制筛选

请接续 Windows RTX 5070 Ti Laptop 上的 HeteroSpec 研究。目标不是重复已完成的 k3/k7 面板，而是判断：在固定量化参考和完整请求语义下，能否实现一个相对强基线有可归因系统价值的执行器。允许负结果，不以凑到 5% 为完成条件。

先读取仓库 AGENTS.md、#221 最新状态及其 next_study、guard_audit、ARCHITECTURE_HYPOTHESIS、ALGORITHM_IMPLICATIONS，并对照已完成的 #213/#215。此前核实的 #221 head 是 af436df989570ad882db65bd8a4b265b9e8cfdae；开工前重新核对 head 和原执行线程，避免重复工作。保护旧参考、源码、实验数据、失败记录和账本；新实现使用独立分支、目录和 epoch，不覆盖现有材料。

1. 先用一页写清研究问题：什么部署场景、什么真实瓶颈、候选机制改变什么、对照是什么、最终希望改善哪个完整服务指标。把已有 speculation 相对 target-only 的整体收益与本文新机制增量分开，不能把 11%–25% 全算到新机制上。

2. 核实实际 GPU 型号、显存、驱动、编译器、模型/词表、源码、加载的 DLL、producer、KV、graph policy、设备映射、资源窗口和当前账本。新一轮建议上限：256 个模型请求、合计 100 万 target/draft rows、3 小时原生 GPU 窗口；启动前按实际授权冻结具体配额，并单独记录 kernel launch、捕获数据量、warmup 和失败余量。缺少必要授权或资源时先完成源码与 CPU 准备并报告。不得挪用旧预算、终止其他任务、修改功耗/风扇/驱动或重置 GPU。

现有 #221 GPU 探针是 Linux/A5000 profile，依赖 libcuda.so.1、ldd 等并禁止 physical GPU0；不能原样用于 Windows 单卡，也不能删除原有服务器保护硬跑。请沿用已验证的 Windows RTX 原生入口，建立独立适配并绑定实际获准设备。

3. 先确定同合同强基线及同请求完整成本。主比较至少包含 backend-loop4、当前 packed 和开发阶段选出的最强合格固定策略；常规优化如 lazy-tail/cap 修复和缓冲复用应公平给予适用的所有臂。另列实际可运行的强 target-only/runtime 作为应用价值背景；若数值语义不同，单独标明，不混进 exact-contract 主比较。记录 reset、prefill、draft、verify、同步、planning、guard、reconciliation 和 fallback 的关键路径；不把重叠阶段相加或拼接不同面板。

4. 先补正确性工具，再测性能。对缺失完整向量、untrimmed state、几何、身份、截断或错误 hash 的记录明确拒绝；关键检查不能依赖可被 python -O 移除的 assert。packed 和 loop4 分别验证 dtype、shape、stride、placement、dispatch、output mask、graph reuse 等，依据 #221 的 22 个资格案例冻结每项预期。区分执行前拒绝、已资格 fallback 和执行后 owner 失效；不要把 capture 观察当成 clean 路径检查。

5. 对同一真实 q=8 projection 输入做三臂：A 为 backend-loop4，B 为当前 packed，C 为同一 CTA 内两组独立四列 accumulator 复用权重片段。C 尚未实现；初始只支持明确的 Q8_0/F32、q=8、g=2 子域。保持每组原有四列 K 遍历、线程分工、算术及归约顺序，不能简单把 native width 改成 8。先比较量化 activation bytes 和全部输出，再分别测 kernel-only 与包含共同量化/同步的完整 operator。记录寄存器、spill、共享内存、occupancy；没有 DRAM/L2 计数器就写 unknown。解释 A→B 和 B→C 各自贡献，不能把全部差距都归因于权重复用。

6. 闭合真实请求链：k3 全接受 → bonus 成为下一阶段真实 seed → 第五 proposal 被拒绝时读取 L4 → correction、trim/pending 更新 → 后续继续。比较完整 requested logits、target/draft 活动状态、输出所有权、accepted、CAP/EOG 与终止原因。固定 token 37、相同 KV 或 argmax 不能替代真实消费者；找不到自然覆盖时如实标记，可用单独标注的构造 fixture 补状态机测试。

7. 第一轮输出三个结论之一：GO、NO-GO 或 INCONCLUSIVE。进入第二轮至少要求资格通过、相对当前 packed 有可解释的配对改善、真实请求覆盖和完整服务成本显示有现实净收益空间。若不满足，保留反例或负结果，不扩大样本追正号。交付可复建源码、身份、资格记录、A/B/C 原始配对、成本分解、资源与账本、独立复算及第二轮建议。

不要重跑 #213 的完整 live 面板或 #215 已完成补证，不启动多卡或 B570/Metal 移植；不自动合并 PR、发布 Release、改论文或提交论文。
