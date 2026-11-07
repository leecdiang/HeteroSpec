# 原机接入契约与已确认缺口

本目录的CPU工具已经可运行；**Vulkan PQ/QB native actor、原生调度和结果适配尚未在作者电脑上实现/编译/验证**。该状态不是一个额外研究问题，但必须在native前完成，不能用合成测试回执冒充。

## 1. 源码边界已经核查

- PR101 `26706c9fb4818ec3465e45acea029c4ab88a390f` 的 `native/worker.cpp` blob `c45b45b26d998bbbcfe20a115c319041b8e167a8`：main只接受k1；请求的`Diagnostic target-only partition contract`明确禁止draft与非ordinary。其旧speculative代码虽然还在文件里，却被此guard排除。本研究不能直接复用该可执行文件来做k3实验。
- 该worker在`Context::prefill`逐段调用decode，只有最后绝对位置索要logits；`schedule100`是全局对象。新actor必须把target schedule与draft schedule分开，不能误使draft继承P128。
- PR92 `82946adf946491e6cf7fef761bcc1ec0772e914e`的SCIENCE CAS保存自然k1 actor、原始R_stock、draft和F0。由原机恢复自然生成/内存/输出逻辑后，**显式扩展k3**；不能从RTX复制一套不同tokenizer/格式的loop。
- PR98 `3235d44c26edd92db33e574094c26af8e29d2452` 的 `scripts/platform/rtx_querylayout_mechanism_v1/replay95.cpp` blob `7c4cb5bb51cadff7b6b829c5ad4aee855e1d0396`提供Q/mask view、PQ concat、QB recombination语义；该程序硬编码CUDA0，直接运行不能算Vulkan验证。`build95.py` blob `7a132a2cc69658c241d40402e6d0a7cb17fe90be`定位了图构造和reuse义务，但不能对未核查的Vulkan源码做无条件文本替换。

## 2. 最短的 native patch 范围

新增隔离actor与graph层：process固定consumer `{MQ,PQ,QB,SERIAL}`；请求固定target producer `{P128,P512}`。target prefill关闭局部变换，按共同UB512/cap4执行显式caller schedule。continuation启动前，在同一context中切换UB为4或SERIAL的1，保留KV/positions/pending/native greedy状态。所有切换、同步和可能的reservation属于真实请求成本。

如支持接口不能在同一context里合法绑定，S0记录确切障碍；不自动恢复外部KV来“代替”自然执行，也不引入额外model context或更大内存占用后不计费。

新graph需保留：实际strides、Q `(d,q,h,1)`→`(d,1,h,q)`、mask同步、共享K/V（不可重复投影）、integral GQA、原operator params、输出顺序；PQ按query做局部子图，SERIAL才是target-wide U1。q1应调用共同native路径；q>4、FA、MLA、额外bias/sinks、多stream直接不支持。

role/phase必须在observation关闭时仍然生效；新request reset正确恢复prefill；cache reuse身份含layout/phase需要的拓扑变量。固定counts/heavy之外不能改变数学路径。prefill宽度可能128/512，故不能把本研究q<=4的consumer guard错误应用到prefill。

保留ggml/ggml-base/ggml-cpu/ggml-vulkan既有字节；新的llama graph library和actor允许按上述范围重编译，并清楚列出其新身份。若ABI不兼容、需要shader或算术backend变化，则STOP_SCOPE_EXPANSION，不能声称数值runtime全部未变。

## 3. 原参考、模型与计量

R真实指向PR92 R_stock已冻结的可执行文件/参数/模型/输入包装；不是名字相同就通过。R_PORT在新build上关闭所有变换，重现同recipe，桥接全部四任务两个重复。初始capacity或实际partition有不同就明确记录，不预设P128一定是reference-state exact。

