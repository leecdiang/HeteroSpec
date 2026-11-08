"""Finite q4/reserve8 bridge, real q8 transactions, geometry and branch gates."""
from pathlib import Path
import copy,json
import harness as h

def dispatch_gate(proof,core,cut,k):
    d=proof['dispatch'];hist=d['verify_physical_width_histogram']
    if hist and cut=='LOCAL':h.need(set(hist)=={str(k+1)},'LOCAL must retain actual physical k+1, never globally split q8')
    if hist:h.need(d['quantized_verify_nodes']>0,'Actual quantized GPU verification projection descriptors required')
    if hist and core=='loop4' and any(int(z)>4 for z in hist):h.need(d['marked_loop4_verify_nodes']>0,'Actual wide loop4 projection marker required')
    if hist and core=='packed' and k==7 and cut=='LOCAL':h.need(d['packed_verify_nodes']>0,'Actual q8 packing dispatch missing')
    if k==3:h.need(d['packed_verify_nodes']==0 and d['q4_plain_projection_shapes'],'Physical q4 negative control must use ordinary <=4-column projections; no wide packing')

def qualification(s):
    read,save,sha,need=h.read,h.save,h.sha,h.need
    roots=read(s.baseline/'inputs-01/Qwen-DEVELOPMENT.json')['inputs']
    # One previously registered semantic fixture, new8B autonomous R. No14B
    # output/reference is used as an8B oracle; this is not a performance root.
    fixture_source=s.root/'d14-source-07/D14/EOG_FIXTURE_V1.json'
    eog=copy.deepcopy(read(fixture_source)['inputs'][0]);eog.update(family='Qwen',id='M2/Qwen8B/termination-fixture-v1')
    save(s.out/'EOG_FIXTURE_REGISTERED.json',dict(input=eog,borrowed_prompt_source_sha256=sha(fixture_source),
        target_sha256=s.models['Qwen']['target_sha256'],selection='Fixed registered instruction before its own8B outcomes; no forced literal answer; finite termination diagnostic only'))
    r=s.execute('Qwen8B-EOG-free-R','Qwen',{'inputs':[dict(name='eog',input=eog,capture=True)]})
    ep=read(r/'native/eog/receipt.json');need(ep['terminal_kind']=='EOG' and len(ep['ids'])>1,'Actual8B EOG inside a later verification required')
    s.custom_reference[('Qwen',4)]=r/'native/eog'
    save(s.out/'EOG_R_CHECKED.json',dict(passed=True,ids=ep['ids'],eog=ep['eog'],receipt_sha256=sha(r/'native/eog/receipt.json'),
        actual_target_sha256=s.models['Qwen']['target_sha256'],scope='Autonomous unchanged pristine8B R; qualification fixture, not benchmark'))
    natural=[]
    for arm,(core,cut,k) in h.ARMS.items():
        arm_rows=[]
        for index,original in enumerate(roots+[eog]):
            x=copy.deepcopy(original)
            # Full CAP128 on first short root; fixed short/long/tail roots CAP32;
            # separate genuine EOG at cap128 and explicit cap1 for every arm.
            if index in (1,2,3):x['cap']=32
            inputs=[dict(name='heavy',input=x,capture=True),dict(name='clean',input=x,capture=False)]
            if index==0:
                cap1={**x,'cap':1};inputs.extend([dict(name='cap1-heavy',input=cap1,capture=True),dict(name='cap1-clean',input=cap1,capture=False)])
            actual=s.execute('natural-'+arm+'-root'+str(index),'Qwen',dict(inputs=inputs,lowering=cut),core,k)
            proof=s.check_pair('Qwen',index,x,actual,'heavy','clean');dispatch_gate(proof,core,cut,k);arm_rows.append(proof)
            if index==0:arm_rows.append(s.check_pair('Qwen',0,cap1,actual,'cap1-heavy','cap1-clean'))
            save(s.out/('natural-'+arm+'-root'+str(index)+'-CHECKED.json'),dict(passed=True,arm=arm,k=k,reserve=8,input=x,proof=proof,
                cap1=arm_rows[-1] if index==0 else None))
            print('M2_NATURAL_PASS',arm,index,flush=True)
        path=s.out/(arm+'-NATURAL-CHECKED.json');save(path,dict(passed=True,arm=arm,roots=arm_rows));natural.append(path)
        if k==3:
            old=s.root/'m1-run-01/qualification-01/NATIVE_CHECKS_COMPLETE.json';need(read(old)['passed'],'Qualified original k3/reserve4 baseline required')
            save(s.out/(arm+'-RESERVE8-BRIDGE.json'),dict(passed=True,k=3,new_output_reserve=8,original_output_reserve=4,
                original_M1_qualification_sha256=sha(old),unchanged_R_freeze_sha256=sha(s.baseline/'reference-01/REFERENCE_FREEZE.json'),
                new_natural_proof_sha256=sha(path),basis='Full requested vectors, active KV/frontier and complete transactions match original independent R; original reserve4 files and timings unchanged'))
    geometry(s,roots[0])
    controls=[]
    # Owned R-derived mechanism counterexamples: each rejection rank, cap during
    # acceptance, all-accepted bonus, cap1. They are never performance samples.
    free=s.retained('Qwen-free-independent-R')/'native/dev-0';oracle=read(free/'receipt.json')
    for arm,(core,cut,k) in h.ARMS.items():
        cases=[];vocab=s.structures['Qwen']['target']['vocab']
        for j in range(k):cases.append(('reject-'+str(j),j+2,j))
        for cap in range(2,k+2):cases.append(('cap-'+str(cap),cap,None))
        cases.extend([('bonus',k+2,None),('cap1',1,None)])
        inputs=[];lookup={}
        for name,cap,reject in cases:
            x={**roots[0],'cap':cap};proposals=oracle['ids'][1:8];need(len(proposals)==7,'Frozen independent greedy fixture continuation')
            if reject is not None:proposals[reject]=(proposals[reject]+1)%vocab
            tape=dict(schema='heterospec.m2.R-derived-boundary-fixture.v1',root=x['id'],prompt_ids=x['prompt_ids'],max_k=7,
                target_sha256=s.models['Qwen']['target_sha256'],draft_sha256=s.models['Qwen']['draft_sha256'],
                autonomous_R_receipt_sha256=sha(free/'receipt.json'),rows=[dict(base=len(x['prompt_ids']),seed=oracle['ids'][0],proposals=proposals)],
                fixture='Independent greedy continuation plus one structurally mismatching proposal for rejection tests; no implementation token exception')
            x.update(proposal_tape=tape,proposal_tape_sha256=h.canonical(tape));lookup[name]=(x,reject)
            for kind in ('heavy','clean'):inputs.append(dict(name=name+'-'+kind,input=x,capture=kind=='heavy'))
        actual=s.execute('boundaries-'+arm,'Qwen',dict(inputs=inputs,lowering=cut),core,k,'replay');rows=[]
        for name,cap,reject in cases:
            x,_=lookup[name];proof=s.check_pair('Qwen',0,x,actual,name+'-heavy',name+'-clean');dispatch_gate(proof,core,cut,k)
            receipt=read(actual/'native'/(name+'-heavy')/'receipt.json')
            if reject is not None:need(len(receipt['cycles'])==1 and receipt['cycles'][0]['rejected'] and receipt['cycles'][0]['accepted']==reject,'Requested correction/rollback boundary not executed')
            if name=='bonus':need(len(receipt['cycles'])==1 and receipt['cycles'][0]['commit_kind']=='bonus' and receipt['cycles'][0]['accepted']==k,'Actual all-accepted bonus not executed')
            if name=='cap1':need(not receipt['cycles'],'cap1 must not materialize pending output')
            if name.startswith('cap-'):need(receipt['cycles'][0]['commit_kind']=='accepted' and receipt['length']==cap,'Cap during accepted suffix not executed')
            rows.append(dict(case=name,requested_rejection_rank=reject,proof=proof))
        path=s.out/(arm+'-BOUNDARIES-CHECKED.json');save(path,dict(passed=True,arm=arm,mode='target replay qualification, zero drafting',cases=rows));controls.append(path)
        print('M2_BOUNDARIES_PASS',arm,flush=True)
    negatives(s)
    proofs=natural+controls+[s.out/'GEOMETRY-CHECKED.json',s.out/'NATIVE_NEGATIVES-CHECKED.json',s.out/'EOG_R_CHECKED.json']
    need(len(natural)==len(controls)==8,'All eight arm qualifications required')
    summary=s.out/'NATIVE_CHECKS_COMPLETE.json';save(summary,dict(passed=True,finite_only=True,all_eight_k_cut_projection_arms=True,
        k3_reserve8_bridge=True,common_candidate_reserve=8,scalar_R_unchanged=True,actual_Qwen8B_EOG=True,
        complete_vectors_active_KV_frontier_pending_rollback_cap=True,all_rejection_ranks_and_bonus=True,
        physical_q8_and_actual_packing_dispatch=True,controlled_proposal_replay_and_live_separate=True,
        original_requested_outputs_compared=True,original_generation_policy_including_extra_work_near_cap_retained=True,
        boundary_scope='All rejection ranks, cap-during-accept and bonus are controlled target-replay fixtures; live full-state checks cover observed native ranks, with exact coverage retained',
        proofs=[dict(path=str(p),sha256=sha(p))for p in proofs],historical_operands_reverified=len(s.verified)))
    kinds={'source_freeze','whole_prompt_producer','full_requested_logits','active_KV','frontier','pending','rollback','cap','native_EOG','clean_no_state_transfer','physical_work','actual_module_map','all_fixed_controls'}
    registry=dict(contract_checks=dict(linux_reference_precedes_candidate_outputs=True),checks={z:dict(passed=True,evidence=str(summary))for z in kinds},
        executables=[dict(build=str(s.builds/core/'BUILD.json'),loaded_modules=str(s.modules[(core,'Qwen')]))for core in ('loop4','packed')])
    registry['checks']['source_freeze']['evidence']=str(s.w/'SOURCE_FREEZE.json');save(s.out/'REGISTRY.json',registry)
    print('M2_BASE_NATIVE_GATES_PASS_AWAITING_OWNED_TAPE_BRIDGE',flush=True)

