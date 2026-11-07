# PR112 27cfad39：纯 CPU 对齐与夹具审查

审查对象固定为 `27cfad39cbffcac413760900c6deedbb93bdfc78`。本轮新增内容仅在
`host/alignment_review_v1/`，没有启动 GPU、设备查询、模型或 CPU/GPU 图计算。
只启动一次 GGML 元数据程序，构造图和检查地址；后续诊断程序仅离线编译。
原 S1 仍为 **2 次尝试 / 5.109 owned 秒 / 159 未启动 / S2、S3 不准入**。

**确定的源码与条件**

冻结 `ggml-vulkan.cpp` 实际 SHA256：
`04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d`，
与原 `HOST_SOURCE_BINDINGS.json` 中的期望值、实测值一致；没有使用当前上游源码。
原构图 `native/host/vulkan.cpp` 的 SHA256 为
`3dccfa2f6f54673076d0990cfa1c0b032c24bb74e5fb436be66cfee0436605a1`，
与原 S1 F0 一致。函数摘录、行号和相邻恢复源码哈希在
`FROZEN_SOURCE_REVIEW.json`。相邻 allocator/backend/softmax shader 文件不是原 F0
逐文件绑定项，本轮单独记录身份，不把它们声称为新增的历史编译证明。
ACTOR_SOURCE_FIXED.zip 不含这些文件，本轮也没有用其替代源码证明。

第 8301 行属于 `ggml_vk_tensor_subbuffer(ctx,tensor,allow_misalign=false)`：

1. 离散设备路径取 `O = vk_tensor_offset(tensor) + tensor->view_offs`。
   `vk_tensor_offset` 对视图取已展平根 `view_src->data - 0x1000`，对非视图取
   `tensor->data - 0x1000`。视图偏移只加一次；GGML 的新建/视图初始化也相应展平。
   UMA 的 host-pinned 路径另有 `ggml_vk_host_get`，历史设备记录 B570 为非 UMA。
2. 令 `A=minStorageBufferOffsetAlignment`，`e=ggml_type_size(type)`。
   `D=O & ~(A-1)`，必要时每次再向前减 A，直到 `(O-D)%e==0`。
3. `misalign_bytes=O-D`。只有 `allow_misalign || misalign_bytes==0` 成立才继续。
   descriptor range 还会加上这段回退字节。F32/F16 元素对齐不能推出描述符对齐。
4. `allow_misalign=true` 也不是充分条件：后续 push-constant 类型必须真正传递
   shader 使用的偏移。通用模板第 2594–2598 行反而要求所有偏移为零。

**最可能触发位置，及证据强度**

历史首个图确实是 q1/MQ，没有应用 QH 变换。纯 CPU 重建显示可执行顺序是
`QK MUL_MAT → SOFT_MAX → AV MUL_MAT → CONT`，第一个 QK 的 src0=K、src1=Q。
K 是连续 F16；没有 Hadamard hint；目标 `ne1=1`。静态路由最可能是：

```
ggml_vk_mul_mat:10263/10265
  → ggml_vk_mul_mat_vec_q_f16
      9831: destination          allow_misalign 默认 false
      9832: src0 = K             allow_misalign 默认 false
      9833: src1 = Q             allow_misalign 默认 false
        → ggml_vk_tensor_subbuffer:8301
```

Q 的根内偏移明确为 32 字节；K 和 QK 输出没有该显式视图偏移。即使 q1 的逻辑数据
紧凑，Q 的 `nb1=4096`，仍不满足后端 `ggml_vk_dim01_contiguous` 的 `nb1=512`
检查。通用 matvec 在后续可能拷贝/转换 Q 之前，已经先调用第 9833 行。
若根偏移 `B` 已满足描述符对齐，则 Q 的要求为 `(B+32)%A==0`；若 `A>32`
且为通常的二次幂，这不成立。它是首个显式非零起始偏移，也是最强的源码解释。

**这仍是条件性定位，不是动态调用栈证明。** 历史记录没有 A、B、实际 descriptor
offset、misalign_bytes、具体触发 tensor 或调用点。相邻 allocator 源码显示独立
tensor 分配按 buft alignment 舍入、视图继承根 buffer；但这些具体运行偏移没有记录。
对假设 A 整除 `0x1000` 的单 buffer 分配可作对齐推导，不能把假设写成实测。
错误码 `0xc0000409` 只和 stderr 的实际断言一起记录，不据此推断内存损坏。

**统一的地址/边界条件表**

以下 B 都表示对应根的实际 buffer 内偏移，历史数值均 UNKNOWN。
`OFFSET_CONDITIONS.zip` 内的完整 JSON 包含全部 16 输入、6 表示、3 存储策略的
每个可执行节点/操作数、ne/nb、根、视图偏移、字节范围和条件；其中假设 A 的例子
均标为 hypothetical，实际设备对齐结论统一为 UNKNOWN。

