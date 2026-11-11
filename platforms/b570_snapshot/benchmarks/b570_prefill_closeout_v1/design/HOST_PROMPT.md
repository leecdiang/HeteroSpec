# 平台执行交接

请执行 HeteroSpec 的 B570 最后一个软件成本收尾：仅检验 draft-prefill 单次逻辑提交，physical q1、threads8、target QB和原数值运行时均不变。先完整读同目录 PROTOCOL.md，恢复 PR134四输入、346个原始logits及端点/状态，核对 PR135 attempt2 数值资格和任何原机未提交计时；旧失败全部保留，不把新数据补进旧UUID。冻结唯一代码差异、新输入/顺序/资产清单、全成本预算和作者执行授权。先4个校准请求和24个资格请求，全部通过后四独立进程完成64次测量+64次同输入同arm预热。主计时包括context建立到销毁，R/BASE_A/BASE_B/SUBMIT四臂，完整状态与物理q核验在计时外。禁止混入CPU1、target-prefill改动、persistent context或shader更换。没有固定时钟截止，不追正结果，不删波动块，失败不自动重试。缺历史raw或安全执行器就BLOCKED结束，不重开CPU8；不启动QH、M4/358H、RTL或更多扫描。结果PR交付全槽位、所有成本窗口、raw访问/哈希、进程回执、独立复算和PAPER_ADDENDUM；完成后关闭该支线。

当前PR是设计与CPU工具；真正原生执行前仍需填实注册字段并完成独立的host接线/原始数据审查。不得把模板校验当作运行许可。
