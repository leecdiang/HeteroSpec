# RTX 第一轮：INCONCLUSIVE

本轮完成了源码、构建和 CPU 正确性准备，**没有启动新的模型请求或 GPU 实验**。因此尚不能判断 C 相对 packed 的系统收益，也不能进入第二轮。主要执行阻塞是无法读取原执行线程的当前终态；此外，Windows 独占锁、窗口期限和 worker 监控仍需接成实际执行适配。设备空闲快照不替代这项排重检查。

开工核对的 #221 head 仍为 `af436df989570ad882db65bd8a4b265b9e8cfdae`，状态 Draft；#213/#215 均已合并。已读取 next_study、guard audit、架构假设、算法影响、CPU frontier 结果及两次 RTX 结果/限制。远端该 head 的根 AGENTS.md 返回404，本次遵循用户提供的项目指令及原生私有核心的适用指令。当前线程接口两次返回 MCP -32000，只能取得昨日已完成 CPU 工作的历史记录，不能据此断言现在仍空闲。

本机为 RTX 5070 Ti Laptop，显存12227 MiB，驱动616.92；可用工具链为 CUDA12.9.86、MSVC14.44、Zig0.16.0和 Python3.11.9。已核对 target/draft Qwen3-8B/0.6B Q8_0 模型、151936词表指纹、历史源码/可执行文件/DLL磁盘身份、F16 KV、reserve8与 graph policy。**新进程实际加载的 DLL 仍为未观察**，磁盘哈希不能替代新进程加载证据。三个旧账本主文件哈希保持原值：2716请求、2872841预留行。

新 epoch 独立冻结上限256请求、1000000 target/draft rows、10800秒原生GPU窗口、4096个kernel launch、2 GiB捕获；warmup和失败余量均在限额内。实际全部为0。没有借用旧余额，也没有重新执行 #213 live 面板或 #215 补证。

| 交付 | 已完成 | 证据边界 |
| --- | --- | --- |
| 一页研究问题 | `RESEARCH_QUESTION.md` 明确部署、瓶颈、A/B/C归因及完整服务指标 | 不将已有11%–25%投机收益算成新机制增量 |
| 正确性工具 | 完整向量、量化缓冲、untrimmed/committed target/draft状态、几何、身份、设备、dispatch、mask、graph reuse与owner失效检查；外部冻结行集/词表绑定 | 22×3资格格均为NOT_RUN；host测试不升级为native资格 |
| C原型 | 同CTA两组独立四列accumulator，显式复用权重片段；保留四列K/lane/归约组织；sm120编译成功 | 独立算子原型，未集成runtime；默认编译禁用执行，在任何CUDA API前拒绝 |
| 资源结果 | A/B每线程63寄存器、3072 B静态共享；C为91寄存器、6144 B；编译器报告spill为0 | occupancy、DRAM/L2和延迟unknown；不能由寄存器增加推断输赢 |
| 原始材料复核 | 真实q32输入前八列及历史q8 A/B输出独立重哈希，32768个F32输出逐字节一致 | 派生replay，不冒充本轮真实q8捕获；没有C输出或新配对计时 |
| 请求语义 | CPU构造fixture覆盖bonus→实际seed→L4第五proposal拒绝→correction→继续→CAP，并检查EOG分支 | 逻辑token状态不是原生KV；旧真实bonus与第五拒绝分属固定k请求，未拼接成新覆盖 |
| 完整成本 | 同请求互斥分解工具、控制臂/共用优化/端点协议已写好 | `SERVICE_COSTS.json`全部成本为null，没有跨面板拼接 |

独立审查发现并修复了输出合同自报、未绑定GPU UUID、冻结阻塞未生效、实际计数可为小数、超额成本丢失及超额后继续等问题；初始失败和修复后的对抗复核分别保留。最终41项CPU测试在普通Python和`-O`下全部通过。独立读者还核对了11份上游源码快照、17个构造向量与三次状态迁移。源码哈希和日志见 `review/final/FINAL_INDEPENDENT_REVIEW.json`；这不是GitHub CI，也不是GPU复验。

请求循环的动态schedule适配器已生成源码，但独立的前端编译遇到Zig环境错误，保留为FAILED_NOT_VERIFIED，尚未链接或运行；不能与已成功编译的算子C混为一谈。完整原生状态捕获、事务范围失效和计时hooks也尚未接入该适配器。

后续应继续完成**第一轮**：先恢复原执行线程的当前可核验终态并完成实际Windows资源门禁；再获取一个真实q8投影描述符，在原参考下完成22案例及A/B/C全字节检查；通过后才做固定小规模配对计时。真实请求必须补全原生target/draft的untrimmed与committed状态、owned logits及完整终止语义。最后在公平共用lazy-tail/cap/缓冲优化后，选定并冻结最强固定控制，测同请求完整服务成本。任何数值失败或可解释负收益均保留并停在预定规模，不追正号。

进入第二轮的四个条件目前均未满足：native资格、C相对packed的配对改善、组合真实请求链和完整服务净收益空间。结论是证据不足的 **INCONCLUSIVE**，不是已经测出的NO-GO。没有改论文、合并PR、发布Release或启动其他平台。
