"""P0: authentic selected PR116 data, existing tools, immutable source provenance."""
import datetime,hashlib,json,os,shutil,subprocess,sys,uuid
from pathlib import Path
V=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def save(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pin(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def main():
    root=Path('D:/hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3')
    assert not (root/'RUN_SPEC.json').exists(),'existing prepared dispatch'
    save(root/'P0_PATH_REPAIR.json',dict(first_prepare_failed='import libraries live in original s1b_cost_v1 rather than monitor overlay',GPU_calls=0,prior_directory_preserved=True))
    prior=Path('D:/hs116-s1b/benchmarks/rtx_lowering_envelope_v1/s1b_monitor_repair_v2');old=Path('D:/hs114-bridge-v2/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v2')
    f=load(prior/'F0.json');plan=load(prior/'PLAN.json');authentic=load(old/'PLAN.json');index=load(old/'REFERENCE_INDEX.json')
    assert len(authentic['descriptors'])==24 and {d['id'] for d in authentic['descriptors']}=={d['id'] for d in plan['descriptors']}
    analysis=load(old/'closure/ANALYSIS.json');assert analysis['completed_qualified']==240
    provenance=[]
    for name in ['graph_base.h','hs113_graph.h','core_gate.h']:
        src=prior/name;data=subprocess.check_output(['git','-C','D:/hs120','show','8a4cbb4246323a3f159f94cae8c92544d5a215dc:benchmarks/rtx_lowering_envelope_v1/s1b_monitor_repair_v2/'+name]);assert src.read_bytes()==data
        (V/name).write_bytes(data);provenance.append(dict(name=name,source_commit='8a4cbb4246323a3f159f94cae8c92544d5a215dc',sha256=sha(src)))
    contexts=[];inputs={}
    for d in authentic['descriptors']:
        assert d['id'] in index;ref={}
        for layout in ['PQ','QB','QH_C']:
            slot=next(s for s in plan['clean_slots'] if s['descriptor']==d['id'] and s['layout']==layout)
            ref[layout]=slot['ordinary_reference'];assert sha(ref[layout]['path'])==ref[layout]['sha256']
        for row in d['input_files']:assert sha(row['path'])==row['sha256'];inputs[row['path']]=row
        meta=load(Path(d['root'])/'snapshot.json');assert meta==d['metadata']
        contexts.append(dict(id=d['id'],root=d['root'],family=d['family'],phase=d['phase'],q=d['q'],layer=d['layer'],metadata=meta,inputs=d['input_files'],references=ref))
    for name,digest in f['numerical_DLLs'].items():assert sha(Path(f['runtime_directory'])/name)==digest
    imports=V/'build';imports.mkdir(exist_ok=True)
    for name in ['libggml.dll.a','libggml-base.dll.a']:shutil.copyfile(prior.parent/'s1b_cost_v1'/name,imports/name)
    compiler=Path('D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe')
    assert shutil.disk_usage(root).free>10*1024**3
    spec=dict(schema=1,run_id='rtx-reference-envelope-v2',execution_id=root.name,root=str(root),start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),start_epoch=__import__('time').time(),global_seconds=28800,delivery_reserve_seconds=3600,storage_bytes=8*1024**3,host_RAM_bytes=8*1024**3,native_timeout_seconds=120,stage_max=dict(D0_hosts=48,D0_calls=1600,N1_hosts=216,N1_calls=7344,T1_hosts=432,T1_calls=16416),runtime_directory=f['runtime_directory'],numerical_DLLs=f['numerical_DLLs'],python=pin(sys.executable),compiler=pin(compiler),ggml_include='D:/hs113/benchmarks/rtx_lowering_envelope_v1/native/source/ggml/include',vendor_include='D:/hs113/benchmarks/rtx_lowering_envelope_v1/native/source/vendor',contexts=contexts,reference_index=pin(old/'REFERENCE_INDEX.json'),PR116_plan=pin(old/'PLAN.json'),PR116_analysis=pin(old/'closure/ANALYSIS.json'),parent_PR118='8a4cbb4246323a3f159f94cae8c92544d5a215dc',source_provenance=provenance,GGML_CUDA_DISABLE_GRAPHS='1',practical_ratio=1.02,practical_us=1.0,raw_retention='RAW_LOCAL_ONLY',no_W1=True)
    save(root/'RUN_SPEC.json',spec);save(V/'LOCAL_RUN.json',dict(root=str(root)))
    save(V/'INVENTORY.json',dict(execution_id=spec['execution_id'],python=spec['python'],compiler=spec['compiler'],reference_index=spec['reference_index'],PR116_plan=spec['PR116_plan'],context_count=len(contexts),input_files=len(inputs),input_unique_bytes=sum(r['bytes'] for r in {r['sha256']:r for r in inputs.values()}.values()),runtime=f['runtime_directory'],numerical_DLLs=f['numerical_DLLs'],source_provenance=provenance,free_disk_bytes=shutil.disk_usage(root).free,raw_root=str(root),new_GPU_calls=0,PR104_snapshots='exact local authenticated restore referenced by PR116',missing=['no admitted kernel profiler','no recovered RTX reduction DAG']))
    print(root)
if __name__=='__main__':main()
