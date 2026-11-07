"""Prospectively sealed mechanical corrections; resumes only untouched formal blocks."""
from common95 import *
from runner95 import Worker95,Ledger95,native,ACTIVE,signature,cooling
import ctypes,traceback,copy,delivery95
CODE=Path(__file__).parent
ORIGINAL_READ=native.read
CURRENT_BUILD=None
USE_V02=True
def native_read(path):
    path=Path(path)
    if path==PUB/'NATIVE_BUILD.json' and CURRENT_BUILD is not None:return CURRENT_BUILD
    if path==LOCAL/'F0A_REMOTE_RECEIPT.json' and USE_V02:return read(LOCAL/'F0A_V02_REMOTE_RECEIPT.json')
    if path==LOCAL/'F0B_REMOTE_RECEIPT.json' and USE_V02:return read(LOCAL/'F0B_V02_REMOTE_RECEIPT.json')
    return ORIGINAL_READ(path)
native.read=native_read

class CorrectedWorker(Worker95):
    def __init__(self,*args):
        super().__init__(*args)
        self.repaired=self.family in ['SmolLM2','Llama'] and self.c['layout']=='PQ'
        if self.repaired:self.cmd[0]=read(PUB/'NATIVE_BUILD_V02.json')['server_path']
    def __enter__(self):
        global CURRENT_BUILD
        CURRENT_BUILD=read(PUB/'NATIVE_BUILD_V02.json') if self.repaired else None
        try:return super().__enter__()
        except BaseException:CURRENT_BUILD=None;raise
    def __exit__(self,*args):
        global CURRENT_BUILD
        try:return super().__exit__(*args)
        finally:CURRENT_BUILD=None

