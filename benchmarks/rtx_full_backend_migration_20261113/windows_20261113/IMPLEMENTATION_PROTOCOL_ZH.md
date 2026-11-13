# #244本机执行合同细化（GPU前冻结）

用户在本轮批准必要构建与两面板执行，取代原PLAN/RUNBOOK的“尚未授权”状态；上限228请求、204288 rows、18模型驻留部署、首次加载起6小时、10GiB新证据不变。不得合并或改论文，不重建ETW/私有量化/launch门控。

R为repo/work/native-original-v4原有完整静态核心libllama.a SHA 8fa2731e05cd064156ed4587b3a85d59498ef11b2b6d5f95fec1262a420db445，逐字等于D:/rtx192-review-v2/R-Qwen/BUILD.json；所有原始运行DLL逐项匹配同一旧BUILD并复制，数学核心不修改。不是e04/e11 DLL或提取B。薄adapter采用原参考ubatch1、outputs reserve1，batch32和2线程用于共同请求profile；独立R driver采用历史batch1024、ubatch1、reserve1、24线程，并必须复现历史前缀764 frontier。若不符，不再把它称为恢复的旧参考。

M完整构建0fb8f157的llama+ggml/CPU/CUDA，CUDA12.9.86、MSVC14.44.35207、120a-real，graph/PDL默认保留。Flash disabled、ctx1024、batch/ubatch32、F16KV、2线程、单device/full-layer offload。CMake compiler ABI设备执行显式跳过，实际编译链接另证。两臂不同编译器/运行库属于完整部署迁移，不归因于单kernel。

资格共16请求，使用6部署：每臂一个独立native-reference进程2请求、一个fresh-adapter进程2请求、另一个fresh-adapter进程先重复2请求再reset/reuse2请求。每进程只建一个context，不用同进程重复冒充两个fresh进程。连同正式12个session共18部署，原2-load余量用于更严格fresh检查，不再有自动加载重试。请求保守按每次896行预留，220计划请求总预留197120行，另8请求/7168行余量；失败不退款。实际decode行另记。

两个诊断根：短根自主greedy，模式H捕获每次请求的完整词表行并对比token/EOG；长根为真实历史764-token前缀+预先指定的128-token数据集continuation，模式Q。参考driver独立实现batch/位置/greedy循环，不include adapter。逐位对比所有实际请求的完整向量、tokens、rows/calls、KV末位置及reset；R额外历史fixture。只声称集成/重放/continuation检查，不是独立全输入数学证明；M不需与R逐位一致，也不套用旧提取U的CPU-RN合同。

原始候选文本与确定性规则在首次加载前固定。第一次R reference部署同时用真实模型tokenizer导出所有候选IDs，不额外加载词表模型，不执行推理来选择文本。HumanEval canonical_solution+tests和MATH-500 solution提供真实continuation，少于128 tokens者过滤，不重复/pad。若原长度bin无法填满，则按已固定算法选择满足每段2code+2math的最小连续切点；记录新切点并在任何decode/计时前冻结16根。它不保证未见训练数据，也不增加虚假长问题。M reference对全部选中prompt和continuation重新native tokenize，必须相同。

执行器使用一个累计fsync账本、唯一已知RTX锁、单自有子进程Windows Job/16GiB进程commit、kill-on-close；无管理员、AppContainer、ETW、系统设置/ACL变更。每次加载前3次只读空闲/VRAM检查；过程中采样温度、显存、其他compute PID、磁盘与证据大小。>=85C、foreign compute、资源压力、600s无完成进度、6h截止则终止自有Job并停止，不终止其他进程，不保证驱动卡死后的即时清理。

资格可开graph诊断日志；正式P/G不加graph debug，环境不禁用graph/PDL。P/G同步host timer保持共同边界，输出detokenization/JSON落盘在timer外；模型load与warmup不混入resident请求时间，另报process时间。G是state-complete greedy，最终emitted token也decode，EOG只记录不作为正文decode；有轨迹长度差异不能称质量等价。完整输出文本保留。

本合同不重置旧ledger，不保证物理launch或隐式context上界。资格FAIL则受影响面板不计性能；修复或追加工作若需要突破任一总限，先交付已完成证据及具体额外需求。
