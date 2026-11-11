"""Final supplemental report, only after qualification and archive recheck."""
from common import HERE,RUNTIME,read,put,sha

def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n\n'
def main():
    arm=read(HERE/'results/ARM_QUALIFICATION.json');ledger=read(HERE/'results/CUMULATIVE_LEDGER.json');archive=read(HERE/'results/ARCHIVE_READBACK.json');recheck=read(HERE/'results/ARCHIVED_NUMERICAL_RECHECK.json')
    assert arm['passed'] and archive['passed'] and recheck['passed'] and ledger['new_requests']==37
    complete=arm['complete'];counts=complete['counts'];text='# PR213：37请求补正与自然跨界状态补证结果\n\n'
    text+='已按明确授权完成全部37个逻辑请求：29个独立Windows标量R case、八臂各1个heavy请求；16个native worker均退出0并原生完成。所有新full-vector、active target KV/frontier、pending/拒绝/bonus/trim/cap、物理切分及旧clean语义轨迹检查通过。原1024条正式测量没有重跑，原统计未更新。\n\n'
    text+=f"新增数值证据：独立R库257个完整151936维F32向量、40个active状态前缀；候选共 **{counts['full_vector_comparisons']:,}次完整向量比较、{counts['active_KV_comparisons']:,}次active target KV比较**，全部采用全字节SHA256相等，无容差放宽。另检查1352个完整draft提案向量的有限性、维数和argmax；未声称独立重算draft全部KV字节。\n\n"
    text+='## 完整八臂资格表\n\n'
    text+=table(['臂','cycles','跨界cycles','跨界拒绝','完整向量比较','active KV比较','target/draft物理行'],[[a['job'].removeprefix('rtx213-s1-'),a['cycles'],a['boundary_cycles'],a['boundary_rejections'],a['full_vector_comparisons'],a['active_KV_comparisons'],f"{a['target_physical_rows']}/{a['draft_physical_rows']}"] for a in arm['arms']])
    text+='k3在base254拒绝后继续至255；k7在base251/254/255等处跨界并拒绝。whole真实切分、LOCAL保留真实4/8物理验证宽度，完整mask与loop4/packed GPU投影标记均按冻结判据核对。全部初始、每个commit和terminal状态与预绑定R一致。\n\n'
    text+='## 冻结、读取器失败与复用\n\n'
    text+='用户明确授权“完善草案后，执行37次GPU补证”。输入、token路径、29个R case、257/40参考映射、顺序、native版本及数值检查器在任何本轮模型输出前于`b1a41dc0fe60012a331552510dd6156d58391ba5`发布并完整回读。候选沿用Qwen3-8B/0.6B Q8_0、C1024、F16 KV、noFA、24线程、target UB32/reserve8和draft UB4/reserve1；R为原UB1/reserve1。\n\n'
    text+='首R worker的4个case已原生COMPLETE/退出0后，收尾模块读者误把native返回的路径字符串当成对象，造成Python TypeError。原FAILED host/ledger、原控制器源码、STOPPED及所有raw保留，4请求预留不退款。对完整文件哈希、全部已请求R向量/状态、原job和数值DLL离线重核后复用原4个case，0 native重跑。\n\n'
    text+='仅模块清单适配器在`b4ae9cd01a343261e9c541fc61b3223aa9b4c816`修正并在剩余33请求前完整回读；未改native、输入、数值比较、顺序或容差。新R自身只报告已加载路径，host对当前文件哈希并与运行前绑定夹证；不虚构native原本未记录的内存哈希。整个执行器不能因此被描述成“所有源文件一次性事前冻结”，读者修补与间隙继续披露。\n\n'
    text+='## 账本与成本\n\n'
    text+=f"本轮预留37请求、18543保守行；原生实际报告{ledger['new_actual_requests']}请求、{ledger['new_actual_rows']}行。RTX最新累计 **{ledger['cumulative_requests']}/3072请求、{ledger['cumulative_reserved_rows']}/4000000保守行**；资格500/512，余12；new tranche1812/2048。新C盘账本与两个只读旧账本的继承链见[CUMULATIVE_LEDGER.json](results/CUMULATIVE_LEDGER.json)。1次postprocessor失败仍在历史账本内，native非零退出0次，退款0，native重跑0。\n\n"
    text+='加载、准备、prefill/draft/verify、全向量物化、状态导出、模型/模块哈希、worker/wrapper和2秒资源采样见[完整成本](results/COMPLETE_COSTS.json)与原始材料。本轮全部为heavy资格开销，不能作生产延迟，也不加入旧干净计时；重叠时钟不可相加，host phase不等于kernel时间。初始工程/协调总墙钟未完整计量，不伪造总值。profiling0、primers0。电源/驱动/全局设置未修改。\n\n'
    text+='## 补正后可支持与仍不能支持的表述\n\n'
    text+='现在可补充：“在事后按覆盖选定的已暴露APPS/train/603、固定prompt178/cap96与原V2版本上，37请求补证确认全部八臂自然跨界拒绝/回退的完整向量及active target KV/frontier与独立R相同，并与原clean语义轨迹一致。”这是对原审计联合覆盖缺口的有限加强。\n\n'
    links=read(HERE/'results/OLD_ROOT_TRACE_ALL_BLOCKS.json');assert links['all64_old_root_traces_equal']
    text+='另行离线核对该根在原8个顺序块中的全部64条clean语义轨迹，cycles/物理切分/端点均与本补证绑定轨迹一致，见[旧轨迹全块关联](results/OLD_ROOT_TRACE_ALL_BLOCKS.json)。这是token/branch层面的关联，不等于恢复旧运行KV字节。\n\n'
    text+='原审计的全局冻结违例仍成立；本补证不改写历史，不恢复旧clean当时未导出的KV，不是独立盲样本，不验证其他所有根/状态/长horizon。APPS/train/296、305等旧clean状态仍未逐字节追溯恢复。原首live worker的312秒间隙影响、未记录尝试与历史时间公证边界没有被消除，不能把总体审计升级为“已经证明零影响”。\n\n'
    text+='原八臂k7耗时增加13.6%～14.6%的统计保持原值，仅在披露分阶段资格、有限状态证据及本补证范围后使用。本轮不产生新速度或kernel/架构因果结论，不构成相对同期M的优越性证明，不借旧target-only数据。论文、历史基线和原实验数据未修改。\n\n'
    text+='## 归档与复核\n\n'
    text+=f"新归档包含{archive['logical_files']:,}个逻辑文件、{archive['logical_bytes']:,}逻辑字节，ZIP为{archive['archive_bytes']:,}字节。所有唯一blob完整解压/重新哈希并恢复全部路径；从恢复出的源、原始向量和KV重新运行独立比较，所有参考库/八臂向量、状态及冻结轨迹证明完全一致，不调用GPU。见[字节回读](results/ARCHIVE_READBACK.json)、[归档数值复核](results/ARCHIVED_NUMERICAL_RECHECK.json)。\n\n"
    public=read(HERE/'results/PUBLIC_READBACK.json');assert public['passed']
    text+=f"完整raw/source/失败/账本在全新C盘supplement runtime与CAS归档目录中，原路径不删除。远端24分片、{public['joined_bytes']:,}字节、{public['text_records_verified']}条文字记录已完整下载并逐字节哈希核对；此文字/二进制承诺回读不冒充远端原始数值重检。见[公开回读](results/PUBLIC_READBACK.json)。权重不归档。归档后生成的报告、全块关联、读回证明和交付回执作为Git sidecar避免自指哈希。未合并PR、发布Release、提交或改论文、启动32B/B570。\n"
    (HERE/'RESULT.md').write_text(text,encoding='utf8');print('Wrote bounded supplement report preserving original conclusions and both reader deviations',flush=True)

if __name__=='__main__':main()
