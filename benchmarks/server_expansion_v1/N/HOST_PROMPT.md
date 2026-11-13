# 远程执行 prompt

从本 PR 的实际最新 head 新建独立结果分支，先读本目录 PLAN.md、study.json 及 ../shared/COORDINATION.md、ADAPTER.md；先做自然会话的零前向/tokenizer几何普查，绑定原始会话版本、实际模板及逐turn有效head，区分静态provided历史和原参考生成的开发历史。比较完整WB-cut/WB-rechunk/local调度，不用padding/截断/速度筛选制造跨界；q整除padding时WB-rechunk的额外调用上界要保留。存在未被旧实验回答的实际差异再实现同一context连续会话，处理pending、EOG和模板边界，使用真实顺序producer R而非冷全量prefill替代；四个同投影强对照完整计费，以会话根而非turn聚类。普查或自然性能分支关闭不妨碍有限接口集成结案。 自主完成正常构建、ABI、源码和记录适配以及有机制依据的通用修复，保留失败、版本和重新资格，不停在 helper 测试；不得替换 R、按输入特判或删除不利对照。保护正在运行的 PR196 与公司服务，使用已授权 UUID 和协调后的安静计时窗口；交付独立结果 PR，不自动合并、不改论文、不租卡。
