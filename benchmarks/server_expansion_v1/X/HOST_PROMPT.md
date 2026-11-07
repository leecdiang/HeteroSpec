# 远程执行 prompt

从本 PR 的实际最新 head 新建独立结果分支，先读本目录 PLAN.md、study.json 及 ../shared/COORDINATION.md、ADAPTER.md；这是条件性后置POC，不立即占两张卡。先对实际Linux同卡记录执行完整成本核算，缺失项为null；有明确显存/延迟问题及授权后，单独实现CPU/第二GPU draft adapter，保留target原GPU/R与各自驻留KV，显式检查两个设备参数和CPU核预算，不绕过PR196单卡保护。先做固定proposal诊断再做真实draft资格；四根三轮 M_MATCHED/同卡/CPU/双卡完整服务保留全部成本。初版不加跨轮异步或prefill重叠，若要主张资源效率必须面对两卡各跑一个worker的等资源替代，不能只报单请求延迟。 自主完成正常构建、ABI、源码和记录适配以及有机制依据的通用修复，保留失败、版本和重新资格，不停在 helper 测试；不得替换 R、按输入特判或删除不利对照。保护正在运行的 PR196 与公司服务，使用已授权 UUID 和协调后的安静计时窗口；交付独立结果 PR，不自动合并、不改论文、不租卡。