def geometry(s,root):
    read,save,sha,need=h.read,h.save,h.sha,h.need
    free=s.retained('Qwen-free-independent-R')/'native/dev-0';ep=read(free/'receipt.json');owned=root['prompt_ids']+ep['ids'];cases=[]
    for width in (4,8):
        for p in (31,32,99,127,128):
            cases.append(dict(name=f'p{p}-q{width}',forced=[dict(ids=owned[:p],phase='PREFILL',all=False),dict(ids=owned[p:p+width],phase='VERIFY',all=True)],
                observe_positions=[p]+list(range(p+1,p+width+1)),state_positions=[p,p+width]))
    ref=s.execute('geometry-R','Qwen',dict(cases=cases));reports=[]
    for arm,(core,cut,k) in h.ARMS.items():
        selected=[x for x in cases if x['name'].endswith('-q'+str(k+1))]
        actual=s.execute('geometry-'+arm,'Qwen',dict(cases=selected,lowering=cut),core,k);meta=read(actual/'native/result.json');rows=[];packed_count=loop_count=0
        for i,c in enumerate(selected):
            vectors=[];states=[];native=meta['cases'][i]
            verify=[x for x in native['executions']if x['phase']=='VERIFY'];need(sum(x['width']for x in verify)==k+1,'Forced actual verification width')
            need(sorted(j for x in verify for j in x['requested_rows'])==list(range(k+1)),'Forced requested row mask ownership')
            for n in c['observe_positions']:
                aa=actual/'native'/c['name']/'captures'/str(n);bb=ref/'native'/c['name']/'captures'/str(n)
                pair=h.checks.vector_pair(aa/'frontier.f32',bb/'frontier.f32',meta['vocab']);need(pair['equal'],'Forced full vector mismatch');vectors.append(pair)
                if n in c['state_positions']:
                    pair=h.checks.state_pair(aa/'sequence.bin',bb/'sequence.bin',n,h.parse,s.profiles['Qwen']);need(pair['equal'],'Forced active KV mismatch');states.append(pair)
            graph=[x for x in native['geometry']if x['phase']=='VERIFY' and x['op']=='MUL_MAT']
            packed=[x for x in graph if x['name'].startswith('frontier_packed_')];loop=[x for x in graph if x['name'].startswith('hs_backend_loop4_')]
            if k==3:need(not packed,'q4 wide-packing negative control')
            if cut=='LOCAL':need(len(verify)==1 and verify[0]['width']==k+1,'LOCAL actual q8 must not be split')
            if k==7 and core=='packed' and (cut=='LOCAL' or c['name'].startswith(('p32-','p128-'))):need(packed,'Actual eligible q8 packing dispatch')
            if packed:need(all(z['ne'][1]==4 and z['ne'][2]==2 and z['sources'][0]['type']=='q8_0' and z['sources'][1]['type']=='f32' for z in packed),'Actual two independent four-column packed groups')
            packed_count+=len(packed);loop_count+=len(loop)
            rows.append(dict(case=c['name'],full_vectors=vectors,active_states=states,actual_verify_executions=verify,packed_nodes=len(packed),loop4_nodes=len(loop),packed_samples=packed[:2]))
        reports.append(dict(arm=arm,rows=rows,packed_nodes=packed_count,marked_loop4_nodes=loop_count,native_result_sha256=sha(actual/'native/result.json')))
        print('M2_GEOMETRY_PASS',arm,flush=True)
    save(s.out/'GEOMETRY-CHECKED.json',dict(passed=True,owned_operands_source_R_receipt_sha256=sha(free/'receipt.json'),arms=reports,
        dispatch_scope='Actual scheduled GPU graph descriptors/device buffers and original physical width counters, not CUDA kernel-symbol timing'))

