"""S1 finite qualification. Every native job comes from the complete F0 plan."""
import argparse
from collections import Counter
import json
from pathlib import Path
import time
from check_numeric import vectors,state,operand,quantized_chunks,physical
from host import Host,utc
from materialize import model_job,assemble_inputs,gold_job,projection_job
from support import fresh,need,read,sha,write,historical_receipt


def geometry_pair(actual,reference,manifest,profile,arm=None):
    name=manifest['geometry_case']['name'];a=Path(actual)/name/'captures';r=Path(reference)/name/'captures'
    vector_proofs=[vectors(a/str(p)/'frontier.f32',r/str(p)/'frontier.f32',1,151936)for p in range(1,1025)]
    state_proofs=[state(a/str(p)/'sequence.bin',r/str(p)/'sequence.bin',p,profile)
                  for p in manifest['geometry_case']['state_positions']]
    result=dict(full_vectors=vector_proofs,all64_KV_states=state_proofs)
    result['crossing_cases']=[]
    for extra in manifest['extra_geometry_cases']:
        ar=Path(actual)/extra['name']/'captures';rr=Path(reference)/extra['name']/'captures'
        result['crossing_cases'].append(dict(case=extra['name'],full_vectors=[
            vectors(ar/str(p)/'frontier.f32',rr/str(p)/'frontier.f32',1,151936)for p in extra['observe_positions']],
            all64_KV_states=[state(ar/str(p)/'sequence.bin',rr/str(p)/'sequence.bin',p,profile)for p in extra['state_positions']]))
    if arm:
        raw=read(Path(actual)/'result.json');case=raw['cases'][0]
        executions=case['executions'];forced=manifest['geometry_case']['forced'];groups=[];base=0
        for call in forced:
            width=len(call['ids']);i=0
            while i<width:
                extent=max(256,((base+i+1+255)//256)*256);end=i+1
                while end<width and end-i<32 and max(256,((base+end+1+255)//256)*256)==extent:end+=1
                groups.append(dict(position=base+i,width=end-i));i=end
            base+=width
        need(len(executions)==len(groups),'Unexpected full-model W/SIMPLE splitting')
        position=0
        for execution,group in zip(executions,groups):
            width=group['width'];need(group['position']==position,'W group continuity');position+=width
            need(execution['width']==width and execution['position']==position-width and
                 execution['active_cells']==position and len(execution['requested_rows'])==width,
                 'Full-model physical width/output/active-extent contract')
            expected=[max(256,((p+255)//256)*256)for p in range(position-width+1,position+1)]
            need(execution['expected_extents']==expected and execution['actual_attention_extent']==max(expected),
                 'Physical KV/frontier extent')
        need(position==1024,'Complete capacity materialization')
        typed=[node for node in case['geometry']if node['op']=='MUL_MAT'and node['sources']and
               node['sources'][0]['type']in ('q4_K','q6_K')]
        need({node['sources'][0]['type']for node in typed}=={'q4_K','q6_K'},'Both actual weight types')
        for node in typed:
            need(node['device']=='NVIDIA RTX A5000'and all(source['device']=='NVIDIA RTX A5000'for source in node['sources'][:2]),
                 'Actual typed operator device placement')
            if arm=='B'and node['sources'][1]['ne'][1]>1:
                need(node['strong_backend_loop_marker']is True,'B graph silently bypassed backend loop')
            if arm in ('G','C'):need(node['ne'][1]==1,'Scalar-column arithmetic contract')
        work=case['application_work'];need(work['scalar_dot_columns']>0,'Missing real scalar dispatch evidence')
        need((work['backend_loop_entries']>0)==(arm=='B'),'Actual full-model B dispatch')
        probe=case['overflow_probe'];need(probe['expected_rejection']is True and probe['observed_kernel_launches']==0,
                                          'Capacity overflow was not rejected before GPU compute')
        result['overflow_state']=state(Path(actual)/name/'after-overflow/sequence.bin',Path(actual)/name/'before-overflow/sequence.bin',1024,profile)
        result['overflow_frontier']=vectors(Path(actual)/name/'after-overflow/frontier.f32',Path(actual)/name/'before-overflow/frontier.f32',1,151936)
        result['physical']=dict(work=work,actual_executions=executions,typed_nodes=len(typed))
        cross=raw['cases'][1]['executions']
        verify=[e for e in cross if e['phase']=='VERIFY']
        need([(e['position'],e['width'],e['requested_rows'])for e in verify]==[(255,1,[0]),(256,3,[1,2,3])],
             'Original W/SIMPLE must split the crossing q4 caller at the physical frontier')
        result['physical']['crossing_caller_actual_executions']=cross
        actual4=raw['cases'][2]['executions']
        need(len(actual4)==1 and actual4[0]['position']==0 and actual4[0]['width']==4 and
             actual4[0]['requested_rows']==[0,1,2,3],'Actual unsplit q4 input capture source')
        result['physical']['initial_q4_actual_executions']=actual4
    return result


def reference_services_pair(actual,reference,manifest,profile):
    proofs=[]
    for service in manifest['services']:
        name=service['id'];a=Path(actual)/name;r=Path(reference)/name
        ar,rr=read(a/'receipt.json'),read(r/'receipt.json')
        need(historical_receipt(ar)['heavy']is True and historical_receipt(rr)['heavy']is True,'Actual scalar R receipt/clock schema')
        for key in ('ids','eog','cap','pending_id','pending_position','materialized_tokens','terminal_kind'):
            need(ar[key]==rr[key],'Repeated pristine R service mismatch: '+key)
        need(1<=len(ar['ids'])<=service['input']['cap'],'Natural EOG/cap length')
        n=len(service['input']['prompt_ids']);rows=[]
        for i in range(len(ar['ids'])):
            p=n+i;rows.append(dict(vector=vectors(a/'captures'/str(p)/'frontier.f32',r/'captures'/str(p)/'frontier.f32',1,151936),
                                  active_KV=state(a/'captures'/str(p)/'sequence.bin',r/'captures'/str(p)/'sequence.bin',p,profile)))
        if name.startswith('termination-'):
            cap=service['input']['cap'];need(ar['ids']==[3925,13,151645][:min(cap,3)]and
                ar['terminal_kind']==('CAP'if cap<3 else'EOG'),'Frozen exposed native EOG boundary')
        proofs.append(dict(input_id=name,endpoint=ar,full_steps=rows))
    return proofs


def service_pair(actual,reference,manifest,profile,arm):
    proofs=[];meta=read(Path(actual)/'result.json')
    for service in manifest['services']:
        name=service['id'];ref=Path(reference)/name;rr=read(ref/'receipt.json')
        heavy=Path(actual)/(name+'-heavy');clean=Path(actual)/(name+'-clean')
        hr,cr=read(heavy/'receipt.json'),read(clean/'receipt.json')
        need(historical_receipt(hr)['heavy']is True and historical_receipt(cr)['heavy']is False,'Actual heavy/clean receipt clock schema')
        n=len(service['input']['prompt_ids']);count=len(rr['ids']);steps=[]
        for r in (hr,cr):
            need(r['ids']==rr['ids']and r['eog']==rr['eog']and r['stop_reason']==rr['terminal_kind'],
                 'Candidate/reference complete greedy endpoint')
            need(r['target_final_kv']==dict(min=0,max=n+count-2),'Pending/committed position lifecycle')
            need(not r['draft_enabled']and r['draft_calls']==0 and r['graphs_reused']==0,'Unexpected draft/graph policy')
            need(r['target_output_reserve']==32,'Actual reserve32')
            executions=r['executions'];widths=[min(32,n-i)for i in range(0,n,32)]+[1]*(count-1)
            need([e['width']for e in executions]==widths,'Actual service projection width sequence')
            need(dict(Counter(str(e['width'])for e in executions))==r['target_physical_width_hist'],'Native physical widths differ from caller execution')
            position=0
            for execution in executions:
                width=execution['width'];need(execution['position']==position and execution['active_cells']==position+width,'Committed active state sequence')
                need(execution['phase']==('PREFILL'if position<n else'ORDINARY'),'Service phase attribution')
                wanted=[]if position+width<n else [n-1]if position<n else [0]
                need(execution['requested_rows']==wanted,'Requested output mask changed')
                extents=[max(256,((p+255)//256)*256)for p in range(position+1,position+width+1)]
                need(execution['expected_extents']==extents and execution['actual_attention_extent']==max(extents),'Service physical frontier')
                position+=width
            need(position==n+count-1,'Materialized/pending terminal position')
        for i in range(count):
            key='initial'if i==0 else'ordinary-'+str(i);p=n+i;expected=ref/'captures'/str(p)
            steps.append(dict(vector=vectors(heavy/'target'/(key+'.f32'),expected/'frontier.f32',1,151936),
                              frontier=vectors(heavy/'target/state'/key/'frontier.f32',expected/'frontier.f32',1,151936),
                              KV=state(heavy/'target/state'/key/'sequence.bin',expected/'sequence.bin',p,profile)))
        final=n+count-1;expected=ref/'captures'/str(final)
        for terminal in (heavy/'target/state/terminal',clean/'post-service-terminal'):
            vectors(terminal/'frontier.f32',expected/'frontier.f32',1,151936)
            state(terminal/'sequence.bin',expected/'sequence.bin',final,profile)
        need(all(cr['observed_API_calls_within_service'][k]==0 for k in ('state_exports','state_imports','context_creates','heavy_captures')),
             'Heavy observer/state export entered clean service')
        need(cr['online_reference_replays']==0 and cr['online_state_exports']==0 and cr['online_context_creates']==0,
             'Hidden clean replay/reset context lifecycle')
        for directory,r in ((heavy,hr),(clean,cr)):
            tape=read(directory/'semantic-tape.json')
            raw=json.dumps(tape,sort_keys=True,separators=(',',':'))
            # nlohmann dump orders object keys lexicographically, compact UTF8.
            need(__import__('hashlib').sha256(raw.encode()).hexdigest()==r['semantic_tape_sha256'],'Complete semantic tape binding')
        need(read(heavy/'semantic-tape.json')==read(clean/'semantic-tape.json'),'Heavy/clean semantic trajectory differs')
        need((hr['application_work']['backend_loop_entries']>0)==(arm=='B'and n>1),'Actual service backend dispatch')
        proofs.append(dict(input_id=name,arm=arm,all_steps=steps,clean_terminal_state_checked=True,
                           pending_final_token_not_materialized=True,context_reset_checked_in_native=True))
    need(meta['native_capability']['arm']==arm,'Native arm echo')
    return proofs


def projection_checks(worker,directory,inputs,golds):
    directory=Path(directory);result=read(directory/'native/result.json');records=result['operations']
    need([r['operation_id']for r in records]==[op['operation_id']for op in worker['operations']],'Actual operation IDs/order')
    c=inputs[worker['class_id']]['shape_class'];q=worker['q'];proofs=[];host=read(directory/'HOST.json')
    gold=golds[worker['class_id']]
    if q==4:gold=gold['q4']
    for path,digest in zip(gold['vectors']+gold['quantized'],gold['vectors_sha256']+gold['quantized_sha256']):
        need(sha(path)==digest,'Frozen independent gold bytes changed')
    for record in records:
        need(host['launch_begin_monotonic_ns']<=record['start_ns']<record['end_ns']<=host['exit_observed_monotonic_ns'],
             'Native/host clock bridge')
        need(record['start_ns']<=record['fence_ns']<=record['end_ns']and
             record['start_ns']<=record['owned_ready_ns']<=record['end_ns'],'Full owned-output/fence timing boundary')
        need(record['all_outputs_owned']is True and record['callback_continues']is True,'Output lifetime/continuation')
        vector=operand(directory/'native',gold['vectors'],record['operation_id'],q,c['M'])
        dispatch=physical(record,worker['arm'],q)
        quant=None
        if worker['capture_quantization']:
            quant=quantized_chunks(directory/'native',record['quantized_activations'],gold['quantized'],q)
        else:need(not record['quantized_activations'],'Heavy quantized-byte observer entered clean bridge')
        proofs.append(dict(operation_id=record['operation_id'],output=vector,quantized_activations=quant,physical=dispatch))
    return proofs


def run(configuration):
    started=time.monotonic();h=Host(configuration);manifest=h.manifest
    need(sha(h.c['state_profile'])==h.c['state_profile_sha256'],'Pinned complete state writer profile')
    profile=read(h.c['state_profile']);need(profile['target_model_sha256']==manifest['model']['sha256'],'Profile model binding')
    reference_geometry={};reference_services={};inputs=None;golds={};reports=[];oracle=False
    with h:
        write(h.root/'STATE.json',dict(status='S1_RUNNING',utc=utc(),native_jobs_started=0))
        try:
            for worker in manifest['workers']:
                kind=worker['kind'];name=worker['worker_id']
                if kind=='S2-fixed-diagnostic':continue
                write(h.root/'STATE.json',dict(status='S1_RUNNING',worker=name,utc=utc(),completed_workers=len(reports)))
                if kind.startswith('pristine-model-'):
                    if name in manifest.get('reference_reuse',{}):
                        from resume import reuse_reference
                        output=reuse_reference(h,worker,model_job(manifest,worker,h.c['model']['path']))
                    else:output=h.run(worker,model_job(manifest,worker,h.c['model']['path']),'R')
                    native=output/'native'
                    (reference_geometry if kind.endswith('geometry')else reference_services)[name]=native
                    proof=dict(reference_only=True)
                elif kind=='candidate-model-geometry':
                    if not oracle:
                        gr=geometry_pair(reference_geometry['R-geometry-1'],reference_geometry['R-geometry-0'],manifest,profile)
                        sr=reference_services_pair(reference_services['R-services-1'],reference_services['R-services-0'],manifest,profile)
                        fresh(h.root/'R_ORACLE_CONTENT_FREEZE.json',dict(status='REPEATED_PRISTINE_R_BYTES_FROZEN',
                              geometry=gr,services=sr,utc=utc(),native_candidate_requests_started=0));oracle=True
                    output=h.run(worker,model_job(manifest,worker,h.c['model']['path']),'model')
                    proof=geometry_pair(output/'native',reference_geometry['R-geometry-0'],manifest,profile,worker['arm'])
                    if worker['arm']=='G':
                        inputs=assemble_inputs(manifest,read(h.c['descriptor_inventory']),output/'native',h.c['model']['path'],h.root/'real-inputs')
                elif kind=='pristine-scalar-gold':
                    need(inputs is not None,'No real input capture')
                    job=gold_job(worker,inputs);output=h.run(worker,job,'gold');records=read(output/'native/result.json')['operations']
                    need([r['operation_id']for r in records]==[op['operation_id']for op in worker['operations']],'Gold logical columns')
                    collected={width:dict(vectors=[],quantized=[],vectors_sha256=[],quantized_sha256=[])for width in (32,4)}
                    c=inputs[worker['class_id']]['shape_class'];checks=[]
                    for i,r in enumerate(records):
                        p=output/'native'/(r['operation_id']+'.f32');q=output/'native'/(r['operation_id']+'.q8_1')
                        need(sha(p)==r['output_sha256']and sha(q)==r['quantized_sha256'],'Pristine gold payload identity')
                        op=worker['operations'][i];width=op['source_width'];col=op['column']
                        source=inputs[worker['class_id']]['q4_columns'if width==4 else'columns'][col]
                        checks.append(vectors(p,source['actual_G_scalar_output'],1,c['M']))
                        data=collected[width];data['vectors'].append(str(p));data['quantized'].append(str(q))
                        data['vectors_sha256'].append(sha(p));data['quantized_sha256'].append(sha(q))
                    golds[worker['class_id']]={**collected[32],'q4':collected[4]}
                    fresh(h.root/'gold-bindings'/('GOLD-'+worker['class_id']+'.private.json'),golds[worker['class_id']])
                    proof=dict(independent_columns=len(checks),all_G_capture_outputs_match=checks)
                elif kind in ('typed-operand-qualification','clean-operand-bridge'):
                    job,_=projection_job(worker,inputs,manifest,'S1');output=h.run(worker,job,'operand')
                    proof=projection_checks(worker,output,inputs,golds)
                elif kind=='candidate-model-services':
                    output=h.run(worker,model_job(manifest,worker,h.c['model']['path']),'model')
                    proof=service_pair(output/'native',reference_services['R-services-0'],manifest,profile,worker['arm'])
                elif kind=='expected-native-negative':
                    job,error=projection_job(worker,inputs,manifest,'S1');output=h.run(worker,job,'operand',expected_error=error)
                    proof=read(output/'EXPECTED_REJECTION.json')
                else:raise ValueError('Unregistered qualification kind: '+kind)
                report=dict(worker_id=name,kind=kind,proof=proof,HOST_sha256=sha(output/'HOST.json'))
                fresh(h.root/'comparisons'/(name+'.json'),report);reports.append(report)
            expected=[w['worker_id']for w in manifest['workers']if w['kind']!='S2-fixed-diagnostic']
            need([r['worker_id']for r in reports]==expected,'Incomplete S1 qualification')
            fresh(h.root/'S1_CERTIFICATE.json',dict(status='ALL_REQUIRED_S1_GATES_PASSED',utc=utc(),
                manifest_sha256=h.c['manifest_sha256'],compiled_closure_sha256=h.c['compiled_closure_sha256'],
                input_bindings_sha256=sha(h.root/'real-inputs/INPUT_BINDINGS.private.json'),
                gold_registry_sha256={c:sha(h.root/'gold-bindings'/('GOLD-'+c+'.private.json'))for c in golds},
                workers=len(reports),logical_operations=sum(len(w['operations'])for w in manifest['workers']if w['kind']!='S2-fixed-diagnostic'),
                comparisons=[dict(path=str(h.root/'comparisons'/(r['worker_id']+'.json')),sha256=sha(h.root/'comparisons'/(r['worker_id']+'.json')))for r in reports],
                graphs_policy='off_only',draft_accept_reject='NOT_APPLICABLE_TARGET_ONLY_M',
                private_raw_numeric_validation='PASSED',public_numeric_payloads='UNAVAILABLE_UNLESS_SEPARATELY_DISTRIBUTED',
                S2='NOT_RUN_REQUIRES_F1_COMPLETE_PUBLIC_READBACK',caller_s=time.monotonic()-started))
            write(h.root/'STATE.json',dict(status='S1_PASSED_WAITING_F1_PUBLIC_READBACK',utc=utc(),caller_s=time.monotonic()-started))
        except BaseException as error:
            write(h.root/'STATE.json',dict(status='S1_STOPPED',error_type=type(error).__name__,reason=str(error),utc=utc(),
                 completed_workers=len(reports),caller_s=time.monotonic()-started,no_automatic_retry=True))
            raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--configuration',required=True);a=p.parse_args();run(a.configuration)


if __name__=='__main__':main()
