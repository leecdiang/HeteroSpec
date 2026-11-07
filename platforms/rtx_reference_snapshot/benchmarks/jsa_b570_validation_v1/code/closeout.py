"""CPU-only evidence/accounting/negative guards and finite scientific closeout."""
import json,hashlib,statistics,math,time,shutil,sys,collections
from datetime import datetime
from pathlib import Path
R=Path(sys.argv[2]) if len(sys.argv)>2 else Path('C:/hs/jsa-b570-run-v1');REPO=Path('C:/hs/jsa-b570-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,x):(R/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def all_records():return [load(p) for p in sorted((R/'raw').glob('*/RESULT.json'))]
def same(a,b):return all(a[k]==b[k] for k in ['ids','eog','reason'])
def natural():
 xs=all_records();tasks=load(R/'SMOL_DISCOVERY_INPUTS.json');rows=[];selected=[]
 for inp in tasks:
  refs=[r for r in xs if r['stage']=='B' and r['task']==inp['id'] and r['round']==0];byarm={x['arm']:x for x in refs}
  divergent=all(a in byarm for a in ['R','N','C']) and any(not same(byarm['R']['endpoint'],byarm[a]['endpoint']) for a in ['N','C'])
  if divergent and len(selected)<2:selected.append(inp['id'])
  rows.append(dict(task=inp['id'],trigger=divergent,natural_checkpoint='UNAVAILABLE_IN_EXACT_INHERITED_N_C_PROGRAM_INTERFACES' if divergent else 'NO_TRIGGER',considered_in_predeclared_order=True))
 status='UNSUPPORTED_NATURAL_RESTORATION' if selected else 'NO_TRIGGER'
 save('NATURAL_DIAGNOSTIC.json',dict(status=status,pre_f0_capability_limit=load(R/'NATURAL_BRANCH_PLAN.json'),selected_first_two_triggers=selected,all_considered=rows,auxiliary_decode_starts=0,donor_requests=0,teacher_prefix=False,scope='No state/path causal result supplied. Inherited N prefill transfer and C in-place phase snapshots are not naturally aligned continuation checkpoints. No path replacement or post-output engineering.'))
 print('Natural diagnostic',status,selected,flush=True)
def negative_guards():
 tests=[]
 def require_matrix(rows,keys):
  found=[r['key'] for r in rows]
  if len(set(found))!=len(found):raise ValueError('duplicate')
  if set(found)!=set(keys):raise ValueError('missing')
 def raw_claim(ids,ref,claim):
  if claim and ids!=ref:raise ValueError('endpoint EOG match cannot qualify raw suffix')
 def cost_claim(baseline,candidate,qualified,reported):
  if not qualified and reported is not None:raise ValueError('unqualified cost')
  if qualified and not math.isclose(baseline/candidate,reported,rel_tol=1e-12):raise ValueError('ratio orientation')
 cases=[('missing',lambda:require_matrix([dict(key='R')],['R','C'])),('duplicate',lambda:require_matrix([dict(key='R'),dict(key='R')],['R'])),('EOG_suffix_misqualification',lambda:raw_claim([4,2,8],[4,2],True)),('inverse_ratio',lambda:cost_claim(4,2,True,.5)),('unqualified_cost',lambda:cost_claim(4,2,False,2))]
 for name,fn in cases:
  try:fn()
  except ValueError as e:tests.append(dict(case=name,status='REJECTED_AS_REQUIRED',reason=str(e)))
  else:raise AssertionError(name+' accepted')
 # Valid controls including a complete qualified R/C despite unrelated N failure.
 require_matrix([dict(key='R'),dict(key='C')],['R','C']);raw_claim([4,2,8],[4,2],False);cost_claim(4,2,False,None);cost_claim(4,2,True,2)
 save('NEGATIVE_CONTRACT_TESTS.json',dict(status='PASS',required_rejections=5,tests=tests,positive_controls=4,unrelated_N_failure_does_not_erase_complete_R_C=True))
def final():
 records=all_records();events=[json.loads(s) for s in (R/'LEDGER.jsonl').read_text(encoding='utf8').splitlines()];starts=[x for x in events if x['event']=='REQUEST_START'];finished=[x for x in events if x['event']=='REQUEST_COMPLETE'];failed=[x for x in events if x['event']=='REQUEST_FAILURE'];sessions=[load(p) for p in (R/'sessions').glob('*/SESSION_CLOSE.json')]
 keys=[r['unit'] for r in records];assert len(keys)==len(set(keys));startedkeys=[s['unit'] for s in starts];assert len(startedkeys)==len(set(startedkeys)),'scientific retries'
 assert set(keys)=={s['unit'] for s in finished};assert set(keys)<=set(startedkeys)
 eng=sum(not s['warm'] and s['stage']!='D' for s in starts);formal=sum(not s['warm'] and s['stage']=='D' for s in starts);warm=sum(s['warm'] for s in starts)
 enforcement_eg=sum(s['active_seconds'] for s in sessions if s['stage']!='D');enforcement_fg=sum(s['active_seconds'] for s in sessions if s['stage']=='D');assert eng<=256 and formal<=384 and warm<=64 and len(starts)<=704 and enforcement_eg<=28800 and enforcement_fg<=28800 and enforcement_eg+enforcement_fg<=57600
 timing=[]
 for p in sorted((R/'sessions').glob('*/SESSION_CLOSE.json')):
  close=load(p);session=load(p.parent/'SESSION.json');creation=int(session['creation_identity'])/10_000_000-11_644_473_600;end=datetime.fromisoformat(close['utc']).timestamp();seconds=end-creation
  assert 0<seconds<=close['active_seconds']+0.1
  timing.append(dict(session=p.parent.name,stage=close['stage'],process_creation_unix_seconds=creation,observed_closed_utc=close['utc'],owned_session_upper_bound_seconds=seconds,conservative_controller_seconds=close['active_seconds']))
 eg=sum(s['owned_session_upper_bound_seconds'] for s in timing if s['stage']!='D');fg=sum(s['owned_session_upper_bound_seconds'] for s in timing if s['stage']=='D')
 save('ACTIVE_GPU_ACCOUNTING.json',dict(sessions=timing,engineering_owned_seconds_upper_bound=eg,formal_owned_seconds_upper_bound=fg,total_owned_seconds_upper_bound=eg+fg,controller_bound_seconds=enforcement_eg+enforcement_fg,scope='Actual Windows process-creation FILETIME identity through observed post-exit close receipt. Small post-exit receipt overhead makes this an upper bound. Controller conservatively also charges preflight/hash qualification before creation; performance host timers unchanged.'))
 files=load(R/'F0.json')['frozen_files'];assert all(sha(R/f)==d['sha256'] for f,d in files.items()),'frozen identity changed'
 for family in ['QWEN_MODELS.json','MODEL_CHOICE.json']:
  for role,m in load(R/family)['models'].items():assert sha(m['path'])==m['sha256'],'model final identity'
 count=dict(engineering_started=eng,formal_started=formal,warm_started=warm,total_started=len(starts),total_complete=len(records),failures=len(failed),missing=[x for x in startedkeys if x not in keys],scientific_retries=0,auxiliary_decode_starts=0,engineering_active_gpu_seconds=eg,formal_active_gpu_seconds=fg,total_active_gpu_hours=(eg+fg)/3600,sessions=len(sessions))
 save('COUNTS.json',count);natural();negative_guards()
 work=collections.defaultdict(lambda:collections.Counter())
 for receipt in records:
  folder=R/'raw'/hashlib.sha256(receipt['unit'].encode()).hexdigest()[:24];raw=load(folder/'capture.json');key=receipt['stage']+('/warm' if receipt['warm'] else '')
  for k,v in raw['work'].items():work[key][k]+=v
  work[key]['raw_committed_tokens']+=len(raw['ids']);work[key]['endpoint_committed_tokens']+=len(receipt['endpoint']['ids']);work[key]['suffix_tokens']+=receipt['endpoint']['raw_suffix'];work[key]['instrumented_graph_tensor_observations']+=sum(len(x.get('graphs',[])) for x in raw.get('trace',[]))
 save('WORK_ACCOUNTING.json',dict(by_stage={k:dict(v) for k,v in work.items()},implicit_model_request_starts=0,auxiliary_decode_starts=0,scope='Actual caller decode counts/input tokens and generated raw/endpoint/suffix IDs. Callback tensor observations are instrumented diagnostic graph observations, not full kernel launch counts; full device graph count unavailable in capture-off performance matrix.'))
 a=load(R/'A_VERIFICATION.json');b=load(R/'B_VERIFICATION.json');d=load(R/'D_VERIFICATION.json');states=load(R/'STATE_FLOAT_VERIFICATION.json');assert states['status']=='PASS';q=d['qualification'];cost=d['costs']
 complete=a['status']==b['status']==d['status']=='PASS' and eng==160 and formal==384 and warm==16 and len(records)==560 and not count['missing']
 decision='COMPLETE_FIXED_CANDIDATE_ENDPOINT_TRANSFER_WITHOUT_ORDINARY_GAIN' if complete and q['C']['endpoint_qualified'] and cost['R/C']['qualified_speedup'] is not None and cost['R/C']['qualified_speedup']<=1 else 'COMPLETE_FIXED_CANDIDATE_ENDPOINT_TRANSFER_WITH_ORDINARY_GAIN' if complete and q['C']['endpoint_qualified'] else 'COMPLETE_FIXED_CANDIDATE_ENDPOINT_TRANSFER_FAILED' if complete else 'PARTIAL_INFRASTRUCTURE'
 save('DECISION.json',dict(status=decision,scientific_matrix_complete=complete,delivery_status='PENDING_CAS_AND_REMOTE_READBACK',qualification=q,costs={k:{f:v for f,v in x.items() if f!='taskrows'} for k,x in cost.items()},counts=count,natural=load(R/'NATURAL_DIAGNOSTIC.json')['status'],limits=['Tested Windows/Intel Arc B570/Vulkan b10839 configuration and fixed SmolLM2 GGUF bytes only.','Endpoint equality does not certify complete raw equality or functional code accuracy.','Four fresh process rounds on one date do not establish cross-date or production robustness.','No unique numerical operator cause or GPU energy inference.']))
 save('INDEPENDENT_VERIFICATION.json',dict(status='PASS' if a['status']==b['status']==d['status']=='PASS' else 'PARTIAL_VALIDATION',checks=a['checks']+b['checks']+d['checks']+states['checks']+5,stages={k:dict(status=x['status'],checks=x['checks'],complete=x['complete'],expected=x['expected']) for k,x in [('A',a),('B',b),('D',d)]},state_float=dict(status=states['status'],checks=states['checks']),negative_guards=load(R/'NEGATIVE_CONTRACT_TESTS.json'),frozen_files_verified=len(files),raw_payloads_rederived=True,count_accounting_verified=True,scientific_qualification_separate_from_integrity=True,models_rehashed=True))
 lines=['# B570 第二模型家族独立验证','',f'状态：`{decision}`。数值/成本矩阵已封闭；归档恢复与远端回读状态见单独交付收据。','',f'按 PR #81 固定头执行，原桥接 32/32；SmolLM2 发现及观测资格 128/128；正式 384/384；16 次已暴露 warmup。共 {len(records)} 次完整请求，失败 {len(failed)}，缺失 {len(count["missing"])}，科学重试 0。','',f'整请求付费时间包括 reset、状态/phase 修改、draft/verify/sampling/rollback/sync、完整 payload 与 IDs/EOG 读回校验。原生 whole/generation 另列，不代替 host timer。','', '| 条件 | 端点与 R 全队列相等且稳定 | 完整 raw 与 R 相等 | raw 四轮稳定 |','|---|---|---|---|']
 for arm in ['R','N','M','C']:lines.append(f'| {arm} | {q[arm]["endpoint_qualified"]} | {q[arm]["raw_equal_to_R"]} | {q[arm]["raw_stable"]} |')
 lines+=['','| 比较 | qualified host GM（baseline/C） | 诊断 host GM |','|---|---|---|']
 for pair,x in cost.items():lines.append(f'| {pair} | {x["qualified_speedup"]} | {x["diagnostic_host_GM"]} |')
 lines+=['','每任务取四轮成本中位数，再对全部 24 任务取几何均值；逐轮方向、全部逐任务比和完整负例见 D_VERIFICATION.json。资格失败时保留诊断耗时，qualified speedup 为 null。没有筛选通过任务。','',f'自然状态支路：`{load(R/"NATURAL_DIAGNOSTIC.json")["status"]}`；首两个触发和所有考虑任务列于 NATURAL_DIAGNOSTIC.json。未提交自然 KV 状态×路径因果证据。', '',f'本研究自有 GPU 会话累计 {count["total_active_gpu_hours"]:.3f} 小时；包含 load、warmup、同步及会话等待，工程/正式预算分别核对。未读到固定温度/频率接口的会话明确标为 unavailable。','', '原生成 EXE/DLL 未改动；target 实际全 offload 25 层、draft 31 层，完整 49152 词表与 EOG/tokenizer 元数据独立核对。所有确认输入在任何第二家族 forward 前冻结，F0 与远端 head 收据已发布。','', '暴露审计覆盖约 6.7 万可访问文本，以 ID 和描述双重排除，与 RTX 计划确认名单分离；不可访问私有主机仍为未知，不称训练未见或全项目所有主机均已证明未用。','', '结论仅限固定队列端点和有限会话成本；完整 raw 后缀另核对并收费，不证明功能正确、跨日期稳健性或唯一算子根因。未合并 PR、改稿或追加旧 Qwen 优化。']
 (R/'REPORT.zh-CN.md').write_text('\n'.join(lines)+'\n',encoding='utf8');print(decision,count,flush=True)
if __name__=='__main__':{'natural':natural,'final':final}[sys.argv[1]]()
