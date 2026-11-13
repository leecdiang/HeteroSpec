# 给 SSH / Codex 执行端

从本 PR 的实际最新 head 创建独立 Linux 结果分支。先阅读 README、PROTOCOL 和
HOST_ADAPTER；第一步只做公司服务器的只读清点，确认当前 GPU UUID、占用、工具链、
权限与资源，不能依据之前“七张空闲”的快照直接启动。用户确认或已有调度分配后仅用
一张空闲卡，默认避开 GPU0/既有服务，不用 sudo、不升级驱动、不杀其他任务、不租卡。

随后用固定源码包和 pristine upstream 完整重建 Linux llama/base/CPU/CUDA 模块；
禁止沿用 Windows DLL 或静默升级源码。先建立独立本机 R 并冻结，再将源自 PR195 的
四种切分/projection 组合迁移、完成原生完整数值和状态资格。Linux R 不要求与 Windows
跨卡逐位相同，旧 R 不变。提供的 POSIX 补丁、独立 reference、CMake、资源监督、排程
和统计工具是起点，不是已通过的原生实现；自主完成正常 ABI、源码定位、编译和实际
observer/trace 适配，保留版本与失败，不停在 helper 测试。

只在实际支持域内冻结六臂单卡确认：四个真正 target-only M、SIMPLE-D4、LOCAL-D4；
沿用固定十六根作独立部署迁移，诚实标注已暴露而不是新盲样。完整服务、真实请求串、
启动/内存和全部强控制都保留，未知成本为 null，不挑输入、不追有利结果、不扩大为
多卡跑分。按协议交付独立结果 PR、可重建源码与原始证据索引；不自动合并、不改论文。
