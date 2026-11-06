"""Finite native development. Saved historical GPU bytes remain valid evidence."""
from host import *
import numpy as np
from active_kv import parse
from trace import reconstruct

MATRIX_VERSIONS={'SIMPLE':'SIMPLE/runtime-v4','LOCAL':'LOCAL/runtime-v3','R-Qwen':'R-Qwen/runtime-v2','R-Smol':'R-Smol/runtime-v2'}
VERSIONS=dict(MATRIX_VERSIONS,SIMPLE='SIMPLE/runtime-v5',LOCAL='LOCAL/runtime-v4')
HEADS=[255,256,511,512,767,768]
WIDTHS=[1,2,3,4,5,8,16,32]

def profile(result,family):
    s=result['model_structure'];old=OLD if family=='Qwen' else META
    return dict(format='dense_seq_f16_v1',writer_sha256=sha(old/'source/src/llama-kv-cache.cpp'),layer_map_source_sha256=sha(old/'source/src/llama-kv-cache.cpp'),target_model_sha256=MODELS[family]['target_sha256'],host_writer_reviewed=True,capacity=1024,layers=[dict(id=i,k_elements=s['K_elements'],v_elements=s['V_elements']) for i in range(s['layers'])])

def matrix_case(head,width,tape):
    end=head+width;all_rows=width<=4
    return dict(name=f'h{head}-q{width}',forced=[dict(ids=tape[:head],phase='PREFILL',all=False),dict(ids=tape[head:end],phase='VERIFY',all=all_rows)],observe_positions=[head]+(list(range(head+1,end+1)) if all_rows else [end]),state_positions=[end])

def finished(label,name,family,payload,reservation,output=None):
    out=Path(output) if output else ROOT/'runs'/label
    if out.exists():
        assert (out/'COMPLETE.json').exists(),'retained failed attempt requires a new version, never implicit retry'
        binding=json.loads((out/'binding.json').read_bytes());assert binding['exe']==sha(ROOT/name/'bin/worker.exe')
        assert json.loads((out/'job.json').read_bytes())==dict(MODELS[family],**payload),'job binding differs'
        return out
    return execute(label,name,family,payload,reservation,out)

def compare_cases(reference,candidate,cases,family,label):
    rr=json.loads((reference/'native/result.json').read_bytes());cr=json.loads((candidate/'native/result.json').read_bytes());assert rr['model_structure']==cr['model_structure']
    p=profile(rr,family);rows=[]
    for case in cases:
        for n in case['observe_positions']:
            a=candidate/'native'/case['name']/'captures'/str(n);b=reference/'native'/case['name']/'captures'/str(n)
            row=dict(case=case['name'],prefix=n,full_vector_equal=sha(a/'frontier.f32')==sha(b/'frontier.f32'))
            if n in case['state_positions']:
                av,_=parse((a/'sequence.bin').read_bytes(),list(range(n)),p);bv,_=parse((b/'sequence.bin').read_bytes(),list(range(n)),p);row['active_KV_equal']=av==bv
            rows.append(row)
    result=dict(rows=rows,all_passed=all(all(v for k,v in r.items() if k.endswith('equal')) for r in rows),reference=str(reference),candidate=str(candidate),observed_boundaries='All originally requested vector rows; final committed active KV for every controlled call.',source_graph_geometry_in_native_result=True)
    receipt=ROOT/(label+'.json')
    if receipt.exists():assert json.loads(receipt.read_bytes())==result,'existing qualification differs'
    else:put(receipt,result)
    assert result['all_passed'],'retained numerical qualification failure'

