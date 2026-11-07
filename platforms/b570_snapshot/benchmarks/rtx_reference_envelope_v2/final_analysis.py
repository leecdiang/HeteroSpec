"""Pure CPU closure: exact old analyzer plus memoization and explicit restored I/O.
No qualification tolerance or source data change;R1 remains a separate cohort.
"""
import argparse,collections,csv,functools,hashlib,json,math,os,statistics
from pathlib import Path
from common import V,load,save,sha
import analyze
def norm(p):return os.path.normcase(str(Path(p).resolve()))
def source_adapter(mapping):
    original_sha=analyze.sha
    class RestoredPath(type(Path())):
        def read_bytes(self):return Path(mapping.get(norm(self),str(self))).read_bytes()
    analyze.Path=RestoredPath
    analyze.sha=lambda p:original_sha(mapping.get(norm(p),p))
def core(root,out):
    # Exact,immutable byte-array function;cache changes execution work only.
    uncached=analyze.compare;analyze.compare=functools.lru_cache(maxsize=512)(uncached)
    for a,b in [(b'\0'*4,b'\0'*4),(b'\0'*4,b'\0\0\0\x80')]:assert analyze.compare(a,b)==uncached(a,b)
    writer=analyze.writecsv;host_lookup={}
    def environment(block):
        p=Path(root)/f'T1_BLOCK_{block}_ENDED.json';return load(p)['environment_qualified'] if p.exists() else False
    def tables(directory,name,rows,columns=None):
        if name in ['TIMING_HOST.csv','TIMING_RAW.csv']:
            for r in rows:
                numerical=r['eligible'] if name=='TIMING_HOST.csv' else load(Path(root)/'attempts'/r['attempt_id']/'ENDED.json').get('eligible',False)
                r['numerical_eligible']=numerical;r['timing_eligible']=bool(numerical and r['stage']=='T1' and environment(r['block']) and not r.get('warmup',False));r['status']='NUMERICALLY_QUALIFIED' if numerical else 'CONTROL_FAILED';r['timing_scope']='checked resident replay;host completed latency,not kernel latency'
                if name=='TIMING_HOST.csv':host_lookup[r['context_id'],r['layout'],r['block'],r['cost_view']]=r
        if name=='CONTRASTS.csv':
            for r in rows:
                view='resident_graph' if r['cost_view']=='input_inclusive_first_call_phase_sum' else r['cost_view']
                for role in ['numerator','denominator']:
                    host=host_lookup.get((r['context_id'],r[role],r['block'],view));r[role+'_source_revision']=host.get('source_revision') if host else None
                r['lifecycle']='persistent_inputs';r['source_cohort']='exposed PR116 fixed24';r['missing_reason']=None if r['eligible'] else 'missing/unqualified arm or invalidated acquisition block'
        writer(directory,name,rows,columns)
    analyze.writecsv=tables
    return analyze.analyze(root,out)
