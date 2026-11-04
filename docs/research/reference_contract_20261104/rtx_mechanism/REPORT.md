# Draft收益机制：完整成本、实际调用工作与输出长度识别边界

2026-11-04；历史CPU重算，不含新GPU实验。来自#151固定提交29511ed91eb9f3d9773cfdda53e3554b0f4ad08b的day1/day2原始ZIP，共672条formal native记录，24个固定输入各4重复session、7arm。逐ZIP SHA/CRC校验、288个scope配对、逐M/C endpoint IDs/长度/stop原因核对；并重新读取#162固定0f2bb3a3482e58f6f48aadf936a8a43c14bcbf37交叉长度面板的原始service秒数。未重验完整logits/KV；无新GPU证据。

## 结论先行

- **同acceptance、同输出长度、同target/draft调用数，也可能从显著收益变成亏损。** Qwen QB三个现有输入：短数学99prompt tokens、代码423tokens、代码811tokens，都输出128token，接受92/108=85.185%，36个周期、37次target调用、145次draft调用。draft收益M/C分别1.6723、1.1361、0.9790；核心差异的会计证据是draft prefill均值0.2052、0.8638、1.6649s。实际nonprefill净残差却分别为1.4184、1.4309、1.5094s，长输入并不是没有continuation收益。
- **这是QB局部机制，不是全scope。** GS全部96对的同步nonprefill decode节省为负；PQ95/96正，QB96/96正。GS不能普遍用“输出更长就摊销”叙述，延长输出在冻结速率模型中反而扩大continuation劣势。
- **不能计算已被数据识别的“完整break-even输出长度”。** 每输入只测一个cap128/EOG输出长度，没有长度干预或每周期时间序列，且KV长度、接受序列、末轮浪费、EOG与分派会随输出变化。可写精确当前请求的成本恒等式，并给明确假设下的两套外推；不能把外推当新样本预测、可靠上下界或实现收益。
- **DRAFT_SYNC不是纯同步开销。** 它是真实seed解码，相位名表达draft状态追齐。约占QB draft非prefill解码时间26%。不能从表里把它删掉，再声称通过少调用cuda同步获得收益。

## 1. 源码与计时定义

固定worker.cpp：
- 第137–138行顺序target prefill、draft prefill。
- 第146行先draft->trim(base)，再draft->decode({seed}, base, ..., "DRAFT_SYNC")。
- 第148行逐个采样proposal并调用draft decode；k=3每周期执行3次。
- 第150行target VERIFY一次处理seed+3proposal，共4行。
- 第92–93行时钟包括llama_decode、llama_batch_free以及llama_synchronize，累计的是同步host decode墙钟，不是单独kernel或GPU同步空转时间。
- trim、sample、结果处理、状态记账等未被上述decode phase单独计时。它们留在service−全部phase和的未分配host间隙，不能全部称为额外同步。

全部672条记录/288对满足：M的target_calls=实际输出长度L；C的target_calls=1+周期数n；C的draft_calls=1+4n；proposed=3n。M/C同一输入scope的输出ID、L和停止原因相同。每个输入同scope的4session实际输出长度、acceptance、周期数和调用数相同，这些重复没有产生新独立工作负载。

M在target prefill后产生第一个输出，后续L−1次ORDINARY。C每周期产生变长的接受/纠正/bonus输出，因此精确有效步长用(L−1)/n；不能不加末轮/EOG修正地等同1+3×acceptance。

## 2. 把完整收益拆到已测相位

以下仅QB，day1/day2均值。数学/代码分别对应短/中长输入，#151本身仍然领域长度混杂。单位秒；每格含4或8独立输入、4重复session，不能把16/32块当总体独立样本。

|模型/组|M ORDINARY|C VERIFY|C PROPOSE|C seed decode|C draft prefill|C−M未分配host间隙|
|---|---:|---:|---:|---:|---:|---:|
|Qwen数学|2.509094|0.767970|0.276239|0.095440|0.176863|0.012791|
|Qwen代码|2.492742|0.792482|0.294501|0.102631|1.125670|0.013210|
|Smol数学|0.601580|0.243976|0.164615|0.059606|0.115159|0.005438|
|Smol代码|0.579299|0.226367|0.154527|0.055614|0.648966|0.005153|

