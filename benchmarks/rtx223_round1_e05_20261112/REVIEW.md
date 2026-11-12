# e05 复核意见

**A 的可执行性门槛 FAIL；B 的设计复核 PASS，执行 NOT_RUN。** 本次对另一位撰写者的 B 提案做独立内容复核；对自己撰写的 A 矩阵做引用回查。未在 Windows 下验证实际 loader、Job、CUPTI、设备或 GPU 路由。

1. 针对 A，核对了 `7ce00b3c` e04 子树及本地 Git blob。前端的 `e03_binding.hpp:71–85` 在加载数值 DLL 后才解析预算导出，`entry.cpp:50–51` 的现有入口始终先拒绝。独立 PE 报告列有 fatbinary 注册导入；该导入只能证明存在入口，不能断言加载时实际产生 kernel。CPU planner 对 bootstrap 缺证即拒绝。即使将自有 CUDA graph 编译关闭，加载及驱动回收仍缺可信物理包络。核对四项原始源码 SHA 与 `runtime/SOURCE_RECEIPT.json`、v2 ZIP 哈希和 `runtime/build-v2/deps/059.d` 所在位置。A 文档已分别给出 Git、原始 ZIP 和源码重建的定位方式。
2. 针对 B，以普通文件读取重算九个预期模块的 SHA-256，全部匹配，总计 807,245,888 字节；另复核 CUPTI DLL、System32 的 nvcuda.dll 和 CUPTI 活动头文件 SHA。数值 DLL 的 PE 导入第 75、90 行分别是两项拟查的设备 API。冻结 runtime 头文件的导出别名和 UUID 字段与提案相符。磁盘和 PE 证据止于此，实际 driver-store、API-set、DLL 映射、ABI 和设备身份均待验证。
3. 初稿留下了先建进程再入 Job 的父进程崩溃窗口，并仅要求按已知 context/stream 读取丢失数。修订稿要求创建时原子入 Job，且以全局队列累计每次读取后清零的 dropped 增量；对强制 flush 的未完成记录、回调未排空、ETW 丢失及退出证据缺失均拒绝通过。相关语义与 API 28 的冻结头文件一致。具体实现仍需在同 Windows 环境用 CPU 替身检验进程归属及父控故障行为。运行两次查询可以给出 API 观察正例；kernel 观察灵敏度没有正例，任何事后统计均不能封闭启动前及退出后的盲区。[Windows 进程创建属性](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute) · [CUPTI Activity API](https://docs.nvidia.com/cupti/12.9/api/group__CUPTI__ACTIVITY__API.html)
4. B 不读模型，不创建 ggml 上下文，不调用 forward。窗口、许可次数、数据量及进程控制限定探针可主动做的事；显存阈值是采样停止条件，超时只能触发终止自有 Job，均未承诺设备端或失败清理瞬时完成。原执行会话的残余任务按所有者本次确认记录；未来窗口的唯一 runner/lease、探针及依赖绑定、准入时状态复核与 B 专项批准仍待落实。实际批准、执行、66 格资格和模型性能没有在本复核中发生。
