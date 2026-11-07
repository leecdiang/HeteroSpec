# PR119 Windows入口修复实测：ENGINEERING_BLOCKED

锁定提交 dda93f5bd8f787b4c88f369072e4aba63e3e080c。新UUID 14a37e28-9d85-4e76-8032-83a3b14a3e10。本轮运行已交付源码版本，未改源码、未重试、未生成执行F0；原八项全部UNSTARTED。

## 已实际完成

- 三层精确部署：原始legacy源码/依赖、历史adapter覆盖、本次entry修复覆盖。26个复审源码摘要与17个证据摘要全部一致；所有远端文件逐字节通过Git blob认证。仅新根写入；旧根未复用。
- 正式Python查询Windows/System目录和解释器身份；真实系统为Windows AMD64、Python3.12.10。没有补填SystemRoot。早期工具/便携进程OS生命周期缺失单列。
- 31项入口回归、原30项能力回归、11项预算回归全部通过。
- 真实隔离子进程四入口预检 STARTUP_PREFLIGHT_PASS；模块实际来源正确。不是mock结果或原生门槛的替代。
- observer正常review smoke：21个身份实际关闭；case上限负例：21/21关闭；review上限负例：65/65关闭。两个负例均由live_process_count真实触发，原始核验器确认正确原因和空Job。包含conhost辅助身份，不能当作actor数。
- 健康C1/C2/C3全部通过，5个actor实际退出；外层正常有效间隔最大1.020153600秒，按本能力层5秒规则审计，绝不追认为旧内层1秒资格。
- 4项实际win.freeze_check反例全部正确拒绝。
- watchdog真实暂停后身份与RSS仍可读；最后进度过期5,001,125,500ns时监督器拒绝；第二用例未启动；20秒独立救援未触发；监督器/watchdog真实退出且Job空。原始native_gate_audit重建通过。
- 本轮C#真实编译成功，DLL39424字节、SHA256 faa2dca04aa8555a8269a1119475dea5c931138778a0c2e4203c1d8252964a8e。仅compiled证据，未加载、未混入source-only导入树。

## 首个实际阻断与证据界限

完整候选独立复审仅启动一次，使用修复后的review_entry与独立review profile，900秒截止。复审未形成最终报告：生产observe.py第60行抛出RuntimeError('duplicate PID')，OS_EVENTS seq144保存完整栈。最后资源决策未超限；不是旧8进程误用，也不是审核clean。

该分支以PID为observed字典键，已关闭PID仍在字典内，这是源码可见的复用风险。原始记录PID22360的旧conhost身份创建FILETIME134367912881575333，seq101已实际关闭；seq154又有EXIT_OBSERVED/124，却没有对应的新创建身份与实际退出FILETIME。触发CREATE的PID/新身份未被保存，故不能声称唯一因果匹配已证实。不得补造该身份或生命周期。

INCOMPLETE记录cleanup_confirmed=true；已记录复审43个身份均实际关闭，FAILURE_JOB_EMPTY seq180证实该时点Job为空。这不消除额外退出观察的身份缺口，也不证明整机全部进程状态。监督器自己、工具外层和晚期交付进程的生命周期继续UNKNOWN。

按新prompt立即停止，未现场修源码、未再次审查。未执行bridge D0 smoke/其反事实回归；未产生完整adapter独立clean或正式执行冻结。旧legacy SOURCE_REVIEW_FREEZE保持历史数据，未伪造当前批准。

## 正式八项

| 用例 | 状态 |
|---|---|
| normal_single | UNSTARTED |
| normal_transition（8对/16槽位） | UNSTARTED |
| terminal_pending_completion | UNSTARTED |
| frozen_input | UNSTARTED |
| late_closed_slot_write | UNSTARTED |
| resource_read_failure | UNSTARTED |
| directory_read_timeout | UNSTARTED |
| journal_write_failure | UNSTARTED |

0/8启动；不报告CPU8_INTEGRATION_PASS、ENGINEERING_READY、旧57项资格或论文结论。

## 成本和原始重建

