# 双平台实验 PR：独立 CPU 设计与门禁复核

日期：2026-10-27。角色：独立审查代理，未编写两个实验包的作者实现，本轮未修改作者源文件、未远程写入、未启动模型/GPU。审查沿用统计分析、科学批判性思维和审稿技能中的抽样单位、声明—证据与失败门禁原则；这不是外部人类同行评审。

**最终结论：两个包均可发布为预执行设计/CPU工具PR。RTX未发现阻断或重大必修问题；B570初版发现的两项重大门禁缺口已经作者修复，并由本审查定向复核关闭。当前未解决阻断/重大项为0。两包都没有新的native实验结果，也没有完成真实native正向bundle验收。**

## 1. 范围与判定标准

对象为 `experiment_prs/rtx/` 与 `experiment_prs/b570/` 的设计、冻结计划、CPU工具、测试和host handoff；本轮没有重新审查论文，也不评估未运行的实验结果。只检查可能改变科学结论或错误开放资格门禁的缺口，不要求扩大面板、增加GPU预算或引入通用验证框架。

两包均是设计/CPU工作包。新增原生请求、模型执行、实验结果为零；没有提供已实现并资格通过的新native worker。允许发布此类实验PR，不能据此宣称已经获得跨平台实验结果或可直接启动新增原生矩阵。

## 2. RTX：设计与CPU工具通过本轮范围内复核

### 预算、来源与执行单位

独立读取最终 SLOTS/DIAGNOSTIC_SLOTS 得到 **196 qualification、1008 formal、84 warmup**，共1288 factorial请求；12个family-session workers。Llama独立A1=18、A2=36，共54诊断请求；没有混入1008条性能测量。

我直接以保留的 PR144 `INPUT_MANIFEST.json` 和 `MODEL_CONTRACT.json` 原快照对照 PANEL，核对两份原文件SHA256；Qwen与SmolLM2各12/12条任务ID、源顺序、完整native prompt IDs与cap128完全相同。它们是固定、已暴露的独立transfer panel，未被包装成新的blind panel。

七臂每输入连续执行，顺序由固定hash与六个不同rotation给出；所有slot ID唯一。warmup每family-session七次、输入固定，不随输出追加。技术重试限制在正式session的完整新attempt，原失败保留，禁止把局部attempt拼成完整会话；数值失败不能以技术重试方式覆盖。

### 日期与统计量

代码以UTC时间戳转换到Asia/Shanghai自然日，要求三天、每天两次独立进程会话；进程及请求不跨其声明的当地日期，并检查相邻日期首次会话至少20小时。family顺序和owned process不重叠门禁也保留。

估计层次为每会话12输入等权log contrast → 每日两会话等权 → 三日等权。主要量 `I=log(D_QB)-log(D_GS)` 与 drafting 是否盈利分别报告；I>0不自动代表D_QB>1，也不自动代表GS/QB跨越parity。df2、两主家族Bonferroni的97.5%区间明确只是weak sensitivity；三日不能被表述为充分估计日期总体方差或建立一般功效。

### 门禁与Llama边界

公开 `analyze` 必须重新调用 `audit`，没有外部eligible=true快捷路径。缺bundle、缺arm、失败qualification、历史reference不匹配、未绑定runtime/date/resource、synthetic marker或未完成family固定分母均不能为受影响家族生成qualified_performance。另一家族独立通过仍要求共享host/process清理门禁。

RTX明示的 `is_synthetic` 必须恰为false；测试fixture被标识为synthetic。原生记录与envelope的identity、端点、cycles、state bounds、context、geometry和计时等字段需匹配，heavy vector inventory要求完整payload与hash，且PQ/QB比较不把仅端点一致当作全部向量一致。完整真实native正向bundle验收仍是PENDING，不能用CPU单元测试代替。

Llama默认54请求仅测试各context中固定layout的producer recipe。P1/P4_NATIVE不是同一donor state的跨layout移植；checkpoint restore、额外operator replay和修复确认默认关闭。旧反例A0只定位到已存endpoint输出81，不虚构更早的logit/operator归因。

### 实际执行的CPU复核