| 对象/表示 | 根内偏移与 stride（字节） | 消费路径的条件 |
|---|---|---|
| 原 Q / 所有 q1 公共图 | Q view=32；ne=[128,q,8,1]，nb=[4,4096,512,4096q] | 通用 matvec Q 要求实际起点零 delta；不能由 F32 对齐推出 |
| K | ne=[128,K,Hkv,1]，nb=[2,256,256K,256K·Hkv]，view=0 | 描述符起点取 B；内部行/head stride 不等于重新绑定 descriptor |
| V | ne=[K,128,Hkv,1]，nb=[2,2K,256K,256K·Hkv]，view=0 | K63/257 时行 stride=126/514；元素合法不证明全部向量访问资格；历史没有指向 V 的触发记录 |
| 原 mask / MQ | ne=[K,32,1,1]，nb=[4,4K,128K,128K]，view=0 | 小 softmax 要求起点零 delta；内部行 stride=252/1028 本身不是独立 descriptor 偏移 |
| PQ Q(j) | 展平根偏移=32+4096j | q1 子链的通用 matvec 默认 false；条件按完整偏移检查 |
| PQ mask(j) | 展平根偏移=4Kj，即 252j / 1028j；ne=[K,1,1,1]，nb=[4,4K,128K,128K] | 小 softmax 虽传 true，随后通用模板第2595行仍要求零 delta；这是另一项潜在失败，未在原运行触发 |
| QH_C Q | permuted Q 经原有 CONT 后 reshape，packed 根内偏移=0 | CONT unary 有元素偏移补偿；packed Q 的 matvec 仍要求零 delta；不能省略原有 CONT 成本 |
| QH_C mask | view=[K,1,q,1]，偏移=0，nb1=nb2=4K | head 选列在同一个 descriptor 内按 stride/modulo 处理，不能把每列起点都要求 A 对齐 |
| QH_D mask | 同一 compact view 经真实 REPEAT 到 [K,1,8q,1]，新根=0 | REPEAT unary 有偏移字段；softmax 绑定新根；实际物化、分配和成本未执行 |
| QB4 / REPEAT4 Q 与 mask | Q view=32；mask view=0，query 进入第4轴；REPEAT4 有真实新 K/V 根 | 同标准逐节点列条件；QB4 没有原设备 census，不把 metadata 审查当支持通过 |
| QK / softmax / AV 中间结果 | 独立根=0，内部 stride 由 ne 决定；PQ 各链各有根 | 起点与行内 stride 分开检查；MQ q>1 走矩阵路径，其原始 descriptor/转换分支须另查，不能套用9833 |
| 输出恢复 | PERMUTE/RESHAPE 偏移=0、继承 AV 根；CONT/CONCAT 是实际操作 | unary/concat 各有元素偏移编码；仍检查范围与编码位宽，不把 VIEW 计作 shader |

softmax 的关键证据：K63/257 都进入第13882行 `ggml_vk_op_f32`；第12278行传 true，
第12284行实例化 `vk_op_soft_max_push_constants`。冻结文件没有该类型的偏移特化；
其结构和恢复的 shader 没有 descriptor 起始补偿字段。因此 `(B+4Kj)` 未对齐时，
应预期的是第2595行模板断言，而不是直接假定为历史8301故障点。
例如**假设** A=64、B 对齐，j1 的余数分别是60与4；它们都能被4整除，却不对齐64。

原 supports_op 的 MUL_MAT/SOFT_MAX 分支检查类型/维度等，没有对本夹具的上述实际
起点建立完整保证。历史证据分别是：五表示80组支持查询 PASS；buffer 归属只有
已启动 q1/MQ 的计算前记录 PASS；成功执行0；GPU数值资格 UNKNOWN。
QB4 的支持、其余图的实际归属、成功执行和数值资格都不能从 CPU 重建补成 PASS。

**仅限夹具层的候选修复**

候选 Q0：把 Q payload 放到其独立 base 存储起点，base 少32字节前缀，Q view offset
由32变0。逻辑 Q/K/V/mask 字节、ne/nb、全部算术操作和精度参数保持不变；物理布局和
元数据发生变化，不称为原布局通过。原32字节布局/失败始终保留为历史与边界用例。

候选 Q0+PQ_SLAB：在 Q0 基础上，每个 PQ softmax 的单列 mask 复制到独立 F32 slab
根，视图 offset=0，保留旧视图的 ne/nb，再绑定该 softmax。它不加 GPU CONT、
不修改 stride 或 shader，但改变输入叶节点/所有权和分配；增加 q·K·4 逻辑存储字节、
CPU 拷贝和 GPU 上传/校验，allocator 舍入后的真实内存另计。q2/K63 为504字节，
q2/K257 为2056字节；旧32行 mask 保留，不拿删去未用存储制造收益。