Qwen数学/代码在nonprefill阶段分别净省1.356654/1.289919s（含host间隙差），但额外prefill成本F分别0.167275/1.144126s，最终收益被拉开。Smol非prefill仅净省0.127945/0.137637s，额外prefill为0.110266/0.640680s；草稿模型虽较小，其冷启动成本相对较便宜target明显更难摊销。

这里F = C_draft_prefill + C_target_prefill − M_target_prefill，保留真实target prefill两臂差，不将其强设为零。它不是只由算法新增工作决定的常量，也含实际运行条件和噪声；13/96个GS块F为负，不能据此假定draft在算法上加速了target prefill。

平均draft prefill每prompt token：Qwen数学2.102ms、代码2.040ms；Smol1.264/1.220ms。只是有限面板描述，未拟合线性预测器、不能外推未知长度/模型。平均接受率Qwen数学0.798/代码0.764，Smol0.670/0.662；接受率差远不足以单独表述完整请求利润。

### 一个相同输出长度、接受总数和调用次数、但利润不同的解释性对照

|Qwen QB input|prompt|L|accepted/proposed|target/draft calls|M/C|draft prefill|nonprefill残差|
|---|---:|---:|---:|---:|---:|---:|---:|
|GSM8K/test/806|99|128|92/108|37/145|1.6723|0.205189s|1.418378s|
|CodeContests/valid/43|423|128|92/108|37/145|1.1361|0.863833s|1.430853s|
|CodeContests/valid/6|811|128|92/108|37/145|0.9790|1.664918s|1.509419s|

这并非相同工作量：prefill UB1实际处理行数不同，verify时KV上下文长度不同，即使调用数相同每次调用的运算量也可能不同。这是事后解释性例子，不是随机化长度干预；输入内容与逐周期接受序列确实不同。其严格意义是反驳“只凭最终接受率、L和调用数便能确定完整收益”。两个代码输入也给出同领域反例，仍不能据此估计长度的因果效应。

## 3. 精确当前请求恒等式与速率条件

令N=L−1，n为真实周期数：
- a = M_ORDINARY / N，单位s/新增输出；
- b = (C_VERIFY+C_PROPOSE+C_DRAFT_SYNC) / n，单位s/周期；
- F = C_draft_prefill + C_target_prefill − M_target_prefill；
- H = C未分配host间隙 − M未分配host间隙。

则当前已观测请求严格满足：C−M = F + n·b − N·a + H。

等效：观测的N/n > (b + F/n + H/n)/a 时C<M。脚本对288个配对逐条验证判别结果一致。这是事后会计恒等式，a/b/n/H不是admission前凭空可知的特征。

只看nonprefill同步decode，需要N/n > b/a。QB各组平均速率的描述性概览：Qwen数学/代码b/a约1.528/1.557，而实际N/n约3.367/3.275；Smol约2.311/2.242，而实际约2.992/2.977。因此Smol continuation的剩余利润小得多，易被prefill吃掉。表中ratio-of-means概览不替代逐块精确判别，逐块值完整保留。

当前数据不能独立分辨“实际cuda同步调用自身要多少时间”。减少同步可能改变执行资格/错误可见性/后续状态一致性，应独立设计instrumentation和合法异步路径验证，不能从DRAFT_SYNC名称推断可消除开销。

## 4. 输出break-even：能算什么，不能算什么

### 可复验的条件性外推

脚本给两套明确不同的模型，供识别实验价值，均未训练：

A. 把全部nonprefill会计净节省B以当前平均速率B/N按输出长度线性延伸，F固定：L* = 1 + N·F/B（仅F>0、B>0适用）。另给加10ms固定开销情景。

B. 把未分配host间隙差H视为固定，只延伸已测同步decode净节省B_decode：L* = 1 + N·(F+H)/B_decode（仅正分子分母适用）。

A、B只是两种会计假设，不是置信区间或可靠上下界。host采样/状态处理可能随N增长，attention/KV变化也会使每token成本改变。所有288行都保留，不选最有利结果。

