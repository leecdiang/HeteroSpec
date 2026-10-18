"""Independent byte verification and context/block paired analysis, no GPU APIs."""
import collections,csv,hashlib,itertools,json,math,random,statistics,struct,sys
from pathlib import Path
from common import V,load,save,sha
LAYOUTS=['PQ','QB','QH_C']
def quantile(xs,p):
    xs=sorted(xs);return xs[max(0,math.ceil(p*len(xs))-1)] if xs else None
def summarize(xs):return dict(mean=statistics.mean(xs),median=statistics.median(xs),p95=quantile(xs,.95),max=max(xs)) if xs else dict(mean=None,median=None,p95=None,max=None)
def paired(num,den):
    assert num>0 and den>0
    return dict(ratio=num/den,difference_us=num-den,log_contrast=math.log(num/den))
def compare(left,right):
    assert len(left)==len(right) and len(left)%4==0
    mismatches=[];maximum=0.;ulp=0;finite=True
    def order(v):return (~v)&0xffffffff if v&0x80000000 else v|0x80000000
    for i in range(0,len(left),4):
        a=struct.unpack_from('<I',left,i)[0];b=struct.unpack_from('<I',right,i)[0]
        finite&=(a&0x7f800000)!=0x7f800000
        if a!=b:
            if len(mismatches)<4:mismatches.append(dict(index=i//4,actual_bits=hex(a),expected_bits=hex(b),actual=struct.unpack_from('<f',left,i)[0],expected=struct.unpack_from('<f',right,i)[0]))
            maximum=max(maximum,abs(struct.unpack_from('<f',left,i)[0]-struct.unpack_from('<f',right,i)[0]));ulp=max(ulp,abs(order(a)-order(b)))
    return dict(exact=left==right,finite=finite,different_words=sum(a!=b for a,b in zip(struct.iter_unpack('<I',left),struct.iter_unpack('<I',right))),max_abs=maximum,max_ULP=ulp,first=mismatches[:1],signed_zero='bitwise distinct;no tolerance',nonfinite_policy='disqualify')
def aliases(graph):
    rows=graph['addresses'];out=[]
    for a in rows:
        if not a['id'].startswith('input'):continue
        for b in rows:
            if b['id'].startswith('input') or b['metadata_only']:continue
            if max(a['data'],b['data'])<min(a['data']+a['bytes'],b['data']+b['bytes']):out.append(dict(input=a['id'],node=b['id'],op=b['op'],bytes=min(a['data']+a['bytes'],b['data']+b['bytes'])-max(a['data'],b['data'])))
    return out
def writecsv(out,name,rows,columns=None):
    p=out/name;assert not p.exists()
    columns=columns or list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows({k:json.dumps(v,separators=(',',':')) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
def analyze(root,out):
    root=Path(root);out=Path(out);out.mkdir(exist_ok=False);spec=load(root/'RUN_SPEC.json');contexts={c['id']:c for c in spec['contexts']};contextrows=[]
    for c in contexts.values():
        m=c['metadata'];mask=(Path(c['root'])/'mask.bin').read_bytes();counts=[sum(math.isfinite(struct.unpack_from('<f',mask,k*m['mask']['nb'][0]+j*m['mask']['nb'][1])[0]) for k in range(m['mask']['ne'][0])) for j in range(c['q'])]
        contextrows.append(dict(context_id=c['id'],cohort='historical_PR116_exposed',exposure='previously exposed;not holdout',family=c['family'],layer=c['layer'],phase=c['phase'],q=c['q'],d=m['Q']['ne'][0],Hq=m['Q']['ne'][2],Hkv=m['K']['ne'][2],tensor_key_extent=m['K']['ne'][1],visible_keys_min=min(counts),visible_keys_max=max(counts),shapes_strides_dtypes={r:{k:m[r][k] for k in ['ne','nb','type']} for r in ['Q','K','V','mask']},source_reference_hashes=c['references']))
    attempts=[];qualification=[];timing=[];hosts=[];diagnosis=[];seen=set()
    for p in sorted((root/'attempts').glob('*/JOB.json')):
        folder=p.parent;j=load(p);c=j['context'];assert c==contexts[c['id']]
        identity=(j['stage'],j.get('block'),c['id'],j['layout'],folder.name if j['stage']=='D0' else None);assert identity not in seen;seen.add(identity)
        ended=load(folder/'ENDED.json') if (folder/'ENDED.json').exists() else {};n=folder/'native';r=load(n/'RECORD.json') if (n/'RECORD.json').exists() else None
        base=dict(attempt_id=folder.name,stage=j['stage'],block=j.get('block'),context_id=c['id'],family=c['family'],phase=c['phase'],q=c['q'],layout=j['layout'],lifecycle=j['lifecycle'],source_revision=ended.get('source_revision'),status='UNCONFIRMED',reason='missing RECORD')
        attempts.append(dict(base,eligible=ended.get('eligible',False),wall_seconds=ended.get('wall_seconds')))
        if r is None:qualification.append(base);continue
        blobrows=load(n/'BLOBS.json');assert len({b['name'] for b in blobrows})==len(blobrows)
        for b in blobrows:assert sha(n/b['name'])==b['sha256'] and (n/b['name']).stat().st_size==b['bytes']
        graph=load(n/'GRAPH.json');placement=all(row['CUDA_owned'] for row in graph['addresses']);supports=all(node['CUDA_support'] is True for node in graph['nodes']);imports=len(r['plugin_core_IAT'])==41
        modules=[Path(x).name.lower() for x in r['modules_end']];runtime=Path(spec['runtime_directory']).resolve()
        for path in r['modules_end']:
            if Path(path).name in spec['numerical_DLLs']:assert Path(path).resolve().parent==runtime
        assert 'ggml-cuda.dll' in modules and graph['actual_device']=='CUDA0'
        before=after=True
        for role in ['Q','K','V','mask']:
            expected=(Path(c['root'])/c['metadata'][role]['file']).read_bytes();before&=(n/f'input_{role}_before.bin').read_bytes()==expected;after&=(n/f'input_{role}_after.bin').read_bytes()==expected
        reference=Path(c['references'][j['layout']]['path']).read_bytes();assert hashlib.sha256(reference).hexdigest()==c['references'][j['layout']]['sha256']
        all_exact=True;finite=True;completed=True;callvalues=[];comparisons=[]
        for call in r['calls']:
            b=(n/f'ordinary_{call["index"]}.bin').read_bytes();result=compare(b,reference);comparisons.append(result);all_exact&=result['exact'];finite&=result['finite'];assert result['exact']==call['ordinary_exact'];freq=r['QPC_frequency'];assert freq>0
            t=[call[k] for k in ['begin','compute_return','sync_return','readback_return']];assert t==sorted(t) and t[2]>t[0];completed&=call['compute_status']==call['sync_status']==0
            costs=dict(resident_graph=(t[2]-t[0])*1e6/freq,resident_call=(t[3]-t[0])*1e6/freq)
            first=sum(r['cost_ticks'][k] for k in ['CPU_materialize','upload_and_sync'])*1e6/freq+costs['resident_call']
            row=dict(base,call=call['index'],warmup=call['warmup'],frequency=freq,raw_ticks=call,ordinary_exact=result['exact'],finite=result['finite'],completion=completed,**costs,input_inclusive_first_call_phase_sum=first if call['index']==0 else None)
            timing.append(row);callvalues.append(row)
        qualified=before and after and r['host_input_unchanged'] and all_exact and finite and completed and supports and placement and imports and len(r['calls'])==j['warmups']+j['calls']
        assert qualified==ended['eligible']
        qualification.append(dict(base,status='QUALIFIED' if qualified else 'CONTROL_FAILED',reason=None if qualified else 'ordinary or input bytes differ',support=supports,placement=placement,plugin_imports=imports,input_before=before,input_after=after,host_input=r['host_input_unchanged'],completion=completed,ordinary_exact=all_exact,finite=finite,repeat_count=len(r['calls']),eligible=qualified,first_mismatch=next((x for x in comparisons if not x['exact']),None)))
        if j['stage']=='D0':diagnosis.append(dict(base,status=r['status'],calls=len(r['calls']),inputs_after=after,ordinary_exact=[x['exact'] for x in comparisons],mismatches=[x for x in comparisons if not x['exact']],input_node_aliases=aliases(graph)))
        for view in ['resident_graph','resident_call']:
            samples=[x[view] for x in callvalues if not x['warmup'] and qualified];stats=summarize(samples)
            hosts.append(dict(base,cost_view=view,eligible=qualified,valid_samples=len(samples),raw_calls=len(callvalues),warmups=sum(x['warmup'] for x in callvalues),**stats,initialization_us=r['cost_ticks']['initialize']*1e6/r['QPC_frequency'],graph_build_us=r['cost_ticks']['graph_build']*1e6/r['QPC_frequency'],allocation_us=r['cost_ticks']['allocation']*1e6/r['QPC_frequency'],materialization_us=r['cost_ticks']['CPU_materialize']*1e6/r['QPC_frequency'],source_read_us=r['cost_ticks']['source_read']*1e6/r['QPC_frequency'],upload_us=r['cost_ticks']['upload_and_sync']*1e6/r['QPC_frequency'],input_inclusive_first_call_phase_sum=callvalues[0]['input_inclusive_first_call_phase_sum'] if qualified else None,graph_bytes=r['graph_buffer_bytes'],persistent_input_bytes=r['persistent_input_bytes']))
    cells=[];qualified_by={(x['context_id'],x['layout'],x['block']):x for x in qualification if x['stage']=='N1'}
    times={(x['context_id'],x['layout'],x['block'],x['cost_view']):x for x in hosts if x['stage']=='T1'};contrasts=[]
    for stage,blocks in [('N1',range(3)),('T1',range(6))]:
        for block in blocks:
            for c in contexts.values():
                for l in LAYOUTS:
                    q=qualified_by.get((c['id'],l,block)) if stage=='N1' else times.get((c['id'],l,block,'resident_graph'))
                    cells.append(dict(stage=stage,block=block,context_id=c['id'],family=c['family'],phase=c['phase'],q=c['q'],layout=l,lifecycle='persistent_inputs',status='UNSTARTED' if q is None else 'QUALIFIED' if q['eligible'] else 'CONTROL_FAILED',attempt_id=q['attempt_id'] if q else None))
    for block in range(6):
        eb=root/f'T1_BLOCK_{block}_ENDED.json';environment=load(eb)['environment_qualified'] if eb.exists() else False
        for c in contexts.values():
            for num,den in [('QB','QH_C'),('PQ','QB')]:
                for view in ['resident_graph','resident_call','input_inclusive_first_call_phase_sum']:
                    a=times.get((c['id'],num,block,'resident_graph' if view=='input_inclusive_first_call_phase_sum' else view));b=times.get((c['id'],den,block,'resident_graph' if view=='input_inclusive_first_call_phase_sum' else view));ok=bool(a and b and a['eligible'] and b['eligible'] and environment)
                    av=(a[view] if view=='input_inclusive_first_call_phase_sum' else a['mean']) if ok else None;bv=(b[view] if view=='input_inclusive_first_call_phase_sum' else b['mean']) if ok else None
                    contrasts.append(dict(context_id=c['id'],family=c['family'],phase=c['phase'],q=c['q'],block=block,numerator=num,denominator=den,cost_view=view,eligible=ok,numerator_us=av,denominator_us=bv,environment_qualified=environment,**(paired(av,bv) if ok else dict(ratio=None,difference_us=None,log_contrast=None))))
    aggregate=[]
    for num,den in [('QB','QH_C'),('PQ','QB')]:
        for view in ['resident_graph','resident_call','input_inclusive_first_call_phase_sum']:
            for group in ['q>1','q1','Qwen','SmolLM2','Llama','prefill','continuation','q2','q3','q4']:
                selected=[r for r in contrasts if r['eligible'] and r['numerator']==num and r['cost_view']==view and (r['q']>1 if group=='q>1' else r['q']==1 if group=='q1' else r['family']==group if group in ['Qwen','SmolLM2','Llama'] else r['phase']==group if group in ['prefill','continuation'] else r['q']==int(group[1:]))]
                blocks=collections.defaultdict(list)
                for r in selected:blocks[r['block']].append(r)
                logs=[statistics.mean(r['log_contrast'] for r in rs) for _,rs in sorted(blocks.items())];diff=[statistics.mean(r['difference_us'] for r in rs) for _,rs in sorted(blocks.items())]
                ratio=math.exp(statistics.mean(logs)) if logs else None;difference=statistics.mean(diff) if diff else None
                ci=None
                if len(logs)>=3:
                    rng=random.Random(20261019);draws=sorted(math.exp(statistics.mean(rng.choices(logs,k=len(logs)))) for _ in range(10000));ci=[draws[249],draws[9749]]
                aggregate.append(dict(numerator=num,denominator=den,cost_view=view,stratum=group,pairs=len(selected),blocks=len(logs),geometric_ratio=ratio,mean_improvement_us=difference,block_log_contrasts=logs,leave_one_block_out_ratios=[math.exp(statistics.mean(logs[:i]+logs[i+1:])) for i in range(len(logs))] if len(logs)>1 else [],descriptive_block_bootstrap95=ci,regressions=sum(r['ratio']<1 for r in selected),screen=bool(ratio and ratio>1.02 and difference>1 and len(logs)>=3),interpretation='limited single-session blocks;screen is heuristic,not population significance'))
    coverage=[]
    for stage in ['N1','T1']:
        for family,phase,q in itertools.product(['Qwen','SmolLM2','Llama'],['prefill','continuation'],range(1,5)):
            rows=[r for r in cells if r['stage']==stage and r['family']==family and r['phase']==phase and r['q']==q];coverage.append(dict(stage=stage,family=family,phase=phase,q=q,planned=len(rows),qualified=sum(r['status']=='QUALIFIED' for r in rows),failed=sum(r['status']=='CONTROL_FAILED' for r in rows),unstarted=sum(r['status']=='UNSTARTED' for r in rows)))
    for name,rows in [('CONTEXTS.csv',contextrows),('CELLS.csv',cells),('QUALIFICATION.csv',qualification),('TIMING_RAW.csv',timing),('TIMING_HOST.csv',hosts),('CONTRASTS.csv',contrasts),('COVERAGE.csv',coverage),('AGGREGATES.csv',aggregate)]:writecsv(out,name,rows)
    result=dict(execution_id=spec['execution_id'],spec_sha256=sha(root/'RUN_SPEC.json'),attempts=len(attempts),actual_calls=sum(r['repeat_count'] for r in qualification if 'repeat_count' in r),stage_counts={s:dict(started=sum(r['stage']==s for r in qualification),qualified=sum(r['stage']==s and r.get('eligible',False) for r in qualification),calls=sum(r.get('repeat_count',0) for r in qualification if r['stage']==s)) for s in ['D0','N1','T1']},diagnosis=diagnosis,aggregates=aggregate,raw_root=str(root),raw_retention='RAW_LOCAL_ONLY',RTX_numerical_DAG='UNKNOWN',hardware_decision='INCONCLUSIVE;no physical model or request-critical-path evidence',R1='UNSTARTED',M1='UNSTARTED',W1='NOT_AUTHORIZED',independent_external_review=False)
    save(out/'SUMMARY.json',result);return result
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args();r=a.root or Path(load(V/'LOCAL_RUN.json')['root']);out=a.out or V/'results';result=analyze(r,out);print(json.dumps(result['stage_counts']))
if __name__=='__main__':main()