def negatives(s):
    read,save,sha,need=h.read,h.save,h.sha,h.need
    rows=[];models=s.models['Qwen'];structure=s.structures['Qwen']
    for name,patch in [('unsupported-k',dict(k=5)),('insufficient-reserve',dict(target_output_reserve=4)),('unknown-option',dict(unregistered_m2_field=True))]:
        job={**models,'draft':True,'draft_width':4,'lowering':'LOCAL','residency':'matched','profile':False,'k':7,'target_output_reserve':8,'proposal_mode':'live','inputs':[],
            'capability_request':h.capability(models,structure,'packed','LOCAL',7,'live'),**patch}
        path=s.out/'jobs'/('negative-'+name+'.json');save(path,job);dest=s.out/'runs'/('negative-'+name)
        error=None
        try:h.host.run(s.cfg,s.builds/'packed/BUILD.json',path,dest,'development')
        except RuntimeError as e:error=str(e)
        need(error is not None and read(dest/'HOST.json')['status']=='FAILED' and (dest/'native/failure.json').exists(),'Actual native negative gate did not reject')
        rows.append(dict(case=name,host_sha256=sha(dest/'HOST.json'),native_failure=read(dest/'native/failure.json'),native_failure_sha256=sha(dest/'native/failure.json'),retained=True))
    save(s.out/'NATIVE_NEGATIVES-CHECKED.json',dict(passed=True,cases=rows,expected_failures_charged_without_refund=True))
