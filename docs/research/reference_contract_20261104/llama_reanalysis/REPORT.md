# PR162 Llama：原生phase重新核算，非跨研究推断

2026-11-04，CPU只读历史分析，无新GPU运行，无已实现缓存收益声明。来源release rtx-llama-repair-v1-evidence-20261102 的 evidence-095.zip，331012312 bytes，SHA256 c5e4fa83a9a1ae006abf38fed4eaa036853db63c631772b0cca09f14fb204437。原始RAW_ACCESS索引及所有864 measured成员大小/SHA均已核对，864 service_seconds与固定PR162 FINAL_COST逐值完全一致。未把warmup、诊断或其他epoch混入。

## 核心发现

- QB全部144配对的decode phase净节省为正，却有93块完整service亏损。保持其他测量不变、理想删除完整draft prefill的会计反事实可使93块均转正，但没有任何实现/自然复用/因果保证。
- 数学短/长各6input×6session，均输出128且CAP终止。短组draft prefill平均0.624782s、非prefill净节省1.007503s；长组1.897807s、非prefill净节省1.132894s。target prefill C−M分别−0.063408/−0.039953s，所以完整C−M分别−0.446129/+0.724960s。长组continuation收益没有消失，额外prefill超过现有收益。
- 数学短/长平均acceptance75.62%/73.00%，每周期提交3.2513/3.1773个首token之后的输出。接受率并未崩溃，不能仅凭它做收益admission。输入内容仍不同，不能把组间差异认定为长度因果。
- 代码短/长平均L87.5/116.83，draft prefill0.803021/1.774625s，非prefill净节省0.768296/1.000204s，完整C−M+0.014849/+0.743363s。代码短6输入中5个自然EOG、长组2个，数学均CAP；域间“更适合draft”的对比同时受输出长度与停止机制影响，不能只归因代码/数学能力。
- PQ不是普遍正continuation：APPS/test/684（L73）在session0的A/B和session4的A分别decode净节省−59.768/−60.017/−55.179ms。这3项即使理想删除draft prefill仍亏。A/B共享同一M_PQ且同输入跨session重复，不能把432配对视作432独立样本。

## 完整session预算

QB各session按总service加总，C/M为1.0393–1.0683，均比target-only慢。保持同一M和全部其他成本，理想只消除draft prefill需要削减其总量14.4%–24.2%才到总成本持平。这是后验会计预算，不是缓存命中率预测或新策略收益；个别亏损输入仍需超过90%的prefill削减，整体预算不能保证逐请求收益。重复session不能当自然prefix命中。

## 口径与恒等式

所有记录明确fresh contexts、native prefill、capture false、observer off。与#151 resident cleared不同。最终worker.cpp已从evidence-000.zip提取并按原生identity SHA e6dca9e58f61dc2aae0bf43e8d90f2147067f9447a043e5e1b4b025adcee8a2a匹配。第170–268行service覆盖setup、request、teardown及区间内host记录工作，代码显式减state_capture_seconds；本分析全部capture=false，所以snapshot分支未进入、扣除为0，不能将此结论用于capture诊断样本。phase外残差同时包含生命周期及host工作，不能称作纯同步。这里直接使用#162原始phase标量，不从#151移植数值。worker第143–145行phase从llama_decode之前计到llama_batch_free及llama_synchronize之后，是同步host elapsed，不是GPU kernel时间或纯同步开销；batch初始化及hsc::decode_begin在该phase之前，hsc::decode_end在之后。第217行DRAFT_SYNC为实际seed解码；第239行另有末尾同步，包含在request/service但不在对应decode phase内，不能由残差单独拆出其时间。

令F=C_draft_prefill+C_target_prefill−M_target_prefill；B_decode=M_ordinary−C_verify−C_propose−C_seed；H为C/M service扣除各phase后的残差之差。432配对C−M=F−B_decode+H均通过1e−12秒容差。setup/teardown单独保留，不与残差重复相加。QB四格H约11–18ms，其中setup差2–4ms、teardown差1–2ms，主量级仍是prefill，而不是现有host差的数量级。

逐配对核对输出IDs、L、stop一致，target calls C=1+n、M=L，draft calls=1+4n，proposal=3n。仅核endpoint IDs不是重新完成完整KV/logits数值资格。

## 推理边界

每输入仍只有一个cap/EOG长度，没有C(L)/M(L)干预曲线。不能识别完整break-even输出长度，也不能为了摊销让EOG样本强行继续。实际prefix-cache须计状态兼容/导入/维护/内存开销，并给target-only相同合法target cache资格。任何从本面板挑选的阈值是后验解释，不能宣称盲泛化。6session重复测同24inputs，不增加到144个独立任务。

## 复现

在本目录运行 python analyze.py，只用Python标准库，无需GPU或访问用户设备。data/只含计时/计数标量、领域/长度分层、whole-source member hash，不含prompt/endpoint内容摘要，不含原题、提示或输入/输出token序列。SOURCE_MANIFEST.json固定原始release、提交及源worker identity。

脚本对最小投影hash及432配对会计重算，产出mechanism.json；其预期hash见GENERATED_OUTPUTS.json。原ZIP逐成员SHA/CRC、原始端点及864 service对齐已在导出前独立复核；投影不含内容或内容摘要，因此不能重验端点一致性，投影重跑不会重新证明完整KV/logits资格。无需下载原始107GB证据。完整JSON产物本地生成，不作为大文件提交。
