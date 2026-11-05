"""Bounded session launcher with durable reservation BEFORE process creation.
Adapters execute declared native lifecycles within logical sessions. This is not a native adapter.
No model is run unless the caller passes --execute-native and a reviewed binding.
"""
from __future__ import annotations
import argparse,os,sqlite3,subprocess,time,signal
from pathlib import Path
from common import need,digest,read,write_new,file_sha

class Ledger:
    def __init__(self,path:Path,limits:dict):
        self.db=sqlite3.connect(path);self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,requests INTEGER,token_rows INTEGER,operators INTEGER,status TEXT,started REAL,ended REAL,code INTEGER)')
        old=self.db.execute('SELECT v FROM meta WHERE k=?',('limits',)).fetchone();pin=digest(limits)
        if old:need(old[0]==pin,'budget changed in-place; publish a new development tranche instead')
        else:self.db.execute('INSERT INTO meta VALUES(?,?)',('limits',pin));self.db.commit()
        self.limits=limits
    def reserve(self,key,cost):
        for k in ('requests','token_rows','operators'):need(type(cost[k]) is int and cost[k]>=0,'invalid reservation')
        try:
            self.db.execute('BEGIN IMMEDIATE')
            need(not self.db.execute('SELECT 1 FROM attempts WHERE id=?',(key,)).fetchone(),'attempt already exists')
            used=self.db.execute('SELECT COALESCE(SUM(requests),0),COALESCE(SUM(token_rows),0),COALESCE(SUM(operators),0) FROM attempts').fetchone()
            for i,k in enumerate(('requests','token_rows','operators')):need(used[i]+cost[k]<=self.limits[k],'budget exhausted: '+k)
            self.db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?)',(key,cost['requests'],cost['token_rows'],cost['operators'],'RESERVED',time.time(),None,None));self.db.commit()
        except Exception:self.db.rollback();raise
    def finish(self,key,status,code):
        self.db.execute('UPDATE attempts SET status=?,ended=?,code=? WHERE id=?',(status,time.time(),code,key));self.db.commit()
    def close(self):self.db.close()

def kill_owned(p):
    if p.poll() is not None:return
    if os.name=='nt':
        subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,check=False)
    else:
        try:os.killpg(p.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass

def admission_for_phase(phase,binding):
    need(phase in ('admission','bridge','qualification','development','main'),'phase')
    if phase in ('admission','bridge'):
        need(binding['status']=='HOST_READY_BRIDGE','bridge/admission binding required')
        need(binding.get('original_assets_verified') is True,'actual old assets must be bound')
        need(binding.get('bounded_native_entry_reviewed') is True,'bounded native entry not reviewed')
    else:
        need(binding['status']=='HOST_READY_FINITE_STUDY','native adapter not qualified')
        need(binding['reference_bridge_passed'] is True,'old-R gate not passed')
    if phase=='main':need(binding['frozen_before_test'] is True,'freeze required')

def execute(job_path:Path,binding_path:Path,run_root:Path,execute_native=False):
    need(execute_native,'explicit native execution permission required')
    job=read(job_path);binding=read(binding_path)
    need(job['binding_sha256']==digest(binding),'binding mismatch')
    admission_for_phase(job['phase'],binding)
    need(binding['hardware_platform'] in ('rtx','b570'),'unsupported host')
    need(binding['input_manifest_sha256']==job['input_manifest_sha256'],'input binding')
    cmd=binding['adapter_argv'];need(isinstance(cmd,list) and all(isinstance(x,str) for x in cmd) and cmd,'adapter command')
    for item in binding['file_pins']:
        need(file_sha(Path(item['path']))==item['sha256'],'adapter/binary source changed')
    need(binding['file_pins'],'no executable/script pin')
    need(type(binding['timeout_s']) in (int,float) and binding['timeout_s']>0,'host timeout')
    run_root.mkdir(parents=True,exist_ok=True);attempt=run_root/job['attempt_id']
    need(Path(job['attempt_id']).name==job['attempt_id'],'attempt path')
    ledger=Ledger(run_root/'ledger.sqlite',binding['limits'])
    try:
        ledger.reserve(job['attempt_id'],job['reservation']);attempt.mkdir(exist_ok=False)
        write_new(attempt/'job.json',job);write_new(attempt/'binding.json',binding)
        args=cmd+['--session-job',str((attempt/'job.json').resolve()),'--output-dir',str(attempt.resolve())]
        start=time.monotonic();code=None;status='FAILED'
        p=None
        try:
            with (attempt/'stdout.log').open('xb') as out,(attempt/'stderr.log').open('xb') as err:
                p=subprocess.Popen(args,stdout=out,stderr=err,cwd=binding['working_directory'],
                    start_new_session=os.name!='nt',creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0)
                try:code=p.wait(timeout=binding['timeout_s'])
                except subprocess.TimeoutExpired:kill_owned(p);code=p.wait();status='TIMEOUT'
            if code==0:
                receipt=read(attempt/'session-result.json')
                need(receipt['attempt_id']==job['attempt_id'] and receipt['binding_sha256']==digest(binding),'native result provenance mismatch')
                need(receipt['completed'] is True,'native session incomplete')
                actual=receipt['actual_work']
                for k in ('requests','token_rows','operators'):
                    need(type(actual[k]) is int and 0<=actual[k]<=job['reservation'][k],'work exceeds reservation')
                status='COMPLETE'
        finally:
            if p is not None:kill_owned(p)
            write_new(attempt/'launcher-receipt.json',{'status':status,'returncode':code,'wall_s':time.monotonic()-start,
                'attempt_id':job['attempt_id'],'native_origin_is_host_reported':True,'budget_released':False})
            ledger.finish(job['attempt_id'],status,code)
        need(status=='COMPLETE','session failed; retain attempt, diagnose; no silent retry or partial aggregate')
    finally:ledger.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('job',type=Path);p.add_argument('binding',type=Path);p.add_argument('run_root',type=Path);p.add_argument('--execute-native',action='store_true');a=p.parse_args()
    execute(a.job,a.binding,a.run_root,a.execute_native)
if __name__=='__main__':main()
