"""Generate scientific delivery from fully audited observations, never raw relabeling."""
import argparse,collections,csv,json,math,shutil,statistics,time
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from export_rtx import rows_csv

def read(p):
    with Path(p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def sign(x):return 1 if x>0 else -1 if x<0 else 0

def prediction_score(plan,a,hosts,raw):
    if not (raw/'PREDICTION_FREEZE.json').exists():return dict(status='UNSTARTED'),[]
    freeze=load(raw/'PREDICTION_FREEZE.json');groups=collections.defaultdict(dict);rows=[]
    for h in hosts:
        if h['stage']=='holdout' and h['numerical_qualified']=='True' and h.get('environment_qualified')=='True':groups[h['case_id'],int(h['block'])][h['arm']]=h
    for (cid,b),arms in groups.items():
        if set(arms)!=set(['PQ','QB_A','QH_C','QB_B']):continue
        costs={arm:float(h['resident_mean_us']) for arm,h in arms.items()};prediction=freeze['predictions'][cid];chosen='QB_A' if prediction['layout']=='QB' else 'QH_C';alternate='QB_B' if prediction['layout']=='QB' else 'QH_C';lookup=freeze['lookup_us'];oracle=min(costs[x] for x in ['PQ','QB_A','QH_C']);oracle_alt=min(costs[x] for x in ['PQ','QB_B','QH_C'])
        rows.append(dict(case_id=cid,block=b,session_id=arms['QB_A']['session_id'],chosen=prediction['layout'],predicted_log_QB_over_QH=prediction['predicted_log_QB_over_QH'],observed_log_QB_over_QH=math.log(costs['QB_A']/costs['QH_C']),observed_alt_log_QB_over_QH=math.log(costs['QB_B']/costs['QH_C']),lookup_us=lookup,selected_phase_sum_us=costs[chosen]+lookup,fixed_QB_us=costs['QB_A'],fixed_QB_B_us=costs['QB_B'],fixed_PQ_us=costs['PQ'],fixed_QH_us=costs['QH_C'],oracle_us=oracle,regret=(costs[chosen]+lookup)/oracle,alternate_regret=(costs[alternate]+lookup)/oracle_alt,fixed_QB_regret=costs['QB_A']/oracle))
    bycase=collections.defaultdict(list)
    for row in rows:bycase[row['case_id']].append(row)
    errors=[];alt_errors=[];correct=0;alt_correct=0;choice_correct=0;alt_choice_correct=0
    for cid,items in bycase.items():
        if len(items)!=8:continue
        observed=statistics.mean(x['observed_log_QB_over_QH'] for x in items);predicted=freeze['predictions'][cid]['predicted_log_QB_over_QH'];errors.append((predicted-observed)**2);correct+=sign(predicted)==sign(observed);alt_observed=statistics.mean(x['observed_alt_log_QB_over_QH'] for x in items);alt_errors.append((predicted-alt_observed)**2);alt_correct+=sign(predicted)==sign(alt_observed);choice=freeze['predictions'][cid]['layout'];choice_correct+=choice==('QH_C' if observed>0 else 'QB');alt_choice_correct+=choice==('QH_C' if alt_observed>0 else 'QB')
    summary=dict(status='OBSERVED' if rows else 'UNSTARTED',rule_sha256=sha(raw/'PREDICTION_FREEZE.json'),evaluated_pairs=len(rows),complete_cases=len(errors),correct_point_directions=correct,correct_alternate_QB_directions=alt_correct,chosen_lower_point_cost_cases=choice_correct,chosen_lower_alternate_cost_cases=alt_choice_correct,alternate_log_contrast_RMSE=math.sqrt(statistics.mean(alt_errors)) if alt_errors else None,log_contrast_RMSE=math.sqrt(statistics.mean(errors)) if errors else None,mean_oracle_regret=statistics.mean(x['regret'] for x in rows) if rows else None,max_oracle_regret=max(x['regret'] for x in rows) if rows else None,mean_alternate_QB_oracle_regret=statistics.mean(x['alternate_regret'] for x in rows) if rows else None,mean_fixed_QB_oracle_regret=statistics.mean(x['fixed_QB_regret'] for x in rows) if rows else None,geometric_selected_over_fixedQB=math.exp(statistics.mean(math.log(x['selected_phase_sum_us']/x['fixed_QB_us']) for x in rows)) if rows else None,lookup_us=freeze['lookup_us'],interpretation='charged offline selected-mapping mean+measuredPythonlookup;not a native integrated selector;point-direction accuracy isnot significance',no_holdout_retraining=True)
    return summary,rows

def main():
    r=root();data=r/'analysis_final';a=load(data/'ANALYSIS.json');audit=load(data/'AUDIT.json');plan=load(r/'plan.json');hosts=read(data/'HOSTS.csv');coverage=read(data/'COVERAGE.csv');out=V/'results';out.mkdir(exist_ok=False)
    for name in ['HOSTS.csv','COVERAGE.csv','ANALYSIS.json','FACTOR_REVIEW.csv','OTHER_COST_VIEWS.json']:shutil.copyfile(data/name,out/name)
    decision=load(r/'METHOD_DECISION.json');geometry=[]
    case_map={(x['stage'],x['case_id']):x for x in a['case_summaries']}
    for g in a['geometry_summaries']:
        primary=g['comparisons']['QB_QH'];alt=g['comparisons']['QB_QH_alt'];aa=g['comparisons']['AA'];directions=[]
        for mode in [0,1]:
            one=case_map.get((g['stage'],g['geometry_id']+f'-v{mode}'))
            for cycle in [0,1]:
                for label in ['QB_QH','QB_QH_alt']:
                    vals=[p['log_ratio'] for p in one['comparisons'][label]['pairs'] if p['block']//4==cycle] if one else []
                    directions.append(sign(statistics.mean(vals)) if len(vals)==4 else 0)
        consistent=len(set(directions))==1 and directions[0]!=0
        geometry.append(dict(stage=g['stage'],geometry_id=g['geometry_id'],blocks=primary['n_blocks'],sessions=primary['sessions'],QB_A_over_QH=primary['ratio'],QB_B_over_QH=alt['ratio'],AA_ratio=aa['ratio'],AA_log_interval=aa['log_interval'],AA_us_interval=aa['difference_interval'],AA_scale_ratio=math.exp(max(abs(x) for x in aa['log_interval']))-1 if aa['log_interval'] else None,QB_QH_screen=g['QB_QH_decision']['status'],PQ_QB_screen=g['PQ_QB_decision']['status'],consistent_modes_sessions_bothQB=consistent,mode_cycle_directions=directions,plausible_local_QH_boundary=consistent and g['QB_QH_decision']['status']=='DENOMINATOR_LOWER_COST',plausible_QB_advantage=consistent and g['QB_QH_decision']['status']=='NUMERATOR_LOWER_COST'))
    rows_csv(out/'GEOMETRY.csv',geometry)
    inputs=load(r/'INPUTS.json');
    if (r/'HOLDOUT_INPUTS.json').exists():inputs.update(load(r/'HOLDOUT_INPUTS.json'))
    rows_csv(out/'INPUTS.csv',[dict(case_id=c['case_id'],geometry_id=c['geometry_id'],q=c['q'],keys=c['keys'],d=c['d'],Hq=c['Hq'],Hkv=c['Hkv'],storage=c['storage'],mask=c['mask'],realization=c['realization'],seed=c['seed'],visible_keys=c['visible_keys'],input_sha256=c['input_sha256']) for c in inputs.values()])
    distributions=[]
    for stage in ['confirm','holdout']:
        for q in sorted({c['q'] for c in inputs.values()}):
            ids={c['case_id'] for c in inputs.values() if c['q']==q}
            for arm in ['PQ','QB_A','QH_C','QB_B']:
                hh=[h for h in hosts if h['stage']==stage and h['case_id'] in ids and h['arm']==arm and h['numerical_qualified']=='True' and h.get('environment_qualified')=='True']
                if not hh:continue
                distributions.append(dict(stage=stage,q=q,arm=arm,hosts=len(hh),mean_of_host_means_us=statistics.mean(float(h['resident_mean_us']) for h in hh),median_of_host_medians_us=statistics.median(float(h['resident_median_us']) for h in hh),median_host_p95_us=statistics.median(float(h['resident_p95_us']) for h in hh),maximum_single_call_us=max(float(h['resident_max_us']) for h in hh),median_host_wall_seconds=statistics.median(float(h['host_seconds']) for h in hh),median_allocation_us=statistics.median(float(h['allocation_us']) for h in hh),median_preparation_us=statistics.median(float(h['CPU_materialize_us']) for h in hh),median_upload_sync_us=statistics.median(float(h['upload_and_sync_us']) for h in hh),median_compute_return_interval_us=statistics.median(float(h['compute_return_interval_mean_us']) for h in hh),median_explicit_sync_interval_us=statistics.median(float(h['explicit_sync_interval_mean_us']) for h in hh),median_post_sync_readback_interval_us=statistics.median(float(h['post_sync_to_readback_return_mean_us']) for h in hh),median_cold_initialize_audit_us=statistics.median(float(h['initialize_us']) for h in hh),median_graph_build_us=statistics.median(float(h['graph_build_us']) for h in hh),median_source_read_us=statistics.median(float(h['source_read_us']) for h in hh),median_observer_buffer_allocation_us=statistics.median(float(h['observer_preallocation_us']) for h in hh)))
    rows_csv(out/'HOST_DISTRIBUTIONS.csv',distributions)
    pred,pr=prediction_score(plan,a,hosts,r);save(out/'PREDICTION_SCORE.json',pred);rows_csv(out/'PREDICTION_PAIRS.csv',pr)
    if (r/'cpu_preparation_analysis').exists():
        for name in ['CPU_HOSTS.csv','COMMON_PRODUCER_PHASE_SUMS.csv','COMMON_PRODUCER_AGGREGATES.csv','AUDIT.json']:shutil.copyfile(r/'cpu_preparation_analysis'/name,out/('CPU_PREPARATION_AUDIT.json' if name=='AUDIT.json' else name))
    environment=[load(p) for p in sorted((r/'environment').glob('*.json'))];lifetime=[load(p) for p in (r/'attempts').glob('*/host.LIFETIME.json')];module=load(r/'NUMERICAL_MODULES_POSTCHECK.json')
    resource=dict(native_hosts=len(lifetime),graph_calls=audit['graph_calls'],host_job_process_starts=sum(x['job_total_processes'] for x in lifetime),sum_native_command_wall_seconds=sum(x['seconds'] for x in lifetime),peak_native_job_commit_bytes=max(x['peak_job_commit_bytes'] for x in lifetime),device_queries=len(environment),supports_API_queries=sum(2*int(h['graph_nodes']) for h in hosts),model_requests=0,profilers=0,elapsed_since_registration_seconds=time.time()-load(r/'RUN_SPEC.json')['start_epoch'],full_OS_process_ledger='not captured;not required',maximum_temperature_C=max(e['temperature'] for e in environment),minimum_observed_free_MiB=min(e['total_MiB']-e['used_MiB'] for e in environment),observed_SM_clocks=sorted({e['SM_clock_MHz'] for e in environment}),observed_power_schemes=sorted({e['power_scheme'] for e in environment}),continuous_exclusivity='not established by endpoint telemetry',module21_postcheck=module['status'])
    stage_times=[load(p)['seconds'] for p in r.glob('*_ENDED.json') if 'seconds' in load(p)]
    resource['conservative_native_job_plus_controller_owned_upper_seconds']=2*resource['sum_native_command_wall_seconds']+sum(stage_times)
    resource['owned_basis']='native/conhost<=2processes per Job wall plus actual stage controller wall;upper bound,not exact OS ledger'
    if (r/'CPU_PREPARATION/ENDED.json').exists():resource['CPU_preparation']=load(r/'CPU_PREPARATION/ENDED.json')
    save(V/'RESOURCE_SUMMARY.json',resource);arc=load(Path(str(r)+'-archive')/'ARCHIVE.json');fresh=load(Path(str(r)+'-archive')/'FRESH_RECOMPUTE.json');fresh['auxiliary_replay']=load(Path(str(r)+'-archive')/'AUX_FRESH_RECOMPUTE.json');factors=read(data/'FACTOR_REVIEW.csv');core=[g for g in geometry if g['stage']=='confirm' and not g['geometry_id'].startswith('q1-')];stableQB=[g['geometry_id'] for g in core if g['plausible_QB_advantage']];stableQH=[g['geometry_id'] for g in core if g['plausible_local_QH_boundary']]
    pointQH=[g['geometry_id'] for g in core if g['QB_A_over_QH'] is not None and g['QB_A_over_QH']>1]
    q1_null_flags=[g['geometry_id'] for g in geometry if g['stage']=='confirm' and g['geometry_id'].startswith('q1-') and g['QB_QH_screen'] in ['NUMERATOR_LOWER_COST','DENOMINATOR_LOWER_COST']]
    result=dict(status='MEASURED_BOUNDARY_WITH_AA_LIMITS',canonical_run_id=load(r/'RUN_SPEC.json')['run_id'],execution_id=load(r/'RUN_SPEC.json')['execution_id'],execution_freeze_sha256=sha(r/'FREEZE.json'),audit=audit,method_decision=decision,full_panel=a['full_panel_summaries'],geometry=geometry,point_QH_geometries=pointQH,q1_same_path_timing_flags=q1_null_flags,stable_QB_geometries=stableQB,plausible_local_QH_geometries=stableQH,unresolved_geometries=[g['geometry_id'] for g in core if not g['plausible_QB_advantage'] and not g['plausible_local_QH_boundary']],factor_direction_consistent=sum(x['consistent_all_value_modes_sessions']=='True' for x in factors),factor_above_AA_guard=sum(x['larger_than_AA_plus2percent_heuristic']=='True' for x in factors),prediction=pred,resources=resource,archive=arc,fresh_restore=fresh,hardware='SOFTWARE_FIRST/HOLD',profiler='PROFILE_UNAVAILABLE_NO_ADMITTED_COLLECTOR',historical_runs='unchanged;no old outputs pooled',external_review=False)
    save(V/'RESULT.json',result);save(V/'RAW_LOCATION.json',dict(**arc,canonical_run_id=result['canonical_run_id'],execution_id=result['execution_id'],fresh_restore=fresh,remote_raw_uploaded=False,numerical_runtime_payloads_embedded=False,new_host_binaries_embedded=True))
    text=['# PR121：A/A 分辨率与几何成本边界','', '**所有结论限于声明的普通输出参考与主机完成计时；硬件保持 SOFTWARE_FIRST/HOLD。**','',
    f"实际完成 {resource['native_hosts']} 个原生 GPU 宿主、{resource['graph_calls']} 次图调用。完整覆盖、失败和 UNSTARTED 坐标见 [COVERAGE.csv](results/COVERAGE.csv)。历史 PR120/118 没有重启或改写。",'',
    '## 1. 先确认分辨率','',
    f"H1 全部52输入×PQ/QB/QH_C×两进程，以及H0八个QB anchors×两进程完成资格。A/A pilot为两方法×八anchors×六块×两个同QB标签，共192宿主。选用H1，保持8warmups+30测量；选择只用了QB A/A，不看候选成本。H0逐anchor区间包络中位比例尺度为 {decision['method_evidence']['H0']['approximate_median_ratio_scale']:.3%}，H1为 {decision['method_evidence']['H1']['approximate_median_ratio_scale']:.3%}。这是描述性包络，不是2%分辨率证书或校准显著性检验。",'',
    'H1预分配每次ordinary的独立缓冲和固定QPC记录，循环内仍有同步、readback和完整逐位/有限值检查，循环后写出全部输出。H0是legacy-style：保留逐调用STARTED JSON、文件及输出分配，但调用汇总JSON也在循环后构造；不把它称为旧二进制的逐指令复刻。二者算术图、数值DLL和输入生命周期相同。核心26几何各有两种值模式；正式8块来自两个实际分别启动的4块采集session，而非两个独立日期。','',
    '## 2. 哪些差异超过同尺度A/A波动','',
    '|面板|QB_A/QH_C|QB_B/QH_C|QB_A/QB_B|描述性判断|','|---|---:|---:|---:|---|']
    for p in a['full_panel_summaries']:
        ss=p['comparisons'];fmt=lambda label:'UNKNOWN' if ss[label]['ratio'] is None else f"{ss[label]['ratio']:.6f}"
        text.append(f"|{p['stage']}/{p['stratum']}|{fmt('QB_QH')}|{fmt('QB_QH_alt')}|{fmt('AA')}|{p['QB_QH_decision']['status']}|")
    text+=['',f"q2/q4几何中，原始几何均值有利于QH的坐标为 {pointQH}。满足原/替代QB、同尺度A/A屏障及两值模式/两session方向一致的QB优势坐标：{stableQB}；可疑局部QH优势坐标：{stableQH}。其余保留未解决，不把未通过屏障解释为无差异。q1同路径计时屏障异常标记为 {q1_null_flags}（数值控制仍逐位通过）。见 [GEOMETRY.csv](results/GEOMETRY.csv)。",'',
    '比值大于1有利于分母。宿主内30次是技术重复；先对宿主求均值，再等权汇总值模式和几何，以session分层重采集块。两QB从不择快。q1同图控制的全部偏差保留。A/A加2%与1µs的屏障是保守描述性筛选，不是等价证明。','',
    '## 3. 几何解释与泛化','',
    f"20条单因素边分别对主、次比较分析，共40项；{result['factor_direction_consistent']}项在两值模式和两session中方向一致，{result['factor_above_AA_guard']}项越过额外A/A包络+2%的探索性屏障。完整方向、替代QB和所有边见 [FACTOR_REVIEW.csv](results/FACTOR_REVIEW.csv)，不能挑最有利比较当普适规律。d变化同时改变常规scale；长度变化包含causal frontier变化，不能把它们都称纯kernel dispatch干预。",'',
    f"可选q3/GQA留出状态：{pred['status']}。规则源码在B0采集期间、查看其成本前登记，完整B0之后只拟合一次；实际系数和12个预测在任何留出输入/参考输出产生前冻结。若已执行，分数为 {pred}。规则成本加上实测CPU特征/lookup开销；这是离线相位和，不是已经集成的selector或decoder收益。",'',
    'PR120中局部反转与本轮输入/方法不同，不能把跨轮点差直接称同一效应被推翻。本轮检验的是哪些原始局部方向能在新的平衡采集、替代QB、值模式和A/A条件下保留。','',
    '## 4. 成本含义与硬件边界','',
    '主视图为QPC的compute调用开始到全设备同步返回；completed-call再加普通输出readback。必要packing、CONT/REPEAT、mask和恢复留在真实图中。输入包含视图是每宿主一次CPU物化+upload/sync+首次warmup完成call的相位和，不是30次独立完整请求。冷初始化含身份哈希/审计，分配、文件读取、输出缓冲预分配和完整宿主墙钟单列；固定记录向量分配等未分项冷开销仍包含在宿主墙钟，不能称其免费。见 [OTHER_COST_VIEWS.json](results/OTHER_COST_VIEWS.json) 和 [HOST_DISTRIBUTIONS.csv](results/HOST_DISTRIBUTIONS.csv)。','',
    '没有合格profiler，所以kernel身份/数量、物理流量、occupancy、Tensor Core和具体backend归因均UNKNOWN。几何/软件成本边界不是硬件收益。没有actor、自然decoder/W1、模型请求、RTL/FPGA、论文修改或B570任务。端点空闲及clock/power观察不保证期间独占或锁频。','',
    '共同producer视图另见 COMMON_PRODUCER_AGGREGATES.csv：真实C++ CPU测量从相同逻辑Q准备目标布局、复制完整KV并构造mask，每输入两个新CPU进程。它替换预格式拷贝分项后与实际GPU upload/首次call作相位和；不是已经集成并计时的事务，也不计自然decoder生成Q/K/V的未知成本。CPU两进程的分量共享于多个GPU块，因此该附加视图仅作描述性成本核算。','','## 失败、资源与复现','',
    f"资源：{resource}。所有预算内已完成数据保留；无按延迟删尾或择优GPU重跑。CPU阶段保留构建回执命名冲突、错误git目录导致freeze拒绝，以及测试fixture选择失误；最后CPU19项协议+3项适配+8项证据负测试通过，156张核心CPU完整图及非法入口检查通过。",'',
    f"原始归档位于 `{arc['archive_path']}`，{arc['members']}成员，容器SHA256 `{arc['archive_sha256']}`；manifest `{arc['member_manifest_sha256']}`。全部成员已本机fresh restore，新解释器复算科学文件字节一致。RAW_LOCAL_ONLY，没有远端raw上传或外部独立审查；紧凑Git结果另做真实远端回读。详见 [RAW_LOCATION.json](RAW_LOCATION.json)。",'',
    '数值运行时按原机路径与21个DLL哈希绑定，归档包含新宿主和完整输入/输出，但没有复制整套CUDA数值DLL。Fresh验证是CPU恢复复算，不是GPU重跑；资格限于每宿主固定输入重放，动态请求、KV更新和graph cache仍未建立。','',
    '下一步按实际分辨尺度选择有信息量的受控机制/更广分布确认；没有物理瓶颈和系统相关性证据前不进入微架构。原始QPC样本、warmups、所有ordinary/input字节、模块/IAT、图和生命周期记录均在归档；不要重启本UUID。']
    (V/'RESULT.md').write_text('\n'.join(text)+'\n',encoding='utf-8');print('Generated result',resource['native_hosts'],resource['graph_calls'])
if __name__=='__main__':main()
