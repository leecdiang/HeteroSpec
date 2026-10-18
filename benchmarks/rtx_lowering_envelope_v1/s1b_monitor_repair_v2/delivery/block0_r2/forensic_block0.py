"""Read-only CPU description of stopped raw evidence; never grants qualification."""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--frozen',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();sys.path.insert(0,str(a.frozen))
    from common import load,save,sha,blob
    import audit,identity
    from monitor_audit import verify
    f=load(a.frozen/'F0.json');plan=load(a.frozen/'PLAN.json');root=a.root;slots=[s for s in plan['clean_slots'] if s['block']==0];rows=[];observations=[];inputs=[];partial=[];monitors=[];processes=[]
    def compare(left,right):
        assert len(left)==len(right) and len(left)%4==0
        ints=lambda b:struct.unpack('<'+'I'*(len(b)//4),b)
        floats=lambda b:struct.unpack('<'+'f'*(len(b)//4),b)
        li,ri=ints(left),ints(right);lf,rf=floats(left),floats(right);diff=[i for i,(x,y) in enumerate(zip(li,ri)) if x!=y]
        finite=all(math.isfinite(x) for x in lf+rf)
        order=lambda x:(~x&0xffffffff) if x&0x80000000 else (x^0x80000000)
        first=diff[0] if diff else None
        return dict(bitwise_equal=left==right,bytes=len(left),words=len(li),both_finite=finite,nonfinite_left=sum(not math.isfinite(x) for x in lf),nonfinite_right=sum(not math.isfinite(x) for x in rf),different_words=len(diff),max_absolute_error=max((abs(x-y) for x,y in zip(lf,rf)),default=0) if finite else None,max_ULP=max((abs(order(x)-order(y)) for x,y in zip(li,ri)),default=0) if finite else None,first_difference=None if first is None else dict(linear_float_index=first,left_bits=f'{li[first]:08x}',right_bits=f'{ri[first]:08x}',left_value=repr(lf[first]),right_value=repr(rf[first])),left_sha256=hashlib.sha256(left).hexdigest(),right_sha256=hashlib.sha256(right).hexdigest())
    for slot in slots:
        d=root/'clean'/f'{slot["index"]:03d}';n=d/'native';started=(d/'native.PROCESS.json').exists();qualified=(d/'COMPLETED.json').exists()
        row={k:slot[k] for k in ['id','family','phase','q','layer','layout','descriptor']};row.update(started=started,completed_qualified=qualified,status='STARTED_FAILED' if started and not qualified else 'COMPLETED_QUALIFIED' if qualified else 'NOT_STARTED_PROTOCOL_STOP',graph_calls=0,warmups=0,formal_evaluations=0,qualified_costs=dict(allocation=None,preparation=None,upload=None,compute=None,sync=None,readback=None,resident=None,input_inclusive=None,median=None,p95=None,max=None),cost_status='UNKNOWN / NO QUALIFIED SAMPLE')
        if started:
            assert not qualified,'this forensic report is specifically stopped failed run;use frozen inspector for successes'
            fail=load(n/'FAILED.json');row.update(graph_calls=fail['actual_graph_calls'],warmups=sum(r['warmup'] for r in fail['partial_intervals']),formal_evaluations=sum(not r['warmup'] for r in fail['partial_intervals']),native_exit_code=load(d/'native.LIFETIME.json')['exit_code'])
            assert fail['actual_graph_calls']==len(list(n.glob('GRAPH_STARTED_*.json')))
            expected=next(r for r in load(a.frozen/'CPU_EXPECTED.json') if (r['descriptor_id'],r['layout'])==(slot['descriptor'],slot['layout']))
            graph=load(n/'GRAPH_AND_OWNERSHIP.json');audit.graphcheck(expected,graph,True)
            row.update(saved_actual_graph_identity_and_placement_pass=True,actual_support_queries=len(graph['nodes']),ordinary_after_input_integrity='UNKNOWN: no after readback exists',full_module_inventory='UNKNOWN: final RECORD not emitted',QK_softmax_AV='NOT_OBSERVED: clean host intentionally has no intermediate diagnostics')
            reference=blob(root/'cas',slot['ordinary_reference']);outputs=[]
            for i in range(fail['output_count']):
                ref=load(n/f'ordinary_{i}.BLOB.json');b=blob(root/'cas',ref);assert ref['slot']==slot['id'];outputs.append(b)
                observations.append(dict(coordinate=slot['id'],index=i,warmup=i==0,reference_comparison=compare(b,reference),qualified=False,output_ref=ref))
            for i in range(1,len(outputs)):observations.append(dict(coordinate=slot['id'],comparison='same_process_output_'+str(i)+'_vs_warmup',comparison_result=compare(outputs[i],outputs[0]),qualified=False))
            for role in ['Q','K','V','mask']:
                meta=next(x['metadata'] for x in plan['descriptors'] if x['id']==slot['descriptor']);source=next(r for r in slot['input_files'] if Path(r['path']).name==meta[role]['file'])
                ref=load(n/f'input_{role}.before.BLOB.json');assert blob(root/'cas',ref)==blob(root/'cas',source)
                assert not (n/f'input_{role}.after.BLOB.json').exists()
                inputs.append(dict(coordinate=slot['id'],role=role,before_equal=True,after_status='UNKNOWN / MISSING',before=ref))
            for r in fail['partial_intervals']:
                frequency=fail['QPC_frequency'];assert frequency==f['QPC_frequency'] and r['begin']<=r['compute_return']<=r['sync_return']<=r['readback_return']
                scale=1000/frequency
                partial.append(dict(coordinate=slot['id'],raw_QPC=r,frequency=frequency,warmup=r['warmup'],F_ms=(r['compute_return']-r['begin'])*scale,G_ms=(r['sync_return']-r['compute_return'])*scale,H_ms=(r['readback_return']-r['sync_return'])*scale,FG_ms=(r['sync_return']-r['begin'])*scale,FGH_ms=(r['readback_return']-r['begin'])*scale,qualified=False,interpretation='raw failed-coordinate execution record only;not qualified timing or acceleration evidence'))
            for prefix in ['readiness','native']:
                m=verify(d/prefix,f['monitor_contract']);monitors.append(dict(prefix=prefix,report=m,lifetime=load(d/(prefix+'.LIFETIME.json'))));e=load(d/(prefix+'.JOB_EVENTS.json'));assert not e['errors'];processes.append(dict(prefix=prefix,events=e,lifetime=load(d/(prefix+'.LIFETIME.json'))))
            # Inspect only saved core/plugin import receipts. Do not invent a
            # complete loaded-module list, which the failed host never emitted.
            gate=load(n/'CORE_ADMITTED_BEFORE_CUDA.json');core=gate['core'];abi=load(a.frozen/'ABI_EXPORTS.json');base=core['module_handle']
            assert core['sha256']==f['numerical_DLLs']['ggml-base.dll'] and core['ready'] and core['events'].count('dll_initializer_returned')==1
            for name,fn in core['functions'].items():assert fn['address']==base+abi['core'][name]['RVA'] and identity.norm(fn['owner_path'])==identity.norm(core['path'])
            assert gate['host_import']['IAT_target']==core['functions']['ggml_init']['address'] and gate['host_import']['module_handle']==base
            plugin=load(n/'PLUGIN_CORE_IMPORTS.json');assert len(plugin)==41 and {p['symbol'] for p in plugin}==set(abi['plugin_core_symbols'])
            assert all(identity.norm(p['owner_path'])==identity.norm(core['path']) and p['target']==base+abi['core'][p['symbol']]['RVA'] for p in plugin)
            row['saved_shared_core_host_and_41_plugin_IAT_receipts_pass']=True
        rows.append(row)
    ended=load(root/'CLEAN0_ENDED.json');assert ended['status']=='INCOMPLETE_STOPPED' and ended['native_started']==1 and ended['completed']==0
    assert sum(r['graph_calls'] for r in rows)==2 and sum(r['started'] for r in rows)==1
    save(a.out,dict(run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(a.frozen/'F0.json'),frozen_analyzer_sha256=sha(a.frozen/'audit.py'),forensic_source_sha256=sha(Path(__file__)),status='STOPPED_NO_RETRY',coordinate_counts=dict(planned=72,started=1,qualified=0,failed=1,unstarted=71),graph_counts=dict(planned=648,actual=2,returned_and_synchronized_observed=2,warmups=1,formal_evaluations=1,not_started=646),readiness=load(root/'clean/000/ADMISSION.json'),stopped=ended,coordinates=rows,ordinary_observations=observations,input_occurrences=inputs,partial_QPC_unqualified=partial,supervision=monitors,owned_child_processes=processes,all_cross_layout_comparisons='UNKNOWN / NOT_OBSERVED',MQ='NOT_IN_S1B_AUTHORIZATION;not executed',q1_public_control='INCOMPLETE;first PQ warmup equal,first formal ordinary differs;QB/QH_C unstarted',qualified_cost_distributions=None,root_cause='UNKNOWN;no shader/accumulator/reduction-tree attribution',Block1_2_admission='NO_GO',next_GPU_authority=False))
    print('CPU forensic complete;1failed/71unstarted;2actual graphs;no GPU task launched')
if __name__=='__main__':main()