def matrix(family='Qwen',batch_index=None):
    if family=='Qwen':
        f=json.loads(Path('D:/rtx184-runs/D-main-forced-10/job.json').read_bytes())['forced'];tape=f['prompt_ids']+f['paths'][0]['suffix']
    else:
        p=json.loads((ROOT/'runs/Smol-old-free/native/r0-heavy/receipt.json').read_bytes());tape=p['prompt_ids']+p['ids']
        # Boundary probes use exposed token IDs as controlled material, never
        # label a repeated/truncated tape as a natural request.
        tape=(tape*((800+len(tape)-1)//len(tape)))[:800]
    cases=[matrix_case(h,q,tape) for h in HEADS for q in WIDTHS]
    if not (ROOT/(family+'-MATRIX-DESIGN.json')).exists():put(ROOT/(family+'-MATRIX-DESIGN.json'),dict(heads=HEADS,widths=WIDTHS,cases=cases,natural_requests=False,selection_before_outcomes=True))
    for start in range(0,len(cases),4):
        if batch_index is not None and start//4!=batch_index:continue
        group=cases[start:start+4];reservation=dict(requests=len(group),token_rows=sum(len(c['forced'][0]['ids'])+len(c['forced'][1]['ids']) for c in group),operators=0)
        label=family+'-matrix-'+str(start//4)
        versions=VERSIONS if family=='Smol' else MATRIX_VERSIONS
        placement=ROOT/(label+'-STORAGE.json')
        if placement.exists():runs=Path(json.loads(placement.read_bytes())['runs'])
        elif (ROOT/'runs'/(label+'-R')).exists():runs=ROOT/'runs'
        else:
            choices=[ROOT/'runs',Path('E:/rtx188/runs')]
            for p in choices:p.mkdir(parents=True,exist_ok=True)
            runs=max(choices,key=lambda p:shutil.disk_usage(p).free)
            put(placement,dict(runs=str(runs),reason='Whole-model diagnostic captures placed by available space only; all methods in this batch share the same volume. Fixed natural timing always uses D.',reserve_bytes=20*1024**3))
        r=finished(label+'-R',versions['R-'+family],family,dict(lowering='SIMPLE',cases=group),reservation,runs/(label+'-R'))
        for lowering in ('SIMPLE','LOCAL'):
            c=finished(label+'-'+lowering,versions[lowering],family,dict(lowering=lowering,cases=group),reservation,runs/(label+'-'+lowering))
            compare_cases(r,c,group,family,label+'-'+lowering+'-QUALIFICATION');dedup()
        print(label,'all full-state comparisons passed',flush=True)

def roots(family):
    oldfamily='Qwen' if family=='Qwen' else 'SmolLM2'
    panel=json.loads((OLD.parent/('admission-'+oldfamily+'-v4')/'PANEL.json').read_bytes())['inputs']
    selected=[next(x for x in panel if x['source_index']==i) for i in range(3)]
    if family=='Qwen':
        prior=json.loads(Path('D:/rtx184-runs/D-main-forced-10/job.json').read_bytes())['forced']
        selected.append(dict(id='APPS/train/65',family='Qwen',source_index='retained-failure',cap=128,prompt_ids=prior['prompt_ids']))
    else:selected.append(next(x for x in panel if x['source_index']==4))
    if not (ROOT/(family+'-EXPOSED-ROOTS.json')).exists():put(ROOT/(family+'-EXPOSED-ROOTS.json'),dict(source='Fixed exposed math roots0..2 plus retained Qwen failure / first exposed Smol code root. Chosen before natural candidate outputs.',source_roots=[dict(id=x['id'],tokens=len(x['prompt_ids'])) for x in selected],new_test_exposure=False,inputs=selected))
    return selected

def natural(family,arm):
    selected=roots(family);inputs=[]
    for i,row in enumerate(selected):
        modes=[('heavy',True),('clean',False)] if arm=='R' else [('heavy',True),('warmup',False),('clean',False)]
        for kind,capture in modes:inputs.append(dict(name=f'r{i}-{kind}',capture=capture,input=row))
    if arm=='R':name=VERSIONS['R-'+family];lowering='SIMPLE';draft=False;width=1
    else:lowering,control=arm.split('-');name=VERSIONS[lowering];draft=control!='M';width=4 if control=='D4' else 1
    count=len(inputs);rows=sum(len(x['input']['prompt_ids'])+(len(x['input']['prompt_ids'])+8*(x['input']['cap']-1) if draft else x['input']['cap']-1) for x in inputs)
    out=finished(family+'-'+('old-free' if arm=='R' else arm+'-development'),name,family,dict(lowering=lowering,draft=draft,draft_width=width,inputs=inputs),dict(requests=count,token_rows=rows,operators=0));dedup();return out

def original_bridge(family):
    family_key='Qwen' if family=='Qwen' else 'SmolLM2';admit=OLD.parent/('admission-'+family_key+'-v4');panel=json.loads((admit/'PANEL.json').read_bytes());binding=json.loads((admit/'BINDING.json').read_bytes());binding['status']='FROZEN_BEFORE_FIRST_NATIVE_REQUEST'
    template=next(x for x in json.loads((admit/'SLOTS.json').read_bytes()) if x['arm']=='R' and x['source_index']==0)
    slots=[dict(template,slot_id=name,observer='heavy' if name!='old-off' else 'off') for name in ('old0','old1','old-off')]
    payload=dict(historical=dict(panel=panel,binding=binding,slots=slots,plan=json.loads((admit/'PLAN.json').read_bytes()),family=family_key))
    label=family+'-unchanged-original-R';out=ROOT/'runs'/label
    if not out.exists():execute(label,'',family,payload,dict(requests=3,token_rows=3*(len(panel['inputs'][0]['prompt_ids'])+127),operators=0))
    assert (out/'COMPLETE.json').exists()
    free=ROOT/'runs'/(family+'-old-free')/'native/r0-heavy';new=json.loads((free/'receipt.json').read_bytes());rows=[]
    original={p.name:sha(p) for p in (out/'native/old0/target').glob('*.f32')}
    for name in ('old0','old1','old-off'):
        r=json.loads((out/'native'/(name+'.json')).read_bytes());row=dict(source=name,endpoint_equal=r['endpoint']==new['endpoint'])
        if name!='old-off':row['full_vectors_equal']={p.name:sha(p) for p in (out/'native'/name/'target').glob('*.f32')}==original
        rows.append(row)
    rows.append(dict(source='new observer adapter',endpoint_equal=True,full_vectors_equal={p.name:sha(p) for p in (free/'target').glob('*.f32')}==original))
    result=dict(rows=rows,passed=all(all(v for k,v in r.items() if k.endswith('equal')) for r in rows),original_executable_unmodified=True,requested_full_vectors=len(original),separate_old_binary=str(out/'launch.json'))
    put(ROOT/(family+'-OLD-R-OBSERVER-BRIDGE.json'),result);assert result['passed'];dedup()

def final_runtime_bridge():
    f=json.loads(Path('D:/rtx184-runs/D-main-forced-10/job.json').read_bytes())['forced'];tape=f['prompt_ids']+f['paths'][0]['suffix'];design=json.loads((ROOT/'FINAL-RUNTIME-BRIDGE-DESIGN.json').read_bytes());cases=[matrix_case(h,q,tape) for h,q in design['cases']]
    reference=ROOT/'final-runtime-original-R-view';native=reference/'native';native.mkdir(parents=True,exist_ok=True);sources=[];meta=None
    for case in cases:
        h=int(case['name'].split('-')[0][1:]);q=int(case['name'].split('-q')[1]);ix=(HEADS.index(h)*8+WIDTHS.index(q))//4;source=ROOT/'runs'/f'Qwen-matrix-{ix}-R'/'native';meta=json.loads((source/'result.json').read_bytes())
        for n in case['observe_positions']:
            for p in (source/case['name']/'captures'/str(n)).iterdir():
                target=native/case['name']/'captures'/str(n)/p.name;target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():assert sha(target)==sha(p)
                else:os.link(p,target)
                sources.append(dict(original=str(p),view=str(target),sha256=sha(p)))
    if not (native/'result.json').exists():put(native/'result.json',dict(model_structure=meta['model_structure'],CPU_reference_view_only=True,source_files=sources))
    reservation=dict(requests=len(cases),token_rows=sum(sum(len(c['ids']) for c in x['forced']) for x in cases),operators=0)
    for lowering in ('SIMPLE','LOCAL'):
        label='Qwen-final-runtime-'+lowering;out=finished(label,VERSIONS[lowering],'Qwen',dict(lowering=lowering,cases=cases),reservation);compare_cases(reference,out,cases,'Qwen',label+'-QUALIFICATION');dedup()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('--family',default='Qwen');p.add_argument('--batch',type=int);p.add_argument('--arm');a=p.parse_args()
    if a.action=='matrix':matrix(a.family,a.batch)
    elif a.action=='natural':natural(a.family,a.arm)
    elif a.action=='bridge':original_bridge(a.family)
    elif a.action=='runtime-bridge':final_runtime_bridge()
