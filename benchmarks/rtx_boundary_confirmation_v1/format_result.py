"""Readable final report from audited compact results; does not change eligibility."""
import csv,json,math,shutil
from pathlib import Path
from common import V,load,sha
from prepare_rtx import root

def read(p):
    with Path(p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def main():
    r=root();arc=Path(str(r)+'-archive');result=load(V/'RESULT.json');resource=load(V/'RESOURCE_SUMMARY.json');env=[load(p) for p in sorted((r/'environment').glob('*.json'))]
    review=dict(status='CLOCK_CHANNEL_VALIDITY_NOT_ESTABLISHED',source='existing70rawendpointqueries only;no newdevicequery',records=len(env),reported_SM_values=sorted({x['SM_clock_MHz'] for x in env}),examples=['0','37976','63915','14242'],units_documentation='https://docs.nvidia.com/deploy/nvidia-smi/index.html',units_scope='documentation defines SM readings inMHz;no causal explanation or conversion imposed',frozen_gate='reported identity/free-memory/util<=5/temp<=55/AC;SMclock wasnotan eligibility gate',block_status_changed=False,root_cause='UNKNOWN',frequency_normalization='NOT_ADMITTED',additional_GPU_queries=0)
    p=arc/'TELEMETRY_REVIEW.json'
    if not p.exists():p.write_text(json.dumps(review,indent=2),encoding='utf-8')
    else:assert load(p)==review
    for name in ['RESULT.md','RESULT.json','RESOURCE_SUMMARY.json']:
        backup=arc/('PUBLIC_PRIOR_'+name)
        if not backup.exists():shutil.copyfile(V/name,backup)
    resource['SM_clock_channel_validity']=review['status'];resource['free_memory_scope']='reportedpre/postcounter;no runtimeVRAMpeak captured';result['resources']=resource;result['telemetry_review']=review;result['telemetry_review_sha256']=sha(p)
    for name,value in [('RESULT.json',result),('RESOURCE_SUMMARY.json',resource)]:
        (V/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    primary=next(x for x in result['full_panel'] if x['stage']=='confirm' and x['stratum']=='q>1');pred=result['prediction'];method=result['method_decision'];archive=result['archive'];factor=read(V/'results/FACTOR_REVIEW.csv');strong=[x for x in factor if x['comparison']=='QB_QH' and x['consistent_all_value_modes_sessions']=='True' and x['larger_than_AA_plus2percent_heuristic']=='True']
    text=['# PR121：RTX A/A分辨率与可信成本边界','',
    '**本面板支持QB作为更强成本基线；没有建立QH_C的稳定优势。时钟通道有效性尚未知，硬件保持SOFTWARE_FIRST/HOLD。**','',
    f"身份 `{result['canonical_run_id']}` / `{result['execution_id']}`。实际3,008个GPU宿主、99,088次图调用；无数值/执行失败、无未启动计划GPU任务、无科学重跑。PR120/118等历史结果未改写或混入。",'',
    '|阶段|GPU宿主|图调用|实际覆盖|','|---|---:|---:|---|',
    '|独立串行参考|368|368|64输入的184个query，各两个新进程|',
    '|重复资格|400|13,600|H1全部64输入×3布局×两进程；H0八anchors×两进程|',
    '|A/A pilot|192|7,296|H0/H1各八anchors、六配对块|',
    '|核心确认|1,664|63,232|52输入×四arm×八块，两次独立启动的四块cycle|',
    '|新seed留出|384|14,592|12个q3/GQA输入×四arm×八块，两cycle|','',
    '## 1. 哪些映射合格，测量能分辨多细','',
    '在独立持久输入buffer、原精度/数值DLL/算术和原CUDA Graph设置下，PQ、QB、QH_C的完整ordinary均与两进程独立serial-q1参考逐位相同。全部输入前后字节、完整实际图、CUDA归属、共享核心/41个插件导入、计算返回与同步检查通过。不是自然prompt、完整decoder或新中间四阶段资格。每宿主固定输入重放，不代表变化请求/KV状态已合格。','',
    f"选用H1，保留8warmups+30测量。pilot逐anchor A/A区间包络中位比例尺度：H0 {method['method_evidence']['H0']['approximate_median_ratio_scale']:.3%}，H1 {method['method_evidence']['H1']['approximate_median_ratio_scale']:.3%}；不能据此认证2%分辨率。H1预分配输出/固定计时记录，循环后写文件，仍逐调用readback、精确比较和保留每次字节。H0是已独立资格的legacy-style变体，并非旧二进制逐指令复刻，见[AMENDMENTS.md](AMENDMENTS.md)。方法选择只依据QB A/A。",'',
    '## 2. 超过同尺度A/A波动的成本差异','',
    '比值大于1有利于分母。宿主内30次为技术重复；按固定input/block配对，再等权汇总两值模式和几何。bootstrap重采集整个块并按实际session分层，两session不是独立日期。主/次比较均用QB_B重算，绝不择快。','',
    '|面板|QB_A/QH_C|QB_B/QH_C|QB_A/QB_B|QB_A−QH_C µs|PQ/QB_A|描述性屏障|','|---|---:|---:|---:|---:|---:|---|']
    for x in result['full_panel']:
        c=x['comparisons'];text.append(f"|{x['stage']}/{x['stratum']}|{c['QB_QH']['ratio']:.6f}|{c['QB_QH_alt']['ratio']:.6f}|{c['AA']['ratio']:.6f}|{c['QB_QH']['difference_us']:.3f}|{c['PQ_QB']['ratio']:.6f}|{x['QB_QH_decision']['status']}|")
    text+=['',f"24个q2/q4几何中，**{len(result['stable_QB_geometries'])}个**同时满足两QB、同尺度A/A+2%/1µs屏障及两模式/两session同向；其余{len(result['unresolved_geometries'])}个未解决。没有合格局部QH优势，q1未出现越过该屏障的假优势。未解决不等于等价。完整坐标、区间、块对比与遗漏见[GEOMETRY.csv](results/GEOMETRY.csv)及[ANALYSIS.json](results/ANALYSIS.json)。屏障是描述性保守启发式，不是校准显著性/等价检验。",'',
    '本轮24个几何汇总均值没有有利于QH的方向，但更细input/block中的反转、尾部全部保留。PR120输入和observer不同，不将本轮解释为直接推翻旧点；结论限于这次已声明条件。','',
    '## 3. 哪些几何效应保留，能否预测留出','',
    '|单因素边（主比较）|改变后/改变前的QB/QH成本比|含义|','|---|---:|---|']
    for x in strong:text.append(f"|{x['base']} → {x['changed']}|{float(x['geometry_log_effect_ratio']):.6f}|两模式、两cycle、替代QB和A/A探索性屏障均保留|")
    text+=['','compact Q改善QH相对成本，但未建立其绝对优势。长度同时改变causal frontier；d同时改变常规scale。20条边×主/次比较的全部40项见[FACTOR_REVIEW.csv](results/FACTOR_REVIEW.csv)，属于探索性多比较；不从这些成本推断kernel选择或物理流量。','',
    f"六特征平滑规则源码在查看B0成本前登记，完整B0后只拟合一次；系数/12个预测在任何留出输入或参考产生前冻结，见[PREDICTION_FREEZE.json](PREDICTION_FREEZE.json)。新seed留出12/12个均值方向与两个QB版本均一致，但log成本比RMSE为{pred['log_contrast_RMSE']:.6f}，明显高估差距。加入实测CPU特征/lookup {pred['lookup_us']:.6f}µs，选择策略/固定QB的成本比为{pred['geometric_selected_over_fixedQB']:.6f}，没有改善固定QB。平均/最大oracle regret为{pred['mean_oracle_regret']:.6f}/{pred['max_oracle_regret']:.6f}。这是离线相位和，非已集成selector，方向正确不等于统计显著或精细幅度可预测。完整错误和每块分数见[PREDICTION_SCORE.json](results/PREDICTION_SCORE.json)及[PREDICTION_PAIRS.csv](results/PREDICTION_PAIRS.csv)。没有留出重训。",'',
    '## 4. 成本边界与硬件决定','',
    'resident_graph=[compute开始,全设备同步返回]；completed-call再包含ordinary readback。HOSTS记录互不重叠的compute-return、explicit-sync和post-sync/readback区间，不能把它们各自称为kernel时间。实际必要packing/CONT/REPEAT/mask/输出恢复留在图内；没有单独测得GPU packing kernel时间。','',
    '原input-inclusive为每宿主一次“预格式CPU物化+upload/sync+首次warmup完成call”的相位和，不是30次完整请求。冷初始化（含身份审计）、分配、源文件读取、输出缓冲预分配和完整host墙钟单列；未分项固定bookkeeping仍在host墙钟中。全部逐宿主mean/median/p95/max与分项见[HOSTS.csv](results/HOSTS.csv)、[HOST_DISTRIBUTIONS.csv](results/HOST_DISTRIBUTIONS.csv)和[OTHER_COST_VIEWS.json](results/OTHER_COST_VIEWS.json)。','',
    '另有128个纯CPU进程实际做Q copy/transpose、完整KV copy和mask构造，每输入两进程，1次CPUwarmup+64次准备，全部字节等于GPU输入。它从共同逻辑Q和已存在完整KV起算，用预分配目标buffer；冷分配另计。替换预格式copy分项后的[共同producer相位和](results/COMMON_PRODUCER_AGGREGATES.csv)是独立CPU分量+实际GPU分量，未集成为连续事务；CPU分量共享于GPU块，只作描述性核算，不计自然decoder产生Q/K/V的未知成本。','',
    '**硬件空间尚未知。** 无合格profiler，kernel身份/数量、traffic、occupancy、Tensor Core及backend因果仍UNKNOWN。先追踪q2/1024邻界和compact-Q等受控对照，并比较强软件组织/复用方案；没有物理瓶颈和系统关键路径证据前保持HOLD。actor/decoder/W1、RTL/FPGA、论文、B570、main和发布均未触碰。','',
    '## 5. 实际限制、资源和复现','',
    '**时钟通道有效性未建立。** 原始`clocks.sm`含0、37976、63915等报告值，原样保留，未作单位缩放、归因或当作实际频率。NVIDIA文档定义该字段为MHz：[官方字段说明](https://docs.nvidia.com/deploy/nvidia-smi/index.html)。本轮预注册门槛只用设备/driver、reported util≤5%、temp≤55°C、free memory与AC；clock不是门槛。所有块达到这些已声明门槛，但不能用时钟读数证明频率相同或连续独占；不事后按延迟删块。该异常限制频率归一化与硬件机制结论，不触发GPU重跑。报告的memory.used在端点均为0，也不是运行期VRAM峰值证据。','',
    f"GPU宿主Job进程启动（native+conhost）{resource['host_job_process_starts']}；native命令墙钟合计{resource['sum_native_command_wall_seconds']:.3f}s，峰值Job commit {resource['peak_native_job_commit_bytes']}bytes，显式设备端点查询{resource['device_queries']}，节点支持API查询{resource['supports_API_queries']}。native/conhost+控制器保守owned上界{resource['conservative_native_job_plus_controller_owned_upper_seconds']:.3f}s；不是GPU busy或完整全机账本。128个CPU准备进程另列，0额外GPU调用。8小时预算内完成；登记后elapsed见[RESOURCE_SUMMARY.json](RESOURCE_SUMMARY.json)。",'',
    '最终19项协议、3项适配、8项证据测试通过；另有156张核心+36张留出实际CPU全图地址检查及3个非法原生入口拒绝。构建日志命名、git目录、测试fixture、UTF8/报告合并等CPU失败/草稿保留，无科学GPU重试。见[CPU_VALIDATION_NOTES.json](CPU_VALIDATION_NOTES.json)。','',
    f"原始归档 `{archive['archive_path']}`：**{archive['members']}成员**，{archive['archive_bytes']}bytes。SHA256 `{archive['archive_sha256']}`；manifest `{archive['member_manifest_sha256']}`。全部成员已fresh restore；GPU主要表、CPU准备表和因素/附加成本/预测评分在新解释器中复算字节一致。RAW_LOCAL_ONLY，无远端raw上传或外部独立审查。详见[RAW_LOCATION.json](RAW_LOCATION.json)。",'',
    '数值运行时按原机路径与21个DLL哈希绑定，归档包含新宿主和完整张量，未复制整套CUDA DLL。Git中绑定的紧凑执行artifact使用原始字节（见EXACT_ARTIFACTS.json）；普通Git源码采用LF，真实消费源码另存raw/SOURCE。Fresh是CPU复算，不是GPU重跑。历史UUID全部保持终止，不得重新调用本轮GPU入口。实际命令见[COMMANDS.md](COMMANDS.md)。']
    (V/'RESULT.md').write_text('\n'.join(text)+'\n',encoding='utf-8');print('Readable result generated; telemetry anomaly retained as UNKNOWN; no eligibility changes')
if __name__=='__main__':main()
