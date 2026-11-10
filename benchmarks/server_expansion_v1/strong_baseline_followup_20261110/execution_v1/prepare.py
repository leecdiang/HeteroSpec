"""S0 prospective complete job enumeration. No model/backend imports or calls."""
import argparse
from collections import Counter
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from inventory import inventory
from support import fresh,need,read,sha

TARGET_SHA='efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689'
WIDTHS=(1,3,4,7,20,30,31,32)


def operation(identity,kind,rows,**extra):
    return dict(operation_id=identity,kind=kind,reserved_rows=rows,**extra)


def expected_runtime(arm):
    return dict(schema='hs.strong.runtime.v1',arm=arm,n_ctx=1024,n_batch=1024,n_ubatch=32,
                output_reserve=32,outputs_per_seq=32,flash_attention=False,kv_K='f16',kv_V='f16',
                vocab=151936,layers=64,query_heads=64,kv_heads=8,head_k=128,head_v=128,GPU_layers=64,GPU_output=True,
                embedding_device_type='CPU',target_sha256=TARGET_SHA,draft=False,k=0,threads=2,
                lowering='WHOLE',native_planner='SIMPLE',cuda_graphs=False,greedy=True,
                requested_output_policy='PREFILL:last;VERIFY:all_original_rows')


def geometry(tokens):
    need(len(tokens)==1024 and all(type(t)is int and 0<=t<151936 for t in tokens),'Frozen synthetic capacity input')
    # Actual q32 first; before/at/after the 256/1024 physical extent boundaries.
    ends=(32,255,256,257,511,512,513,767,768,769,991,992,993,1023,1024);at=0;calls=[]
    for end in ends:
        while at<end:
            stop=min(at+32,end);calls.append(dict(ids=tokens[at:stop],phase='VERIFY',all=True));at=stop
    need(set(len(c['ids'])for c in calls)<=set(WIDTHS),'Unregistered actual width')
    return dict(name='synthetic-capacity1024-actual-q32-first',forced=calls,
                observe_positions=list(range(1,1025)),state_positions=list(ends),
                input_scope='synthetic repeated exposed token stream, correctness only')


