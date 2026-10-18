# 直接发给 B570：PR119 CPU8 修复并持续推进

继续 PR119。作者最新明确授权：“不要再把门槛压得这么死，遇到阻碍自己修复可以继续”。
目标是完成原八项 CPU 验证并交付可信原始证据。你应自主定位、修复、回归、复审、
再继续；不要仅因需要修改入口、第三次复审、第四次修订或第21次开发尝试而停止。
本文件覆盖旧 CPU8_INTEGRATION、v3/v4 prompt 中上述次数/现场适配停止规则。
科学验收和实际证据标准不变，不扩展论文主线。

## 1. 来源、部署和总预算

锁定包含本文件的 PR119 提交，读取 README、RESULT、REVIEW_BINDING 和最终独立
审查报告，核对源文件哈希。runtime 是完整 adapter 源码，不需叠加多代不明覆盖。
历史起点3cc62d1c69804ee582b5077b0e27b9878064c8bf；fb20a198结果、三小时结果、
PR115/117以及所有旧失败和缺失保持原样。不要覆盖旧根或补造历史退出。

在 C:/hs/b570-capability-v1/<新UUID>/ 部署 runtime/source、runtime/src/rev2
和 runtime/legacy/repo，按精确字节复制。将本目录 CONTINUATION_POLICY.json 原样
放在新根。historical_context 只能作配置结构/工具位置/构建来源参考，不复制成
新注册、冻结、审查批准或PASS。新建本轮 ACQUISITION/CONFIG/CPU8_PLAN/TASK_START、
legacy/ROOT_BINDING、前瞻D0预约。保留原八项名称、顺序和normal_transition的8对/16槽位。
用真实工具绝对路径；工具版本变化可自主适配并记录，不假装旧绑定仍有效。

沿用已掌握的正式 exec_command/write_stdin 和独立 Python；不用共享Node私有接口。
临时文件保持本轮tmp，生产命令在既有观察器/Job下运行。编译或复用CPU launcher时，
必须核对C#源码、工具链和DLL摘要；复用已认证同源码构建可以，但标明复用，不写成本轮编译。
继续保留旧内层100ms/1秒、detector、封存、pending completion及清理判据。

从本轮首次准备开始，总计6小时（含下载、开发、复审、失败、恢复、发布）；
开发最多5小时，留下至少1小时给正式八项和交付。单次review最多900秒，
不设两轮总次数上限，不设0/1/2修订或20次开发尝试上限；每次都前瞻登记独立ID，
所有失败及实际启动仍计账。总存储1GiB、至少256MiB收尾预留、磁盘剩余10GiB，
每case/观察器的CPU进程、RSS、日志和硬截止仍按现有profile。不得通过新UUID清零时钟。
若预算将不足以完成下一动作和收尾，进入诚实收尾；不要为了凑几小时空转。

## 2. 开发循环：发现问题就修，带证据继续

先跑新28项 test_continuation_v5.py，以及原入口、身份、异常、预算、桥接和审计回归。
执行实际四入口预检，验证 continuation_policy / evidence_contract 等依赖及源清单。
然后验证原生observer三个smoke、200-worker churn、应用断点负例、健康C1/C2/C3、
冻结反例和watchdog停滞；最后bridge正常和journal_write_failure的D0控制点。
源码来自上轮已跑通版本，保留其 CREATE_NO_WINDOW 与UTF8修复。

已有成功结果仅当本轮源码/依赖/工具身份完全匹配且控制点相关代码未受改动时可继续用，
必须写明来源和依赖哈希；不能把旧报告中的PASS替代当前入口/路径验证。
修改只影响交付审计时，重跑审计反例与相关重建，不重跑所有健康原生用例。
修改影响观察器/监督器/控制器时，重跑受影响原生门槛。不要反复三小时soak。