def boundary(root,out,mapper):
    rr=root/'R1';plan=load(rr/'PLAN.json');cases={c['id']:c for c in plan['fixtures']};rows=[];timing=[];raw_timing=[];reference_parts=collections.defaultdict(list)
    def read(p):return Path(mapper.get(norm(p),str(p))).read_bytes()
    for p in sorted((rr/'attempts').glob('*/JOB.json')):
        job=load(p);n=p.parent/'native';ended=load(p.parent/'ENDED.json');c=job['context'];record=load(n/'RECORD.json') if (n/'RECORD.json').exists() else None
        row=dict(attempt_id=p.parent.name,case=c['id'],layout=job['layout'],mode=ended['mode'],q=c['q'],mask=c.get('maskkind'),split=c.get('split'),family=c.get('family'),status=ended['status'],eligible=False)
        if record is None:rows.append(row);continue
        for blob in load(n/'BLOBS.json'):assert sha(n/blob['name'])==blob['sha256'] and (n/blob['name']).stat().st_size==blob['bytes']
        graph=load(n/'GRAPH.json');assert all(x['CUDA_owned'] for x in graph['addresses']) and all(x['CUDA_support'] for x in graph['nodes']) and graph['actual_device']=='CUDA0';assert len(record['plugin_core_IAT'])==41
        assert record['input_after_equal'] and record['host_input_unchanged'];input_match=True
        for role in ['Q','K','V','mask']:
            original=read(Path(c['root'])/(role+'.bin'))
            for phase in ['before','after']:input_match&=(n/f'input_{role}_{phase}.bin').read_bytes()==original
        assert input_match
        completion=all(x['compute_status']==x['sync_status']==0 for x in record['calls']);assert completion
        outputs=[(n/f'ordinary_{x["index"]}.bin').read_bytes() for x in record['calls']]
        for call in record['calls']:raw_timing.append(dict(attempt_id=p.parent.name,case=c['id'],layout=job['layout'],mode=ended['mode'],call=call['index'],warmup=call['warmup'],frequency=record['QPC_frequency'],ticks=call,ordinary_status='REFERENCE_CAPTURE_NOT_A_COMPARISON' if job.get('capture_reference') else call['ordinary_exact'],completion=call['compute_status']==call['sync_status']==0))
        if job.get('capture_reference'):
            assert job['layout']=='PQ' and c['q']==1 and record['status']=='REFERENCE_CAPTURE' and len(outputs)==1
            assert analyze.compare(outputs[0],outputs[0])['finite'];reference_parts[c['id']].append(outputs[0]);row.update(eligible=True,ordinary_contract='INDEPENDENT_SERIAL_REFERENCE_CAPTURE',actual_calls=1);rows.append(row);continue
        expected=read(c['references'][job['layout']]['path']);assert hashlib.sha256(expected).hexdigest()==c['references'][job['layout']]['sha256'];comparisons=[analyze.compare(b,expected) for b in outputs];eligible=all(x['exact'] and x['finite'] for x in comparisons) and len(outputs)==job['warmups']+job['calls'];assert eligible==(record['status']=='QUALIFIED')
        row.update(eligible=eligible,ordinary_contract='exact serial-reference bytes',actual_calls=len(outputs),first_mismatch=next((x for x in comparisons if not x['exact']),None),d=c['metadata']['Q']['ne'][0],Hq=c['metadata']['Q']['ne'][2],Hkv=c['metadata']['K']['ne'][2],key_extent=c['metadata']['K']['ne'][1],lifecycle=job['lifecycle']);rows.append(row)
        if ended['mode']=='cost':
            for view in ['resident_graph','resident_call','input_inclusive_first_call_phase_sum']:
                freq=record['QPC_frequency'];measure=[(x['sync_return']-x['begin'] if view=='resident_graph' else x['readback_return']-x['begin'])*1e6/freq for x in record['calls'] if not x['warmup']]
                first=(record['calls'][0]['readback_return']-record['calls'][0]['begin']+sum(record['cost_ticks'][k] for k in ['CPU_materialize','upload_and_sync']))*1e6/freq
                environment=load(rr/(c['split']+'_ENVIRONMENT.json'))['qualified'];timing.append(dict(case=c['id'],logical_fixture=c['logical_fixture'],split=c['split'],realization=c['realization'],layout=job['layout'],q=c['q'],family=c['family'],category=c['category'],maskkind=c['maskkind'],d=row['d'],Hq=row['Hq'],Hkv=row['Hkv'],keys=row['key_extent'],cost_view=view,eligible=eligible and environment,samples=1 if view=='input_inclusive_first_call_phase_sum' else len(measure),**analyze.summarize([first] if view=='input_inclusive_first_call_phase_sum' else measure),allocation_us=record['cost_ticks']['allocation']*1e6/freq,materialization_us=record['cost_ticks']['CPU_materialize']*1e6/freq,upload_us=record['cost_ticks']['upload_and_sync']*1e6/freq))
    repeat_controls={identifier:len(values)==2 and values[0]==values[1] for identifier,values in reference_parts.items()}
    oracle_words=0;oracle_cases=0
    for c in plan['fixtures']:
        if all(repeat_controls.get(c['id']+f'/serial{j}',False) for j in range(c['q'])):
            values=[reference_parts[c['id']+f'/serial{j}'][0] for j in range(c['q'])];assert b''.join(values)==read(Path(c['root'])/'ordinary_reference.bin')
            if c['maskkind']=='single_visible':
                import struct
                m=c['metadata'];v=read(Path(c['root'])/'V.bin');mask=read(Path(c['root'])/'mask.bin');D=m['Q']['ne'][0];H=m['Q']['ne'][2];G=m['K']['ne'][2];expected=bytearray()
                for j in range(c['q']):
                    keys=[k for k in range(m['K']['ne'][1]) if math.isfinite(struct.unpack_from('<f',mask,k*4+j*m['mask']['nb'][1])[0])];assert len(keys)==1
                    for h in range(H):
                        for d in range(D):
                            value=struct.unpack_from('<e',v,keys[0]*m['V']['nb'][0]+d*m['V']['nb'][1]+(h//(H//G))*m['V']['nb'][2])[0];expected.extend(struct.pack('<f',value if value else 0.0));oracle_words+=1
                assert bytes(expected)==b''.join(values);oracle_cases+=1
    contrasts=[];selectors=[]
    for c in plan['fixtures']:
        for view in ['resident_graph','resident_call','input_inclusive_first_call_phase_sum']:
            observed={r['layout']:r for r in timing if r['case']==c['id'] and r['cost_view']==view and r['eligible']}
            for numerator,denominator in [('QB','QH_C'),('PQ','QB')]:
                ok=numerator in observed and denominator in observed;contrasts.append(dict(case=c['id'],logical_fixture=c['logical_fixture'],split=c['split'],realization=c['realization'],family=c['family'],q=c['q'],keys=c['metadata']['K']['ne'][1],category=c['category'],cost_view=view,numerator=numerator,denominator=denominator,eligible=ok,**(analyze.paired(observed[numerator]['mean'],observed[denominator]['mean']) if ok else dict(ratio=None,difference_us=None))))
            selected=plan['selector'][str(c['q'])];oracle=min((v['mean'] for v in observed.values()),default=None)
            for policy,layout in [('always_PQ','PQ'),('always_QB','QB'),('always_QH_C','QH_C'),('frozen_q_selector',selected)]:
                cost=observed[layout]['mean']+(plan['selector_lookup_overhead_us'] if policy=='frozen_q_selector' else 0) if layout in observed else None
                selectors.append(dict(case=c['id'],split=c['split'],realization=c['realization'],q=c['q'],keys=c['metadata']['K']['ne'][1],policy=policy,layout=layout,cost_view=view,eligible=cost is not None,cost_us=cost,oracle_cost_us=oracle,oracle_regret_ratio=cost/oracle if cost is not None and oracle else None,scope='descriptive2value realizations;not6independent blocks'))
    for name,data in [('R1_QUALIFICATION.csv',rows),('R1_TIMING_RAW.csv',raw_timing),('R1_TIMING_HOST.csv',timing),('R1_CONTRASTS.csv',contrasts),('R1_SELECTOR.csv',selectors)]:analyze.writecsv(out,name,data)
    planned=[]
    for c in plan['fixtures']:
        for layout in ['PQ','QB','QH_C']:
            for mode,count in [('qualify',2),('cost',1)]:
                observed=[r for r in rows if r['case']==c['id'] and r['layout']==layout and r['mode']==mode]
                for rep in range(count):planned.append(dict(case=c['id'],layout=layout,mode=mode,repeat=rep,status=observed[rep]['status'] if len(observed)>rep else 'UNSTARTED',eligible=observed[rep]['eligible'] if len(observed)>rep else False))
    analyze.writecsv(out,'R1_CELLS.csv',planned)
    return dict(logical_fixtures=24,data_realizations=48,serial_reference_hosts=sum(r['mode']=='reference' for r in rows),qualification_hosts=sum(r['mode']=='qualify' for r in rows),qualified_hosts=sum(r['mode']=='qualify' and r['eligible'] for r in rows),cost_hosts=sum(r['mode']=='cost' for r in rows),cost_numerically_qualified=sum(r['mode']=='cost' and r['eligible'] for r in rows),cost_environment_eligible_hosts=sum(r['eligible'] and r['cost_view']=='resident_graph' for r in timing),calls=sum(r.get('actual_calls',0) for r in rows),all_observed_serial_repeats_exact=all(repeat_controls.values()),independent_single_visible_oracle_cases=oracle_cases,independent_single_visible_oracle_words=oracle_words,selector=plan['selector'],cohort='new synthetic;no natural prompts',remaining_original_fixture_design='48logical fixtures=24development+24holdout UNSTARTED',scope_note='original frozen plan text said12remaining/split;arithmetic annotation error only,plan bytes retained;matrix/counts unchanged')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--source-map',type=Path);args=ap.parse_args();mapping=load(args.source_map) if args.source_map else {};source_adapter(mapping);summary=core(args.root,args.out)
    if (args.root/'R1/PLAN.json').exists():r=boundary(args.root,args.out,mapping);save(args.out/'R1_SUMMARY.json',r)
    print(json.dumps(summary['stage_counts']))
if __name__=='__main__':main()
