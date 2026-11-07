# Reference-Constrained Mapping Costs and Hardware Implications
# 参考契约约束下的映射成本与硬件启示

写作状态：可供论文整合的章节草稿；不是已发表主张，不改写当前论文源码。
证据索引见 [EVIDENCE_MATRIX.md](EVIDENCE_MATRIX.md)。C01–C12对应其中的审查主张。
范围：PR120–123的固定RTX实验；前序模型请求结果应在原系统章节单独报告。

## 一、章节定位与中心论点

本章应回答：“保持指定参考行为时，哪些映射可采用，收益在哪里兑现，
又有哪些表面上的硬件优化机会会被强软件基线和完整成本核算消除？”
本章提供资格约束、受控机制证据与适用边界；不宣称新加速器或普适最优映射。

建议在论文主方法与系统评估之后设置本章：
1. Reference contract and admissible mappings；
2. Measurement controls and strong software baseline；
3. Execution-mode and backend-boundary interventions；
4. Charged representation costs；
5. Implications and limits for hardware design。

不要按PR编号写成实验日志。PR120生命周期诊断用于解释证据为何可信；
PR121用于建立比较基线；PR122/123构成主论证的受控干预与反例。
若篇幅紧张，故障账本/归档表/完整坐标移入附录，阴性结果仍留正文。

## 二、形式化定义：描述研究对象，不把实测包装成定理

固定运行环境 e、输入 x、参考输出 R_e(x)、候选映射 m。
定义经验合格集合：

A_R(X,e) = {m : 对每个已测 x∈X，ordinary(m,x,e)逐字节等于R_e(x)，且执行控制通过}。

这是已测输入上的资格集合，不是所有输入的等价性证明。执行控制包括输入生命周期、
真实设备放置、完整结果、计算返回和同步；原运行时资格不自动迁移到新编译器/设备。

成本必须带窗口：T_W(m,x,e)。只有同一X、e、W与配对设计下的比较才成立。
以实用可选软件基线 b∈A_R 为比较对象；本轮固定QB仍是适当基线，
不可用不合格映射、未计转换的理想布局或逐点事后最快值替代部署基线。

对于表示变换P，至少需要：
1. P保持逻辑输入和可见token；
2. transformed ordinary仍满足原R，而非另建一个更宽松的参考；
3. 在同一起点的完整事务中，转换后方案优于b。
PR123正展示这三个条件不能互相替代。数学上屏蔽新增列，不保证指定后端输出字节相等。

对于硬件构想，系统机会只能在额外假设下写成上界：
若可优化阶段在无重叠串行请求中占比例f，阶段加速s，则
S_system = 1 / ((1-f)+f/s)，理想s→∞时上界为1/(1-f)。
本组实验没有测得自然请求的f，也未验证无重叠假设；因此不能代入微图比值估计请求收益。
若存在CPU/GPU重叠或关键路径迁移，应改用实际依赖时间线，不能简单加阶段均值。

## 三、可直接整合的英文正文

### Reference contract and admissibility

We evaluate mapping choices under a fixed implementation reference rather than
assuming that mathematically equivalent tensor organizations produce identical
floating-point outputs. A mapping is admitted only when its complete ordinary
output matches the prescribed reference bytes and the execution controls pass.
These controls cover input integrity, device placement, operator support, runtime
identity, compute completion, and synchronization. The resulting admissibility
set is empirical: it applies to the tested inputs and frozen environment, not to
all prompts, backends, or arithmetic implementations. Output correspondence also
does not identify the deployed reduction tree or establish greater accuracy
relative to real arithmetic. [C01–C02]

A lifecycle diagnostic motivated these controls. Under the original allocation,
later graph nodes reused storage holding K and V; repeated execution therefore
consumed modified inputs. Address and byte witnesses, re-upload interventions,
and a return to the original allocation distinguished this failure from a
mapping-specific arithmetic failure. Independent persistent input storage
restored the required input and output bytes across repeated calls. We use this
finding to establish the validity of subsequent measurements, not as evidence
of an accelerator opportunity. [C01]

### Measurement controls and the software baseline

