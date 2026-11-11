"""CPU-only finite study accounting, Chinese report and platform comparison."""
from pathlib import Path
import json,csv,hashlib,statistics,math
ROOT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(name,x):(ROOT/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def digest(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()
def report():
 if not all((ROOT/name).exists() for name in ['B_SUMMARY.json','PROTOCOL.json']):
  v=read(ROOT/'INDEPENDENT_VERIFICATION.json');rows=[read(f) for f in (ROOT/'raw').glob('*/RESULT.json')];stages=[]
  for f in ROOT.glob('*_SCHEDULE.json'):
   name=f.name[:-len('_SCHEDULE.json')];n=sum(len(s['inputs']) for s in read(f));done=[r for r in rows if r['unit_id'].startswith(name+'/')]
   stages.append({'stage':name,'status':'COMPLETED_PASS' if sum(not r['warm'] for r in done)==n else 'INFRA_BLOCKED','planned':n,'completed':sum(not r['warm'] for r in done),'warm':sum(r['warm'] for r in done)})
  save('STAGE_COUNTS.json',{'core_complete_measured':False,'stages':stages,'complete_raw_records':len(rows),'reason':'Pipeline interrupted before required core summaries. No finite core closure or speed claim.'})
  save('DECISION.json',{'closure':'PARTIAL','archive_restore':'PENDING','remote_readback':'PENDING','E':{'status':'NOT_RUN_TIME'},'merge':'Do not merge'})
  (ROOT/'REPORT.md').write_text('# B570 部分执行记录\n\n状态 **PARTIAL**。旧参考/工程控制和完整原始记录已保留；核心 B/C/原锚点/D 尚未完整完成，不宣称平台闭环或新增收益。实际完成分母见 STAGE_COUNTS.json，失败原因见 PIPELINE_FAILURE 及原始 attempts。独立解析只认证现有完整记录；缺失阶段并未计作通过。归档和交付状态见实际恢复/远端回读收据。六个研究问题中尚未完成的面板、宽度、长驻、收益与状态机制均保持未验证；当前投入决定为核心未完成。\n',encoding='utf-8',newline='\n')
  return
 v=read(ROOT/'INDEPENDENT_VERIFICATION.json');p=read(ROOT/'PROTOCOL.json');inputs=read(ROOT/'INPUTS.json')
 records=[read(f) for f in (ROOT/'raw').glob('*/RESULT.json')];stages=[]
 required={'G0':144,'G0_BRIDGE':20,'B':p['B'],'C':p['C'],'C_ANCHOR_LONG':p['C_ANCHOR_LONG'],'D_RESET':96,'D_TIMING':96}
 core_complete=v['status']=='PASS'
 for name,n in required.items():
  rr=[r for r in records if r['unit_id'].startswith(name+'/')];completed=sum(not r['warm'] for r in rr);warm=sum(r['warm'] for r in rr)
  gated=name.startswith('D_') and (ROOT/'D_GATE.json').exists()
  qual=[g['qualification'] for g in v['stages'].get(name,{}).get('groups',[])]
  status='GATED_BY_QUALIFICATION' if gated else 'NOT_RUN_TIME' if completed<n else 'COMPLETED_SCIENTIFIC_FAIL' if any(not all(q.values()) for q in qual) else 'COMPLETED_PASS'
  core_complete&=gated or completed==n
  stages.append({'stage':name,'status':status,'planned':n,'completed':completed,'unexecuted':n-completed,'warm':warm,'qualification':qual,'scientific_failed_requests':sum(g.get('scientific_failed_requests',0) for g in v['stages'].get(name,{}).get('groups',[])),'failure_contract':'G0 historical N0 failures are expected retained outcomes, not a G0 contract failure' if name=='G0' else 'Own paid stable reference'})
 for name in ['G0_REBUILT','G0_SHAM','G0_WIDTH','G0_TARGET_FINAL','G0_ETA','G0_ETA_N0','G0_DEVICE_REQUALIFICATION','G0_CONTINUATION_QUAL','E_CAPTURE','E_PILOT','E_CONFIRM','E_LONG','E_D_RESET','E_D_TIMING','MECHANISM']:
  sched=ROOT/(name+'_SCHEDULE.json')
  if not sched.exists():continue
  n=sum(len(s['inputs']) for s in read(sched));rr=[r for r in records if r['unit_id'].startswith(name+'/')]
  sciencefail=sum(g.get('scientific_failed_requests',0) for g in v['stages'].get(name,{}).get('groups',[]))
  if name=='G0_WIDTH':sciencefail=sum(not o['reference_equal'] for o in read(ROOT/'G0_WIDTH.json')['observations'])
  if name=='G0_TARGET_FINAL':sciencefail=sum(not o['reference_equal'] for o in read(ROOT/'G0_TARGET_FINAL.json')['width_observations'])
  stages.append({'stage':name,'status':'NOT_RUN_TIME' if sum(not r['warm'] for r in rr)<n else 'COMPLETED_SCIENTIFIC_FAIL' if sciencefail else 'COMPLETED_PASS','planned':n,'completed':sum(not r['warm'] for r in rr),'unexecuted':n-sum(not r['warm'] for r in rr),'warm':sum(r['warm'] for r in rr),'scientific_failed_requests':sciencefail,'category':'auxiliary or optional, not added to core denominator'})
 e_status=read(ROOT/'E_DECISION.json').get('status') if (ROOT/'E_DECISION.json').exists() else None
 for name,n in [('E_CONFIRM',len(inputs['shared']+inputs['unused'])*16),('E_LONG',(p['C_shared_count']+len(inputs['long']))*12),('E_D_RESET',96),('E_D_TIMING',96)]:
  if not (ROOT/(name+'_SCHEDULE.json')).exists() and e_status in ['CONFIGURATION_PILOT','NO_GO_PILOT','NOT_RUN_TIME']:
   stages.append({'stage':name,'status':'NOT_RUN_TIME' if e_status!='NO_GO_PILOT' else 'GATED_BY_QUALIFICATION','planned':n,'completed':0,'unexecuted':n,'warm':0,'category':'conditional E continuation; not required core','reason':e_status})
 if (ROOT/'MECHANISM.json').exists() and not (ROOT/'MECHANISM_SCHEDULE.json').exists():
  ms=read(ROOT/'MECHANISM.json');stages.append({'stage':'MECHANISM','status':ms['status'],'planned':0,'completed':0,'unexecuted':0,'warm':0,'category':'conditional C failure diagnostic; no pair selected','reason':ms.get('reason','')})
 recovered_units={x['unit_id'] for x in records if x.get('CPU_payload_recovered')}
 failures=[]
 for f in ROOT.glob('**/FAILURE.json'):
  if 'archive' in f.parts:continue
  start=f.parent/'START.json';failures.append({'path':str(f.relative_to(ROOT)).replace('\\','/'),'request':read(start).get('unit_id') if start.exists() else None,'failure':read(f),'category':'controller infrastructure marker; complete payload independently recovered without replay' if start.exists() and read(start).get('unit_id') in recovered_units else 'infrastructure; no complete valid scientific output'})
 save('STAGE_COUNTS.json',{'core_profile':p['budget_profile'],'planned_core':p['planned_core_requests'],'core_complete_measured':core_complete,'all_complete_current_raw':len(records),'stages':stages,'failed_attempts':failures,'original_deadline':read(ROOT/'STARTUP.json'),'recovery_window':read(ROOT/'RECOVERY_AMENDMENT.json'),'authorized_continuation_window':read(ROOT/'CONTINUATION_AMENDMENT.json') if (ROOT/'CONTINUATION_AMENDMENT.json').exists() else None,'engineering_previous_builds':'Separate engineering-* records preserved in archive; not included as formal core or unused inputs.'})
 if (ROOT/'DEVICE_RECOVERY_AMENDMENT.json').exists():
  counts=read(ROOT/'STAGE_COUNTS.json');counts['infra_rejected_platform_records']=read(ROOT/'DEVICE_RECOVERY_AMENDMENT.json')['rejected'];save('STAGE_COUNTS.json',counts)
 b=read(ROOT/'B_SUMMARY.json');e=read(ROOT/'E_DECISION.json') if (ROOT/'E_DECISION.json').exists() else {'status':'NOT_RUN_TIME'};m=read(ROOT/'MECHANISM.json') if (ROOT/'MECHANISM.json').exists() else {'status':'NOT_RUN_TIME','causal_status':'NOT_CAUSALLY_IDENTIFIED'}
 decision={'closure':'MEASURED_CORE_COMPLETE_PENDING_DELIVERY' if core_complete else 'PARTIAL','scope':p['budget_profile'],'E':e,'shared_anchor':b['shared']['qualification'],'unused_anchor':b['unused']['qualification'],'mechanism_causal_status':m.get('causal_status','NOT_CAUSALLY_IDENTIFIED'),'archive_restore':'PENDING','remote_readback':'PENDING','merge':'NOT_AUTHORIZED; leave draft','energy':'NOT_MEASURED; no board-energy claim','functional_accuracy':'NOT_MEASURED; output fidelity only'}
 save('DECISION.json',decision)
 lines=['# B570 有限闭环实验报告','',f"预算档：**{p['budget_profile']}**。当前状态：**{decision['closure']}**。最终交付状态以 `DELIVERY_VERIFIED.json` 为准。",'', '本批次独立追加 PR #63，未改论文、旧实验、驱动或系统设置。驱动差异按用户指示记录；旧参考仍通过本轮实际生成核对。原预算和中断记录保留，恢复窗口见 `RECOVERY_AMENDMENT.json`。','', '## 1. 旧修复与两个输入队列','',f"旧24个 HumanEval 的 R/N0/N1 各两次及五个诊断/控制的 matched bridge 完成。新共享24个 MBPP 与项目审计范围内未执行的 {len(inputs['unused'])} 个 MBPP 独立计数。共享输入已被 RTX 使用，不称项目未执行。",'', '| 队列 | R | matched T | ordinary native | 原修复 native |','|---|---:|---:|---:|---:|']
 for name in ['shared','unused']:
  q=b[name]['qualification'];lines.append('| '+name+' | '+' | '.join('PASS' if q[x] else 'FAIL' for x in ['R_reference','T_matched','N0_ordinary','N1_repaired'])+' |')
 lines+=['','旧 G0 中 ordinary native 的四个历史任务失败按原合同保留；G0 PASS 表示正确复现历史参考、原失败与修复，不把 N0 全部称为合格。费用对照的 matched continuation 输出槽修订及新 33 请求/9 热身资格另见 MATCHED_RESERVATION_AMENDMENT.json 与 G0_TARGET_FINAL.json。','', '本轮使用现有 Windows 桌面环境。旧任务工程探针期间曾观察到动态壁纸视频解码占用；临时暂停操作被自动审批拒绝，未执行，未绕过，未结束用户程序。ENVIRONMENT_OBSERVATIONS.json 保留快照范围。正式费用是该实际桌面条件下的平衡重复结果；没有把 shared-memory 计数解释成分页证明，也没有把耗时变化归因于壁纸、温度或频率。']
 lines+=['','完整 IDs、首 runtime EOG、长度和 cap 契约逐项比较；native 原始 overshoot 保留并计入实际工作与费用，不以输出文本或重分词代替直接 IDs。失败任务和首次差异见 `B_SUMMARY.json`。暴露审计依据可访问历史及固定 RTX 收据；未取得的 RTX 巨型历史没有假称独立扫描。','', '## 2. 宽度与实际长度','', '| k / continuation UB | cap | 共享 matched/native | 旧长 matched/native |','|---|---|---|']
 if not (ROOT/'C_SUMMARY.json').exists():lines+=['','C 核心矩阵尚未完成；已付费完整片段及实际分母保留在独立验证和阶段计数中。未完成的宽度/队列/cap 不计作通过，阶段保持 NOT_RUN_TIME / PARTIAL。']
 if (ROOT/'DEVICE_RECOVERY_AMENDMENT.json').exists():lines+=['','设备枚举修复：第四轮 B 与部分长锚点实际使用 UHD730，共190条完整请求（含12条热身）列为 INFRA_REJECTED_PLATFORM，原字节和计时保留；它们不构成 B570 科学结果。恢复只重做平台身份不合格的请求，完成的 B570 科学结果复用。原截止时刻保留；超时缺失仍为 PARTIAL。详见 DEVICE_RECOVERY_AMENDMENT/FREEZE 与独立核验。']
 if (ROOT/'C_ANCHOR_SUMMARY.json').exists():
  anchor=read(ROOT/'C_ANCHOR_SUMMARY.json');lines+=['','原 k2 / target prefill128 → continuation1 长锚点：84/84 正式请求完成，cap256、512 的 ordinary R / matched T / N1 全部保留参考。任务仍为冻结4个共享输入和3个旧长输入，没有据输出更换队列。实际普通参考终点如下：','', '| cap | task | reference tokens | endpoint |','|---|---|---:|---|']
  for cap,item in anchor.items():
   for d in item['details']:
    if d['label']=='R_reference':lines.append(f"| {cap} | {d['task']} | {d['reference_length']} | {d['reference_reason']} |")
  lines+=['','长输出通过不等于完整长驻 reset 面板通过。']
 if (ROOT/'CONTINUATION_AMENDMENT.json').exists():lines+=['','用户在上一截止后明确授权继续完成平台闭环；续跑时窗另存 CONTINUATION_AMENDMENT.json，原 PARTIAL 报告/截止/失败保留在 engineering-continuation-v1。原输入、配置与数值程序未重选，已完成有效科学输出不重复生成。一个截止时已完整写出的请求经 CPU 核对回收，见 CPU_PAYLOAD_RECOVERY.json；host 延迟为包含停机清理的上界，C++ 计时原样保留。']
 if (ROOT/'PAUSE_RESUME_AMENDMENT.json').exists():lines+=['','用户明确暂停后于晚间授权恢复，并报告已关闭屏保。暂停位置和原结果保留；另有一个暂停时已经写完的请求经 CPU 核对回收，避免重复。环境变化仅按用户描述记录，不宣称动态壁纸已完全退出或性能变化的因果来源。B/部分D属于较早环境，后续C/E属于续跑时段，各自队列/阶段费用分别解释。见 PAUSE_RESUME_AMENDMENT.json 与 CPU_PAYLOAD_RECOVERY_PAUSE.json。']
 old_width=read(ROOT/'G0_WIDTH.json');old_boundary=[o for o in old_width['observations'] if o['config']['native'] and not o['reference_equal']]
 lines+=['',f"旧任务工程宽度 proof 另保留 {len(old_boundary)} 条完整 native 参考偏离，详见 G0_WIDTH.json。它们位于原 C/E 队列之外的旧控制输入；C/E 在自身固定队列通过也不能抹去这些反例或扩张为原24任务的普适资格。"]
 lines+=['', '| k / continuation UB | cap | 共享 matched/native | 旧长 matched/native |','|---|---|---|---|']
 for r in read(ROOT/'C_SUMMARY.json') if (ROOT/'C_SUMMARY.json').exists() else []:
  fmt=lambda name:'/'.join('PASS' if r[name]['qualification'][label] else 'FAIL' for label in ['T_matched','N_candidate'])
  lines.append(f"| {r['k']} / {r['ub']} | {r['cap']} | {fmt('shared')} | {fmt('long')} |")
 lines+=['','所有宽度均固定 target prefill128、draft prefill/continuation1。ctx1024，threads10，FA off，greedy seed123。每个 cap 自然 EOG 或上限结束；实际长度、suffix 和首次差异见 C 明细。容量与实际 query 数不同；旧任务扩展 proof、D/E capture 的实际图观察单独保留，未捕获的逐任务 micrograph 范围记 missing，不猜测 kernel 启动数。','', '## 3. 原锚点的长驻状态','']
 for name in ['D_RESET','D_TIMING']:
  item=next(s for s in stages if s['stage']==name);lines.append(f"- {name}: {item['status']}，{item['completed']}/{item['planned']} 请求，{item['warm']} 热身。")
 if (ROOT/'D_GATE.json').exists():lines+=['',f"跳过理由：`{read(ROOT/'D_GATE.json')['reason']}`。这是原协议的科学资格门槛，不是以新配置冒充原 D 通过。"]
 lines+=['','每请求清两模型 KV、采样器、pending 和历史；模型每会话只加载一次、无 prompt/KV cache、单请求串行服务。capture-on 资格与 capture-off 费用分开，不能称多并发吞吐。','', '## 4. 真实效率与额外收益','', '| 阶段 / 队列 | 基线 → 候选 | 输出资格 | 生成比 | 整请求比 |','|---|---|---|---:|---:|']
 for c in v['costs']:
  if c['stage'] not in ['B','D_TIMING','E_CONFIRM','E_D_TIMING']:continue
  lines.append(f"| {c['stage']} / {c['cohort']} | {c['baseline']} → {c['candidate']} | {'合格' if c['qualified'] else '失败，仅诊断费用'} | {c['generation_ms']:.4f} | {c['whole_request_ms']:.4f} |")
 lines+=['', '比值为基线耗时/候选耗时：每任务取重复中位数，再求任务几何平均。绝对 ms 与每任务分布见 derived CSV。生成计时包括 sampler/batch 初始化、pending 源采样、真实状态序列化/载入/往返校验、草稿、验证、rollback、最终设备同步；整请求另含 prefill/reset/cleanup。证据文件落盘在 C++ 计时外，真实 host 延迟另保留。模型/上下文冷加载和热身单独列账。失败输出费用不称无损加速。','',f"E 决定：**{e['status']}**。E 的实际计划、pilot、选择、独立确认仅以已经生成的对应文件为依据；缺少对应文件的阶段为未执行，不称新增收益。布局原型本批次 `NOT_IMPLEMENTED`，未改变发布 Vulkan shader 算术。",'', '## 5. 状态证据与 RTX 迁移边界','',f"局部机制状态：**{m.get('causal_status','NOT_CAUSALLY_IDENTIFIED')}**。",'', '真实 prefill 状态往返、source 不变、pending 首样本及克隆 sampler 的链/history/seed均有证据。机制诊断的实际执行及自然父轨迹以 MECHANISM.json 和原始 MECHANISM 请求为依据；C 全矩阵没有失败配置时，本次诊断按冻结 C 选择规则为 GATED_BY_QUALIFICATION；这不抹去 B_unused /72 的失败。因果状态仍为 NOT_CAUSALLY_IDENTIFIED。已有 prefill 证据来自 G0、资格控制和实际完成的请求。生成没有使用参考 ID、强制前缀或未来 proposal tape。当前前端缺少自然中途的完整 donor+draft+post-sample sampler checkpoint，未执行 2×2 状态反事实，不称过去状态或当前布局是唯一原因。top1/top2 margin 与指定参考 EOS/替代 token margin 分开，后者未取得完整 logits 时明确 missing。opaque sampler 字节和唯一 Vulkan kernel 身份未认证。','', 'RTX 的局部布局资格和增加 k 可能变慢的经验用作设计依据；RTX k3/UB4、CUDA、global UB1参考不作为 B570 答案。共享24个输入的逐任务平台行见 `RTX_B570_COMPARISON.csv`；两平台参考、ctx、threads、后端及原始 suffix 契约不同，不作直接 token 等同或单变量硬件因果结论。','', '## 6. 投入决定与可恢复证据','',f"当前选择：`{e['status']}`；核心完整性：`{core_complete}`。合格但更慢就是无额外效率收益；无法完成的阶段保持 PARTIAL。本轮核心完成{sum(x['completed'] for x in stages if x['stage'] in required)}/{p['planned_core_requests']}个正式请求；剩余分母逐阶段见下表。核心未完成时，即使归档/回读通过仍为 PARTIAL；只有原合同所有核心测量或科学资格门控以及独立核验、实际恢复和远端回读通过才支持有限范围闭环。",'', '| 阶段 | 状态 | planned | complete | unexecuted | warm |','|---|---|---:|---:|---:|---:|']
 for s in stages:lines.append(f"| {s['stage']} | {s['status']} | {s['planned']} | {s['completed']} | {s['unexecuted']} | {s['warm']} |")
 lines+=['', '## C 的独立匹配成本','', '| 队列 | k / UB | cap | 基线 → 候选 | 输出资格 | 生成比 | 整请求比 |','|---|---|---|---|---|---:|---:|']
 for cost in v['costs']:
  if cost['stage']=='C':lines.append(f"| {cost['cohort']} | {cost['k']} / {cost['ub']} | {cost['cap']} | {cost['baseline']} → {cost['candidate']} | {'合格' if cost['qualified'] else '失败，仅诊断'} | {cost['generation_ms']:.4f} | {cost['whole_request_ms']:.4f} |")
 if (ROOT/'E_PILOT_SUMMARY.json').exists():
  lines+=['', '## 固定 UB 的完整效率 pilot','', '以下均为已暴露选择队列上的探索费用，独立确认未完成时不能作新增收益或部署结论。每配置24请求、两轮；共享8任务与旧4诊断任务分别核算。','', '| 配置 | 全 pilot 参考 | 进入确认门槛 | 全队列生成/整请求比 | 共享生成/整请求比 | 旧诊断生成/整请求比 |','|---|---|---|---|---|---|']
  for obs in read(ROOT/'E_PILOT_SUMMARY.json')['observations']:
   stats=obs['costs'];ratio=lambda q:f"{q['generation_ms']:.4f}/{q['whole_request_ms']:.4f}"
   lines.append(f"| {obs['config']['label']} | {obs['qualified']} | {obs['eligible']} | {ratio(stats)} | {ratio(stats['cohorts']['shared_pilot'])} | {ratio(stats['cohorts']['old_diagnostics'])} |")
 lines+=['',f"独立 CPU 验证：{v['status']}，{v['checks']} 项检查，{v['complete_records']} 条完整记录，零模型 forward。失败 attempts 和此前工程记录全部归档。外部权重/运行库及旧 capsule 是独立哈希依赖，不进入 PR 或新包 payload。",'', '本报告不推断 HumanEval 功能正确率、能耗收益、普适最小范围定理或唯一内核原因。']
 if (ROOT/'WORK_ACCOUNTING.json').exists():
  work=read(ROOT/'WORK_ACCOUNTING.json');lines+=['','## 实际工作量与缺失观察','', '逐请求 caller 次数/输入数量、草稿与接受数量/比例、真实 prefill 状态转移次数及 capture 中的 micrograph 观察见 WORK_ACCOUNTING.json / CSV；已在干净恢复的同一原始字节上独立重算一致。capture-off 没有图数量，统一记 missing。观察器未逐项记录 synchronization 次数，不能从源码估计或把 KV mutation 当同步；完整同步费用仍包含在冻结 C++ 计时中。图观察与 API 调用均不称 kernel 启动数。','', '| 阶段 | 条件 | 请求 | target calls | draft calls | drafted | accepted | accepted/drafted |','|---|---|---:|---:|---:|---:|---:|---:|']
  for stage in ['D_TIMING','E_PILOT']:
   for label in sorted({row['label'] for row in work['records'] if row['stage']==stage and not row['warm']}):
    rr=[row for row in work['records'] if row['stage']==stage and row['label']==label and not row['warm']];drafted=sum(row['drafted'] or 0 for row in rr);accepted=sum(row['accepted'] or 0 for row in rr)
    lines.append(f"| {stage} | {label} | {len(rr)} | {sum(row['target_calls'] for row in rr)} | {sum(row['draft_calls'] for row in rr)} | {drafted} | {accepted} | {accepted/drafted:.4f} |" if drafted else f"| {stage} | {label} | {len(rr)} | {sum(row['target_calls'] for row in rr)} | {sum(row['draft_calls'] for row in rr)} | 0 | 0 | N/A |")
 (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
 # Every shared task gets platform-specific contract rows; references remain separate.
 rtx=read(ROOT/'dependencies/8dfa60a/B_RESULTS.json');comp=[]
 speed=next(c for c in rtx['costs'] if c['numerator']=='target_scopes' and c['denominator']=='matched_target')
 for task in inputs['shared']:
  for label in ['R_reference','T_matched','N0_ordinary','N1_repaired']:
   rr=[r for r in records if not r['warm'] and r['unit_id'].startswith('B/') and r['task']==task['id'] and r['config']['label']==label]
   item=next(d for d in b['shared']['details'] if d['task']==task['id'] and d['label']==label);native=label.startswith('N');c=rr[0]['config']
   captured=[r for r in records if r['task']==task['id'] and r['config'].get('label')==label and r['config'].get('capture') and r['config'].get('cap',128)==128]
   actual=[]
   for r in captured:
    raw=read(next(ROOT/f for f in r['files'] if f.endswith('/capture.json')))
    actual += [g['ne1'] for call in raw['trace'] if call['event']=='decode' and call['role']=='target' and call['phase']=='continuation' for g in call['graphs'] if g['tensor']=='embd']
   comp.append({'platform':'B570','task':task['id'],'condition':label,'target_model_sha256':p['models']['target'],'draft_model_sha256':p['models']['draft'],'backend_runtime':'Vulkan b10839; ASSET_POST binds actual DLL bytes','prompt_sha256':task['formatted_prompt_sha256'],'token_input_sha256':digest(task['prompt_ids']),'reference':'B570 paid ordinary UB128 reference; common prompt batching; serial continuation','ctx':1024,'threads':10,'k':2 if native else 0,'target_prefill_ub':c['prefill'],'target_continuation_ub':c['ub'],'draft_prefill_ub':1 if native else None,'draft_continuation_ub':1 if native else None,'layout':'published Vulkan; no shader arithmetic changes','actual_target_query_range':[min(actual),max(actual)] if actual else 'MISSING: no per-task capture; capacity/old proof not substituted','past_pending':'source sample once + post-sample clone + authentic restored state' if label!='R_reference' else 'source ordinary context, no restoration','endpoint':'inclusive first runtime EOG or cap128; full native overshoot retained and timed','exposure':task['cohort'],'qualified':item['qualified'],'actual_lengths':item['observed_lengths'],'raw_suffix':item['raw_suffix_counts'],'generation_ms':statistics.median(r['metrics']['generation_ms'] for r in rr),'whole_request_ms':statistics.median(r['metrics']['whole_request_ms'] for r in rr),'timing_boundary':'all online costs, terminal synchronization; cold/warm/capture separate','reset':'per-request fresh KV/sampler/pending/history; D separately gated','local_mechanism':m.get('causal_status','NOT_CAUSALLY_IDENTIFIED'),'unknown':'opaque sampler bytes; unique dispatch; no board-energy metric'})
  for label in ['scalar_reference','matched_target','target_scopes','all_scopes']:
   d=next(d for d in rtx['details'] if d['task']==task['id'] and d['condition']==label);scalar=label=='scalar_reference';native=label in ['target_scopes','all_scopes']
   comp.append({'platform':'RTX','task':task['id'],'condition':label,'target_model_sha256':p['models']['target'],'draft_model_sha256':p['models']['draft'],'backend_runtime':'released b10839 CUDA; frozen #62 evidence','prompt_sha256':task['formatted_prompt_sha256'],'token_input_sha256':digest(task['prompt_ids']),'reference':'RTX paid global UB1 scalar reference, not B570 ordinary UB128','ctx':4096,'threads':24,'k':3 if native else 0,'target_prefill_ub':1 if scalar else 4,'target_continuation_ub':1 if scalar else 4,'draft_prefill_ub':4 if native else None,'draft_continuation_ub':4 if native else None,'layout':'mask0/3/15 as frozen RTX table; mask3 target attention per-query, other work batched','actual_target_query_range':'MISSING per-task raw RTX graph; source summary not independently rescanned','past_pending':'RTX natural source state, local graph constraint; no B570 prefill context transfer','endpoint':'inclusive EOG/cap128; RTX native suffix contract differs','exposure':'cross_platform_shared_project_exposed','qualified':d['full_equal'],'actual_lengths':d['observed_token_counts'],'raw_suffix':'not copied from B570','generation_ms':'MISSING: summary retains ratios, RTX bulk timings not locally restored','whole_request_ms':'MISSING: summary retains ratios','timing_boundary':'frozen RTX resident C++ boundaries; actual draft/verify/cleanup included','reset':'RTX separately passed frozen D; no inherited B570 qualification','local_mechanism':'RTX /229 natural state-cross result is configuration-local, not B570 evidence','unknown':'backend/reference/context/thread confounding; inaccessible bulk history disclosed','reported_generation_vs_matched':speed['generation']['task_ratios'][task['id']] if label=='target_scopes' else None})
 save('RTX_B570_COMPARISON.json',comp)
 fields=list(dict.fromkeys(k for r in comp for k in r))
 with (ROOT/'RTX_B570_COMPARISON.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in comp])
 save('REQUEST_ACCOUNTING.json',[{'unit_id':r['unit_id'],'stage':r['unit_id'].split('/')[0],'task':r['task'],'warm':r['warm'],'config':r['config'],'source_commit':r['source_commit'],'actual_length':len(r['endpoint']['ids']),'endpoint':r['endpoint']['reason'],'raw_suffix':r['endpoint']['raw_suffix'],'generation_ms':r['metrics']['generation_ms'],'whole_request_ms':r['metrics']['whole_request_ms'],'host_seconds':r['host_seconds'],'host_seconds_reconstruction':r.get('host_seconds_reconstruction'),'CPU_payload_recovered':r.get('CPU_payload_recovered',False),'drafted':r['metrics'].get('drafted'),'accepted':r['metrics'].get('accepted'),'files':r['files']} for r in records])
 loads=[read(f) for f in (ROOT/'sessions').glob('*/SESSION_LOAD.json')];closed=[read(f) for f in (ROOT/'sessions').glob('*/SESSION_CLOSE.json')];save('COLD_LOAD_ACCOUNTING.json',{'recorded_sessions':len(loads),'model_and_context_initialization_seconds':sum(x['model_and_context_load_seconds'] for x in loads),'model_session_teardown_seconds':sum(x['model_session_cleanup_seconds'] for x in closed),'nonzero_teardown_exit_codes':[x for x in closed if x['process_exit_code']!=0],'records':loads,'teardown_records':closed,'old_sessions':'Pre-amendment G0 load/teardown times were not recorded in these fields; not invented from generator counters'})
 print({'core_complete':core_complete,'E':e['status'],'comparison_rows':len(comp)},flush=True)
if __name__=='__main__':report()
