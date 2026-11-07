"""Reuse actual PR156 local assets to prepare successor configs. No model is launched.
Run on the original Windows host; only reads the old bundle and writes a fresh config directory.
"""
from __future__ import annotations
import argparse,os,subprocess
from pathlib import Path
from common import *

def bootstrap(repo,parent,research,out,roles=0,total_seconds=21600,worker_seconds=3600,source_archive=None):
    repo=Path(repo).resolve();parent=Path(parent).resolve();research=Path(research).resolve();out=Path(out).resolve()
    need(not out.exists(),'fresh config directory required')
    local=read(parent/'LOCAL_PATHS.json');old=read(parent/'BINDING.json');assets=local['assets']
    # Source-runner asset names are explicit; do not search another model by filename.
    required=('target','draft','worker')
    need(all(n in assets for n in required),'old LOCAL_PATHS missing target/draft/worker')
    worker=Path(assets['worker']).resolve();buildfile=Path(assets.get('build_receipt',worker.parent.parent/'BUILD.json'))
    need(buildfile.is_file(),'old BUILD.json not adjacent to bin; set configs manually from real receipt')
    build=read(buildfile);need(file_hash(worker)==old['families']['Qwen']['executable_sha256'],'original worker identity')
    archive=source_archive or assets.get('source_archive') or assets.get('archive')
    if archive is None:
        candidate=read(parent/'CONFIG.json') if (parent/'CONFIG.json').exists() else {}
        archive=candidate.get('source_archive') or candidate.get('archive')
    need(archive is not None and Path(archive).is_file(),'source archive location unavailable; use BUILD_CONFIG example and recorded SHA')
    need(file_hash(archive)==build['source_zip_sha256'],'source archive identity')
    q=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=30)
    devices=[line.split(',') for line in q.stdout.strip().splitlines()]
    matched=[r for r in devices if len(r)==3 and '5070' in r[1]];need(len(matched)==1,'ambiguous RTX device')
    need(type(roles) is int and 0<=roles<=7,'operator roles')
    need(positive(worker_seconds)<=positive(total_seconds),'resource budget')
    out.mkdir(parents=True)
    for name in ('calibration.json','selected_panel.json'):
        (out/name).write_bytes(git_read(repo,BASE,'benchmarks/rtx_dense14b_transfer_v1/host_execution/'+name))
    newbuild=out/'build'
    save(out/'BUILD_CONFIG.json',{'repo':str(repo),'out':str(newbuild),'parent_build':str(buildfile),
        'source_archive':str(Path(archive).resolve()),'dll_dir':str(worker.parent),'rowwise_roles':roles,
        'jobs':4,'command_timeout':3600},exclusive=True)
    save(out/'POLICY.json',{'prefill':'reference','rowwise_roles':roles,'mechanism':'canonical UB1 producer; selected operator repair requires diagnostic evidence','revision':'dev01'},exclusive=True)
    save(out/'HOST_CONFIG.json',{'user_authorized':True,'repo':str(repo),'parent_root':str(parent),
        'research_root':str(research),'target':str(assets['target']),'draft':str(assets['draft']),
        'original_worker':str(worker),'worker':str(newbuild/'bin/rtx-scope-transfer.exe'),
        'build_receipt':str(newbuild/'BUILD.json'),'development_panel':str(out/'calibration.json'),
        'heldout_panel':str(out/'selected_panel.json'),'policy':str(out/'POLICY.json'),
        'gpu_uuid':matched[0][0].strip(),'gpu_driver':matched[0][2].strip(),
        'gpu_lock_file':read(parent/'CONFIG.json')['gpu_lock_file'],
        'resources':{'worker_timeout_seconds':worker_seconds,'total_native_seconds':total_seconds,
          'min_ram_free_bytes':8*1024**3,'min_vram_free_bytes':1024**3,'min_disk_free_bytes':20*1024**3,
          'max_payload_bytes':64*1024**3}},exclusive=True)
    save(out/'PREPARATION_RECEIPT.json',{'status':'CONFIGS_CREATED_NOT_BUILT_OR_EXECUTED','base':BASE,
      'old_worker_sha256':file_hash(worker),'gpu_inventory':q.stdout.strip(),'native_requests':0,
      'note':'Budget values are safety ceilings, not runtime estimates; coordinate the GPU lock path with all existing host agents.'},exclusive=True)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','parent','research','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-archive',type=Path);p.add_argument('--roles',type=int,default=0);p.add_argument('--total-seconds',type=float,default=21600)
    p.add_argument('--worker-seconds',type=float,default=3600);a=p.parse_args()
    print(bootstrap(a.repo,a.parent,a.research,a.out,a.roles,a.total_seconds,a.worker_seconds,a.source_archive))