所有表示仍使用同一地址/边界规则。QH 的原有 CONT、QH_D 的真实 REPEAT 均保留。
增加额外 CONT 会改变算术图/成本；给 mask 行补齐 stride 会改变布局，而且与冻结
`ggml.c:4105` 的 contiguous mask 要求冲突；物化 mask 是新存储/拷贝成本。
本轮均没有把它们混称为无影响。没有删断言、强制 allow_misalign、改 shader、精度、
归约或 K63/257。当前候选不需要广泛改后端；若它仍失败，停止并报告，不继续扩建。

CPU 检查：288 个真实 GGML metadata 图（16×6×3），没有 compute；原五表示80组
metadata 与历史 census 的 op/type/ne/nb/view_offset/op_parameters 逐项一致。
1,260 个展平视图边界检查、737,280 个 Q 字节地址和921,600个 mask 字节地址检查通过；
三个策略的所有算术节点元数据一致。mask REPEAT 的检查是源地址映射模型，不冒充实际
执行或物化结果。7个地址回归和2个禁止启动的 mock 准入测试通过。

保留的问题记录：首次离线编译发生 logger 变量重名，重命名后成功；一个整数单测
最初把12本身已对齐误写成需回退，修正测试预期并保留失败收据。没有为数值输出改规则，
没有重跑 metadata 进程。原94个 PR112 文件 Git 内容保持不变；其中2个原生成 .diff
有既存 CRLF/LF规范化差异，单独记载，没有重写原文件。原 F0/输入/二进制/执行证据
按实际字节 SHA256 核验；见 FINAL_CPU_REVIEW_VALIDATION.json。

**待作者确认的最小原机诊断，不是恢复 S1**

新独立 F0：`DIAGNOSTIC_F0.json`，SHA256
`7a99f5b8e1c06051a6c916e5999201304bd6724ba0a49228f95d765e1b45ce3e`。
新程序/源文件/继承 DLL/driver/输入/七个请求/监督器已绑定；新程序已离线编译，
从未启动。F0 内 A 和实际物理偏移仍为 null。当前上限是 **7个图进程、最多7次图调用、
420累计owned秒、每进程60秒、128MiB产物；0模型/额外probe/warmup/retry**。
每个有偿进程内部记录 actual A、全部 tensor 的 buffer-relative offset、view root、
buffer 大小和完整 supports_op；没有另开免费设备查询进程。监督器100ms nominal，
actual gap 上限1000ms；GPU内存仍只是检查点，不声称连续驻留。

| 启动顺序 | 输入 / 布局 | 要区分的问题 |
|---|---|---|
| 1 | 公共q1/MQ，K63,H8/Hkv8，原Q+32；新增观测程序 | 在独立新坐标中记录原布局的实际A/偏移，检查与8301静态解释是否一致；保留可能的预期失败 |
| 2 | 同一q1/MQ输入，Q0 | 只移动Q存储起点，公共基线是否返回、输入保持、输出有限；不通过则停止全部q2 |
| 3 | q2/PQ，K63,H8/Hkv2，Q0，原mask切片 | 单独暴露PQ列偏移问题；只允许与实测偏移一致的2595断言作为预期负例 |
| 4 | 同一q2/PQ，Q0+PQ_SLAB | 检查独立mask存储是否消除该夹具条件；失败即停止 |
| 5 | 同一q2/QH_C，Q0，原compact mask | 保留QH原CONT，与已完成PQ比较全部向量，有限差异原样保留 |
| 6 | q2/PQ，K257,H8/Hkv2，Q0+PQ_SLAB | 在原奇数长度257检查PQ条件，仍不换长度 |
| 7 | 同一q2/QH_C，Q0 | 检查compact mask另一行距及同输入PQ/QH差异 |

只有第1/3项可接受严格匹配物理布局和指定断言的预期负例；其余异常、输入变化、
非有限、归属或监测失败立即停止。新数据仍不能补出原动态调用栈，也不能由改布局
成功改写原失败。所有差异与新增拷贝成本保留；不输出端到端收益，不准入S2/S3。
不自动申请更多图或扩为完整 S1。
若第1与第2项都返回，必须先检查完整 q1 向量逐位相同，否则在 q2 前停止。
两个未批准的 F0 草稿保留；唯一当前执行对象是上述最终 F0。

待确认后唯一入口（本轮未运行）：

```
python host/alignment_review_v1/run_diagnostic.py --author-approved-f0-sha 7a99f5b8e1c06051a6c916e5999201304bd6724ba0a49228f95d765e1b45ce3e
```

本审查到此收束。是否运行上述7次有界新诊断，等待作者另行确认。