D0预约12/20，实际11项（3个observer smoke＋健康3＋冻结4＋停滞第一项1）；停滞第二项按设计未启动。完整复审1/1，0个最终clean；源码编辑0、单个交付版本。正式GPU/模型/科学操作全部0。

观测命令前缀159个创建/159个实际退出、寿命和490.2769318秒；加上6个独立内层actor，去重已识别165个身份/165个实际退出、寿命和495.7436885秒。额外未匹配退出、早期便携子进程、外层自身和晚期审计/交付不在这个完整总数内，全任务启动/寿命UNKNOWN。原raw_audit的process_ledger_valid=true只针对上述159个有限已记录前缀，不能抹去其未纳入的退出和全任务缺口。该审计实际case列表为空，57项确认保持未完成。

收尾前受控存储约6MiB，另预留256MiB恢复/证据；最终归档、实际远端恢复和尾部成本另列。首次准备UTC2026-10-18T09:51:55.453Z，包含所有读取/准备；最终预算以前瞻登记和尾部实际时间为准。

原始证据包保留完整源码、编译产物、所有日志、工具请求/会话结束、旧审计和独立只读重建。仅调用包内未修改的observer/native/legacy原始审计器，不创建新资格审计器。只读交付聚合调用登记在REPLAY_COMMAND.json，不能替代失败的执行审查。远端实际下载、逐成员认证和隔离重算已完成，详见下列最终交付回执。

## 历史和禁止范围

PR115/117保持原Draft/ENGINEERING_BLOCKED提交。历史6214e73d的NOT_REACHED、十个缺失退出、旧失败和三小时c475bcaf的全部字节/结论不变。PR119本轮仅追加独立结果目录，保持Draft。不改论文/main/RTX/release/自动化；不运行confirm.py、完整19/57、三小时soak或任何GPU/模型/科学执行。

## 实际远端恢复与最终交付前沿

原始证据commit：f62151bbfbf36278da08c4d585ed31555a2468e6。ZIP1265926字节、782成员，SHA256 `09a8d933bef45ec1455bd02c2e3a6b8d29ffefbcafcbcfe4a6d7f8ef8dfdd71e`。通过已发布ASCII Base64传输对象实际从GitHub下载，在全新目录解码恢复为完全相同ZIP；不是本地副本冒充下载。781项清单逐成员大小和SHA256全部一致，清单SHA256 `385e81b6613ca832aa434ca01f3533cbaff2e3ea5b5b0bc8bf5de57b05b49cf7`。

下载包内未修改的observer smoke、native gate和legacy raw auditors在Python `-I -S -B` 隔离环境实际重算；报告5199字节逐字节一致，SHA256 `68251610733ba8a9e210d981d3b72bf2c512d7dd111a2f4ede55ab3fb429b152`。这重建的是完整已保存的**阻断结果**，没有把恢复成功写成CPU8通过。编译DLL只作为证据保存，未加载。

尾部 `REMOTE_RESTORE.json`、`RESTORED_RECONSTRUCTION.json`、`TAIL_EVIDENCE.json`、`TOOL_ENDINGS.json`、`SOURCE_AUTHENTICATION.json` 与 `FINAL_ACCOUNTING.json` 绑定实际恢复、24个正式exec调用及会话结束、121个最终部署文件未变和实际观测时点。执行冻结字段为null，复审最终报告仍缺失。工具会话退出不等同于外层OS生命周期；已知缺口没有填0。

2026-10-18T10:11:24.699Z计账前沿：总任务1169.246秒；从复审根进程实际退出起交付584.965秒。受控逻辑存储10716947字节，4096字节规则下常规文件取整14999552字节；包含256MiB恢复预留、32MiB导出/尾部预留及额外保守元数据收费，总收费上界437379072字节，小于1GiB。两份ZIP，未删除历史或减少证据。后续发布/认证API耗时由最终尾部状态单列，不能把这个时点之后的成本算0。

Git比较确认第一证据提交只增加本新UUID目录的16个文件；旧文件没有修改。PR115/117仍为原提交和Draft。本轮最终状态 **ENGINEERING_BLOCKED**；不允许自动修复该观察器、重试审查、启动八项或任何GPU/科学后续。
