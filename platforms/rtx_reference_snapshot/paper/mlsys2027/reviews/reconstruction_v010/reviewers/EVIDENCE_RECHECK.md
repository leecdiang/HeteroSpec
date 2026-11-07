# EVIDENCE_RECHECK — 唯一一轮修订的确切稿核对

这是内部模拟的针对性复核，不是会议判断或接收概率。首评 EVIDENCE_INITIAL.md 保持不变；保留原内部评级与 confidence，不重新评分。没有读取其他 reviewer 意见，没有运行模型、新GPU实验或访问 packet 之外的科学工作记录。唯一修订稿输入是 `review_packet_final/`；仅为验证“原1005数组不变”，另读取首评已授权 initial packet 的匿名ZIP对应数组/DERIVED/历史ZIP作为基线。

## 确切对象与范围

| 对象 | 复核 SHA-256 |
|---|---|
| manuscript-v0.10.0.pdf（12页） | `d4c0ffeefd60b4d0b3b0b3c480157a3f298f7045410720a4a4a2ded3846df1a9` |
| appendix-v0.10.0.pdf（24页） | `2f3c0743eff79f0531954a9a129f3e6b4518e4138f2380b601b03f8b8527dc1f` |
| INDEX.md | `455d7762d93136665437f8459db811ac3a6a93660a7f811fe807441887a64600` |
| anonymous-intervention-evidence-v0.10.0.zip | `ff9f4cfd873225a71afceae4a5fa8c01f385f4d7377296393e98912e77ad8ffe` |
| author-controls/rtx/SELECTED_RAW_CASES.tar.gz | `dab64c8cf8ea53e22316462367956d10d590b27b58573ffc8a62c1b365711506` |
| author-controls/b570/NATIVE_UNTRUNCATED_ARRAYS.json | `048422d9dd8d746d53ceb0fd4faf31ff2d2e8c46af64cf9240725f4d65ce803f` |

顶层 SHA256SUMS.json 全部25项通过。匿名ZIP内部六项manifest通过。重读新main全部12页和appendix全部24页，重点是 main §2.2/3.1/4/7、Appendix T.1/A27–A28；读取 author-controls 的coverage、source/Git/freeze/seal/attempt/sham/transfer/provenance摘要、三份实际 frozen sources 与 raw parser相关函数。所有CPU计算在内存执行，仅写本报告；未执行 archive restore/audit 主程序、未重建整个CAS archive，也未将subset称为全档案重审。

## 原数组及CAP128澄清

**澄清准确，且没有改变原来的array比较结果。** 从initial和final ZIP直接按study/cohort/task/condition/rep逐项比较，1005个IDs数组、endpoint与cap均完全相同。DERIVED.json和historical-v0.9.0.zip也分别字节相同，其SHA-256为 `f8cd692cf852e77d333f094b31890387b70de410d676412f96d74a29d63dd7d7` 与 `f24352a7b9fb5ee077186ea4db4a255a03d3ec401da90097799a4ca57dd66964`。

再次执行 supplied verify_v010.compute()并比对完整DERIVED，仍为1005数组/67任务/五条件/三次稳定观察，所有P0=N0及P1=N1。B570 reference task matching为20→24，RTX旧19为17→17（/15恢复、/25新偏离），MBPP为22→22；/304仍为47-ID EOS输出index33的488→481变化，persistent mismatch不等于output no-op。三 cohort 的N0=N1 task数仍为20/17/23。

新增匿名 `B570_UNTRUNCATED_NATIVE.json` 的144单元与author-controls的对应raw export在共有字段（包括IDs、EOG flags、contract IDs、endpoint及capture/result digests）一致；匿名版本仅删去两类author路径。每个raw IDs的前128项与相应formal合同数组逐项一致，formal endpoint为CAP128，raw overshoot等于raw长度减128。再逐项核对144单元与360项RAW_OUTPUT_PROVENANCE的source digest、长度与overshoot绑定，均通过。

| native condition | 128 IDs | 129 IDs | 130 IDs | capture数 | 额外post-cap IDs总数 |
|---|---:|---:|---:|---:|---:|
| N0 | 33 | 18 | 21 | 72 | 60 |
| N1 | 33 | 15 | 24 | 72 | 63 |

因此“128–130、suffix60/63、suffix独立保存并排除equality”的陈述有实际export支持。main §3.1、Appendix T.1、A27/A28现在区分contract-bounded完整性与未裁剪native capture；不应再将原来72/72 prediction equality或N0=N1解释为post-cap suffix也相等。这个区别与first128/inclusive-earlier-EOG的原比较合同一致，不是通过后验截断更改结果。首次报告中“无法确认raw overshoot保留”的问题已得到实质回答。

