"""Independent stdlib-only closeout auditor. Never imports an executor or calls native code.
All derived conclusions use complete native arrays. Hash-only state/logit evidence is
checked for structure/provenance, not represented as independently rehashed tensors.
"""
import argparse,collections,hashlib,itertools,json,math,pathlib,statistics,re
EOG={128001,128008,128009}
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def check(b,why):
 if not b:raise AssertionError(why)
def endpoint(x):
 ids=x['ids'];flags=x['eog'];check(0<len(ids)<=128,'complete output bounds')
 check(all(type(i)is int and 0<=i<128256 for i in ids),'native token IDs')
 check(all(type(f)is bool for f in flags) and flags==[i in EOG for i in ids] and not any(flags[:-1]),'complete EOG flags')
 check(x['cap']==128 and x['length']==len(ids)==len(flags) and x['terminal_id']==ids[-1],'full endpoint identity')
 check(x['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==128),'native stop boundary')
 return (tuple(ids),tuple(flags),len(ids),ids[-1],x['stop_reason'])
def observer_equal(xs):
 check(all(endpoint(xs[0])==endpoint(x) for x in xs[1:]),'observer/full-output drift')
 return True
def difference(a,b):
 for i,(u,v) in enumerate(itertools.zip_longest(a,b)):
  if u!=v:return {'index':i,'left_id':u,'right_id':v}
 return None
def coordinates(records,plan,failed=()):
 expected={s['slot']:(b,s) for b in plan['blocks'] for s in b['slots']}
 check(len(expected)==108 and len(records)+len(failed)==108,'all 108 prospective requests attempted with explicit failure')
 actual={}
 for r in list(records)+list(failed):
  check(r['slot'] not in actual,'duplicate started coordinate')
  check(r['slot'] in expected,'unregistered coordinate');b,s=expected[r['slot']]
  check((r['task'],r['arm'],r['phase'],r['repeat'],r['observation_mode'],r['own_bind_sham'])==
        (s['task'],b['arm'],b['phase'],b['repeat'],b['observation_mode'],b['own_bind_sham']),'prospective factor coordinate')
  check(r['actual_recipe']==plan['arms'][r['arm']] and not r['paid_formal_latency'],'diagnostic not formal price')
  actual[r['slot']]=r
 check(set(actual)==set(expected),'missing prospective coordinates')
 return expected
def histogram(hist,graphs,rows):
 check(all(str(int(k))==k and 0<int(k)<=512 and type(v)is int and v>0 for k,v in hist.items()),'physical histogram occupied rows')
 check(sum(hist.values())==graphs and sum(int(k)*v for k,v in hist.items())==rows,'native graph-row conservation')
def workload(x,counter):
 w=x['workload'];check(w['counter_semantics_sha256']==counter,'counter source semantic binding')
 check(w['prompt_ids_count']==len(x['prompt_ids']) and w['output_ids_count']==len(x['ids']),'denominator includes full output')
 check(w['proposal_generated']==sum(w[k] for k in ['accepted_committed','first_mismatch_rejected','unexamined_after_mismatch','terminal_discarded','unverified_before_verify']),'exclusive proposal fate conservation')
 check(len(x['ids'])==sum(w[k] for k in ['initial_target_committed','accepted_committed','bonus_committed','correction_committed','fallback_committed']),'committed output conservation')
 for role in ['target','draft']:histogram(w[role+'_physical_width_hist'],w[role+'_micrographs'],w[role+'_micrograph_rows'])
 check(w['draft_continuation_rows']==w['draft_proposal_rows']+w['draft_catchup_rows'],'proposal and catchup work both counted')
 check(x['GPU_completion_event_ms'] is None and x['component_completed_wall'] is None,'no fabricated GPU completed timing')
def memory(samples,pid):
 check(bool(samples),'native memory samples required');out=[]
 for m in samples:
  check(m['pid']==pid and m['scope']=='OWNED_MODEL_PROCESS','same owned PID memory scope')
  check(m['vendor_id']==0x8086 and m['device_id']==0xE20C and m['adapter_luid_valid'],'actual B570 LUID')
  h=[h for h in m['heaps'] if h['device_local']];check(len(h)==1,'one dedicated heap')
  h=h[0];check(h['index']==0 and h['physical_size_bytes']==10563354624,'native B570 physical heap')
  d=int(h['budget_bytes'])-int(h['usage_bytes'])
  check(d==m['device_local_headroom_bytes'] and d>=536870912 and m['headroom_gate'],'signed sampled dedicated headroom')
  out.append(d)
 return out
def tracecheck(e,x):
 check(not e['memory']['violation'],'memory observer violation')
 traces=e['target']+e['draft'];count=collections.Counter();rows=collections.Counter();hist={'TARGET':collections.Counter(),'DRAFT':collections.Counter()}
 bindings=[t for t in e['target'] if t['phase']=='BINDING']
 check(len(bindings)==x['workload']['phase_binding_calls'],'actual binding trace calls')
 for t in traces:
  if t['phase']=='BINDING':
   check(t['actual_full_state_bytes_equal'] and t['before_bytes']==t['after_bytes']>0 and t['from_ub']==x['actual_condition']['prefill_ub'] and t['to_ub']==1,'same-context binding actual byte guard')
   continue
  role=t['role'];check(role in hist and bool(t['input_ids']),'native decode caller IDs')
  histogram(t['physical_width_hist'],t['successful_micrographs'],t['occupied_rows'])
  check(t['occupied_rows']==len(t['input_ids']),'caller occupied rows conserved')
  check(t['kv_min']==0 and t['kv_max']==t['pos']+len(t['input_ids'])-1,'natural decode KV positions')
  check(t['GPU_completed_stage_wall'] is None,'graph counters not GPU wall')
  count[role]+=t['successful_micrographs'];rows[role]+=t['occupied_rows'];hist[role].update(t['physical_width_hist'])
  if t['phase']=='VERIFY':
   check(role=='TARGET' and len(t['input_ids'])==2 and t['ub']==1,'k1 target verify caller2 UB1')
   check(t['physical_width_hist']=={'1':2} and t['successful_micrographs']==2,'verify caller2 actually two width1 graphs')
  elif t['phase']!='PREFILL':check(len(t['input_ids'])==1 and t['physical_width_hist']=={'1':1},'ordinary/draft continuation width1')
 for role in hist:
  p=role.lower();w=x['workload']
  check(count[role]==w[p+'_micrographs'] and rows[role]==w[p+'_micrograph_rows'] and dict(hist[role])==w[p+'_physical_width_hist'],'actual trace-summary crosscheck')
 if x['actual_condition']['maximum_k']==1:
  check(sum(t['phase']=='VERIFY' for t in e['target'])==x['workload']['verify_cycles'],'all cycles witnessed')
 return sum(t['phase']=='VERIFY' for t in e['target'])
def cyclecheck(e,x):
 w=x['workload'];vs=e['verify'];check(len(vs)==w['verify_cycles'],'all captured verification cycles')
 if not x['actual_condition']['maximum_k']:
  check(not vs,'target-only no speculative cycle');return
 sequence=[x['ids'][0]];accepted=0;corrections=0;bonus=0;ah=collections.Counter();ph=collections.Counter()
 traces=[t for t in e['target'] if t['phase']=='VERIFY']
 for v,t in zip(vs,traces,strict=True):
  batch=v['batch_ids'];ds=v['decisions'];check(batch==t['input_ids'] and len(batch)==2 and batch[0]==sequence[-1],'actual naturally pending verify seed')
  n=int(ds[0]==batch[1]);check(v['accepted']==n and len(ds) in (1,2),'actual acceptance decision')
  check(v['target_ub']==1 and v['keep_pos']==t['pos']+1+n,'actual trim to consumed/accepted positions')
  check(len(ds)==1 or n==1,'bonus follows accepted proposal')
  accepted+=n;corrections+=1-n;bonus+=len(ds)-1;ah[str(n)]+=1;ph[str(len(ds))]+=1;sequence+=ds
 check(sequence==x['ids'],'all complete output IDs rederived from native cycle decisions')
 check((accepted,corrections,bonus)==(w['accepted_committed'],w['correction_committed'],w['bonus_committed']),'commit acceptance/correction/bonus counter conservation')
 check(dict(ah)==w['accepted_prefix_hist'] and dict(ph)==w['cycle_progress_hist'],'actual prefix acceptance/progress histograms')
 check(w['verification_seed_rows']==len(vs) and w['target_verification_rows']==2*len(vs),'logical verify seed/proposal rows')
 check(w['draft_proposal_rows']==w['draft_catchup_rows']==len(vs),'actual proposal/catch-up work both paid')
 check(w['rollback_calls']==len(vs) and w['kv_trim_calls']==3*len(vs),'both context trim plus draft pre-cycle trim')
 check(x['proposed']==w['proposal_generated']==w['proposal_verified'] and x['accepted']==accepted,'legacy and new native acceptance agree')

def boundarycheck(x,c,sham):
 p=x['phase96'];check(p['requested_boundary_indices']==c['boundary_cuts'],'prospective cuts')
 check(p['GPU_completed_stage_wall'] is None,'no completed phase price')
 boundaries=p['boundaries'];heavy=x['observation_mode']=='heavy'
 check(p['diagnostic_capture']==heavy and p['own_bind_sham']==sham,'capture/sham mode')
 check([b['output_index_zero_based'] for b in boundaries]==([i for i in c['boundary_cuts'] if i<len(x['ids'])] if heavy else []),'all natural pre-registered boundaries')
 for b in boundaries:
  i=b['output_index_zero_based'];check(b['naturally_committed_prefix_ids']==x['ids'][:i] and b['sampled_top1_id']==x['ids'][i],'natural prefix and current sampled endpoint')
  check(b['top2_id']!=b['sampled_top1_id'] and 0<=b['top2_id']<128256,'actual top2 distinct')
  l1,l2=b['top1_logit'],b['top2_logit'];check(math.isfinite(l1) and math.isfinite(l2) and l1>=l2 and math.isclose(l1-l2,b['top2_margin'],abs_tol=1e-7),'finite native greedy top2 margin')
  for k in ['full_logits_sha256','full_context_sha256','sequence_KV_sha256']:check(re.fullmatch('[0-9a-f]{64}',b[k]) is not None,'live-native serialized/hash witness format')
  check(b['full_context_serialized_bytes']>0 and b['sequence_KV_serialized_bytes']>0 and b['same_owned_target_context'],'native state has nonempty serialization')
  check(b['actual_current_ub']==x['actual_condition']['continuation_ub'] and b['output_capacity']==x['actual_condition']['output_capacity'],'current continuation recipe')
  check(not i or b['last_consumed_input_ids'],'native consumed IDs retained')
  s=b['own_path_binding_sham']
  if sham:
   check(s['status']=='PASS_SAME_CONTEXT_BINDING_NOOP_NOT_RESTORE' and s['ub_before']==s['ub_after']==b['actual_current_ub'],'same owned binding no-op')
   check(s['full_context_bytes_equal'] and s['sequence_KV_bytes_equal'] and not s['future_tokens_forced'] and not s['state_clone_or_restore_performed'],'no invalid donor clone claim')
  else:check(s is None,'no hidden sham')
 check(p['own_bind_sham_calls']==(len(boundaries) if sham else 0),'exact own-binding sham count')
 return boundaries
def baseline(R):
 B=R/'baseline/pr92_restore';M=read(R/'baseline/pr92_manifest.json')
 check(sha(R/'baseline/pr92_manifest.json')=='9980272eb9490eccc137da47480f279af24ab37f0a6e21138006c658bc0ece27','immutable PR92 manifest')
 check(len(M['files'])==7379,'full inherited logical archive')
 for f in M['files']:
  p=B/f['path'];check(p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],'immutable inherited bytes '+f['path'])
 rs=read(B/'FORMAL_RECORDS.json');check(len(rs)==1200,'no old formal rerun')
 grid={};natives={};counter=sha(B/'COUNTER_SEMANTICS.json')
 for r in rs:
  k=(r['task'],r['session'],r['round'],r['condition']);check(k not in grid,'old unique coordinate')
  check(r['phase']=='formal' and r['status']=='COMPLETED' and not r['warmup'] and r['measurement_mode']=='counts','inherited paid counts scope')
  check(r['observation']=={'phase_timers':False,'heavy_capture':False,'etw':False,'added_sync':False},'immutable uninstrumented price channel')
  p=B/r['raw_path'].replace('\\','/');check(sha(p)==r['raw_evidence_sha256'],'old raw exact bytes')
  x=read(p);check(x['pid']==r['worker_pid'] and x['prompt_ids'],'old owned raw PID/prompt')
  endpoint(x);workload(x,counter)
  o=r['output'];check((o['ids'],o['eog_flags'],o['length'],o['terminal_id'],o['stop_reason'])==(x['ids'],x['eog'],x['length'],x['terminal_id'],x['stop_reason']),'old normalized output complete')
  check(o['cached_tokens']==0 and o['truncated'] is False and r['workload']==x['workload'],'old output cache and native work')
  check(math.isfinite(r['wall_ms']) and r['wall_ms']>0,'old paid whole-request fee')
  grid[k]=r;natives[k]=x
 tasks=sorted({r['task'] for r in rs});arms=['R_stock','R_prod','M_match','N_k1','C_k1']
 check(set(grid)==set(itertools.product(tasks,range(2),range(5),arms)) and len(tasks)==24,'old full 24x2x5x5 grid')
 pinned=read(R/'baseline/audit93_rederived/PAIRWISE_AUDIT.json');pairs=[]
 for left,right in itertools.combinations(arms,2):
  matched=sum(endpoint(natives[(t,s,j,left)])==endpoint(natives[(t,s,j,right)]) for t,s,j in itertools.product(tasks,range(2),range(5)))
  effects=[]
  for t in tasks:
   session=[statistics.median(grid[(t,s,j,left)]['wall_ms'] for j in range(5))/statistics.median(grid[(t,s,j,right)]['wall_ms'] for j in range(5)) for s in range(2)]
   effects.append(dict(task=t,ratio=math.exp(statistics.mean(math.log(v) for v in session)),session_ratios=session))
  ratio=math.exp(statistics.mean(math.log(e['ratio']) for e in effects))
  pp=next(p for p in pinned['pairs'] if p['pair']==left+'/'+right)
  check(matched==pp['matched_requests'] and math.isclose(ratio,pp['diagnostic_cost_ratio'],rel_tol=1e-14),'independent historical pairwise and fee arithmetic')
  if (left,right) in [('R_prod','C_k1'),('M_match','C_k1'),('R_prod','M_match')]:
   check(matched==240 and all(e['ratio']<1 for e in effects),'complete same-output negative request costs')
   pairs.append(dict(pair=left+'/'+right,complete_pairwise_equal=True,matched_requests=matched,tasks=24,left_fee_over_right_fee=ratio,right_cost_increase_pct=(1/ratio-1)*100,negative_tasks=24,domain_ratios={d:math.exp(statistics.mean(math.log(e['ratio']) for e in effects if e['task'].startswith(d+'/'))) for d in ['MBPP','GSM8K']},task_effects=effects,scope='immutable PR92 counts whole requests, audited posthoc; not requalified against R_stock'))
 for arm in arms:
  check(all(len({endpoint(natives[(t,s,j,arm)]) for s,j in itertools.product(range(2),range(5))})==1 for t in tasks),'all inherited arms full-output stable')
 for task in tasks:
  check(len({tuple(natives[(task,s,j,arm)]['prompt_ids']) for s,j,arm in itertools.product(range(2),range(5),arms)})==1,'same immutable prompt IDs across old pair arms')
 old=read(B/'RESULTS.json')['families']['Llama'];qual=old['qualification']
 for a,n in [('R_prod',20),('M_match',20),('C_k1',20),('N_k1',80)]:
  check(not qual[a]['native_qualified'] and not qual[a]['request_cost_qualified'] and not qual[a]['qualified'] and len(qual[a]['mismatches'])==n,'original R_stock qualification failure preserved')
 for p in old['comparisons']:check(p['request_qualified_ratio'] is None and p['qualified_ratio'] is None,'original null qualified ratios retained')
 paid_work=[]
 for domain,arm in itertools.product(['MBPP','GSM8K'],arms):
  group=[x for (t,s,j,a),x in natives.items() if a==arm and t.startswith(domain+'/')]
  keys=['output_ids_count','proposal_verified','accepted_committed','draft_continuation_rows','target_verification_rows','target_ordinary_rows','target_micrographs','verify_cycles']
  totals={k:sum(x['workload'][k] for x in group) for k in keys}
  widths=sorted({int(k) for x in group for k in x['workload']['target_continuation_physical_width_hist']})
  original=next(w for w in pinned['work_summary'] if w['domain']==domain and w['arm']==arm)
  check(totals==original['totals'] and widths==original['physical_continuation_widths'],'independent entire paid-population work counters')
  acceptance=totals['accepted_committed']/totals['proposal_verified'] if totals['proposal_verified'] else None
  check(acceptance==original['acceptance'],'actual verified-proposal acceptance denominator')
  check(len(group)==120,'paid domain request denominator')
  paid_work.append(dict(domain=domain,arm=arm,requests=120,totals=totals,acceptance=acceptance,cap_requests=sum(x['stop_reason']=='CAP' for x in group),physical_continuation_widths=widths,denominator='full output IDs including EOG; all CAP cases retained'))
 return pairs,natives,dict(inherited_paid_work=paid_work,original_results_sha256=sha(B/'RESULTS.json'),original_results=read(B/'RESULTS.json'),scope='Original PR92 record unchanged. New pairwise output equality is a separate posthoc production-path claim.')
def source_proof(R,A):
 import zipfile
 old=read(R/'versions/pre-forward-log-amendment/F0A_AUTHENTICATED.json')
 p=R/'receipts/F0A_AUTHENTICATED_SOURCE.zip'
 check(sha(p)==old['archive_sha256'],'actual pre-forward GitHub source archive retained byte-for-byte')
 with zipfile.ZipFile(p) as z:
  mb=z.read('MANIFEST.json');m=json.loads(mb)
  mm=next(x for x in old['remote_files'] if x['path']=='F0A_MANIFEST.json')
  check(hashlib.sha256(mb).hexdigest()==mm['sha256'] and len(m['files'])==306,'authenticated prospective source manifest')
  check(set(z.namelist())=={'MANIFEST.json'}|{'objects/'+x['sha256'] for x in m['files']},'complete source capsule objects')
  for f in m['files']:
   b=z.read('objects/'+f['sha256']);check(len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],'source capsule byte hash')
   path=f['path'];changed={'F0A.json':'versions/pre-forward-log-amendment/F0A.json','code/common96.py':'versions/pre-forward-log-amendment/common96.py','code/controller96.py':'versions/pre-forward-log-amendment/controller96.py'}
   check((R/changed.get(path,path)).read_bytes()==b,'original frozen source version preserved '+path)
 for x in A['amendment_remote_files']:
  path={'source/common96.py':'code/common96.py','source/controller96.py':'code/controller96.py'}.get(x['path'],x['path'])
  check((R/path).stat().st_size==x['bytes'] and sha(R/path)==x['sha256'],'authenticated source amendment actual byte binding '+path)