target固定`Meta-Llama-3.1-8B-Instruct-Q6_K.gguf`（6596011424 bytes，SHA256 `33981adf6bae52c503fb5c24f72539010632f7ed290a56c1315a8cd50adca587`）；draft从PR92真实冻结取得`Llama-3.2-1B-Instruct-Q4_K_M.gguf`完整身份，不猜hash。完整词表和EOG需现场从固定model/source复核：本CPU协议绑定128256词表及EOG {128001,128008,128009}；不符则改协议需在native前重新审查，不用硬编码掩盖错模型。

一份总runtime_fingerprint应绑定**按arm选择的**原参考binary/new actor/library及backend模块、compiler、driver、source inventory；不能把同一可执行文件无差别套到R与candidate。每个进程actual加载模块需与对应route核对，而不仅核对磁盘文件。

每worker：先登记LOAD_STARTED/attempt，创建owned子进程，读取READY且load_forward_calls=0，验证权重与KV在Vulkan0、driver/LUID/headroom>=536870912 bytes，然后发送已校验请求。S3 warmup后清空target/draft KV、sampler、pending、phase和计数，才开始测量。**测量前process总forward不应为0**：warmup已经发生；zero-forward检查只约束初始化无隐藏推理。

## 4. 新协议与raw来源

`study.native_request`定义新的`SYSTEM_COMPOSITION_V1`外层schema，不是声称旧worker接受这些字段。实际native frontend须解析并回显slot/recipe/原始token/schedule/plan fingerprint；host用`admit_request`逐字节检查真正发送对象后直接发送，不再lookup或重新构造。生产请求禁止restore、外部KV或logits路径。

对每个COMPLETED记录留四个不同的、被raw_pins列出的真实源：

1. `raw_request_path`：实际发送的完整wire请求（含plan/runtime绑定）；
2. `raw_result_path`：native实际输出，含slot/status/pid/worker_id/output/observation_mode/natural_prefill/restore_used/actual_prefill_schedule/counts，与导出字段一致；
3. `raw_timer_path`：控制器单调ns起止、slot/pid、scope=`INCLUSIVE_NATURAL_REQUEST_WITH_SELECTION_AND_STATE_TRANSITION`；从请求策略选择起，到完整最终response止。包括prefill/normal sync/draft/verify/reconcile，不含model load；
4. `raw_identity_path`：当前进程对应来源、真实加载验证回执、load_forward_calls、pre_request_reset_passed和observer状态。

不能把raw_result定义成分析器再生成的“理想摘要”。若原worker字段不同，固定adapter要从实际原始REQUEST/RESULT/trace逐字段转换，并保留原始字节和映射源码；至少用一套独立读取脚本核对转换，不把转换器写出的PASS当自证。

失败保留`raw_failure_path`，有slot/status和真实lifecycle；未启动的后续slots保持missing。启动数、请求发送数、decode调用、成功micrograph、occupied rows分开记账。不能把错误输出作接口失败而擦除，不能把错误输入作有意义负结果。

## 5. 运行控制必须由host补齐

当前CPU文件不提供Popen执行器。host必须补齐：一次性执行F0、完整前瞻plan/源体/module/输入/budget冻结及远端回读、顺序stage执行、每worker唯一lifecycle、单调时间/磁盘/内存watchdog、只结束owned PID、append-only ledger、raw状态保存、三session间隔>=15分钟、每个arm/任务的输出资格及heavy/counts对应。

无native失败时按固定stage顺序推进，不等待RTX，不重复请求作者确认既定常规步骤；若要超出本文模型/数值backend/请求预算/计划则先停止并申请变更。提交新F0不能使已经发生的请求变成事前注册。本PR的设计提交不是execution F0。

CPU必须补端到端合成：0/1/2/3接受长度、全接受bonus、首错、EOG、cap余量1、pending只消费一次、错误mask/位置、target/draft trim、反向phase切换、reuse/observeroff、正确hash错route、load失败、time/disk限额。测试不足以证明GPU数值一致，但能避免再次只测局部helper。