def prepare(root,out,resume_configuration=None):
    out.mkdir();old=root/'q32-q4-full-20261109-01';model=root/'q32-models-01/Qwen3-32B-Q4_K_M.gguf'
    need(model.stat().st_size==19762149024 and sha(model)==TARGET_SHA,'Exact target model')
    inv=inventory(model);need(len(inv['classes'])==8,'Frozen eight type/shape classes')
    classes=[dict(class_id='class'+str(i),weight_name=c['first_tensor'],K=c['dimensions'][0],M=c['dimensions'][1],
                  type=c['type'],type_ggml='q4_K'if c['type']=='Q4_K'else'q6_K')for i,c in enumerate(inv['classes'])]
    oldcap=read(old/'closure-09/jobs/capacity1024-W_REF1L_M.json')['cases'][0]
    tokens=[t for c in oldcap['forced']for t in c['ids']];case=geometry(tokens)
    crossing=dict(name='crossing-extent-q4-W-split',forced=[dict(ids=tokens[:255],phase='PREFILL',all=False),
        dict(ids=tokens[255:259],phase='VERIFY',all=True)],observe_positions=list(range(255,260)),state_positions=[255,259])
    terminate=copy.deepcopy(read(old/'closure-09/jobs/EOG-cap-W_REF1L_M.json')['inputs'][0]['input'])
    ordinary=copy.deepcopy(read(old/'panel-01/jobs/r0-p0-W_REF1L_M.json')['inputs'][0]['input']);ordinary['cap']=4
    need(tokens[:32]==ordinary['prompt_ids'][:32],'Real captured prefix must match the exposed natural root333 prefix')
    prefix4=dict(name='actual-initial-prefix-q4',forced=[dict(ids=ordinary['prompt_ids'][:4],phase='VERIFY',all=True)],
                 observe_positions=[1,2,3,4],state_positions=[4])
    services=[]
    for cap in (1,2,3,4):
        one=copy.deepcopy(terminate);one['cap']=cap
        services.append(dict(id='termination-cap'+str(cap),input=one))
    services.append(dict(id='exposed-root333-cap4',input=ordinary))
    for s in services:
        need(1<=len(s['input']['prompt_ids'])<=192 and s['input']['cap']<=4,'S1 service bounds')
    services.append(dict(id='synthetic-capacity-M-pending',input=dict(id='synthetic/q32-strong-capacity-M-1023-cap1',
        domain='synthetic-correctness',prompt_ids=tokens[:1023],cap=1,family='Qwen32B',
        scope='Capacity/pending correctness only, never a natural performance sample')))
    workers=[]
    for repeat in range(2):
        name='R-geometry-'+str(repeat)
        workers.append(dict(worker_id=name,kind='pristine-model-geometry',
                            operations=[operation(name,'reference',1024),operation(name+'-crossing','reference',259),
                                        operation(name+'-prefix4','reference',4)],cases=[case,crossing,prefix4]))
    for repeat in range(2):
        name='R-services-'+str(repeat)
        workers.append(dict(worker_id=name,kind='pristine-model-services',
                            operations=[operation(name+'-'+s['id'],'reference',len(s['input']['prompt_ids'])+s['input']['cap'])for s in services]))
    for arm in 'GBC':
        name='model-geometry-'+arm
        workers.append(dict(worker_id=name,arm=arm,kind='candidate-model-geometry',
                            operations=[operation(name,'qualification',1024),operation(name+'-overflow','expected-negative',1),
                                        operation(name+'-crossing','qualification',259),operation(name+'-prefix4','qualification',4)],
                            capture_operands=arm=='G'))
    for c in classes:
        name='gold-'+c['class_id']
        workers.append(dict(worker_id=name,kind='pristine-scalar-gold',class_id=c['class_id'],
                            operations=[operation(name+'-q'+str(width)+'-col'+str(i),'gold',2,column=i,source_width=width,
                                        scalar_projection_rows=1,audit_quantizer_rows=1)for width in (32,4)for i in range(width)]))
    for c in classes:
        for q in WIDTHS:
            for arm in 'GBC':
                name='operand-'+c['class_id']+'-q'+str(q)+'-'+arm
                workers.append(dict(worker_id=name,kind='typed-operand-qualification',arm=arm,q=q,class_id=c['class_id'],
                                    capture_quantization=True,operations=[operation(name+'-'+str(i),'qualification',q)for i in range(2)]))
    for arm in 'GBC':
        name='model-services-'+arm
        workers.append(dict(worker_id=name,kind='candidate-model-services',arm=arm,
                    operations=[operation(name+'-'+s['id']+'-'+role,'qualification',len(s['input']['prompt_ids'])+s['input']['cap'])
                                for s in services for role in ('heavy','clean')]))
    negatives=('empty-K','q0','q33','wrong-type','wrong-stride','partial-output-mask','empty-operations')
    for kind in negatives:
        for arm in 'GBC':
            name='negative-'+kind+'-'+arm
            workers.append(dict(worker_id=name,kind='expected-native-negative',arm=arm,negative=kind,
                                operations=[operation(name,'expected-negative',0)],
                                zero_forward_basis='Descriptor/operation guards precede backend initialization'))
    # S2's four declared cells use the first legal tensor, never timing values.
    def order(c):
        name=c['weight_name'];return(int(name.split('.')[1]) if name.startswith('blk.') else 999,name)
    selected={typ:min((c for c in classes if c['type']==typ),key=order)for typ in ('Q4_K','Q6_K')}
    cells=[dict(slot=i,type=typ,q=q,class_id=selected[typ]['class_id'],weight_name=selected[typ]['weight_name'])
           for i,(typ,q)in enumerate((('Q4_K',4),('Q4_K',32),('Q6_K',4),('Q6_K',32)))]
    for cell in cells:
        for arm in 'GBC':
            name='clean-bridge-c'+str(cell['slot'])+'-'+arm
            workers.append(dict(worker_id=name,kind='clean-operand-bridge',arm=arm,cell=cell['slot'],
                class_id=cell['class_id'],q=cell['q'],capture_quantization=False,
                operations=[operation(name+'-'+str(i),'qualification',cell['q'])for i in range(2)]))
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location('sb217_design',Path(__file__).parent.parent/'design_checks.py')
    module=module_from_spec(spec);spec.loader.exec_module(module)
    for w in module.plan()['q32_diagnostic']:
        cell=cells[w['slot']]
        workers.append(dict(worker_id=w['id'],kind='S2-fixed-diagnostic',arm=w['arm'],cell=w['slot'],block=w['round'],
                q=cell['q'],class_id=cell['class_id'],capture_quantization=False,
                operations=[operation(op['id'],op['role'],cell['q'])for op in w['operations']]))
    ranks={'pristine-model-geometry':0,'pristine-model-services':1,'pristine-scalar-gold':3,
           'typed-operand-qualification':4,'candidate-model-services':6,'expected-native-negative':7,
           'clean-operand-bridge':8,'S2-fixed-diagnostic':9}
    workers.sort(key=lambda w:2 if w['kind']=='candidate-model-geometry' and w['arm']=='G' else
                 5 if w['kind']=='candidate-model-geometry' else ranks[w['kind']])
    ops=[op for w in workers for op in w['operations']];need(len(ops)==855 and len({op['operation_id']for op in ops})==855,'Exact prospective operation enumeration')
    ledger=old/'ledger.jsonl';inherited=read(old/'INHERITED_ACCOUNTING.json')
    rows=[json.loads(line)for line in ledger.read_text().splitlines()]
    reservations=[x for x in rows if x['event']=='RESERVE']
    old_requests=inherited['requests']+sum(x['requests']for x in reservations)
    old_rows=inherited['rows']+sum(x['rows']for x in reservations)
    need((old_requests,old_rows)==(514,652026),'Ledger has changed; re-audit, never reset')
    plan=dict(schema='hs.strong.prospective-manifest.v1',status='CPU_PREPARED_NOT_F0_NOT_GPU_ADMITTED',
         original_PR_head='c85b98636d5e0a7d9c367be8f3447b0799d12a78',graphs_policy='off_only',
         lowering_binding='WHOLE is the original W/SIMPLE planner; split at physical KV-extent boundaries, no LOCAL substitution',
         model=dict(bytes=19762149024,sha256=TARGET_SHA),classes=classes,widths=list(WIDTHS),
         geometry_case=case,extra_geometry_cases=[crossing,prefix4],services=services,S2_cells=cells,workers=workers,
         budget=dict(inherited_requests=old_requests,inherited_rows=old_rows,inherited_ledger_sha256=sha(ledger),
                     planned_logical_operations=len(ops),failure_closeout_reserve=16,
                     new_request_ceiling=len(ops)+16,cumulative_request_ceiling=old_requests+len(ops)+16,
                     new_reserved_rows=sum(op['reserved_rows']for op in ops)+16*1024,
                     cumulative_reserved_rows=old_rows+sum(op['reserved_rows']for op in ops)+16*1024,row_ceiling=2000000,
                     authority='User explicitly permits autonomous expansion beyond proposed 256, 2026-11-10'),
         optional_stages=dict(S3='AUTHORIZED_CONDITIONAL_REQUIRES_NEW_INPUT_FREEZE_AND_EXACT_BUDGET',
                              B2='AUTHORIZED_SECOND_PRIORITY_REQUIRES_SEPARATE_8B_LEDGER_AND_NEW_WINDOW',second_GPU='DEFER'),
         data_binding='R content is frozen first; first registered G real scalar columns are assembled in numeric column order; independent pristine gold before all operand qualification',
         stage_order=['repeated_R','R_content_freeze','G_geometry_and_real_input_capture','typed_pristine_gold',
                      'all_typed_operands','B_C_full_geometry','all_service_bridges','all_expected_negatives','all_clean_operand_bridges','S1_report','F1_public_readback','S2_fixed_order'],
         stop_policy='Stop at first unexpected qualification/resource/budget/source error; no automatic native retry',
         CPU_only=True,native_model_requests_started=0)
    need(plan['budget']['cumulative_reserved_rows']<=2000000,'Cumulative row budget')
    journal=root/'strong-baseline-followup-20261110/PR217_GLOBAL_LEDGER.jsonl'
    if resume_configuration:
        from resume import register_reference_reuse
        register_reference_reuse(plan,resume_configuration,journal)
    else:need(not journal.exists()or journal.stat().st_size==0,'Existing global journal requires explicit audited continuation')
    fresh(out/'MANIFEST.json',plan);fresh(out/'DESCRIPTOR_INVENTORY.json',inv)
    fresh(out/'BUDGET_SUMMARY.json',dict(plan['budget'],workers=len(workers),operation_kinds=dict(Counter(op['kind']for op in ops))))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--resume-configuration',type=Path)
    a=p.parse_args();need(not a.out.exists(),'Fresh prospective registration');prepare(a.root,a.out,a.resume_configuration)


if __name__=='__main__':main()
