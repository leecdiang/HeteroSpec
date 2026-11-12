# 提权 CPU ETW 检查结果

用户明确同意提权范围后，固定 CPU ETW launcher 已执行。2026-11-12 23:37:05 上海时间开始的检查通过，`ELEVATED_ETW_CPU_001.json` 保留同 Windows/登录身份的上下文摘要。StartTrace、provider enable 和正常停止都成功，进程 start/stop 各 1 条，映像 load/unload 各 31 条，三个丢失计数均为 0。CPU 子进程的创建 FILETIME 与实际进程句柄匹配，Python 与 ntdll 映像记录齐全。没有 NVML、CUPTI、数值 DLL、CUDA、GPU 或模型调用。

该结果证明拟用提权身份能够完成本次 CPU 进程及映像观测。它还不能证明未来数值 DLL 的全部加载、GPU 活动或退出尾部完整，更不能闭合原 4096 硬上限。后续 B 必须在匹配身份、绑定新观察器及准入证据后由唯一 runner 执行。

第一次提权 launcher 未产生 ETW 回执，原因是 smoke 源码在 Windows 以 CRLF 落盘，而错误预期摘要来自内存 LF。原 launcher 已复制到 `launcher-001/` 保留，`LAUNCHER_FAILURE_001.json` 记录纠正。新的 launcher 在校验前启动 transcript，并按实际文件 SHA-256 `7bd633782504f85462e84c44c2f0b6f3c636bb028ad2d712967d367efb2aa819` 检验 smoke.py。数字 DLL 和 GPU attempt 均未被该失败消耗。