“1005数组不变”不等于FORMAL_ARRAYS.json整文件字节不变：final将旧overshoot字段换为raw_overshoot，B570 CAP128的360条inclusive_eog metadata由false改为true。IDs/endpoint/cap均不变。CAP128这些数组没有实际提前EOG；reader应将新inclusive_eog理解为合同允许inclusive earlier EOG的政策标识，不能把它当作这360条实际以EOG结束。raw contract_eog/EOG flags和endpoint足以区分。建议给字段语义一句说明；该metadata问题不改变本次equality核验或科学结论。

## Selected RTX raw captures 的实际核验

SELECTED_RAW_CASES.tar.gz恰有262个实际文件，与SELECTED_RAW_CAPTURE_MANIFEST逐项路径、字节数、SHA256一致。它包括HumanEval/15、/18、/25与MBPP/304、/463的第一重复，五条件R/H0/H1/N0/N1，共25个complete salient captures；它不是随机抽样或全645个RTX单元。

按每个result的selected attempt选择其native.log或R/P wire+tape：

- 运行packet所给独立raw parser的native()/predictor()函数，检查完整输出、终点、native连续生成ordinal/remaining budget/stop markers、H的proposal request/prefix hash/chain/emit关系，25项均与result及formal neutral export吻合。
- 另用自行写的raw ID读取重建15份native生成流和10份H target committed-ID流，25份均与对应result数组相同，不以result.ids作为解析输入。
- 25个result哈希与SELECTED_ATTEMPTS中的绑定吻合；所有实际提供的attempt文件哈希与result.files一致。各result的freeze/protocol/cohort/assets digests与FREEZE_DOCUMENT_BINDINGS吻合。
- 10份H0/H1 result及其tape字节哈希均与REMOTE_SEALED_MEMBERS中对应成员吻合。这支持提供的sealed-member摘要与当前raw bytes的内容绑定；它不是我独立获取远端封存档案或认证原始绝对时刻。
- 10份native trace的handoff记录在source UB2、dest UB2/UB1、consumed/state sizes、source/restored/source-after positions、state_equal/source_unchanged以及first pending ID等字段上自洽；pending ID为本native输出首ID。选中trace的decode returncode、单sequence与capacity设置一致。实际captured target continuation occupied token维度：N0为1或2，N1仅1；draft/prefill仍为1或2。它们支持正文capacity/occupied-shape的区别。

三个实际frozen sources `controller.py`、`execution.py`、`worker.cpp`的SHA256均与SOURCE_BINDINGS一致，按Git blob算法算出的SHA1均与IMPLEMENTATION_GIT_BINDINGS中reviewed/implementation blob一致。读取它们可看到role-specific输入allowlist、P/R自身反馈、首pending在source sample/accept后clone与transfer、native独立CLI/live draft、不输入H tape、24线程，以及258个H prediction/tape records的seal流程。这明显优于首包只有口头输入合同的状态。未提供相关native observer全部源码，故没有宣称逐行审核全部native instrumentation。

新增SHAM_WITNESSES共有30摘要（H/N各15），每项full_ids_endpoint_equal为true；TRANSFER_WITNESSES为516项（2→2与2→1各258）。这些使denominators及hash见证可检查。**本selected tar不含sham pairs的两端raw captures，也不含result.files所引用的60个KV文件与20个pending-logit f32文件。** 这些大字节的实际同一性仍是作者侧全档案审计/摘要，不是我的本地独立重算。我的subset检查不能据此声称已验证所有30个sham或所有516个KV handoff；也不能把reported15192-files/645-units全审计当作本次覆盖。上述限制与manifest及COVERAGE说明一致。

## 首评fixable blockers的处置

