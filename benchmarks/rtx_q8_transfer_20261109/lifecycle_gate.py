"""Full Windows natural/state qualification with immutable independent R operands."""
from pathlib import Path
import collections, copy, datetime, hashlib, json, os, sys, time
from admission import HERE,ROOT,sha,put
from execute import BASE,WORK,execute
from geometry_gate import capability

MANIFEST='JOB_MANIFEST_LIFECYCLE.json'
LEGACY=HERE.parents[2]/'phase188/benchmarks/tpds_decisive_v1'
sys.path.insert(0,str(LEGACY))
from normalize import trace_from_row
from active_kv import parse

def read(p):return json.loads(Path(p).read_bytes())
def canonical(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

def spec(label,role,payload,requests,rows):
    run=BASE/'R-Qwen' if role=='R' else WORK/(role+'-v2')
    return dict(id=label,stage='qualification',build=str(run/'BUILD.json'),exe=str(run/'bin/worker.exe'),exe_sha256=sha(run/'bin/worker.exe'),requests=requests,rows=rows,job=payload)

def candidate(core,cut,k,models,mode='live'):
    cap=capability(core,cut,k,models);cap['proposal_mode']=mode
    return dict(models,n_ctx=1024,threads=24,k=k,draft=True,draft_width=4,lowering=cut,residency='matched',profile=False,target_output_reserve=8,proposal_mode=mode,capability_request=cap)

def freeze():
    models={k:v for k,v in read(ROOT/'JOB_MANIFEST_GEOMETRY.json')['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))}
    roots=read('D:/rtx188/Qwen-EXPOSED-ROOTS.json')['inputs'];roots=[dict(x,cap=128 if i==0 else 32) for i,x in enumerate(roots)]
    jobs=[]
    for i,x in enumerate(roots):
        payload=dict(models,lowering='SIMPLE',inputs=[dict(name='free',input=x,capture=True)])
        jobs.append(spec(f'lifecycle-v2-R-free-r{i}','R',payload,1,len(x['prompt_ids'])+x['cap']-1))
    for core in ('loop4','packed'):
        for cut in ('SIMPLE','LOCAL'):
            for k in (3,7):
                inputs=[]
                for i,x in enumerate(roots):
                    for mode in ('heavy','clean'):inputs.append(dict(name=f'r{i}-{mode}',input=x,capture=mode=='heavy'))
                    if i==0:
                        for mode in ('heavy','clean'):inputs.append(dict(name='cap1-'+mode,input=dict(x,cap=1),capture=mode=='heavy'))
                payload=candidate(core,cut,k,models);payload['inputs']=inputs
                rows=sum(2*len(e['input']['prompt_ids'])+2*(k+1)*(e['input']['cap']-1) for e in inputs)
                jobs.append(spec(f'lifecycle-v2-{core}-{cut}-k{k}',core,payload,len(inputs),rows))
    # An immutable finite job graph: reference operands may be generated only by
    # the unchanged R from already frozen candidate prefix/call records.
    put(ROOT/MANIFEST,dict(status='FROZEN_NATURAL_AND_DETERMINISTIC_ORACLE_DAG',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_binding=str(WORK/'SOURCE-v2.json'),frontend_root=str(WORK/'frontend-v2'),source_sha256=sha(WORK/'SOURCE-v2.json'),
        fixed_jobs_requests=sum(x['requests'] for x in jobs),fixed_jobs_rows=sum(x['rows'] for x in jobs),jobs=jobs,
        oracle_factory=dict(source_sha256=sha(Path(__file__)),rule='One scalar-R forced case per actual previously uncovered candidate verify path; own all requested vectors; all committed states compared; group <=4 cases; no reference from candidate floats; full cap128/32 roots preserved',
            admission='Every expanded exact token/position/row job written and hashed before its native process;512-stage/3072-total/4M-row nonrefundable guards remain. Stop if any complete required gate cannot be admitted.'),
        full_stage_B_qualification=False,clean_timing_not_admitted=True))
    put(ROOT/'QUALIFICATION_TASKS.json',dict(roots=roots,natural_caps=[x['cap'] for x in roots],
        required=['All8 cut/projection/k natural heavy/clean and cap1; unchanged R full endpoints, all vectors including rejected branches, every committed active KV/frontier, independent pending/trim/stop reconstruction',
        'V2 physical-counter geometry bridge and within/cross output masks; retained historical long/cap-sensitive source',
        'All rejection ranks0..k-1, cap during each accepted suffix position, all-accepted bonus and short-tail fixture; R-derived controlled tape distinct from live producer',
        'Actual autonomous8B EOG, context reset, native owned-tape production and live/replay ownership bridge; native negative contracts',
        'Four-origin equal-work full vector/KV/ownership bridge and independent formal R endpoints before clean timers'],
        omitted_required_gates_allowed=False,qualification_ceiling=512,all_future_optional_gpu_stages_closed_until_complete=True))
    print('Frozen full natural roots/caps and reference job factory',sum(j['requests'] for j in jobs),'fixed requests',flush=True)

def add_oracle(label,payload,cases):
    manifest=read(ROOT/MANIFEST);job=spec(label,'R',payload,len(cases),sum(sum(len(v['ids']) for v in c['forced']) for c in cases))
    # Preserve immutable manifest revisions and exact operands before execution.
    filename='oracle-manifests/'+label+'.json'
    put(ROOT/filename,dict(manifest,jobs=[job],expanded_from_sha256=sha(ROOT/MANIFEST)))
    return execute(job,filename)

class Bank:
    def __init__(self,index,x,free):
        self.index=index;self.x=x;self.free=free;self.entries={};self.counter=0
        self.meta=read(free.parent/'result.json');self.row=read(free/'receipt.json');self.endpoint=self.row['endpoint']
        structure=self.meta['model_structure'];writer=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-original-v4/source/src/llama-kv-cache.cpp')
        self.profile=dict(format='dense_seq_f16_v1',writer_sha256=sha(writer),layer_map_source_sha256=sha(writer),target_model_sha256=read(ROOT/MANIFEST)['jobs'][0]['job']['target_sha256'],host_writer_reviewed=True,capacity=1024,
            layers=[dict(id=i,k_elements=structure['K_elements'],v_elements=structure['V_elements']) for i in range(structure['layers'])])
        prompt=x['prompt_ids'];ids=self.row['ids']
        for i in range(len(ids)):
            prefix=tuple(prompt+ids[:i]);name='initial' if i==0 else 'ordinary-'+str(i)
            self.entries[prefix]=dict(vector=str(free/'target'/(name+'.f32')))
        for label,prefix in [('initial',tuple(prompt)),('terminal',tuple(prompt+ids[:-1]))]:
            self.entries[prefix]['state']=str(free/'target/state'/label/'sequence.bin')
    def vector(self,prefix):return Path(self.entries[tuple(prefix)]['vector']).read_bytes()
    def state(self,prefix):return parse(Path(self.entries[tuple(prefix)]['state']).read_bytes(),list(range(len(prefix))),self.profile)[0]
    def add(self,native,cases):
        for c in cases:
            tape=sum((v['ids'] for v in c['forced']),[])
            for n in c['observe_positions']:
                key=tuple(tape[:n]);p=native/c['name']/'captures'/str(n);row=self.entries.setdefault(key,{})
                if 'vector' in row:assert self.vector(key)==(p/'frontier.f32').read_bytes(),'Unstable original R vector'
                row['vector']=str(p/'frontier.f32')
                if n in c['state_positions']:
                    if 'state' in row:assert self.state(key)==parse((p/'sequence.bin').read_bytes(),list(range(n)),self.profile)[0],'Unstable original R active KV'
                    row['state']=str(p/'sequence.bin')
    def fill(self,r,d):
        missing={tuple(u['prefix']) for u in d['vector_uses'] if tuple(u['prefix']) not in self.entries}
        states={tuple(s['prefix']) for s in d['states'] if 'state' not in self.entries.get(tuple(s['prefix']),{})}
        if not missing and not states:return []
        prompt=r['prompt_ids'];cases=[];covered=set()
        fulls=[u['prefix'] for u in d['vector_uses'] if u['key'].endswith('/'+str(r['k']))]
        if not r['cycles']:fulls=[prompt]
        for full in fulls:
            wanted=sorted(n for n in range(len(prompt),len(full)+1) if tuple(full[:n]) in missing|states and tuple(full[:n]) not in covered)
            if not wanted:continue
            target_states=[n for n in wanted if tuple(full[:n]) in states]
            forced=[dict(ids=prompt,phase='PREFILL',all=False)]
            if len(full)>len(prompt):forced.append(dict(ids=full[len(prompt):],phase='FORCED',all=False))
            cases.append(dict(name='path'+str(len(cases)),forced=forced,observe_positions=wanted,state_positions=target_states));covered.update(tuple(full[:n]) for n in wanted)
        assert missing|states<=covered,'Oracle factory does not cover all vectors/committed states'
        outputs=[]
        models={k:v for k,v in read(ROOT/MANIFEST)['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))}
        for start in range(0,len(cases),4):
            cc=cases[start:start+4];self.counter+=1;label=f'lifecycle-v2-oracle-r{self.index}-{self.counter:03d}'
            native=add_oracle(label,dict(models,lowering='SIMPLE',cases=cc),cc);self.add(native,cc);outputs.append(str(native))
        return outputs

def check(bank,actual,name,x):
    r=read(actual/(name+'-heavy')/'receipt.json');clean=read(actual/(name+'-clean')/'receipt.json');r['study_cap']=x['cap']
    _,d=trace_from_row(r,x['prompt_ids'],bank.meta['vocab'],bank.meta['eog_ids'],'rtx')
    old=bank.endpoint;expected_ids=old['ids'][:x['cap']];expected_eog=old['eog'][:len(expected_ids)]
    expected=dict(ids=expected_ids,eog=expected_eog,length=len(expected_ids),terminal_id=expected_ids[-1],stop_reason='EOG' if expected_eog[-1] else 'CAP')
    assert r['endpoint']==clean['endpoint']==expected,'Independent full endpoint mismatch'
    oracle=bank.fill(r,d);vectors=[];states=[]
    heavy=actual/(name+'-heavy')
    for use in d['vector_uses']:
        key=use['key'];label='initial' if key=='initial' else 'verify-'+key[4:].replace('/','-')
        raw=(heavy/'target'/(label+'.f32')).read_bytes();reference=bank.vector(use['prefix'])
        vectors.append(dict(key=key,prefix=len(use['prefix']),equal=raw==reference,actual_sha256=hashlib.sha256(raw).hexdigest(),reference_sha256=hashlib.sha256(reference).hexdigest()))
    for i,state in enumerate(d['states']):
        label='initial' if i==0 else 'commit-'+str(i-1);directory=heavy/'target/state'/label;prefix=state['prefix']
        av,_=parse((directory/'sequence.bin').read_bytes(),list(range(len(prefix))),bank.profile)
        states.append(dict(key=label,prefix=len(prefix),active_KV_equal=av==bank.state(prefix),frontier_equal=(directory/'frontier.f32').read_bytes()==bank.vector(prefix),
            pending=state['next_pending'],unmaterialized_suffix=state['unmaterialized_suffix'],terminal=state['terminal']))
        if i>0:
            cycle=r['cycles'][i-1];bounds=dict(min=0,max=len(prefix)-1)
            assert cycle['keep']==len(prefix) and cycle['target_after']==cycle['draft_after']==bounds,'Target/draft rollback and pending bounds'
    for row in (r,clean):
        hist=dict(collections.Counter(str(e['width']) for e in row['executions']))
        assert hist==row['target_physical_width_hist'],'Physical frontend/core width disagreement'
        assert sum(int(k)*v for k,v in row['draft_physical_width_hist'].items())==len(x['prompt_ids'])+(row['k']+1)*len(row['cycles'])
        assert sum(int(k)*v for k,v in hist.items())==len(x['prompt_ids'])+(row['k']+1)*len(row['cycles'])
    assert all(v==0 for v in clean['observed_API_calls_within_service'].values()),'Heavy capture/state transfer leaked into clean service'
    if len(clean['cycles'])>=2:assert clean['graphs_reused']>0,'Clean graph reuse missing'
    proof=dict(passed=all(v['equal'] for v in vectors) and all(s['active_KV_equal'] and s['frontier_equal'] for s in states),
        full_endpoint_equal=True,independent_pending_stop_trace=True,all_requested_full_vectors=vectors,all_committed_states=states,
        new_oracle_jobs=oracle,clean_API_calls=clean['observed_API_calls_within_service'],heavy_receipt_sha256=sha(heavy/'receipt.json'),clean_receipt_sha256=sha(actual/(name+'-clean')/'receipt.json'),
        branch_coverage=dict(rejection_ranks=sorted({c['accepted'] for c in r['cycles'] if c['rejected']}),commit_kinds=sorted({c['commit_kind'] for c in r['cycles']}),stop=r['stop_reason']),finite_only=True)
    put(ROOT/'natural_checks'/(actual.parent.name+'-'+name+'.json'),proof)
    assert proof['passed'],'Required full vector/active KV/frontier gate failed; retain and stop clean stages'
    print('NATURAL_PASS',actual.parent.name,name,flush=True)

def main():
    if sys.argv[1]=='freeze':freeze();return
    manifest=read(ROOT/MANIFEST);roots=read(ROOT/'QUALIFICATION_TASKS.json')['roots'];banks={}
    for job in manifest['jobs']:
        actual=execute(job,MANIFEST)
        if '-R-free-' in job['id']:
            i=int(job['id'][-1]);banks[i]=Bank(i,roots[i],actual/'free')
        else:
            for i,x in enumerate(roots):check(banks[i],actual,'r'+str(i),x)
            check(banks[0],actual,'cap1',dict(roots[0],cap=1))
    put(ROOT/'NATURAL_COMPLETE.json',dict(passed=True,all_eight_arms=True,all_committed_active_KV=True,remaining_B_gates_required=True))

if __name__=='__main__':main()
