"""Observe the actual projection graph and bridge it to formal native binaries.

One fixed exposed short generation per arm, k3/q4 and reserve4 throughout.
Existing Bank checks compare every requested vector/committed state to frozen R.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse, copy
import run_m1 as m

def main():
    p=argparse.ArgumentParser()
    for key in ('work','baseline','runtime','repo','builds','observer-builds'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();m.load_runtime(a.runtime.resolve());w=a.work.resolve();baseline=a.baseline.resolve();out=w/'qualification-dispatch-01';need,read,save,sha=m.need,m.read,m.save,m.sha
    need(not out.exists() and read(w/'qualification-01/NATIVE_CHECKS_COMPLETE.json')['passed'],'Fresh projection diagnostic after all finite gates');out.mkdir()
    need(read(a.observer_builds/'BUILD_COMPLETE.json')['passed'],'Complete observer builds first')
    trace,parse=m.checks.legacy_readers(a.repo.resolve());profiles=read(baseline/'qualification-02/STATE_PROFILES.json')
    index={x['path']:x['sha256'] for x in read(baseline.parent/'public-export-final-01/BINARY_CAPTURE_INDEX.json')['files']};verified=set()
    def verify(path):
        path=Path(path)
        if path.is_relative_to(baseline) and str(path) not in verified:
            key=str(path.relative_to(baseline));need(sha(path)==index[key],'Frozen R operand changed');verified.add(str(path))
    for name in ('vector_pair','state_pair'):
        original=getattr(m.checks,name)
        def pair(x,y,*args,_original=original,**kwargs):verify(x);verify(y);return _original(x,y,*args,**kwargs)
        setattr(m.native,name,pair)
    models=read(w/'inputs-01/MODELS.json')['Qwen'];root=read(w/'inputs-01/Qwen-DEVELOPMENT.json')['inputs'][0];root=dict(root,cap=8)
    def execute_reference(label,family,job):
        payload={**models,**job};payload.pop('draft_model',None);payload.pop('draft_sha256',None);payload.update(draft=False,residency='target_only')
        path=out/'jobs'/(label+'.json');save(path,payload);dest=out/'runs'/label;m.host.run(w/'config.json',baseline/'build-R-01/BUILD.json',path,dest,'reference');return dest
    s=SimpleNamespace(trace=trace,parse=parse,profiles=profiles,physical=m.native.Study.physical,execute=execute_reference)
    bank=m.native.Bank.__new__(m.native.Bank);bank.s=s;bank.family='Qwen';bank.index=0;bank.input=root;bank.entries={};bank.teacher_count=100
    free=baseline/'qualification-02/runs/Qwen-free-independent-R/native/dev-0';ep=read(free/'receipt.json')
    text_index={x['path']:x['raw_sha256'] for x in read(baseline.parent/'public-export-final-01/TEXT_INDEX.json')['files']}
    need(sha(free/'receipt.json')==text_index[str((free/'receipt.json').relative_to(baseline))],'Frozen free R endpoint commitment changed')
    need(len(ep['ids'])>=8 and not any(ep['eog'][:8]),'Fixed frozen greedy prefix supports short cap8')
    bank.ep={**ep,'ids':ep['ids'][:8],'eog':ep['eog'][:8],'terminal_kind':'CAP','stop_reason':'CAP'};bank.free=free
    for path in sorted((baseline/'qualification-02/jobs').glob('Qwen-root0-R-*.json')):
        bank.add(baseline/'qualification-02/runs'/path.stem,read(path)['cases'])
    structures={role:m.checks.gguf_structure(models[role+'_model']) for role in ('target','draft')};proofs=[]
    for arm,(core,cut,_) in m.ARMS.items():
        base={**models,'draft':True,'residency':'matched','draft_width':4,'lowering':cut,'profile':False,'capability_request':m.capability(models,structures,core,cut)}
        paths={}
        for kind,build in (('observer',a.observer_builds/core/'BUILD.json'),('formal-bridge',a.builds/core/'BUILD.json')):
            inputs=[dict(name='heavy',input=root,capture=True),dict(name='clean',input=root,capture=False)] if kind=='observer' else [dict(name='clean',input=root,capture=False)]
            job=out/'jobs'/(arm+'-'+kind+'.json');save(job,{**base,'inputs':inputs});dest=out/'runs'/(arm+'-'+kind);m.host.run(w/'config.json',build,job,dest,'development');paths[kind]=dest
        actual=paths['observer'];bridge=paths['formal-bridge'];meta=read(actual/'native/result.json')
        proof=bank.check(actual/'native/heavy',bridge/'native/clean',meta,True);need(proof['passed'],'Observer/formal bridge numerical mismatch')
        observer_clean=read(actual/'native/clean/receipt.json');bridge_clean=read(bridge/'native/clean/receipt.json');observer_clean['study_cap']=bridge_clean['study_cap']=8
        need(m.native.endpoint(observer_clean)==m.native.endpoint(bridge_clean),'Observer clean/actual formal endpoint mismatch')
        need(trace(observer_clean,root['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')[1]==trace(bridge_clean,root['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')[1],'Observer/formal transaction mismatch')
        heavy=read(actual/'native/heavy/receipt.json');graph=[x for x in heavy['geometry'] if x['op']=='MUL_MAT'];need(graph,'No observed projection graph nodes')
        packed=[x for x in graph if x['name'].startswith('frontier_packed_')];loop4=[x for x in graph if x['name'].startswith('hs_backend_loop4_')]
        need(all(x['phase']=='PREFILL' for x in packed),'Unexpected packed verification in k3/q4 negative control')
        if core=='packed':need(packed and all(x['ne'][1]==4 and x['ne'][2]>=2 and x['sources'][0]['type']=='q8_0' and x['sources'][1]['type']=='f32' for x in packed),'Actual independent four-column packed groups not observed')
        else:need(loop4 and not packed,'Actual marked loop4 graph not observed')
        verify=[x for x in graph if x['phase']=='VERIFY' and x['sources'] and x['sources'][0]['type']=='q8_0']
        need(verify and all(x['ne'][1]<=4 and x['ne'][2]==1 for x in verify),'q4 projection negative-control shape')
        cut_hist={}
        for i in range(4):
            natural=read(w/'qualification-01/runs'/('Qwen-natural-'+arm)/'native'/f'dev-{i}-heavy'/'receipt.json')
            for e in natural['executions']:
                if e['phase']=='VERIFY':cut_hist[str(e['width'])]=cut_hist.get(str(e['width']),0)+1
        if cut=='LOCAL':need(set(cut_hist)=={'4'},'Actual LOCAL verification must retain physical q4')
        else:need(any(int(k)<4 for k in cut_hist),'Fixed unaligned natural counterexample must exercise SIMPLE rechunking')
        save(out/(arm+'-CHECKED.json'),dict(passed=True,arm=arm,numerical_bridge=proof,projection_graph_nodes=len(graph),packed_nodes=len(packed),marked_loop4_nodes=len(loop4),
            q4_verify_projection_nodes=len(verify),q4_wide_packing_active=False,actual_graph_evidence_sha256=sha(actual/'native/heavy/receipt.json'),
            independent_natural_qualification_verify_width_hist=cut_hist,aligned_short_diagnostic_may_coalesce_across_cuts=True,
            formal_bridge_receipt_sha256=sha(bridge/'native/clean/receipt.json'),observer_build_sha256=sha(a.observer_builds/core/'BUILD.json'),formal_build_sha256=sha(a.builds/core/'BUILD.json'),
            requested_generation_cap=8,verification_width=4,k=3,output_reserve=4,reference='Unchanged frozen R greedy prefix and complete independent per-prefix vectors/states',
            observation_scope='Actual scheduled GPU MUL_MAT graph descriptors and device buffers; not CUDA kernel-symbol profiling'))
        path=out/(arm+'-CHECKED.json');proofs.append(dict(path=str(path),sha256=sha(path)));print('PROJECTION_DISPATCH_PASS',arm,len(packed),len(loop4),flush=True)
    save(out/'CHECKED.json',dict(passed=True,all_four_D4_paths=True,proofs=proofs,formal_binaries_replaced=False,M2='NOT_RUN',R_binary_or_freeze_changed=False,
        historical_binary_operands_reverified=len(verified),finite_only=True))

if __name__=='__main__':main()