- 直接重跑作者14项synthetic CPU checks：全部PASS。
- 独立核对16个白名单科学/工具文件的size与SHA256：全部一致，总1,275,504B。
- 独立核对计划分母、slot唯一性、12个正式workers及所有expected_status仍为PENDING。
- 独立核对24条固定PR144输入；没有新tokenization或输入选择。

**RTX结论：未发现阻断或重大必修问题，可发布为预执行设计/CPU工具PR。它的正确状态仍是 PLAN_VALID / NOT_RUN / NATIVE_EXTENSION_REQUIRED。**

## 3. B570：科学矩阵正确，两项具体门禁缺口已修复关闭

### 已确认的设计边界

矩阵为B0=32、B1=120，总 **152 primary完整请求**。B0含新增16个speculative natural/resumed own-path sham，不能以C1恢复sham替代。历史controls为HumanEval/38的181 IDs和HumanEval/115的349 IDs，沿用cap64；8个尚未绑定新输入使用cap128。plan保持DRAFT_UNBOUND，新输入与native extension尚未具备执行资格。

producer为固定PQ的P1/P4T，P4T尾长3固定为2+1；consumer是C1/PQ/QB，spec k=1。所有cross结果限定于boundary0 clean-receiver合同，不把P4T移植失败直接宣称为未测自然生产路径失败。完整producer状态包括KV和initial logits，不能据此声称KV是唯一原因。

B570没有性能估计器；记录必须 `performance_eligible=false`，诊断时间不可转为速度收益。这个边界不同于RTX的synthetic/qualified_performance门禁。synthetic单元测试中的任何内部正向结构例子，都不是native资格或真实PR148复现实验。

独立重算本地保存的8份实际source snapshots的SHA256，全部与SOURCE_PINS吻合。我还直接读取固定 `native/formal.cpp` 的k1事务实现，确认真实cap/EOG尾部规则，避免修复误拒合法末尾。

### 重大问题 B1：restore读回缺证据仍可开放B0——已解决

**位置：** `work_package.py` 的 `audit_records`、`boundary_signature`，及HOST_HANDOFF的resumed record合同。

**修复前观察：** resumed路径接受 `checks.restore_roundtrip=true`、`extra_forward_calls_on_restore=0` 和 `imported_boundary_sha256`，但不强制保留实际恢复后再读出的KV/initial-logits payload。存在donor文件并重hash，不能证明receiver真的读回了相同状态。

**最小反例：** 我构造32条明确synthetic B0记录，提供实际临时donor文件及payload_root；16条resumed记录均不含receiver readback boundary。为隔离restore门禁，历史control audit在该fixture内仅作为synthetic结构收据，不冒称真实PR148运行。修复前结果为 `b0_qualified=true`、`errors=[]`、`payloads_rehashed=true`。

**影响：** 该CPU门禁可能把“声明导入donor”误当成“实际恢复后状态相等”，从而使后续producer-state总效应结论缺少关键own-path基础。

**最小修复要求：** resumed必须提供实际 `restored_boundary` 的KV、initial logits、positions、sequence ID，与donor的完整byte signature比较；payload重hash必须覆盖donor及receiver读回。没有实际payload核对不能开放B0。heavy请求的恢复initial logits还需与实际消费的target_initial向量一致。不能只新增一个布尔自报字段。

**最终修复与复核：** 作者加入必填的实际 `restored_boundary`，要求receiver读回KV/initial-logits文件、完整positions、full-vocabulary大小，与donor完整signature及heavy实际target_initial向量一致。donor两项payload也显式强制重hash，不能因缺path而跳过。我重新运行原32条synthetic负例：16条缺readback记录均报错，`b0_qualified=false`；新增测试还拒绝metadata-only、缺donor path、合法hash但读回内容不同及实际消费initial向量不同。该问题关闭。这是CPU门禁行为验证，不是native恢复资格实验。

### 重大问题 B2：k1非终止accept省略bonus被接受——已解决

**位置：** `work_package.py` 的 `cycles`。

**修复前观察：** 验证允许accepted=1时提交一个或两个token，未区分第一个commit是否已因cap/EOG终止。