def seal(phase):
    assert phase in ['F0A_V02','F0B_V02']
    # Original hashes and failures are evidence, not rewritten recovery state.
    for oldphase in ['F0A','F0B']:
        for name,h in read(PUB/(oldphase+'.json'))['payload_sha256'].items():assert sha(REPO/name)==h
    paths=[p for root in [PUB,CODE] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    payload={p.relative_to(REPO).as_posix():sha(p) for p in paths}
    save(PUB/(phase+'.json'),dict(utc=now(),phase=phase,design_head=DESIGN_HEAD,payload_sha256=payload,prospective_before_affected_new_forward=True,no_budget_reset=True,ledger_events_at_seal=len(list((LOCAL/'ledger').glob('*.json'))),original_F0A_commit=read(LOCAL/'F0A_REMOTE_RECEIPT.json')['commit'],original_F0B_commit=read(LOCAL/'F0B_REMOTE_RECEIPT.json')['commit'],correction_sha256=sha(PUB/'IMPLEMENTATION_FAULT_CORRECTION.json')))
    paths.append(PUB/(phase+'.json'))
    subprocess.run(['git','add','--sparse','-f','--',*[p.relative_to(REPO).as_posix() for p in paths]],cwd=REPO,check=True)
    subprocess.run(['git','commit','-m','Prospectively seal RTX '+phase+' resource and alias correction'],cwd=REPO,check=True)
    retry(lambda:subprocess.run(['git','push','-u','origin',git('branch','--show-current')],cwd=REPO,check=True),'push-'+phase)
    head=git('rev-parse','HEAD');tree=api('git/trees/'+head+'?recursive=1');assert not tree.get('truncated');items={i['path']:i for i in tree['tree']};checked={}
    for p in paths:
        name=p.relative_to(REPO).as_posix();oid=items[name]['sha'];b=verified_blob(oid);assert hashlib.sha256(b).hexdigest()==sha(p) and len(b)==p.stat().st_size
        checked[name]=dict(sha256=sha(p),bytes=len(b),git_blob=oid)
    receipt=dict(utc=now(),phase=phase,commit=head,actual_authenticated_remote_bytes=True,before_new_forward=True,payload_sha256=payload,readback=checked)
    save(LOCAL/(phase+'_REMOTE_RECEIPT.json'),receipt);save(PUB/(phase+'_REMOTE_READBACK.json'),receipt);status(phase+'_REMOTE_BYTES_VERIFIED',commit=head,files=len(checked))

def old_engineering(family,arm):
    rows=[read(p) for p in (LOCAL/'runs/engineering'/family/arm).rglob('RECORD.json')]
    return {r['task']:r for r in rows if not r['warmup'] and r.get('study_phase')=='P0_engineering'}

def qb_alias_admission(family,arm):
    root=LOCAL/'runs/engineering'/family/arm
    events=[json.loads(b) for b in (root/'trace.jsonl').read_bytes().splitlines()]
    graphs=[g for e in events if e.get('event')=='decode' for g in e.get('graphs',[]) if g['role']=='target']
    nodes=[g for g in graphs if g['name'] in ['hs_attn_query_batch-0','jsa_llama_query_batch-0'] and g['ne'][1]==1 and 1<g['ne'][3]<=4]
    rows=old_engineering(family,arm);ref=old_engineering(family,'R');panel=read(PUB/'P0_PLAN.json')['P2_panel'][family]
    exact=all(t['id'] in rows and t['id'] in ref and rows[t['id']]['input_sha256']==ref[t['id']]['input_sha256']==digest(t) and rows[t['id']]['contract_valid'] and not rows[t['id']]['workload_error'] and signature(rows[t['id']])==signature(ref[t['id']]) for t in panel)
    return dict(admitted=bool(nodes) and exact,actual_nodes=nodes,full_panel_equal=exact,new_gpu_requests=0,reason='Original source cb sets hs_attn_query_batch then jsa_llama_query_batch on the same tensor; final native name is the latter',retained_rows_sha256={p.relative_to(LOCAL).as_posix():sha(p) for p in root.rglob('RECORD.json')})

def qualify_pq(ledger):
    p0=read(PUB/'P0_PLAN.json');out={}
    for family in ['SmolLM2','Llama']:
        for arm in ['M_PQ','C_PQ']:
            c=next(c for c in p0['arms'] if c['name']==arm);key=family+'/'+arm
            status('RESOURCE_CORRECTION_NATIVE_ADMISSION',family=family,arm=arm);cooling('engineering-v02-'+family+'-'+arm)
            try:
                with CorrectedWorker(ledger,family,c,'engineering-repair',arm) as w:
                    # Do not repeat the failed original warm slots. These panel/probe slots were never started.
                    probe=w.complete(p0['P2_panel'][family][0],f'engineering-v02/{family}/{arm}/GRAPH_PROBE',mode='heavy',meta=dict(study_phase='P0_resource_correction_graph',excluded_from_paid=True))
                    rows=[w.complete(t,f'engineering-v02/{family}/{arm}|'+t['id'],meta=dict(study_phase='P0_resource_correction',exposed=True)) for t in p0['P2_panel'][family]]
                events=[json.loads(b) for b in (w.d/'trace.jsonl').read_bytes().splitlines()];nodes=[g for e in events if e.get('event')=='decode' for g in e.get('graphs',[]) if g['role']=='target']
                topology=any(g['name']=='hs_attn_single_query-0' for g in nodes);refs=old_engineering(family,'R')
                equal=topology and all(r['contract_valid'] and not r['workload_error'] and r['input_sha256']==refs[r['task']]['input_sha256'] and signature(r)==signature(refs[r['task']]) for r in rows)
                out[key]=dict(admitted=bool(equal),actual_nodes=nodes,mismatch_tasks=[r['task'] for r in rows if signature(r)!=signature(refs[r['task']])],capture_on_off_full_equal=signature(probe)==signature(rows[0]),resource_only_binary=read(PUB/'NATIVE_BUILD_V02.json')['server_sha256'])
            except (AssertionError,RuntimeError,OSError,TimeoutError) as e:out[key]=dict(admitted=False,error=repr(e),started_not_retried=True,negative_or_blocked_retained=True)
    save(PUB/'RESOURCE_CORRECTION_QUALIFICATION.json',out);return out

def resume_formal(ledger):
    plan=read(PUB/'FORMAL_PLAN_V02.json');p0=read(PUB/'P0_PLAN.json');failures=[];blocked=set()
    for i,b in enumerate(plan['blocks']):
        if not b['admitted']:continue
        family=b['family'];arm=b['condition']['name'];name=f's{b["session"]}-{arm}';slots=b['slots'];started=[s for s in slots if ledger.started(s['slot'])]
        if started:
            assert len(started)==48,'Cannot resume or retry a partly started formal block'
            assert len([read(p) for p in (LOCAL/'runs/formal'/family/name).rglob('RECORD.json') if not read(p)['warmup']])==48
            continue
        if (family,arm) in blocked:continue
        status('P2_FORMAL_V02',block=i+1,blocks=len(plan['blocks']),family=family,arm=arm,completed=sum(e['phase']=='formal' and e['kind']=='request' for e in ledger.events));cooling('formal-v02-'+family+'-'+name)
        by={t['id']:t for t in p0['P2_panel'][family]}
        try:
            with CorrectedWorker(ledger,family,b['condition'],'formal',name) as w:
                w.complete(p0['warmups'][family],f'formal/{family}/{name}/WARM',warmup=True,meta=dict(study_phase='P2',prospective_correction_version='v02'))
                for s in slots:w.complete(by[s['task']],s['slot'],meta=dict(study_phase='P2',session=b['session'],round=s['round'],position=s['position'],exposed=True,prospective_correction_version='v02'))
        except (AssertionError,RuntimeError,OSError,TimeoutError) as e:
            failures.append(dict(family=family,arm=arm,block=i,error=repr(e),started_not_retried=True));blocked.add((family,arm))
            if ledger.owned_now()>=43200-252 or isinstance(e,AssertionError) and not str(e):break
    save(PUB/'FORMAL_FAILURES_V02.json',dict(failures=failures,blocked_arms=[list(k) for k in sorted(blocked)],started_not_retried=True))

def patched_cpu_audit(repo,local,out):
    subprocess.run([str(PYTHON),str(CODE/'audit95_v02.py'),'--repo',str(repo),'--local',str(local),'--out',str(out)],check=True);return read(out)

def corrected_delivery():
    delivery95.cpu_audit=patched_cpu_audit
    original_report=delivery95.report
    delivery95.report=lambda r:original_report(r)+'\n## Preserved implementation faults and prospective correction\n\nSmol/Llama original PQ warm attempts aborted because the graph metadata pool was undersized. They remain in the exact ledger and failure logs and were never retried. V02 increases only the PQ host graph-capacity bound by the predeclared maximum q=4; models, numerical DLLs, arithmetic operators, strides, masks, k3 and caller geometry are unchanged. Every other arm keeps the original executable. The QB admission detector originally missed the final jsa_llama_query_batch alias; correction uses its already captured actual graph and all twelve unchanged native outputs, without GPU reruns. Original F0A/F0B/qualification remain immutable; prospective V02 seals precede affected forwards and formal slots. The 96 complete formal requests before correction are retained once.\n'
    original_archive=delivery95.archive
    def archive_filtered(path,files):
        # All corrected native source/binary bytes and build logs are in the indexed V02 package; exclude disposable build intermediates.
        return original_archive(path,{n:p for n,p in files.items() if not n.startswith('local/native-repair/')})
    delivery95.archive=archive_filtered
    original_restore=delivery95.restore_verify
    def restore(path,target,expected):
        r=original_restore(path,target,expected);r['corrected_source_runtime_files']=delivery95.check_nested(target/'local/SOURCE_RUNTIME_V02.zip');return r
    delivery95.restore_verify=restore
    return delivery95.closeout()

def main():
    with (LOCAL/'controller-v02.lock').open('xb') as lock:
        lock.write(str(os.getpid()).encode());lock.flush();ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
        try:
            assert (PUB/'NATIVE_BUILD_V02.json').exists() and not (LOCAL/'RESULT_PR.json').exists()
            ledger=Ledger95();assert sum(e['phase']=='formal' and e['kind']=='request' for e in ledger.events)==96
            before_slots={e['slot'] for e in ledger.events};save(PUB/'IMPLEMENTATION_FAULT_CORRECTION.json',dict(utc=now(),formal_retained=96,formal_already_started_slots=sorted(e['slot'] for e in ledger.events if e['phase']=='formal'),diagnostic_paid_at_correction=sum(e['phase']!='formal' and e['kind'] in ['request','warmup'] for e in ledger.events),max_new_diagnostic_requests=52,no_old_warm_or_formal_retry=True,original_parameters_panel_and_2016_slot_coordinates_unchanged=True,resource_fix=read(PUB/'RESOURCE_CORRECTION.json'),QB_alias_gate='Accept either actual compiled native alias with ne=(d,1,h,q),1<q<=4 and the already captured full12-output equality; no timing consultation',prior_formal_timing_not_consulted=True,new_path_admission='Fixed resource-only correction; first13 previously unstarted diagnostic requests/arm, full12 output equality and actual PQ topology, independent final qualification'))
            aliases={f+'/'+a:qb_alias_admission(f,a) for f in ['SmolLM2','Llama'] for a in ['M_QB','C_QB']};save(PUB/'QB_ALIAS_CORRECTION.json',aliases)
            seal('F0A_V02');pq=qualify_pq(ledger)
            plan=copy.deepcopy(read(PUB/'FORMAL_PLAN.json'))
            for b in plan['blocks']:
                k=b['family']+'/'+b['condition']['name']
                if k in aliases:b['admitted']=aliases[k]['admitted']
                if k in pq:b['admitted']=pq[k]['admitted']
            plan['admitted_slots']=sum(len(b['slots']) for b in plan['blocks'] if b['admitted']);plan['correction']='v02 metadata capacity and final tensor name alias; original payload untouched; previously started complete blocks skipped';plan['original_plan_sha256']=sha(PUB/'FORMAL_PLAN.json')
            assert all(a['slots']==b['slots'] and a['condition']==b['condition'] for a,b in zip(plan['blocks'],read(PUB/'FORMAL_PLAN.json')['blocks']))
            save(PUB/'FORMAL_PLAN_V02.json',plan);seal('F0B_V02');resume_formal(ledger);corrected_delivery()
        except BaseException as e:
            fail=LOCAL/('CORRECTION_CONTROLLER_FAILURE-'+str(time.time_ns())+'.json');save(fail,dict(utc=now(),error=repr(e),traceback=traceback.format_exc(),no_automatic_started_slot_retry=True));status('CORRECTION_CONTROLLER_STOPPED',error=repr(e),failure=str(fail));raise
        finally:ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
if __name__=='__main__':main()