QB的A外推：
- Qwen48块范围7.22–284.15个总输出token；15块超过原cap128。另外一个亏损例是自然EOG82token，外推阈值约91token仍低于128，但不能为了赚钱强行让模型越过EOG。
- Smol48块范围53.39–1323.00；40块超过原cap128，18块甚至超过1024−prompt_tokens的保守剩余槽位筛查值；12块来自自然EOG输入。这不是输出token严格最大值：首输出来自prefill、最终token可能pending而不占已消费槽位，scalar情形可能有+1差；spec四行verify、pending/rollback及物理padding又需额外余量。18块在改用1025−prompt_tokens时计数不变，但不得把这个筛查当作合法性证明。
- 例如Smol CodeContests/valid/66只自然输出100token，四session的模型A阈值301–1323；CodeContests/valid/108 prompt797token、实测输出128，模型A阈值897–1026，但保守剩余槽位筛查值仅227。没有理由把这些数字当“让输出长一点就行”。

GS全部96对B_decode<0，简单正收益摊销模型不适用；PQ一个Smol反例也不适用。脚本用null保留不适用项，没有偷偷取绝对值或丢弃失败。

### 为什么不能得到“完整实际阈值”

1. 每输入只有一个实际L和同工作重复计时，没有C(L)、M(L)曲线，也没有每个周期累积时间戳。
2. cap变化会改变末轮边际计算浪费、proposal/bonus是否提交；部分CPU记账也改变。
3. 扩展输出进入更长KV，可能过256/1024等allocator或kernel边界，不能假设a、b常数。
4. 接受序列是内容相关的未来结果。不能拿长输出最终acceptance为短输出admission背书。
5. 自然EOG代表任务完成，强迫延长会改变语义；context容量和完整参考资格也可能先失效。

因此当前能交付的是**观测盈亏点及条件性预算模型**，不是被实验识别的完整break-even长度。

## 5. #162交叉长度数据能额外说明什么

#162 Llama预输出选择了代码/数学×短128–384/长512–768，每格6input×6session。只用原始service_seconds独立重算QB：短代码M/C1.00179（15/36块有利）、长代码0.87687（0/36）；短数学1.14503（35/36）、长数学0.89331（1/36）。长两组平均C−M约+0.7434/+0.7250s。

它在设计上将领域与长度交叉，避免#151“数学全短、代码中长”的完全混杂，支持继续检验prompt长度相关的成本假说。但手头#162 compact cost表**没有对应输出长度、acceptance、每phase或调用计数**；且#162是包含fresh context setup/teardown的service，#151是resident cleared contexts。不可把#151的prefill机制直接当作#162的已证原因，也不能计算#162完整输出break-even。短代码几何比略有利而算术平均C−M为+14.85ms，再次说明几何/总耗时estimand必须区分。

## 6. 真正识别长度曲线所需的下一最小实验

- 固定原模型、scope、runtime、KV格式、prefix与原参考；包含常开draft、常关draft，且两者同等合法target缓存资格。
- 用事前注册的合法cap网格，例如16/32/64/128（只在ctx允许且自然未EOG时继续），不按结果挑输入。需要跨输入新盲面板，不能只反复测当前24条。
- 每次从同一合法前缀状态重启、配对平衡顺序；每个周期同时记录host同步相位、调用/接受/拒绝、实际committed输出和状态。保持主计时清洁，重capture资格与clean timing分离。
- 报告完整C(L)/M(L)及所有不交叉、非单调、多次交叉、EOG/资格容量截断的曲线；不存在唯一根时不强报一个阈值。
- 若加cache，只对真实自然prefix命中定义f和导入/维护成本，不把同输入4session重复当自然命中；若测policy，其开销、miss、fallback均计完整service。
- 自适应规则若需要预测实际L或acceptance，只能使用事前可用特征及独立校准；冻结后在新输入评估。当前结果没有训练/验证这种策略。

## 复现与交付

在本目录运行：python analyze.py --archives /path/to/verified-archives。两个ZIP的文件名、SHA256及member来源均记录在mechanism.json的sources/逐行source中；从#151原始发布证据获取，脚本将先校验SHA及全部CRC。只用标准库；读取原始两个已校SHA/CRC的ZIP及此前固定#162源文件。mechanism.json包含全部source member/SHA、288行及汇总；mechanism_per_block.csv含所有相位、实际工作、恒等式指标和两种外推。所有数据均为历史重算；data/保留固定源文件，SOURCE_MANIFEST.json记录原提交与本地字节SHA。未来#162原始phase分析若可取得，将单独交付，不回填成本表无法证明的机制。