**最小反例：** 合法cap64完整endpoint为64个非EOG token10；63个cycle都proposal=10、decisions=[10,11]、accepted=1、committed_ids=[10]、keep=base+2。修复前endpoint与cycles校验均接受，其中62个非终止accepted cycle错误省略了必需bonus，pending/输出与KV推进不再遵循真实worker。

**原生依据：** 固定formal.cpp先commit decisions[0]；match则accepted=1，且仅在未done时必须再commit decisions[1]；keep=base+1+accepted，随后记录target_kv_max、draft_kv_max。因此达到cap/EOG的accepted尾部可以合法只有一个commit，非终止accepted不能。

**最小修复要求：** 根据完整cap/EOG合同逐cycle重建精确应提交序列、done和keep；拒绝终止后额外cycle、非终止accept省bonus、reject添加bonus和不一致KV max，同时保留合法cap/EOG末尾。

**最终修复与复核：** 作者改为先commit row0、按真实cap/EOG决定是否强制commit row1，并核对两个native KV max为keep−1。我重跑原完整cap64负例，现抛出 `ContractError: native k1 commitment does not match complete endpoint`。新增有限测试保留合法cap/EOG尾部省bonus、拒绝错误trim与终止后额外cycle；与已读的固定formal.cpp实现一致。该问题关闭。

这两项是具体CPU门禁漏洞，不是要求更大实验矩阵。修复后152请求预算、8输入设计、native尚未实现的状态都没有改变。发现后已直接向作者交付最小synthetic反例，修复由作者完成，审查代理未编辑作者文件。

### B570最终稳定快照复核

- 实际重跑最终19项synthetic CPU tests，全部PASS；没有运行模型或native worker。
- 实际运行 `validate-plan`：VALID、DRAFT_UNBOUND、152 slots、native_executions=0。
- 独立核对最终白名单12个文件（原11个科学/工具文件加root的目录 `.gitattributes`），全部size/SHA256相符，总372,048B。
- 直接核对B0=32/B1=120、全部result=null、全部performance_eligible=false、execution_authorized=false、native_extension_implemented=false；两历史control的ID长度及cap64未变。
- 已独立核对8份真实保留source快照的SHA256。`audit-controls`代码实际比较历史reference的完整endpoint、cycles、vectors和geometry；本轮没有将synthetic测试中的历史收据说成真实PR148正向运行。
- 最终work_package.py SHA256：`0e81ae537b18f88c423708f6e087b96e99315590353d9f5650a80e8bc3762684`。
- 最终test_work_package.py SHA256：`3ab503834af9964208ad10d3d66a56a56acd1783a9f530b9d561d6a274e2675c`。
- 最终plan.json SHA256：`9c4fc67d3e7416a08e47f994e3a38a93e5ccad616cb768813d7907eb44b557a4`。

**B570结论：两项已证实的门禁风险已修复并通过本轮针对性复核，可发布为设计/CPU工作包。实际native extension仍未实现/编译/资格，不可把当前PASS描述成已完成B0原生资格。**

## 4. 发布与后续执行边界

原科学/工具白名单与发布整合文件分开：RTX原16文件；B570原11文件。发布整合在RTX的benchmark/scripts目录及B570的benchmark目录使用局部 `.gitattributes`（`* -text`）以避免Windows checkout换行破坏冻结hash，并加入本报告；B570最终白名单已包含这一第12个文件。这些发布整合文件不新增科学数据或改变实验预算。

不得把本报告或CPU checks的PASS用于宣称新GPU结果、native恢复成功或性能提升。RTX仍需新的ArmSpec/context/source-route实现、真实记录适配、host资源/日期绑定和原生资格；B570仍需实际选择冻结8输入、实现和编译boundary extension、真实32-slot B0及其原字节审计通过，方可进入B1。


本轮验证在两个有具体科学风险的漏检关闭后停止，未追加性能测试、扩大native矩阵或执行无关全套测试。报告的通过范围是已列CPU设计与证据门禁；真实host输入、模块、完整原始payload、原生正向资格和实际结果仍须由后续执行提供。
