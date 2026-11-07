"""Freeze a new seven-host diagnostic, without executing it or querying a device."""
import datetime
import hashlib
import pathlib
import sys
import zipfile

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'));sys.path.insert(0,str(ROOT))
from common import load,save,sha,modules
import core


def main():
    before=modules()
    old=(ROOT/'host/run_s1.py').read_text(encoding='utf-8')
    start=old.index('def child(');end=old.index('\ndef main():')
    child=old[start:end].replace('now-start>180','now-start>60').replace('now-start+owned>3600','now-start+owned>420').replace('total>2*1024**3','total>128*1024**2')
    child=child.replace('(used or 0)>8*1024**3','(used is None or used>8*1024**3)')
    child=child.replace('payload[0]=bytes(32)+payload[0]',"payload[0]=bytes(request['q_offset_bytes'])+payload[0]")
    needle="        identities=[]"
    child=child.replace(needle,"""        if request['relocate_pq_mask'] and request['mode']=='PQ' and q>1:
            mask_bytes=payload[3]
            payload.extend(mask_bytes[j*n*4:(j+1)*n*4] for j in range(q))
"""+needle)
    preamble='''"""Frozen child supervisor adapted from original S1. Import only; no launch on import."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
import subprocess,time,shutil,hashlib,struct
from common import ROOT,save,sha
from run_s0 import rss
from run_s1 import runtime_gate,available_ram,read_events
sys.path.insert(0,str(ROOT))
import core
'''
    (HERE/'generated/diagnostic_child.py').write_text(preamble+child,encoding='utf-8',newline='\n')
    inputs=load(ROOT/'host/S1_INPUTS.json')
    def operand(q,n,hk):return next(x for x in inputs if x['cell']['geometry']['q']==q and x['cell']['geometry']['n']==n and x['cell']['geometry']['hk']==hk)
    specifications=[
        (1,63,8,'MQ',32,False,'historical-layout-instrumented-diagnostic'),
        (1,63,8,'MQ',0,False,'common-q1-Q-storage-origin-control'),
        (2,63,2,'PQ',0,False,'isolate-original-PQ-mask-slice'),
        (2,63,2,'PQ',0,True,'PQ-independent-mask-storage'),
        (2,63,2,'QH_C',0,False,'QH-compact-mask-same-q2-operand'),
        (2,257,2,'PQ',0,True,'PQ-odd-length257-mask-storage'),
        (2,257,2,'QH_C',0,False,'QH-compact-mask-length257')]
    slots=[]
    for i,(q,n,hk,mode,offset,relocate,purpose) in enumerate(specifications):
        data=operand(q,n,hk)
        slot=dict(study='b570-query-head-alignment-diagnostic-v1',index=i,cell=data['cell'],input=data['path'],input_sha256=data['sha256'],
                  mode=mode,q_offset_bytes=offset,relocate_pq_mask=relocate,purpose=purpose)
        slot['id']=core.sha(slot);slots.append(slot)
    save(HERE/'DIAGNOSTIC_PLAN.json',dict(slots=slots,capability_only_processes=0,extra_probes=0,warmups=0,retries=0,
         note='Every support/alignment observation belongs to a charged graph host. No original S1 coordinate resumes.'))
    runtime=ROOT/'host_outputs/alignment_review_v1/build/Release'
    files=[runtime/'alignment-metadata.exe',runtime/'alignment-diagnostic.exe']
    with zipfile.ZipFile(HERE/'CPU_AND_UNLAUNCHED_DIAGNOSTIC_BINARIES.zip','x',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(f,f.name)
    with zipfile.ZipFile(HERE/'CPU_AND_UNLAUNCHED_DIAGNOSTIC_BINARIES.zip') as z:
        for f in files:assert hashlib.sha256(z.read(f.name)).hexdigest()==sha(f)
    save(HERE/'BINARY_MANIFEST.json',dict(files=[dict(path=str(f),sha256=sha(f),bytes=f.stat().st_size) for f in files],
         archive_sha256=sha(HERE/'CPU_AND_UNLAUNCHED_DIAGNOSTIC_BINARIES.zip'),all_archived_bytes_rehashed=True,
         diagnostic_launched=False))
    prior=load(ROOT/'host/S1_F0.json')
    sources={str(f.relative_to(ROOT)).replace('\\','/'):sha(f) for f in HERE.rglob('*') if f.is_file() and f.suffix in ('.py','.cpp','.hpp','.txt') and '__pycache__' not in str(f)}
    for name in ('native/query_head.h','native/host/oracle.hpp','host/common.py','host/run_s0.py','host/run_s1.py','host/inputs.py','core.py','plan.py','oracle.py','evidence.py'):
        sources[name]=sha(ROOT/name)
    f0=dict(study='b570-query-head-alignment-diagnostic-v1',status='AWAITING_EXPLICIT_AUTHOR_APPROVAL_NOT_STARTED',
         reviewed_commit='27cfad39cbffcac413760900c6deedbb93bdfc78',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         supersedes_original_S1=False,original_S1_F0_sha256=sha(ROOT/'host/S1_F0.json'),original_S1_result_sha256=sha(ROOT/'host/S1_RESULT.json'),
         plan_sha256=sha(HERE/'DIAGNOSTIC_PLAN.json'),sources=sources,
         executable=dict(path=str(runtime/'alignment-diagnostic.exe'),sha256=sha(runtime/'alignment-diagnostic.exe')),
         dependencies=[dict(path=str(runtime/name),sha256=sha(runtime/name)) for name in ('ggml-base.dll','ggml-vulkan.dll')],
         driver_files=prior['driver_files'],environment=prior['environment'],
         limits=dict(graph_host_attempts=7,graph_computes_at_most=7,owned_seconds=420,per_host_seconds=60,output_bytes=128*1024**2,
                     worker_RSS_bytes=8*1024**3,host_available_bytes=8*1024**3,disk_free_bytes=4*1024**3,
                     nominal_sample_ms=100,maximum_actual_sample_gap_ms=1000,GPU_checkpoint_minimum_free_bytes=512*1024**2,
                     continuous_GPU_residency=False,model_requests=0,warmups=0,retries=0,extra_probes=0),
         admission='Exact F0 SHA author confirmation required; sources/runtime/environment/inputs rehashed before any launch.',
         stop_rules='Unexpected failure or nonfinite/placement/input identity violation stops all later slots. Only slots0/2 have narrowly declared expected assertion outcomes; both positive q1 completion and expected-negative audit gate precede q2 candidates. No automatic S2/S3.',
         performance_claims=False,device_alignment=None,physical_offsets=None,model_requests=0,modules_before=before,modules_after=modules())
    save(HERE/'DIAGNOSTIC_F0.json',f0)
    print(dict(F0_sha256=sha(HERE/'DIAGNOSTIC_F0.json'),attempts=7,owned_seconds=420,started=0))


if __name__=='__main__':main()
