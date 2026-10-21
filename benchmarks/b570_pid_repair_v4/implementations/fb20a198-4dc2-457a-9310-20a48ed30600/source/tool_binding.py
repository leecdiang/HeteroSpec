"""Bind actual terminal tool API evidence to the recorded CPU8 watchdog invocation."""
import json,hashlib,sys
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def load(p):return json.loads(Path(p).read_bytes())
def norm(s):return str(s).replace('/',chr(92))
def quote(s):return "'"+s.replace("'","''")+"'"
def check(root,run,freeze_sha,frozen,start,receipt,binding_path):
    root=Path(root);b=load(root/binding_path);intent=load(root/b['intent_path']);initial=load(root/b['initial_path']);last=load(root/b['final_path'])
    original=Path(load(root/'legacy/ROOT_BINDING.json')['task_root']);argv=intent['argv'];env=intent['environment']
    need(intent['freeze_sha256']==freeze_sha,'tool prospective freeze pin')
    need(set(env)=={'TEMP','TMP'} and all(Path(v)==original/'tmp' for v in env.values()),'tool environment scope')
    expected='$env:TEMP='+quote(env['TEMP'])+'; $env:TMP='+quote(env['TMP'])+'; & '+' '.join(quote(x) for x in argv)
    request=intent['request'];need(request['cmd']==expected,'unrelated tool command')
    need(Path(request['workdir'])==original and request.get('login') is False,'tool workdir/login')
    tools=load(root/'preflight/TOOLS.json');need(Path(request['shell'])==Path(tools['powershell']['path']),'tool shell identity')
    sys.path.insert(0,str(root/'src/rev2'));from verify import command_args
    need([norm(x) for x in argv]==[norm(x) for x in command_args(start['command'])],'actual watchdog command')
    need(hashlib.sha256(start['command'].encode()).hexdigest()==start['command_sha256'],'actual command digest')
    need(Path(argv[0])==Path(frozen['python'])==Path(start['image']),'actual interpreter')
    script=original/'source/outer_watchdog.py';indices=[i for i,x in enumerate(argv) if norm(x)==norm(script)]
    need(len(indices)==1 and argv[1:indices[0]] in (['-B'],['-I','-B']),'actual watchdog entry')
    tail=argv[indices[0]+1:];need(len(tail)%2==0,'watchdog argument pairs')
    pairs=list(zip(tail[::2],tail[1::2]));args=dict(pairs);need(len(args)==len(pairs),'duplicate watchdog option')
    expected_keys={'--root','--run','--mode','--phase-limit','--freeze-sha256','--supervisor-script'}
    need(set(args)==expected_keys and Path(args['--root'])==original and args['--run']==run and args['--mode']=='cpu8' and args['--freeze-sha256']==freeze_sha,'watchdog root/run/mode/freeze')
    need(Path(args['--supervisor-script'])==original/'source/cpu8_supervisor.py','watchdog supervisor entry')
    need(receipt['watchdog_pid']==start['pid'] and receipt['outer_job_empty'] and receipt['owned_handles_closed'] and receipt['error'] is None,'watchdog receipt identity/closure')
    need(initial['request']==request,'tool initial request')
    sid=b.get('session_id')
    if sid is None:
        need(initial['response'].get('session_id') is None and initial['response'].get('exit_code')==0 and last==initial,'actual immediate tool closure')
    else:
        need(initial['response'].get('session_id')==sid and last['request'].get('session_id')==sid and last['response'].get('exit_code')==0,'actual tool session closure')
    lines=last['response'].get('output','').splitlines();ends=[]
    for line in lines:
        try:obj=json.loads(line)
        except ValueError:continue
        if isinstance(obj,dict) and 'watchdog_closed' in obj:ends.append(obj)
    need(len(ends)==1 and ends[0]==dict(watchdog_closed=True,error=None,run=run),'actual watchdog terminal output')
    return dict(status='TOOL_WATCHDOG_BOUND',session_id=sid,run=run,watchdog_pid=start['pid'],scope='Actual API request/terminal output reconciled to recorded OS invocation; outer OS lifetime remains separately unknown')
