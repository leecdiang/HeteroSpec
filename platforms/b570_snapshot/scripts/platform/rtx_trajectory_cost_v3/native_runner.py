"""Fresh original/timer CLI execution; native commitment and timer are captured together."""
import os,json,re,subprocess,time
from pathlib import Path
from prepare import ROOT,STUDY,save,sha,ledger,now
import native
import engine
from guards import authorize
TIMER=re.compile(rb'HS_TIMER start_qpc=(\d+) end_qpc=(\d+) frequency=(\d+) start_steady_ns=(\d+) end_steady_ns=(\d+) count=(\d+) terminal_id=(\d+)')
WIRE={'REFERENCE_UB1':'TARGET_REFERENCE','TARGET_ONLY_UB2':'H1_TARGET_UB2','RTX_BATCHED_K2':'RTX_BATCHED_K2','RTX_SERIALIZED_K2':'RTX_SERIALIZED_K2'}
def commands():
    base=native.templates(native.paths(engine.ASSET));base['H1_TARGET_UB2']=base['TARGET_REFERENCE'].copy()
    base['H1_TARGET_UB2'][base['H1_TARGET_UB2'].index('--ubatch-size')+1]='2'
    return {k:base[v] for k,v in WIRE.items()}
def telemetry():
    q=['nvidia-smi','--query-gpu=name,driver_version,pci.bus_id,temperature.gpu,clocks.current.graphics,clocks.current.memory,utilization.gpu,memory.used,pstate,power.draw','--format=csv,noheader,nounits']
    return {'utc':now(),'monotonic_ns':time.monotonic_ns(),'fields':['name','driver','pci','temperature','graphics_clock','memory_clock','utilization','memory_used','pstate','power'],'values':subprocess.check_output(q,text=True).strip().split(', ')}
def parse_timer(stderr,ids):
    matches=TIMER.findall(Path(stderr).read_bytes())
    if len(matches)!=1:raise ValueError('expected exactly one timer record')
    a,b,f,c,d,n,t=map(int,matches[0])
    if b<=a or d<=c or f<=0:raise ValueError('nonpositive timer interval')
    ms=(b-a)*1000/f;other=(d-c)/1e6
    if abs(ms-other)>max(.020,.001*ms):raise ValueError('timer clocks disagree')
    if n!=len(ids) or t!=ids[-1]:raise ValueError('timer native endpoint count/ID differs')
    return {'start_qpc':a,'end_qpc':b,'frequency':f,'start_steady_ns':c,'end_steady_ns':d,'count':n,'terminal_id':t,'milliseconds':ms,'secondary_milliseconds':other}
def execute(task,rep,wire,out,condition,timed=False,text=None,debug='1'):
    authorize(task,wire)
    phase=os.environ.get('HS_PHASE','ENGINEERING');rid=f'{task.replace("/","-")}-r{rep}-{condition}'
    d=Path(out)/rid;d.mkdir(parents=True,exist_ok=False)
    if text is None:text=engine.prompts()[task]
    (d/'prompt.txt').write_text(text,encoding='utf-8',newline='\n')
    cmd=commands()[wire].copy()
    if timed:cmd[0]=str(ROOT/'work/timer-build/bin/llama-cli.exe')
    cmd=[{'{prompt}':str(d/'prompt.txt'),'{native_log}':str(d/'native.log'),'{transcript}':str(d/'transcript.txt')}.get(a,a) for a in cmd]
    context={'phase':phase,'study':'RTX_MATCHED_QUALIFICATION_COST_V2' if condition.startswith('B_') else 'RTX_TRAJECTORY_AND_MATCHED_COST_V3','run_id':rid,'task_id':task,'repetition':rep,'condition':condition,'wire_condition':wire,'source_head':engine.source_head(),'protocol_sha256':sha(STUDY/'JOINT_PROTOCOL.json') if (STUDY/'JOINT_PROTOCOL.json').exists() else None,'asset_identity_sha256':sha(STUDY/'ASSET_IDENTITY.json'),'command':cmd,'implementation':'TIMER' if timed else 'ORIGINAL'}
    r={**context,'started_utc':now(),'started_monotonic_ns':time.monotonic_ns(),'status':'STARTED','input_sha256':sha(d/'prompt.txt'),'process_environment_overrides':{'LLAMA_BATCH_DEBUG':debug},'device_before':telemetry()}
    save(d/'record.json',r);ledger({**context,'event':'run_planned'});p=None
    try:
        with (d/'stdout.log').open('wb') as so,(d/'stderr.log').open('wb') as se:
            p=subprocess.Popen(cmd,stdout=so,stderr=se,stdin=subprocess.DEVNULL,env={**os.environ,'LLAMA_BATCH_DEBUG':debug})
            r['pid']=p.pid;ledger({**context,'event':'process_started','pid':p.pid})
            r['exit_code']=p.wait(timeout=300)
        if r['exit_code']:raise RuntimeError('native process exit '+str(r['exit_code']))
        parsed=native.parse_capture(d/'native.log',WIRE[wire]);r.update(parsed)
        r['array_sha256']=engine.ah(r['generated_ids']);save(d/'generated_ids.json',r['generated_ids'])
        if debug=='1':
            import verify_replay
            r['prompt_ids']=verify_replay.native_prompt((d/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1'))
            r['prompt_array_sha256']=engine.ah(r['prompt_ids'])
        if timed:r['timer']=parse_timer(d/'stderr.log',r['generated_ids'])
        r['status']='VALID'
    except Exception as e:
        r.update(status='OPERATIONAL_FAILURE',error=repr(e))
        if p and p.poll() is None:p.kill();p.wait();r['exit_code']=p.returncode
    r.update(ended_utc=now(),ended_monotonic_ns=time.monotonic_ns(),device_after=telemetry())
    r['files']={q.name:{'bytes':q.stat().st_size,'sha256':sha(q)} for q in d.iterdir() if q.is_file() and q.name!='record.json'}
    save(d/'record.json',r)
    ledger({**context,'event':'process_completed','pid':p.pid if p else None,'status':r['status'],'exit_code':r.get('exit_code'),'started_utc':r['started_utc'],'ended_utc':r['ended_utc'],'started_monotonic_ns':r['started_monotonic_ns'],'ended_monotonic_ns':r['ended_monotonic_ns'],'record_path':d.relative_to(ROOT).as_posix()})
    # Preserve each observed physical forward group; original native timestamps are
    # process-relative log clocks. Exact per-decode host UTC/end is not exposed.
    if (d/'native.log').exists() and debug=='1':
        lines=(d/'native.log').read_bytes().decode('latin-1').splitlines()
        groups=[(i,l) for i,l in enumerate(lines,1) if 'ubatch_print:' in l and 'n_tokens' in l and '=' in l]
        for j,(line,msg) in enumerate(groups):ledger({**context,'event':'native_forward_observed','pid':p.pid,'subevent':j,'raw_log_line':line,'native_message':msg,'native_log_sha256':r['files']['native.log']['sha256'],'host_decode_start_utc':None,'host_decode_end_utc':None,'timing_limit':'native process-relative batch log; no exact host start/end observation'})
    return r
