"""Actual C1024 all-tensor/KV GPU admission, with zero token forwards.

Numerical qualification and independent14B references are intentionally separate
later gates. No M1/8B R is reused as a14B oracle.
"""
from pathlib import Path
import argparse, json, sys, time

def main():
    p=argparse.ArgumentParser()
    for key in ('baseline','supervisor','build','work','target','draft'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(a.supervisor.resolve()));from common import need,read,save,sha
    import admission_host as host
    w=a.work.resolve();need(not w.exists(),'Fresh admission output epoch');w.mkdir(parents=True)
    spec=read(Path(__file__).parent/'models.json');cfg=read(a.baseline/'config-reference-frozen-01.json')
    cfg.update(work_root=str(w),reference_freeze=None,reference_freeze_sha256=None,freeze=None,freeze_sha256=None)
    save(w/'config.private.json',cfg);host.inspect(w/'inventory.private.json')
    save(w/'PREFLIGHT.json',dict(study_head='a44f58fc40fdab1220434569fa86f65dfd4c56a8',qualified_linux_successor='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',
        completed_M1_result='https://github.com/leecdiang/HeteroSpec/pull/204',model_manifest_sha256=sha(Path(__file__).parent/'models.json'),
        inherited_ledger_sha256=sha(a.baseline/'ledger.jsonl'),M1_ledger_sha256=sha(a.baseline.parent/'m1-run-01/ledger.jsonl'),
        GPU_allocation_inherited=True,model_forwards_permitted=0,R14B_C1024='NOT_FROZEN_NO_CANDIDATE_OUTPUTS',C4096='NOT_RUN'))
    need(a.target.stat().st_size==spec['target']['bytes'] and a.draft.stat().st_size==spec['draft']['bytes'],'Exact declared file sizes')
    job=dict(family='Qwen14B',target_model=str(a.target.resolve()),target_sha256=spec['target']['sha256'],draft_model=str(a.draft.resolve()),draft_sha256=spec['draft']['sha256'],
        n_ctx=1024,threads=2,target_ubatch=32,draft_ubatch=4,target_outputs=4,draft_outputs=1,zero_forward=True,inputs=[],placement='all_model_tensors_and_KV_on_one_GPU_v1')
    save(w/'JOB.json',job);started=time.monotonic();host.run(w/'config.private.json',a.build/'BUILD.json',w/'JOB.json',w/'native-01','admission');elapsed=time.monotonic()-started
    r=read(w/'native-01/native/result.json');need(r['status']=='ZERO_FORWARD_ADMISSION_PASS' and r['model_forwards']==r['token_rows']==r['trajectories']==0,'True zero-forward result')
    for role in ('target','draft'):
        need(r[role+'_model']['all_model_tensors_on_selected_GPU'] and r[role+'_context']['all_K_and_V_buffers_on_selected_GPU'],'All actual weights/KV on selected GPU')
        need(r[role+'_context']['n_ctx']==1024 and r[role+'_context']['active_prefix_tokens']==0,'Actual capacity distinct from empty prefix')
    telemetry=[json.loads(x) for x in (w/'native-01/resources.jsonl').read_text().splitlines()];need(telemetry,'Actual memory samples')
    summary=dict(status='ZERO_FORWARD_C1024_ADMISSION_PASS',model_forwards=0,token_rows=0,all_target_draft_weights_and_KV_on_one_GPU=True,
        context_capacity=1024,active_prefix_tokens=0,minimum_sampled_free_bytes=min(float(x['gpu']['memory.free'])*1024**2 for x in telemetry),
        maximum_sampled_total_minus_free_bytes=max((float(x['gpu']['memory.total'])-float(x['gpu']['memory.free']))*1024**2 for x in telemetry),
        memory_quantity_scope='Total-minus-free includes driver-reserved/unavailable memory; not NVML memory.used or per-process high water',
        safety_reserve_bytes=cfg['gpu_reserve_bytes'],native_receipt_sha256=sha(w/'native-01/native/result.json'),loaded_module_map_sha256=sha(w/'native-01/LOADED_MODULES.json'),
        build_receipt_sha256=sha(a.build/'BUILD.json'),full_supervisor_invocation_s=elapsed,numerical_qualification='NOT_RUN',R14B_C1024='NOT_FROZEN',
        full_model_confirmation='NOT_STARTED',C4096='NOT_RUN',scope='Actual zero-forward load/context placement admission only; does not establish forward workspace peaks, numerical equivalence or speed')
    need(summary['minimum_sampled_free_bytes']>=cfg['gpu_reserve_bytes'],'Original safety reserve retained');save(w/'ADMISSION.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