Initial completed-graph measurements favored QB over QH_C. A subsequent
balanced study added two arms executing the same QB implementation, separate
sessions, paired block analysis, and an observer selected using A/A behavior.
Its core q2/q4 panel yielded QB_A/QH_C = 0.900826, with a mean difference of
−7.499 microseconds; the alternative QB arm yielded 0.901081. Nineteen of
twenty-four geometries supported lower QB cost under the declared descriptive
screen, while five remained unresolved. The pilot's median A/A envelope scale
fell from 16.054% to 2.762%, which does not certify two-percent resolution for
every geometry. [C03–C04]

A frozen rule predicted the direction of the twelve held-out q3/GQA input
means, but overestimated the cost gap. Including measured feature and lookup
cost made its offline estimated cost 1.010298 times that of fixed QB. Thus,
directional predictability did not translate into a useful selection policy.
This negative result motivates retaining a strong fixed baseline rather than
treating every observed ordering change as an opportunity for adaptation.
The selector estimate is a phase sum, not an integrated decoder measurement.
[C05]

### Execution mode changes the apparent mapping opportunity

We next compared graph-disabled execution with actual CUDA Graph capture and
replay. Instrumented qualification hosts established capture, instantiation and
replay for the relevant signatures; clean timing hosts were bound to the same
graph and runtime identities without loading the observer. On the selected
geometries, QB_A ON/OFF completed-cost ratios ranged from 0.615 to 0.849.
For four permuted-q2 coordinates, the absolute QH_C-minus-QB_A gap decreased
from 12.056–12.975 microseconds to 0.735–1.627 microseconds. The intervention
therefore materially changes the apparent mapping opportunity. It does not
isolate every CPU submission component or demonstrate end-to-end speedup.
[C06]

A substantial geometry-dependent boundary nevertheless remained. At key
extents 1023, 1024 and 1025, the observed QB kernel counts were 8, 3 and 8,
and clean ON completed costs were 113.085, 50.439 and 114.618 microseconds.
The traces establish an execution-path boundary; kernel counts alone do not
identify a bandwidth, occupancy or arithmetic bottleneck. In this original
comparison, logical sequence extent and causal visibility also changed.
[C07]

### A controlled representation intervention meets the reference boundary

To separate logical visibility from physical extent, we retained each logical
input and its original mask columns while appending finite zero K/V elements
and fully masked columns. For logical length 1023, physical extent 1024 reached
a three-kernel path in the observed first execution, but failed the original
unpadded reference-byte qualification in all four qualification hosts.
Physical extent 1025 preserved the reference in all four hosts, retained eight
kernels, and increased completed cost by approximately 1.5% relative to both
native QB controls. Padding logical length 1024 to 1025 or 1026 also failed
the exact-reference requirement. [C09–C10]

These results distinguish a reachable backend path from an admissible
optimization. We do not report a clean speedup for failed paths: they stopped
at the first mismatching output and lack qualified steady-state measurements.
Nor do we interpret their finite numerical differences as proof of incorrect
mathematics or degraded model quality. The first internal divergence remains
unlocalized, and the source-to-DLL correspondence remains unauthenticated.
The intervention changes physical work as well as dispatch, so it does not
identify an isolated causal effect of kernel count. [C09]

### Charging the representation transaction

Compact Q removed one repeated copy kernel from the observed QH path.
However, reducing a candidate's own graph cost is insufficient when the
representation must first be produced. We therefore measured one continuous
ON transaction from a common preexisting permuted host Q through copy or
transpose, Q upload and completion, graph replay and synchronization, and
complete ordinary readback. K/V and the mask were resident, and targets were
preallocated. This window excludes original model-Q production and ongoing
KV-cache updates. [C08, C11]

For q2 and q4, compact-QH/QB_A transaction-cost ratios were 1.002216 and
1.001598; ratios against the second identical QB control were 1.008295 and
1.004167. No candidate satisfied the predeclared practical screen against
both controls. We therefore close this compact-QH optimization branch for the
tested inputs and retain QB. This is an absence of established practical benefit
within the measured scope, not a proof that the implementations are equivalent
or that other devices and workloads cannot benefit. [C11]

### Hardware implications and limitations