def run(R,out,rehash_models=True):
 P=read(R/'PLAN.json');F=read(R/'F0A.json');A=read(R/'F0A_AUTHENTICATED.json');I={c['id']:c for c in read(R/'INPUTS.json')['cases']}
 source_proof(R,A)
 am=read(R/'REMAINING_EXECUTION.json');ra=read(R/'REMAINING_AUTHENTICATED.json')
 check(ra['status']=='PASS_ACTUAL_AUTHENTICATED_GITHUB_BYTES' and ra['before_remaining_forward'] and ra['commit']=='b81e1b1835e3db7ee8ef0cb9ad63503116c9a816' and ra['amendment_sha256']==sha(R/'REMAINING_EXECUTION.json') and am['helper_sha256']==sha(R/'code/continue_unstarted96.py'),'unstarted-only orchestration separately sealed/authenticated before fresh trials')
 check(len(am['remaining_slots'])==23 and am['failed_slot_replay'] is False and am['numeric_actor_changed'] is False and am['original_plan_changed'] is False,'remaining starts preserve original actor/plan/no replay')
 for a,b in [('source/continue_unstarted96.py','code/continue_unstarted96.py'),('REMAINING_EXECUTION.json','REMAINING_EXECUTION.json'),('FAILED_REQUESTS.json','FAILED_REQUESTS.json')]:
  check((R/'receipts/remaining_auth_bytes'/a).read_bytes()==(R/b).read_bytes(),'actual authenticated remaining source bytes preserved')
 check(A['status']=='PASS_ACTUAL_AUTHENTICATED_GITHUB_BYTES' and A['before_new_forward'] and A['commit']=='f0d4df7aa98b342ccecc5c7b60f14799be085af2','prospective amended remote source proof')
 check(hashlib.sha256(canonical(P).encode()).hexdigest()==F['plan_sha256'] and sha(R/'INPUTS.json')==F['inputs_file_sha256'],'frozen plan and input bytes')
 check(P['factorial_status']=='PHASE_FACTOR_NOT_ISOLATABLE' and P['fork_status']=='FORK_NOT_IMPLEMENTABLE','source-admitted causal scope')
 for f in F['runtime_files']:check(sha(R/f['path'])==f['sha256'],'actual frozen runtime bytes '+f['path'])
 if rehash_models:
  for m in F['assets']['models']:
   p=pathlib.Path(m['path']);check(p.stat().st_size==m['bytes'] and sha(p)==m['sha256'],'full external GGUF hash '+m['role'])
 rs=read(R/'STUDY_RECORDS.json');failures=read(R/'FAILED_REQUESTS.json');check(len(rs)==107 and [f['slot'] for f in failures]==['P2/s0/C512|GSM8K/test/1248'],'one original failed diagnostic slot, no replay');expected=coordinates(rs,P,failures);ledger=[json.loads(l) for l in (R/'LEDGER.jsonl').read_text().splitlines()]
 started=[r['slot'] for r in ledger if r['event']=='REQUEST_STARTED'];done=[r['slot'] for r in ledger if r['event']=='REQUEST_COMPLETED']
 failed_events=[z['slot'] for z in ledger if z['event']=='REQUEST_FAILED']
 check(len(started)==len(set(started))==108 and len(done)==107 and failed_events==[f['slot'] for f in failures] and set(done).isdisjoint(failed_events) and set(started)==set(done)|set(failed_events)==set(expected),'all starts charged once and closed complete or failed')
 check(collections.Counter(r['kind'] for r in ledger if r['event']=='REQUEST_STARTED')=={'P1':72,'P2':36},'P1/P2 exact budgets')
 probes=[r['slot'] for r in ledger if r['event']=='PROBE_STARTED'];check(probes==['p0_probe_O128','p0_probe_C512'],'old completed probe not replayed')
 workers=[r for r in ledger if r['event']=='WORKER_STARTED'];closes=[r for r in ledger if r['event']=='WORKER_CLOSED'];check(len(workers)==len(closes)==21,'actual 21 owned worker lifetimes')
 check(len({r['block'] for r in workers})==21 and len({r['block'] for r in closes})==21,'unique closed lifetimes')
 charged=collections.Counter()
 for z in ledger:
  if z['event'] in ['REQUEST_STARTED','PROBE_STARTED']:
   check(z['counts_before']==dict(charged),'every start charged prospectively before execution');charged[z['kind']]+=1
 check(sum(charged.values())==110,'total charged lower bound')
 owned=0;headrooms=[];module_pins={pathlib.PurePosixPath(f['path']).name:f['sha256'] for f in F['runtime_files'] if f['path'].startswith('build/Release/')}
 for w in workers:
  d=R/'raw'/w['block'];life=read(d/'LIFECYCLE.json');ident=read(d/'IDENTITY.json');failed_worker=w['block']=='p2_s0_p2_C512_dispatch'
  check((life['returncode']==1 and life['failed']) if failed_worker else (life['returncode']==0 and not life['failed']),'owned native lifecycle includes declared observer failure')
  if failed_worker:
   watch=read(d/'WATCHDOG_STOP.json');check(watch['only_owned_pid']==life['pid']==24252 and watch['api_bytes']>P['limits']['api_dump_bytes'],'only owned API observer stop threshold triggered')
  check(ident['owned_pid']==life['pid'] and ident['physical_residency']=='UNKNOWN','owned identity scoped to physical UNKNOWN')
  headrooms+=memory(ident['memory'],life['pid']);owned+=life['owned_seconds']
  for m in ident['modules']:
   name=pathlib.PureWindowsPath(m['path']).name
   if name in module_pins:check(m['sha256']==module_pins[name],'actual loaded native DLL/exe pin')
   elif m.get('scope')=='optional_instrumentation':
    check(m['sha256']==read(R/'VULKAN_OBSERVABILITY.json')['layer_sha256'],'loaded SDK API layer pin')
  required={'b570-boundary-worker.exe','llama-b570-memory.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll'}
  check(required<={pathlib.PureWindowsPath(m['path']).name for m in ident['modules']},'all six actual loaded actor/numeric module pins')
  check(len(ident['modules']) in (6,7),'all numeric modules inventoried')
  native=[json.loads(z) for z in (d/'stdout.jsonl').read_text(encoding='utf-8-sig').splitlines()]
  ready=[z for z in native if z['event']=='READY'];check(len(ready)==1 and ready[0]['forward_calls']==0 and ready[0]['pid']==life['pid'],'actual initial native zero-forward readiness')
  results=[z for z in native if z['event']=='RESULT'];persisted=[z for z in native if z['event']=='PERSISTED']
  expected_records=[z for z in rs if pathlib.PurePosixPath(z['raw_path']).parts[1]==w['block']]
  check(len(results)==len(persisted)==len(expected_records),'no hidden native warmups/request results')
  for z in expected_records:
   xx=read(R/z['raw_path']);check(xx in results and xx['request_id']==hashlib.sha256(z['slot'].encode()).hexdigest()[:32],'actual FIFO native RESULT and frozen request ID')
  if len(ident['contexts'])==2:
   vocab=[z for z in native if z['event']=='VOCAB_GUARD'];check(len(vocab)==1 and vocab[0]['status']=='PASS' and vocab[0]['full_rows']==128256 and vocab[0]['runtime_eog_equal'] and vocab[0]['load_forward_calls']==0,'actual complete native vocab/EOG guard')
  check(all(a['load_forward_calls']==0 and a['numeric_path']=='Vulkan0_F16_KV_FAoff' for a in ident['contexts']),'fixed native numeric recipe')
  check(len(ident['kv_lines'])==len(ident['contexts']) and all('Vulkan0' in l for l in ident['kv_lines']),'native GPU KV placement')
  check(all(a['all_weights_Vulkan0'] and all(t['backend_device']=='Vulkan0' and t['gpu_backend_buffer'] for t in a['tensors']) for a in ident['weight_maps']),'actual Vulkan tensor placement; not residency proof')
  if w['block'] in probes:
   q=read(d/'PROBE_COMPLETE.json');check(q['forward_calls']==q['target_graphs']==q['draft_graphs']==0,'zero-forward load probe')
 check(owned<18000,'bounded owned GPU time')
 completion=read(R/'STUDY_COMPLETION.json');check(completion['status']=='CLOSED_WITH_FAILED_DIAGNOSTIC' and completion['requests_completed']==107 and completion['requests_failed']==1 and completion['failed_slots']==failed_events and not completion['unexecuted_slots'] and completion['retries']==completion['warmups']==completion['fork_forwards']==0,'complete no replay/warmup/fork execution')
 check(math.isclose(owned,completion['owned_gpu_seconds'],abs_tol=1e-6),'actual owned time ledger')
 oldpairs,oldraw,qualification=baseline(R)
 serialization=read(R/'SOURCE_SERIALIZATION_SCOPE.json');check(sha(R/serialization['source'])==serialization['source_sha256'],'actual serialized-state source contract')
 state_reason='Actual state_write_data serializes model architecture plus memory module, sequence state serializes memory only. Logits are separately hash-captured; dynamic output/logit buffers, frontend pending, sampler ownership and scheduler/reservation are not restored by these APIs. Current actor lacks a validated full retained-state fork.'
 raw={};cuts=[];witness=[];allshams=[];counter=sha(R/'COUNTER_SEMANTICS.json')
 for r in rs:
  check(r['source_commit']==A['commit'] and r['status']=='COMPLETED','prospective request source')
  for key,hkey in [('raw_path','raw_sha256'),('evidence_path','evidence_sha256'),('identity_path','identity_sha256')]:check(sha(R/r[key])==r[hkey],'record actual evidence hash')
  x=read(R/r['raw_path']);c=I[r['task']];check(x['prompt_ids']==c['prompt_ids'] and x['pid']==r['owned_pid'],'fixed native prompt and owned PID');endpoint(x);workload(x,counter)
  cfg=P['arms'][r['arm']];a=x['actual_condition']
  check((a['prefill_ub'],a['continuation_ub'],a['output_capacity'],a['maximum_k'])==(cfg['ub'],cfg['continuation_ub'],cfg['capacity'],int(cfg['spec'])),'actual frozen recipe')
  check(a['logical_batch']==512 and a['n_ctx']==1024 and a['threads']==10 and a['kv']=='F16' and not a['flash_attention'],'no numeric recipe exploration')
  e=read(R/r['evidence_path']);mem=e['memory'] if r['observation_mode']=='heavy' else e;check(not mem['violation'],'same request native memory gate')
  headrooms+=memory(mem['samples'],x['pid'])
  if r['observation_mode']=='heavy':cycles=tracecheck(e,x);cyclecheck(e,x)
  else:cycles=0
  b=boundarycheck(x,c,r['own_bind_sham'])
  for cut in b:
   cuts.append(dict(slot=r['slot'],task=r['task'],arm=r['arm'],repeat=r['repeat'],**cut))
   if cut['own_path_binding_sham']:allshams.append(dict(slot=r['slot'],output_index=cut['output_index_zero_based'],guard=cut['own_path_binding_sham']))
  raw[r['slot']]=x
  if r['phase']=='P2':
   w=x['workload'];witness.append(dict(slot=r['slot'],task=r['task'],domain=r['task'].split('/')[0],arm=r['arm'],session=r['repeat'],output_ids=len(x['ids']),stop_reason=x['stop_reason'],verified_cycles=cycles,workload=w,scope='native successful process_ubatch graph/occupied-row counters; not kernel count or completed GPU timing'))
 # Capture-off, capture-on, own binding no-op repeat guards: full native endpoint.
 guards=[]
 for task,arm in itertools.product(I,['O128','O512','B128','B512']):
  xx=[raw[f'P1/r{r}/{arm}|{task}'] for r in range(3)]
  stable=observer_equal(xx)
  check(stable,'observer or own-binding full-output drift; causal interpretation blocked')
  guards.append(dict(task=task,arm=arm,capture_off_on_and_own_binding_equal=True))
 comparisons=[];mapping={'O128':'R_stock','O512':'R_prod','B512':'M_match','C512':'C_k1'}
 for task in I:
  for arm in ['O128','O512','B128','B512']:
   x=raw[f'P1/r0/{arm}|{task}'];base=oldraw[(task,0,0,mapping[arm])] if arm in mapping else None
   if base:check(endpoint(x)==endpoint(base),'new own-path endpoint reproduces pinned old reference')
  for left,right in itertools.combinations(['O128','O512','B128','B512'],2):
   x,y=[raw[f'P1/r0/{a}|{task}'] for a in [left,right]]
   diff=difference(x['ids'],y['ids']);comparisons.append(dict(task=task,left=left,right=right,complete_output_equal=endpoint(x)==endpoint(y),first_difference=diff,causal_scope='whole frozen recipe comparison; not isolated prefill/continuation UB causality'))
 for r in rs:
  if r['phase']=='P2':
   x=raw[r['slot']];check(endpoint(x)==endpoint(oldraw[(r['task'],0,0,mapping[r['arm']])]),'new P2 own path reproduces complete old output')
 # Boundary comparisons only state whether natural committed prefixes are equal.
 boundary_pairs=[]
 for task in I:
  for left,right in itertools.combinations(['O128','O512','B128','B512'],2):
   a=raw[f'P1/r1/{left}|{task}']['phase96']['boundaries'];b=raw[f'P1/r1/{right}|{task}']['phase96']['boundaries']
   for x,y in zip(a,b,strict=True):
    boundary_pairs.append(dict(task=task,left=left,right=right,index=x['output_index_zero_based'],natural_prefix_equal=x['naturally_committed_prefix_ids']==y['naturally_committed_prefix_ids'],top1_left=x['sampled_top1_id'],top1_right=y['sampled_top1_id'],top2_left=x['top2_id'],top2_right=y['top2_id'],margin_left=x['top2_margin'],margin_right=y['top2_margin'],full_logits_hash_equal=x['full_logits_sha256']==y['full_logits_sha256'],sequence_KV_hash_equal=x['sequence_KV_sha256']==y['sequence_KV_sha256'],scope='live-native top2 and vector/state hashes only; serialized tensors not retained for offline byte recheck'))
 aggregates=[]
 keys=['output_ids_count','proposal_verified','accepted_committed','draft_continuation_rows','draft_proposal_rows','draft_catchup_rows','target_verification_rows','target_ordinary_rows','target_micrographs','target_micrograph_rows','verify_cycles']
 for domain,arm in itertools.product(['GSM8K','MBPP'],['O512','B512','C512']):
  ws=[w for w in witness if w['domain']==domain and w['arm']==arm];tot={k:sum(w['workload'][k] for w in ws) for k in keys};n=tot['output_ids_count']
  aggregates.append(dict(domain=domain,arm=arm,requests=len(ws),totals=tot,acceptance=tot['accepted_committed']/tot['proposal_verified'] if tot['proposal_verified'] else None,per_output={k:v/n for k,v in tot.items() if k!='output_ids_count'},physical_continuation_widths=sorted({int(k) for w in ws for k in w['workload']['target_continuation_physical_width_hist']}),denominator='complete native output IDs including EOG and CAP'))
 dispatch_blocks=[b for b in P['blocks'] if b.get('api_dump')];check(len(dispatch_blocks)==1 and len(dispatch_blocks[0]['slots'])==1,'prospective bounded dispatch witness')
 dd=R/'raw'/dispatch_blocks[0]['name'];ident=read(dd/'IDENTITY.json');p=dd/'vulkan-api.txt'
 check(ident['api_layer_loaded'] and p.stat().st_size==failures[0]['api_actual_final_bytes'] and p.stat().st_size>P['limits']['api_dump_bytes'],'actual incomplete API trace and sampled stop overshoot preserved')
 check(failures[0]['output_ids'] is None and failures[0]['whole_request_endpoint'] is None and failures[0]['completed_native_counters'] is None,'failed scope has no fabricated output/work endpoint')
 native_failure=read(R/failures[0]['raw_failure_path']);check(native_failure['slot']==failures[0]['slot'],'failed raw slot provenance')
 text=p.read_text(encoding='utf-8',errors='replace')
 dispatch_count=len(re.findall(r'vkCmdDispatch\s*\(',text));groups=re.findall(r'groupCount[XYZ].*?=\s*(\d+)',text)
 check(dispatch_count>0 and bool(groups),'actual CPU Vulkan API dispatch/group metadata')
 dispatch=dict(status='PARTIAL_FAILED_OBSERVER_SCOPE',failed_slot=failures[0]['slot'],no_complete_native_endpoint=True,stop_threshold_bytes=P['limits']['api_dump_bytes'],watchdog_sampled_bytes=read(dd/'WATCHDOG_STOP.json')['api_bytes'],overshoot_scope='0.5s sampled watcher stop threshold, not a hard byte-size cap',path=str(p.relative_to(R)).replace('\\','/'),sha256=sha(p),bytes=p.stat().st_size,vkCmdDispatch_calls=dispatch_count,group_count_metadata_values=len(groups),completed_GPU_stage_wall=None,scope='native vkCmdDispatch API recording metadata only, not physical completed kernel timing or GPU residency proof')
 phase=dict(status='WHOLE_RECIPE_DIAGNOSTICS_COMPLETE',clean_2x2_admission='PHASE_FACTOR_NOT_ISOLATABLE',cuts=cuts,comparisons=comparisons,boundary_pairs=boundary_pairs,capture_and_own_binding_guards=guards,full_vectors_retained=False,no_future_tokens_forced=True,causal_claim='UNRESOLVED: occupied target-only continuation is width1 for every arm; capacity, synchronization and scheduler reservation are coupled')
 shams=dict(status='FORK_NOT_IMPLEMENTABLE',donor_crosses=0,own_binding_shams=allshams,own_binding_guard_calls=len(allshams),clone_restore_shams=0,reason=state_reason,source_serialization_scope=serialization,scope='Same-owned same-UB binding no-op guards are not state clone/restore or donor-state causal evidence.')
 work=dict(source_sync_inventory=dict(binding='Private ABI always synchronize(); changed UB sets sched_need_reserve and sched_reserve',wrapper_inherited_explicit_sync_counter='Reset/final direct wrapper syncs only; does not enumerate internal binding/sampler waits',binding_calls='phase_binding_calls records post-prefill bind; own no-op calls separate in phase96; reset/workspace binds preserved in source',observer='Heavy per-decode synchronize, periodic/checkpoint memory, full state/logit readbacks and own no-op guards; all new latency diagnostic only'),status='SUPPORTED_NATIVE_WORK_GEOMETRY',witnesses=witness,aggregates=aggregates,dispatch=dispatch,physical_residency='UNKNOWN',completed_GPU_stage_wall=None,model_status='MODEL_TIMING_UNAVAILABLE',scope='successful native micrographs, occupied rows, caller IDs, proposal and catch-up; no graph-to-kernel/completion-price conflation')
 qualification.update(stock_ref_qualified=False,stock_gate_scope='R_prod/M_match/C_k1 against registered R_stock; original entire arm qualification retained',posthoc_pairwise_output_equal={p['pair']:p['complete_pairwise_equal'] for p in oldpairs},physical_residency_qualified=False,physical_residency='UNKNOWN',new_diagnostic_request_cost_qualified=False,new_diagnostics=dict(requests_started=108,requests_completed=107,requests_failed=1,qualified_formal_cost=False,reason='exposed capture diagnostics only; immutable paid counts source retained'),posthoc_production_pairwise=oldpairs)
 result=dict(schema='heterospec.b570.phasebinding.result.v1',design_head=F['design_head'],source_commit=A['commit'],parents={'PR92':F['parent92'],'PR93':F['parent93']},questions={
 'prefill_recipe_causality':{'status':'UNRESOLVED','reason':phase['causal_claim']},
 'state_continuation_interaction':{'status':'UNRESOLVED','reason':state_reason},
 'physical_geometry_explanation':{'status':'SUPPORTED','scope':'C512 native verify caller2 decomposes into two successful occupied width1 graphs; plus separately counted draft proposal/catchup. Does not quantify fraction of request cost.'},
 'same_output_negative_request_cost':{'status':'SUPPORTED','scope':'PR92/93 full same-output R_prod/M_match/C_k1, 240 pair requests and 24 tasks; original R_stock failures remain.'}},
 execution=dict(requests_started=108,requests_completed=107,requests_failed=1,P1=72,P2=35,P2_planned=36,failed_slots=failed_events,unexecuted_slots=[],zero_forward_load_probes=2,charged_units=110,retries=0,warmups=0,donor_forks=0,owned_native_workers=21,owned_gpu_seconds=owned,minimum_sampled_owned_dedicated_headroom_bytes=min(headrooms),api_dump_budget='FAILED_SAMPLED_STOP_THRESHOLD_WITH_OVERSHOOT',api_dump_final_bytes=171281419,api_dump_threshold_bytes=134217728,sampling_scope='native checkpoints plus engineering periodic/per-decode samples; not continuous residence'),
 original_R_stock_qualified_ratio=None,physical_residency='UNKNOWN',model_status='MODEL_TIMING_UNAVAILABLE',new_formal_cost_ratios=None,paid_posthoc_pairs=oldpairs,inherited_paid_work=qualification['inherited_paid_work'],new_physical_work=aggregates,recipe_comparisons=comparisons,observer_guards=guards,dispatch=dispatch,state_logits_evidence_limit='native finite top2 values and full vector/serialization SHA256 witnesses, source/binary pinned; raw state and FP32 vectors absent, no independent offline tensor rehash',
 failed_requests=failures,failure_preservation=dict(api_dump_failed_threshold=True,api_trace_complete=False,api_sampled_threshold_overshoot_preserved=True,failed_forward_not_replayed=True,pre_forward_log_error=True,completed_O128_probe_not_replayed=True,failed_builds_preserved=True))
 for name,x in [('PHASE_INTERVENTION.json',phase),('FORK_SHAMS.json',shams),('WORK_WITNESSES.json',work),('QUALIFICATION.json',qualification),('RESULTS.json',result)]:write(out/name,x)
 verification=dict(status='PASS_INDEPENDENT_STDLIB',new_native_records=107,failed_native_scopes=1,all_registered_starts_closed=108,inherited_manifest_files=7379,inherited_paid_records=1200,complete_arrays_checked=True,native_trace_counter_conservation=True,no_executor_imported=True,no_new_forward=True,models_rehashed=rehash_models,actor_and_numeric_modules_hashed=True,original_qualification_and_nulls_unchanged=True,prospective_source_authenticated=True,state_logits_hash_evidence='format/provenance checked, payloads not independently rehashed')
 write(out/'INDEPENDENT_VERIFICATION.json',verification)
 return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--output',required=True);a.add_argument('--skip-external-model-rehash',action='store_true');args=a.parse_args()
 r=run(pathlib.Path(args.root),pathlib.Path(args.output),not args.skip_external_model_rehash)
 print(json.dumps(dict(status='PASS_INDEPENDENT_STDLIB',questions={k:v['status'] for k,v in r['questions'].items()},execution=r['execution'])))
