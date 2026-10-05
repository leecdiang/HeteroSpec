"""Execute original native contracts and paid, naturally aligned state forks."""
import argparse, hashlib, importlib.util, json, os, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ORIGINAL=Path(os.environ.get('HETEROSPEC_RTX_STUDY_ROOT','D:/HeteroSpec-RTX-Target-V1'))
OLD=ORIGINAL/'work/rtx-target-v1'
ASSET=Path(os.environ.get('HETEROSPEC_ASSET_ROOT','D:/HeteroSpec-PC'))
CUTS={15:13,25:4,18:4,31:4}

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n');q.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def native_module():
    spec=importlib.util.spec_from_file_location('old_native',ORIGINAL/'scripts/platform/rtx_trajectory_cost_v4/native.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def prepare():
    inputs=read(OLD/'INPUTS.json');m=native_module();contracts={}
    for task,cut in CUTS.items():
        tid=f'HumanEval/{task}';prompt=ORIGINAL/inputs[tid]['prompt']
        assert sha(prompt)==inputs[tid]['prompt_sha256']
        hist={}
        for condition in ['N0','N1']:
            rr=[read(OLD/f'formal/HumanEval-{task}-{condition}-r{rep}/result.json') for rep in range(1,4)]
            assert all(r['ids']==rr[0]['ids'] and r['endpoint']==rr[0]['endpoint'] for r in rr)
            traces=list((OLD/f'formal/HumanEval-{task}-{condition}-r1').glob('attempt-*/trace.jsonl'))
            assert len(traces)==1
            trace=[json.loads(s) for s in traces[0].read_text().splitlines()]
            dec=[r for r in trace if r['event']=='decode' and r['role']=='target']
            np=[r for r in dec if r['phase']=='prefill'][-1]['after']['max']+1
            matched=[r for r in dec if r['phase']=='continuation' and r['positions'][0]-np+1==cut]
            assert len(matched)==1
            call={k:matched[0][k] for k in ['tokens','positions','sequence_ids','logits_mask','before']}
            hist[condition]={'ids':rr[0]['ids'],'endpoint':rr[0]['endpoint'],'call':call,
                             'result_sha256':[sha(OLD/f'formal/HumanEval-{task}-{condition}-r{rep}/result.json') for rep in range(1,4)],
                             'trace_sha256':sha(traces[0])}
        assert hist['N0']['call']==hist['N1']['call']
        contracts[str(task)]={'cut':cut,'prompt':str(prompt),'prompt_sha256':sha(prompt),'historical':hist}
    save(HERE/'INPUT_CONTRACTS.json',contracts)
    save(HERE/'SOURCE_BINDINGS.json',{'paper_main':'e87291d26df32f2cb9571e005ab173b1c7a6830b',
        'upstream':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2',
        'original_native_frontend_sha256':sha(OLD/'native-build/bin/llama-cli.exe'),
        'native_parser_sha256':sha(ORIGINAL/'scripts/platform/rtx_trajectory_cost_v4/native.py'),
        'old_observer_sha256':sha(OLD/'pinned-source/common/hs_observer.h'),
        'old_server_source_sha256':sha(OLD/'pinned-source/tools/server/server-context.cpp'),
        'expected_model_sha256':{'target':'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6',
                                 'draft':'9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'}})
    print('Prepared four original native diagnostic contracts; no inference.',flush=True)

def run_unit(task,condition,rep,kind,formal=False):
    contracts=read(HERE/'INPUT_CONTRACTS.json');rec=contracts[str(task)]
    namespace='formal' if formal else 'engineering'
    d=HERE/f'runs/{namespace}/HumanEval-{task}-{condition}-{kind}-r{rep}'
    if (d/'RESULT.json').exists():
        r=read(d/'RESULT.json');assert r['valid']
        assert all(sha(d/name)==h for name,h in r['files'].items());return r
    if d.exists():raise RuntimeError('Incomplete attempt retained; no automatic retry: '+str(d))
    completed=list((HERE/'runs').glob('*/HumanEval-*/START.json'))
    assert sum('/engineering/' in p.as_posix() for p in completed)<12 or formal
    assert sum('/formal/' in p.as_posix() for p in completed)<24 or not formal
    d.mkdir(parents=True)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=HERE,text=True).strip(),'Freeze implementation before inference'
    executable=(OLD/'native-build/bin/llama-cli.exe') if kind=='old' else HERE/'generated/build/bin/llama-cli.exe'
    if kind!='old':assert sha(executable)==read(HERE/'generated/BUILD_IDENTITY.json')['frontend_sha256']
    m=native_module();cmd=m.templates(m.paths(ASSET))['RTX_BATCHED_K2']
    cmd[0]=str(executable);cmd+=['--threads','24','--threads-batch','24']
    mapping={'{prompt}':rec['prompt'],'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt')}
    cmd=[mapping.get(s,s) for s in cmd]
    keys=['SystemRoot','WINDIR','TEMP','TMP','PATH','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE']
    env={k:os.environ[k] for k in keys if k in os.environ}
    env.update(HS_NATIVE_CAPTURE=str(d/'trace.jsonl'),LLAMA_BATCH_DEBUG='1')
    if condition=='N1':env['HS_TARGET_CONTINUATION_UB']='1'
    if kind!='old':env.update(HS_LIVE_CAPTURE=str(d/'live'),HS_LIVE_CUT=str(rec['cut']))
    if kind=='sham':env['HS_LIVE_SHAM']='1'
    if formal:env['HS_LIVE_FORK']='1'
    start={'utc':now(),'task':task,'condition':condition,'repetition':rep,'kind':kind,'formal':formal,
           'source_commit':head,'source_contracts_sha256':sha(HERE/'INPUT_CONTRACTS.json'),
           'frontend_sha256':sha(executable),'command':cmd,'prompt_sha256':sha(rec['prompt'])}
    assert start['prompt_sha256']==rec['prompt_sha256']
    save(d/'START.json',start);t=time.monotonic()
    try:
        with (d/'stdout.log').open('wb') as so,(d/'stderr.log').open('wb') as se:
            p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=d,env=env)
            save(d/'PROCESS.json',{'pid':p.pid,'started_utc':now()})
            try:rc=p.wait(timeout=300)
            except subprocess.TimeoutExpired:p.kill();p.wait();raise
        if rc:raise RuntimeError('Native frontend exit '+str(rc))
        parsed=m.parse_capture(d/'native.log','RTX_BATCHED_K2')
        ids=parsed['generated_ids'];endpoint=parsed['termination']
        assert ids and len(ids)<=128 and (endpoint=='EOS' or len(ids)==128)
        hist=rec['historical'][condition]
        r={**start,'ids':ids,'endpoint':endpoint,'historical_equal':ids==hist['ids'] and endpoint==hist['endpoint'],
           'elapsed_seconds':time.monotonic()-t,'valid':True}
        if kind!='old':
            if not (d/'live/checkpoint.json').exists():r['checkpoint_status']='UNSUPPORTED'
            else:
                c=read(d/'live/checkpoint.json');r['checkpoint_status']='CAPTURED';r['checkpoint']=c
                expected=hist['call']
                assert all(c[k]==expected[k] for k in ['tokens','positions','sequence_ids','logits_mask'])
                assert c['bounds']==expected['before']
                assert c['committed_ids']==ids[:rec['cut']]
                assert c['source_capture_unchanged']
                if formal:
                    assert c['source_after_forks_unchanged'] and len(c['forks'])==2
                    trace=[json.loads(s) for s in (d/'trace.jsonl').read_text().splitlines()]
                    markers=[i for i,x in enumerate(trace) if x['event']=='live_checkpoint'];assert len(markers)==1
                    decisions=[x for x in trace[markers[0]+1:] if x['event']=='verify_decision']
                    assert decisions
                    own=next(f for f in c['forks'] if f['ub']==c['source_ub'])
                    r['same_path_natural_decision_equal']=own['sampled_ids']==decisions[0]['sampled_ids']
                    r['natural_decision']=decisions[0]
                    assert r['same_path_natural_decision_equal'],'Same-path fork changed decisions'
        r['files']={p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()}
        save(d/'RESULT.json',r)
        print(json.dumps({'unit':d.name,'ids':len(ids),'historical_equal':r['historical_equal'],
                          'checkpoint':r.get('checkpoint_status'),'seconds':round(r['elapsed_seconds'],2)}),flush=True)
        return r
    except Exception as e:
        save(d/'FAILURE.json',{**start,'ended_utc':now(),'elapsed_seconds':time.monotonic()-t,'error':repr(e)});raise

def engineering():
    for task in [15,25]:
        for condition in ['N0','N1']:
            rr=[run_unit(task,condition,1,kind) for kind in ['old','capture','sham']]
            assert all(r['ids']==rr[0]['ids'] and r['endpoint']==rr[0]['endpoint'] and r['historical_equal'] for r in rr)
            assert all(r.get('checkpoint_status')=='CAPTURED' for r in rr[1:])
            assert rr[1]['checkpoint']==rr[2]['checkpoint']
    save(HERE/'runs/ENGINEERING_QUALIFICATION.json',{'status':'PASS','complete_trajectories':12,'utc':now()})

def formal():
    assert read(HERE/'runs/ENGINEERING_QUALIFICATION.json')['status']=='PASS'
    for rep in range(1,4):
        for task in ([15,25,18,31] if rep%2 else [31,18,25,15]):
            for condition in (['N0','N1'] if rep%2 else ['N1','N0']):run_unit(task,condition,rep,'capture',True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','engineering','formal']);a=p.parse_args()
    {'prepare':prepare,'engineering':engineering,'formal':formal}[a.phase]()
