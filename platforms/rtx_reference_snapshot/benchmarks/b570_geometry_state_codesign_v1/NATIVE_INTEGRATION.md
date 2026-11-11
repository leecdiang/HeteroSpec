# 原机接入义务——不可把 CPU 工具误作现成 native runner

## 1. 已从真实源码确认的阻塞

固定 PR101 `26706c9fb4818ec3465e45acea029c4ab88a390f` 的 `native/worker.cpp` Git blob 为 `c45b45b26d998bbbcfe20a115c319041b8e167a8`。读到的代码明确：

```cpp
if ((partition98!=128&&partition98!=512)||draft!="NONE"||mode!="ordinary")
    throw std::runtime_error("Diagnostic target-only partition contract");
```

虽然同一文件还有 speculative 分支，它不代表该路径在这个 actor 的请求合同下已可用。主函数也仅准许 k1，reference/context output capacity 与 mode 绑定。**不能直接删掉这个检查就以为接入完成。**

另一个风险：`schedule100` 是全局；把它直接用于 target/draft，会把 target 的分段/长度复制到 draft。新实现必须 per-context/per-role 拥有 producer plan。

PR101 的 trace 记录是为 ordinary final-only logits 写的，不能不加修改地用它验证 speculative all-output rows。每次VERIFY要记录真实被请求的所有绝对logit位置、caller rows、成功物理micrographs，不能把末行位置冒充全部有效输出。

PR97 的历史 B570 C512 在逻辑 caller2 下执行两个 occupied width1 micrographs。这既不是PQ的实现，也不是QB已经失败的结果；它是全局UB1绑定路径的记录。

## 2. 首版最小新代码边界

在新 benchmark 的 `native/` 与隔离源码副本实现，不改旧目录、不改原二进制：

1. `ProducerPlan`：target与draft独立，caller提交与内部ub明确；记录实际phase和occupied widths。
2. `ConsumerLayout`：MQ/PQ/QB三选一；q1公共路径；支持当前Llama图的真实head/KV/mask/stride。不新增算术kernel或dtype。
3. `PhaseBinding`：prefill入口绑定producer的ub；handoff时保持逻辑KV/位置/pending不被修改，再切到consumer的已注册ub。新reference shadow不切。
4. `RecipeWorker`：继承经过验证的native greedy speculative事务，固定k1；不同layout不改变draft/acceptance/bonus/rollback。
5. `ActualRequestAdmission`：先构造并校验真正序列化请求，再发送同一对象；不要在发送时另行查registry。此研究没有donor registry，但仍要防止arm与binary/recipe错配。
6. `NativeEvidenceAdapter`：将完整raw导出规范化记录；其源码、输入与raw mappings进入F0。现有 `contracts.py` 只校验规范化关系和raw hashes，并不独立证明任意adapter输出都真实。

`Recipe.k=0` 表示没有draft时有效proposal数为0，**不是要求对旧worker传argv k=0**；旧CLI要求k1时适配器应按真实接口保留并记录effective_k与native_arg两个不同字段。同理，CPU请求对象不是旧worker的argv模板。

## 3. 图层与算术 backend 的冻结

新建QB图表示需要改图构建层，可能改变llama DLL及worker SHA；这是预期变化，不是绕过freeze。要求：

- 固定目标GGUF、draft GGUF、tokenizer/template及greedy语义。
- 新旧源码差分限定在图表示、phase recipe、caller/trace、ABI接入。
- 优先保持ggml-vulkan算术backend DLL字节与原实验相同；若ABI构建必须改变其他DLL，记录原因、源diff及shadow验证，不假称字节相同。
- 若必须改具体Vulkan shader算术、精度、分块reduction kernel、量化配置才能获得结果，超出本首版范围，报告NO-GO。不要为2×2实验引入第四个未经控制因子。
- graph cache identity 至少区分role、phase、layout、producer/consumer geometry、output reservation；两个recipe几何一样不代表状态来源保证一样。
- counts-off fast path不能绕过phase guard；diagnostic开关不能改变方法是否生效。

## 4. 自然状态与相位切换

所有正式请求从prompt开始，不导入历史KV。handoff不要求任意opaque clone，不得借助PR105 donor恢复接口让候选“看起来通过”。

在diagnostic下记录：producer完成的逻辑K/V、位置范围、初始logits hash；phase切换前后逻辑KV与位置不变；sampler/pending的自然消费恰好一次；reference128的实际micrograph位置及logits policy。 allocator地址、保留容量、未使用buffer区不能直接混进“逻辑state equality”。

即使initial state相等，仍要验证整个cap128请求。后续verification可再次形成差异；完整endpoint与事务账本不能省略。

禁止中途出现不支持条件后携带当前KV切到reference并继续。若选择保守方案，必须在请求开始前从prompt执行R；中途意外一律停止并保留，不串改已经流出的token。

## 5. 真实启动链的最小负测试

测试必须经过原/新真实serializer，而非另一份理想对象：

- 正确hash但属于另一arm的合法binary/recipe；target/draft schedule互换。
- 只改ub但实际micrographs仍不符；capacity误用；q1误当q2；mask/stride/broadcast错误。
- emitter漏EOG、裁剪后缀、pending采样两次、reconciliation残留未提交KV。
- counts/heavy错配；观察开关关闭时丢失修复；cached MQ topology复用到QB。
- reference输出不一致；候选输出不一致（不能当基础设施PASS或算qualified speedup）。
- 模型/driver/loaded module漂移；源manifest正确但启动了另一DLL。
- stale request/重复slot、进程失败未记账、无completion被补零耗时；不同phase的新请求重用旧状态。

每次attempt先写append-only账本，再创建owned进程，完成或失败都落盘；加载失败也算process attempt，不因为未送模型request而删账。timeout/磁盘/内存watchdog只终止owned child，不能杀另一个对话的任务。

## 6. 执行前交付

原机agent应提交：代码diff、编译manifest、CPU测试覆盖矩阵、真实slot→wire→binary mapping、P1完整80slots与计划执行顺序、预算、F0_EXECUTION及远端回读。

**CPU_PASS 不等于 NATIVE_READY。** 只有完整native接入具备这些gate后，才可在P1预算内启动原机对照。当前包没有这些新二进制，也未运行它们。

## 7. 原始参考不能只在四题上认证后被新版本替代

P2的R始终是原始stock-compatible reference runtime，在全部24个未见输入、每个时间块实际执行。R_SHADOW只在P1测试新执行器关闭改写时的对应；不以其四题通过推断未见输入上与旧runtime普遍相等。R的真实caller/中间logits策略必须从旧代码恢复，不能套用新candidate的一次caller假设。新candidate的prefill单caller是明确设计，reference128只是预定分段标签，不是状态等价证明。若新candidate无法只改变已定义因素，则报告whole-recipe comparison而不是假装正交因子实验。

## 8. counts摘要不能冒充有序微图轨迹

counts可能只有每phase物理width histogram，不足以证明微图的执行次序。归一化记录必须将有序`target_prefill_micrograph_widths`保留为null，同时提供真实`target_prefill_width_hist`；diagnostic才从实际trace提供有序宽度并校验。不得通过复制PLAN的预期列表填充actual字段。VERIFY的multirow witness也必须绑定真实VERIFY trace，而不是仅用总continuation histogram推断。

原始R的接口/计时字段由固定来源恢复；若未能映射本文请求窗口，报告cost-not-comparable，不添加未计费的结束同步或用另一runtime替代。
