"""Execute only a committed freeze, persist each attempt, never select on outcomes."""
import argparse,ctypes,datetime,json,pathlib,subprocess,time,sys
from run import run,save
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rtx_recover import read,sha
P=pathlib.Path
class Power(ctypes.Structure):
    _fields_=[('AC',ctypes.c_byte),('flag',ctypes.c_byte),('percent',ctypes.c_byte),('system',ctypes.c_byte),('life',ctypes.c_uint32),('full',ctypes.c_uint32)]
def host():
    v=subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw','--format=csv,noheader,nounits'],timeout=20).decode().strip().split(', ')
    power=Power();ok=ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power))
    return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpu=v[0],uuid=v[1],driver=v[2],total_mib=float(v[3]),used_mib=float(v[4]),util=float(v[5]),temperature=float(v[6]),power_w=v[7],AC=power.AC if ok else None,power_scheme=subprocess.check_output(['powercfg','/getactivescheme'],timeout=10).decode(errors='replace'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);ap.add_argument('freeze',type=P);a=ap.parse_args();root=a.root.resolve();fdir=a.freeze.resolve();freeze=read(fdir/'FREEZE.json')
    repo=P(__file__).resolve().parents[3]
    rel=(fdir/'FREEZE.json').relative_to(repo).as_posix()
    committed=subprocess.check_output(['git','show','HEAD:'+rel],cwd=repo);assert committed==(fdir/'FREEZE.json').read_bytes(),'freeze must be committed'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo).decode().strip()
    checkroot=root/'formal';checkroot.mkdir(exist_ok=True);statepath=checkroot/'CHECKPOINT.json'
    state=read(statepath) if statepath.exists() else dict(status='STARTED',freeze_sha256=sha(fdir/'FREEZE.json'),freeze_commit=commit,sessions={},attempts=[],failed_cells=[])
    assert state['freeze_sha256']==sha(fdir/'FREEZE.json')
    for path,h in freeze['files'].items():assert sha(path)==h,'Frozen bytes drift: '+path
    save(statepath,state)
    for session in range(freeze['sessions']):
        if str(session) in state['sessions']:
            old=state['sessions'][str(session)];assert sha(old['result'])==old['sha256'];continue
        schedule=fdir/f'SESSION_{session}.json';assert sha(schedule)==freeze['schedule_hashes'][schedule.name]
        for attempt in range(2):
            name=f'formal-s{session}-a{attempt}';prior=root/(name+'-PROCESS.json')
            if prior.exists():
                receipt=read(prior)
                if receipt['status']=='COMPLETE':
                    result=root/name/'result.json';assert sha(result)==receipt['result_sha256'];state['sessions'][str(session)]=dict(result=str(result),sha256=sha(result),attempt=attempt);save(statepath,state);break
                if receipt['status']=='RUNNING':raise RuntimeError('Inspect still-running/interrupted owned process before resumption')
                continue
            technical=sum(1 for x in state['attempts'] if x['status']!='COMPLETE')
            if attempt and technical>freeze['maximum_technical_session_retries']:raise RuntimeError('Retry budget exhausted')
            if sum(x['owned_seconds'] for x in state['attempts'])>=freeze['total_native_owned_seconds_cap']:raise RuntimeError('Native budget exhausted')
            start=time.monotonic();samples=[]
            while True:
                time.sleep(5);h=host();samples.append(h)
                assert all(h[k]==freeze['host'][k] for k in ('gpu','uuid','driver','total_mib','power_scheme')),'Frozen host identity changed'
                if time.monotonic()-start>=30 and h['AC']==1 and h['util']<=5 and h['temperature']<=60:break
                if time.monotonic()-start>=300:
                    save(checkroot/(name+'-ADMISSION.json'),dict(status='FAILED',samples=samples));raise RuntimeError('Host admission unavailable')
            save(checkroot/(name+'-ADMISSION.json'),dict(status='PASS',samples=samples))
            print('START_SESSION',session,'attempt',attempt,flush=True)
            try:receipt=run(root,schedule,name,freeze['native_worker_timeout_seconds'])
            except subprocess.TimeoutExpired:receipt=read(root/(name+'-PROCESS.json'))
            state['attempts'].append(dict(session=session,attempt=attempt,**receipt));save(statepath,state)
            if receipt['status']=='COMPLETE':
                result=root/name/'result.json';state['sessions'][str(session)]=dict(result=str(result),sha256=sha(result),attempt=attempt);save(statepath,state);break
            result=read(root/name/'result.json')
            if 'mismatch' in result.get('error',''):
                state['status']='NUMERICAL_FAILURE';save(statepath,state);raise RuntimeError('Numerical failure: preserve cohort and remove affected cell before independent continuation')
        else:raise RuntimeError('Session did not complete within technical retry limit')
    state['status']='COMPLETE';save(statepath,state);print('CAMPAIGN_COMPLETE',flush=True)
if __name__=='__main__':main()
