"""Complete S3 prospective jobs: all requests are registered before new R output."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent/'execution_v1'))
from build_service import need,read,save,sha
from prepare import TARGET_SHA,expected_runtime
from materialize import model_job


def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def construct(roots,previous_manifest,model_path):
    need(len(roots['inputs'])==12 and roots['generated_outputs_seen']is False,'Prospective twelve roots')
    inputs=[]
    for slot,x in enumerate(roots['inputs']):
        need(x['slot']==slot and x['domain']==('code'if slot<6 else'math')and x['cap']==128,'Six/code six/math fixed slot order')
        need(1<=len(x['prompt_ids'])<=192,'Untruncated natural input ceiling')
        inputs.append({k:x[k]for k in ('id','domain','prompt_ids','cap')}|dict(family='Qwen32B'))
    workers=[]
    def add(name,kind,stage,items,arm=None,slot=None,block=None):
        w=dict(worker_id='s3-v1-'+name,kind=kind,stage=stage,operations=[])
        if arm:w['arm']=arm
        if slot is not None:w['slot']=slot
        if block is not None:w['block']=block
        j=dict(family='Qwen32B',target_model=str(model_path),target_sha256=TARGET_SHA,n_ctx=1024,threads=2,draft=False,residency='target_only',inputs=items)
        if arm:j.update(arm=arm,n_ubatch=32,output_reserve=32,kv='F16',flash_attention=False,cuda_graphs=False,
             lowering='WHOLE',draft_width=1,profile=False,k=0,target_output_reserve=32,proposal_mode='live',capability_request=expected_runtime(arm))
        for ordinal,item in enumerate(items):
            rows=len(item['input']['prompt_ids'])+item['input']['cap']
            w['operations'].append(dict(operation_id=w['worker_id']+':'+item['name'],kind=item['role'],reserved_rows=rows,
                row_formula='prompt_tokens + cap; target-only M actual rows <= prompt + cap -1',ordinal=ordinal))
        # role is scheduling metadata, ignored nowhere: the actual native job
        # carries only its documented entry fields. Roles stay in the manifest.
        native=dict(j,inputs=[{k:v for k,v in x.items()if k!='role'}for x in items])
        w.update(job='jobs/'+w['worker_id']+'.json',job_sha256=hashlib.sha256(canonical(native)).hexdigest())
        workers.append(w);return native
    jobs={}
    def register(*args,**kwargs):
        j=add(*args,**kwargs);jobs[workers[-1]['job']]=j
    for slot,x in enumerate(inputs):
        for repeat in range(2):
            item=dict(name=f'new-root{slot:02d}',input=x,capture=True,state_positions=list(range(len(x['prompt_ids']),len(x['prompt_ids'])+128)),role='reference')
            register(f'R-root{slot:02d}-repeat{repeat}','pristine-model-services','qualification',[item],slot=slot,block=repeat)
    # Requalify the changed request frontend on all six previously frozen
    # EOG/cap/reset/capacity-pending fixtures, in addition to the new12 roots.
    for arm in 'GBC':
        entries=[]
        for service in previous_manifest['services']:
            for role in ('heavy','clean'):
                entries.append(dict(name=service['id']+'-'+role,input=service['input'],capture=role=='heavy',role='qualification'))
        register('frontend-boundaries-'+arm,'frontend-boundary-bridge','qualification',entries,arm=arm)
    for slot,x in enumerate(inputs):
        for arm in 'GBC':
            heavy=dict(name=f'new-root{slot:02d}-heavy',input=x,capture=True,role='qualification')
            if slot==0:
                register(f'bridge-root{slot:02d}-{arm}-heavy','new-root-heavy-only','qualification',[heavy],arm=arm,slot=slot)
                # Exactly one predetermined root per arm supplies a full fresh
                # model-load + two-clean-request caller calibration. Its first
                # clean is a full warm, not a free setup invocation.
                entries=[dict(name=f'new-root{slot:02d}-clean-{i}',input=x,capture=False,role='qualification-calibration')for i in range(2)]
                register(f'calibrate-root{slot:02d}-{arm}','new-root-clean-pair-calibration','qualification',entries,arm=arm,slot=slot)
            else:
                clean=dict(name=f'new-root{slot:02d}-clean',input=x,capture=False,role='qualification')
                register(f'bridge-root{slot:02d}-{arm}','new-root-heavy-clean','qualification',[heavy,clean],arm=arm,slot=slot)
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location('_S3_design',Path(__file__).resolve().parent.parent/'design_checks.py');design=module_from_spec(spec);spec.loader.exec_module(design)
    for w in design.plan()['q32_panel']:
        x=inputs[w['slot']];entries=[dict(name=role,input=x,capture=False,role=role)for role in ('warm','measured')]
        register(w['id'],'S3-formal-full-service','formal',entries,arm=w['arm'],slot=w['slot'],block=w['round'])
    count=sum(len(w['operations'])for w in workers);rows=sum(op['reserved_rows']for w in workers for op in w['operations'])
    need(count==423 and len(workers)==210,'Exact24R +36old bridge +75new bridge/calibration +288formal')
    return dict(schema='hs.strong.S3.complete-plan.v1',workers=workers,planned_requests=count,planned_reserved_rows=rows,
         R_requests=24,old_frontend_bridge_requests=36,new_root_bridge_and_calibration_requests=75,
         warmups=144,measurements=144,formal_workers=144,qualification_workers=66,
         failure_reserve=16,approved_phase_request_ceiling=439,operation_prefix='s3-v1-',
         callback_and_numerical_policy='Unchanged qualified numerical archives and scalar reference; changed shared frontend requalified',
         same_two_request_fresh_process_cost_calibration_root_slot=0,
         formal_estimand='Reset-inclusive complete resident target-only M service; primary C/B, root-level stratified bootstrap'),jobs


def main(roots_path,previous_manifest_path,model_path,out):
    need(not out.exists(),'Fresh prospective job directory');out.mkdir(parents=True)
    plan,jobs=construct(read(roots_path),read(previous_manifest_path),model_path)
    for relative,value in jobs.items():
        target=out/relative;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb')as f:f.write(canonical(value))
    save(out/'MANIFEST.json',plan)
    save(out/'PLAN_PROVENANCE.json',dict(roots_sha256=sha(roots_path),old_manifest_sha256=sha(previous_manifest_path),
         jobs_generated_before_any_new_root_model_output=True,no_runtime_input_selection=True,
         budget_expansion_authority='Explicit user:256 insufficient may expand; latest user approves B2 and conditional S3. Original384 S3 proposal preserved;439 now required by exact extra checks/calibration/failure reserve.'))
    print(json.dumps({k:v for k,v in plan.items()if k!='workers'}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('roots','previous-manifest','model','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();main(a.roots,a.previous_manifest,a.model,a.out)