遇到导入、编码、路径、console、句柄、计账、清单、schema或其他接入问题，
先保存原始错误和实际退出/清理证据，再修改本轮源码，加能触发该问题的回归，
给修订生成唯一源码摘要和变更说明，在新的run ID下继续。不是每次都回用户报BLOCKED。
不得删失败、改旧结果、跳过清理、降低资源/科学判据，或把未到达控制点算负例通过。
若实际进程仍未受控，先恢复清理，不继续启动更多任务。

review ID 可用 full-review、full-review-2、full-review-3……；不要复用目录。
完整候选独立P0–P2复审发现问题后，自行修复、针对性回归，再复审，预算内继续。
每轮必须实际结束并保存报告、输入字节清单和观察器退出证据。最终candidate需要
真实scoped-clean；不能把findings报告、工具退出0或本地交付审查冒充部署审查。
审查不得修改候选、不得绕过隔离；取证输出可保存在候选之外。
审查/下载工具短暂故障可在保留回执后修复或重试，消耗同一个总预算，不是实验PASS。

## 3. 冻结与正式八项

完成受影响门槛和独立复审后，更新本轮 ENTRY_SOURCE_MANIFEST.final 与实际预检、
FINAL_REVIEW_BINDING、INTEGRATION_GATE_BINDING、D0证据快照和原始审计绑定。
运行 source/freeze_cpu8.py。冻结应包含 CONTINUATION_POLICY.json 和实际完整源码；
原协议 acquisition/repair 文件是历史来源，另存本次授权prompt，不能假称旧协议批准了新预算。
旧接口要求的来源文件可按其字段复制并标明历史来源，执行规则以本次授权为准。

通过 source/outer_watchdog.py --mode cpu8，指定 source/cpu8_supervisor.py、
真实root/run、冻结SHA和可用phase-limit，保存真实工具请求、会话和最终回执。
按原 CPU8_PLAN 串行执行：normal_single、normal_transition、terminal_pending_completion、
frozen_input、late_closed_slot_write、resource_read_failure、directory_read_timeout、journal_write_failure。
每项都核对真实控制点、目标detector、OS退出、I/O完成和原始审计；正常/transition/
清理界限仍90/180/30秒，外层5秒不替代内层1秒。

正式批次内不得改源码或就地重试。若出现工程缺陷：结束并封存该批次，标明失败及后续
UNSTARTED，恢复开发修复循环；允许在同一总预算内建立新的冻结批次重新执行八项。
若现有实现只接受单个冻结根，可创建新的attempt根并适配campaign索引，保存原根不可变，
沿用最初first_preparation_utc；跨attempt的所有失败、时长、存储与进程消耗累计，
既有actor启动/寿命上限也不得重置。适配代码需要对应回归和复审；无需再次请示。
只报告最后一个完整冻结批次的八项资格，同时列出全部早期失败，不拼接不同版本的PASS。

## 4. 完整交付，不因运输问题推翻实验

停止所有本轮受控进程后封存证据树。清单必须覆盖整个封存root中的每个文件，
只排除清单自身；不得通过排除目录漏掉失败。清单生成后不再往封存root添加文件。
外部completion receipt、下载/恢复回执和最终发布尾部记录放在封存root之外，
明确绑定原清单SHA及其自身SHA；远端恢复到另一新目录后按包内未修改核验器重建。
WATCHDOG_RECEIPT必须逐字段匹配WATCHDOG_END.receipt及真实生命周期，不能缩短end_ns。

归档直接下载404时可使用正式GitHub blob/Base64等运输方式，核对同一归档SHA，
不重新实验、不修改包内证据。接口问题可自行修复；未恢复成功只能先报PENDING_DELIVERY，
不得假称恢复完成，也不把运输故障当作八项原生失败。
最终通过才报CPU8_INTEGRATION_PASS；仍有实质问题或预算耗尽则诚实报告证据和未启动项。
保持Draft、不合并、不启动GPU或后续科学任务；报告全任务总账仍有的UNKNOWN。
交付PR119新UUID实现、全部修订/失败、原始包、恢复认证和结果，最后给出最终提交。
