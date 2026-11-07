"""Two frozen same-day sessions; no formal slot is retried."""
import ctypes
from common import *
class Power(ctypes.Structure):
    _fields_=[('ACLineStatus',ctypes.c_ubyte),('BatteryFlag',ctypes.c_ubyte),('BatteryLifePercent',ctypes.c_ubyte),('SystemStatusFlag',ctypes.c_ubyte),('BatteryLifeTime',ctypes.c_uint32),('BatteryFullLifeTime',ctypes.c_uint32)]
def host_sample():
    p=Power();ok=ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p))
    fields=subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,temperature.gpu,memory.used,power.draw','--format=csv,noheader,nounits'],text=True).strip().split(',')
    return {'utc':now(),'utilization':float(fields[0]),'temperature':float(fields[1]),'memory_mib':float(fields[2]),'power_w':float(fields[3]),'AC':p.ACLineStatus if ok else None}
def admission(d):
    begun=time.monotonic();samples=[];time.sleep(120)
    while time.monotonic()-begun<600:
        three=[]
        for i in range(3):
            if i:time.sleep(10)
            three.append(host_sample())
        samples+=three;passed=all(r['utilization']<=5 and r['temperature']<=55 and r['AC']==1 for r in three) and max(r['temperature'] for r in three)-min(r['temperature'] for r in three)<=2
        if passed:break
        print('ADMISSION_WAIT',d.name,three,flush=True);time.sleep(10)
    save(d.with_name(d.name+'-ADMISSION.json'),{'passed':passed,'samples':samples,'seconds':time.monotonic()-begun})
    return passed
def main():
    plan=read(PUB/'S_F0.json');receipt=read(LOCAL/'S_REMOTE_RECEIPT.json');assert receipt['remote_sha']==receipt['frozen_sha'] and receipt['manifest_sha256']==sha(PUB/'S_F0.json')
    assert sha(PUB/'S_INPUTS.json')==plan['inputs_sha256'];assert read(PUB/'S_BRIDGE_QUALIFICATION.json')['status']=='PASS'
    root=LOCAL/'runs/S_formal';root.mkdir(parents=True,exist_ok=False);ledger=read(LOCAL/'S_SLOTS.json');tasks={t['id']:t for t in read(PUB/'S_INPUTS.json')};cfg=read(LOCAL/'CONFIG.json');assets=read(PUB/'ASSET_CHECK.json')
    for name,h in assets['runtime_S_files'].items():assert sha(Path(cfg['runtime_S'])/name)==h
    for role,m in cfg['models'].items():assert sha(m['path'])==m['sha256']
    save(root/'START.json',{'utc':now(),'execution_freeze_commit':receipt['frozen_sha'],'actual_repository_head':head(),'plan_sha256':sha(PUB/'S_F0.json'),'planned':768,'warmups':32})
    for b in plan['blocks']:
        for name,h in plan['code_sha256'].items():assert sha(Path(__file__).parent/name)==h,'immutable S code drift'
        d=root/b['block'];print('ADMISSION',d.name,flush=True)
        if not admission(d):
            for slot in b['slots']:ledger[slot].update(status='MISSING_HOST_ADMISSION',utc=now())
            save(LOCAL/'S_SLOTS.json',ledger);continue
        # Date is part of the amended single-day contract.
        local_now=datetime.now(timezone.utc).timestamp()+8*3600
        if datetime.fromtimestamp(local_now,timezone.utc).date().isoformat()!=plan['calendar_date']:
            for slot in b['slots']:ledger[slot].update(status='NOT_RUN_CALENDAR',utc=now())
            save(LOCAL/'S_SLOTS.json',ledger);continue
        try:
            with Server(d,b['condition']) as s:
                for tid,slot in zip(b['tasks'],b['slots']):
                    assert ledger[slot]['status']=='PLANNED';ledger[slot].update(status='STARTED',utc=now());save(LOCAL/'S_SLOTS.json',ledger)
                    try:
                        r=measure(s,tasks[tid],slot);r.update(session=b['session'],round=b['round'],position=b['position'],execution_freeze_commit=receipt['frozen_sha']);p=d/(tid.replace('/','-')+'.json');save(p,r)
                        ledger[slot].update(status='COMPLETED',record=str(p.relative_to(LOCAL)),record_sha256=sha(p),utc=now());print('DONE',slot,flush=True)
                    except Exception as e:
                        ledger[slot].update(status='FAILED_OPERATION',error=repr(e),utc=now());print('FAILED',slot,repr(e),flush=True)
                    save(LOCAL/'S_SLOTS.json',ledger)
        except Exception as e:
            save(d.with_name(d.name+'-ERROR.json'),{'error':repr(e),'utc':now()})
            for slot in b['slots']:
                if ledger[slot]['status']=='PLANNED':ledger[slot].update(status='MISSING_BLOCK_FAILURE',error=repr(e),utc=now())
            save(LOCAL/'S_SLOTS.json',ledger)
    save(root/'COMPLETE.json',{'utc':now(),'statuses':{k:sum(r['status']==k for r in ledger.values()) for k in set(r['status'] for r in ledger.values())}})
    print('S FINISHED',flush=True)
if __name__=='__main__':main()