| 首评问题 | 复核处置 | 理由及仍存边界 |
|---|---|---|
| description如何构造，RTX是否只是shared numerical reexecution | **表达/方法描述部分已解决** | main §2.2与Appendix T.1说明手写、study-specific程序，B570删除draft，RTX保留P/R live feedback及共享数值计算；MBPP/304给出具体预测案例。明确不是automatic extraction、不证明execution compression、没有debugging saving。 |
| 把预测的额外价值说成reference gate无法拒绝候选 | **已解决** | main §7与T.1明确普通reference gate已足以拒绝RTX，description新增的是完整trajectory forecast与testable reproduction contract。Table5表头也不再暗示每项都是超出gate的新决策能力。 |
| 新干预的source/seal/sham/handoff/attempt/原始映射在packet不可检查 | **实质改善；不再是“完全不可审阅”缺口，但不是全档案重审完成** | source/identity/attempt bindings与25selected raw cases有直接检查；sham、KV/logit大字节及其余raw记录仍为digest/作者审计摘要。B570新增144raw array/provenance解决cap来源，B570本次全部source/sham/handoff细节仍未以实际字节全部提供。剩余属于明确的审计范围限制，应保留而非假称已经全证实。 |
| anonymous arithmetic vs author-side raw review混淆 | **能力界限明显更清楚** | INDEX、T.1与COVERAGE/selected manifest分开1005 arrays、144B570 captures、25RTX selected raw与reported full audit。main §3.1沿用“offline intervention review”措辞，须结合这些能力界限理解；本文复核仅按自己实际覆盖报告。 |
| B570 CAP128与overshoot的“complete”含义 | **已解决** | 60/63个post-cap IDs实际可查，contract数组128且原IDs/endpoint不变，A27/A28明确后缀不参与equality。metadata inclusive_eog的小残项见上，不是array结论失败。 |

当前d4/2f3稿的两项小表达残项是：Appendix A22仍主要是六个早期study的map，没有单列本次两个controlled interventions；main §4.3的“45 unchanged H arrays reused”可明确为prediction-worker(H) arrays。二者都不影响本次科学核验。若本轮closeout仅修这两项，可作有限文字/hash对齐，不需要新一轮整体评阅或评分。

## Remaining substantive blockers

首评最重要的fundamental-novelty-impact疑问仍在，尽管现在表述更准确：论文已清楚展示B570 draft-free reproducer和RTX有限输出forecast，却没有建立这些手写shared-numerics descriptions的通用构造方法、减少诊断工作量、预测比native reexecution更经济，或一个新的可迁移系统能力。修订正确地承认这些没有测量，解决了夸大/含混，但诚实缩小scope不自动增加research impact。成本研究仍是不同历史路径与独立cohort，其正确算术不会变成新干预的performance benefit。

首评的外延/impact门槛也仍然存在：B570 restoration只在已曝光24任务；RTX的新24MBPP增强finite prediction evidence却未展示统一修复或跨stack迁移。按作者当前有限case-study主张，这不是逻辑缺口；若要提升方法影响力，需要与具体用途对应的独立应用/未曝光干预测试或实际诊断收益，而非默认做stage factorial、寻找unique kernel cause或无目的加重复次数。本轮没有新模型实验，我不把它虚构成已经解决此问题。

本复核没有发现1005 endpoint-bounded数组、paired outcomes或60/63suffix数据的矛盾，且selected RTX raw/source检查提供了比首包更强的provenance支持。它仍不认证omitted weights/runtime/driver/compiler bytes、opaque sampler byte equality、可信绝对实验时间、project exposure的底层全集、全部645单元的raw真实性或全30sham/516handoff大字节。没有凭这些范围限制推导造假、unique-stage necessity或population failure rate。原评级保持不变；这是修订核对结果，不是重新评分。


## 同一修订的closeout有限delta receipt

在保留以上d4/2f3对象及实际审计记录的前提下，按后续授权仅核对 `review_packet_closeout/` 的DELTA.md及两个指定文字改动，没有开展新整轮review或评分。

| closeout对象 | SHA-256 | 页数 |
|---|---|---:|
| manuscript-v0.10.0.pdf | `5433df69f8f091c41b604f9f02714c435672a06e0379a63d2dcb96db30500185` | 12 |
| appendix-v0.10.0.pdf | `ff1a69b1d425bf01108a59d7fb4de6d27e7e74b1b25d7849c33fd3d33715ac28` | 24 |

closeout SHA256SUMS.json全部3项（两份PDF与DELTA.md）吻合。主文§4.3现在准确写“45 unchanged prediction-worker (H) arrays reused”，区分75个新24线程native arrays与45个复用H arrays；它不声称120个全新native输出。Appendix A22在保留原六行之前新增B570 prefill intervention和RTX continuation intervention两行，分别给出exposed24×3、19×3/24×3、T0/T1或H0/H1对应N0/N1、CAP128或EOG/cap128、paired outcomes及no timing。新增map与已核计数、输入合同及历史研究身份一致。

另目视检查closeout主文第5页与appendix第17页，两处改动正常显示，未见重叠或裁切。以上两项小表达残项至此解决。closeout目录是三个文件的PDF/delta receipt，不另含证据ZIP；证据范围沿用已完整hash检查的review_packet_final匿名ZIP `ff9f4cfd873225a71afceae4a5fa8c01f385f4d7377296393e98912e77ad8ffe` 与author-controls检查。本delta核对不扩大raw覆盖、不改变先前remaining substantive blockers或原评级。
