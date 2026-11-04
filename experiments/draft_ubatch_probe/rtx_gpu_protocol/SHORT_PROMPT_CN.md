# 未来RTX执行者短prompt（当前不是可启动runner）

按PROTOCOL.md先只读G0：核验最新#183、实际GPU与源码/模型/数值模块、可执行文件和真实绝对路径；给出新run_root、LOCAL_PATHS及完整预算。现CPU bridge仅tiny synthetic、target ub1/output4、fresh参考、固定KV parser，不能当旧R或GPU资格。

G0不执行模型。下一步G1-R须另有明确授权/预算，核定旧R reserve1、whole-prompt caller/mask、resident history、实际dispatch/state与峰值；旧binary只收cap128，短prefix adapter须单独桥接。缺adapter、路径或预算就BLOCKED，不能造命令开跑。

通过后只按已授权的小阶段执行：C1/C2/C4保持draft output reserve1，对照真正target-only B_default/B_QB，给予同cache资格，不关闭默认可命中cache制造优势。fresh与resident、weights/graph warm与prefix warm分开。每个实际proposal前缀全target logits及每commit activeKV/位置/frontier零差异；自由R独立，不向candidate泄漏答案。

G2仅单prompt、5heavy先资格、10provisional light；light的tape/vector/dispatch桥接通过后才纳入性能。每run/path重建H，内部proposal-control oracle也计reference/setup预算。全部tokens/owned time/RSS/VRAM/payload有硬上限，最坏上界放不进预算就不启动。数值或身份失败立即保留并停，不retry到PASS；G3不自动扩大。

返回真实结果目录、固定身份、未建立项和最强baseline下完整service/TTFT结论。不得自动上传用户prompt/token及其摘要、不得合并部署；不能把本协议称为runner ready。
