# 远程执行 prompt

从本 PR 的实际最新 head 新建独立结果分支，先读本目录 PLAN.md、study.json 及 ../shared/COORDINATION.md、ADAPTER.md；绑定实际合格的 Linux successor，固定 Qwen8B/0.6B Q8、C1024、k3、draft prefill UB4，先完成 W-L4/W-P/L-L4/L-P 四个 D4 的同投影归因。随后将 k7/q8 作为独立候选版本，原生实现输出预留、事务索引、trim/frontier 与瞬时容量，先验证 k3-reserve8 桥接，再做固定四根八臂小型 POC；D4 不是 k4，不能只改 JSON 或把验证全部拆成四行后宣称 q8。M1 不受 M2 受阻影响，只有实测完整成本支持才另冻新确认。 自主完成正常构建、ABI、源码和记录适配以及有机制依据的通用修复，保留失败、版本和重新资格，不停在 helper 测试；不得替换 R、按输入特判或删除不利对照。保护正在运行的 PR196 与公司服务，使用已授权 UUID 和协调后的安静计时窗口；交付独立结果 PR，不自动合并、不改论文、不租卡。