The combined evidence supports a reference-constrained view of mapping costs:
a representation must first be admissible, then competitive under a strong
execution baseline, and finally beneficial within an explicitly charged
transaction. The measurements show why an apparent graph-level opportunity
cannot directly motivate new hardware. They do not establish a calibrated
physical bottleneck, a natural-request critical-path share, or area, frequency
and energy tradeoffs. Consequently, the hardware decision remains
SOFTWARE_FIRST/HOLD. [C12]

The studies use one RTX platform and exposed or synthetic inputs. Their
successive hypothesis selection is adaptive; the selected boundary tests are
not blind replications. Within-host repetitions are technical repeats, and
separately started sessions are not independent devices or dates. Invalid
clock telemetry remains unknown, endpoint readiness does not demonstrate
continuous exclusivity, and a brief CPU audit overlapped one PR123 session.
Raw archives were restored and reanalyzed locally; remote verification of
compact Git artifacts is not external validation of the full raw data.
These limits delimit the claims without erasing the observed admissibility
failures and software-cost results.

## 四、正文图表安排

| 图/表 | 展示内容 | 数据来源 | 必须出现在图注的限制 |
|---|---|---|---|
| Table: admissibility vs representation | L1023/1024与S1023–1026资格；kernel数；仅合格路径成本 | PR123 RESULT、NUMERICAL_MISMATCHES、TRACE_SUMMARY | 不合格路径无性能柱；首调用trace不等于稳态replay |
| Figure: execution-mode interaction | 四个permuted-q2坐标OFF/ON下QH−QB绝对差；配对区间如来自原分析 | PR122 ABSOLUTE_COSTS及原ANALYSIS | 坐标分开；profile与clean分开；不把均值之比冒作原配对估计 |
| Figure: charged ON transaction | q2/q4的QB_A、QB_B、QHpermuted、QHcompact总事务与分项 | PR123原host/cost表 | 总事务直接计量；分项非完全加和时保留未分配开销，禁止调数凑齐 |
| Table: evidence ladder | C01–C12按契约、基线、窗口、范围 | EVIDENCE_MATRIX | 这是证据组织，不是新的算法/硬件贡献 |

本交付规定图表内容，不伪造新的统计区间或新测量图。
最终绘图应直接读取固定提交的生成表；图注列出样本单位与精确比值方向。

## 五、贡献陈述与审稿防线

建议的有限贡献陈述：
“We characterize how reference admissibility, execution mode, and charged
representation costs jointly constrain mapping choices on a fixed RTX backend,
using balanced controls and targeted representation interventions.”

不要写：
- “We propose the first head-query fusion architecture.” 本组实验不建立该新颖性。
- “Padding is invalid for attention.” 失败的是固定后端与指定字节参考下的特定路径。
- “CUDA Graphs remove all mapping overhead.” 存在残余成本，且机制未完全分解。
- “QB is universally optimal.” 仅为已测条件下的强基线。
- “Our hardware model predicts RTX gains.” 抽象CPU模型无RTX物理校准。
- “No hardware opportunity exists.” 当前证据不足以批准设计，不是无机会定理。
- “All experiments independently reproduced remotely.” PR120–123 raw仍本地。

若审稿人质疑逐字节契约太强：应解释它服务于本论文所声明的参考行为，
并承认更弱的数值/质量契约可能得到不同可行集合。放宽契约需要新的预注册评估，
不能事后将失败路径改成成功，也不能仅靠误差阈值替代请求/质量验证。

若质疑新颖性：将本章定位为主方法的机制与适用边界证据，避免把测量规范、
CUDA Graphs或padding本身包装成发明。能否构成更强独立研究贡献仍需相关工作
比较和跨后端验证；本次整理没有新增“首个/首次”检索认证。

## 六、后续研究决策

现在可做：整合主张、引用原表、与B570独立结果对照，形成有边界的章节。
本轮关闭：在相同q2/q4输入上继续追逐compact-QH微小优势、补齐快速路径、
或基于离线方向预测扩展selector。
硬件重启条件：明确新假设，强软件基线后仍存在可测物理瓶颈，并证明其占据
真实工作负载关键路径；然后才讨论模块、资源、精度与PPA验证。
