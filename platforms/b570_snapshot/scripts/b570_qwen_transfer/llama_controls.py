"""One retained boundary and one nonboundary Llama control using the new libraries."""
import collections, importlib.util
from execute import *
BASE=Path('I:/HeteroSpec/b570-llama-20261102')
def run(version):
    root=ROOT/'units'/('llama-controls-'+version)
    root.mkdir(parents=True)
    old=BASE/'combined-epoch-03/units/baseline-candidate'
    config=read(old/'NATIVE_CONFIG.json')
    used=('worker_timeout_seconds','min_vram_free_bytes','min_ram_free_bytes','reference_q8','prefix_extent','threads','target_gpu_layers','draft_gpu_layers','target','draft','reserve_shadow_context')
    write(root/'CONFIG.json',{k:config[k] for k in used if k in config})
    slots=[x for x in read(old/'SLOTS.json') if x['id'] in ('baseline/i0/C_QB/heavy','baseline/i2/C_QB/heavy')]
    assert len(slots)==2
    write(root/'SLOTS.json',slots)
    exe=ROOT/('build-'+version)/'bin/Release/b570_llama.exe'
    files=[exe,*exe.parent.glob('*.dll')]
    write(root/'FILES.json',{'files':[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in files]})
    write(root/'PREDICTION.json',{'utc':now(),'prediction':'Natural k3 cycle8/base765 in CodeContests/valid/108 forms 3+1 on all32 Vulkan layers. GSM8K/test/496 has no verification crossing. Both trajectories and all vectors match PR163 frozen results.'})
    for name,extra in [('admit',['--admit']),('controls',[])]:
        out=root/name;out.mkdir()
        cmd=[sys.executable,'-B',str(SUPERVISOR),'--manifest',str(root/'FILES.json'),'--receipt',str(out/'SUPERVISOR.json'),'--limit','900','--minimum-free-bytes',str(20*1024**3),str(exe),str(root/'CONFIG.json'),str(out/'native'),str(root/'SLOTS.json'),*extra]
        write(out/'COMMAND.json',cmd);write(LOCK,{'pid':os.getpid(),'unit':str(out),'utc':now()})
        with (out/'HOST.log').open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1000).returncode
        receipt=read(out/'SUPERVISOR.json')
        assert receipt['job_accounting']['active_processes']==0
        LOCK.unlink()
        result=read(out/'native/result.json');assert rc==0 and result['normal_cleanup_returned']
        loaded={Path(f['path']).name:f['sha256'] for f in receipt['loaded_module_hashes']}
        assert all(loaded[p.name]==sha(p) for p in files if p.suffix=='.dll')
    spec=importlib.util.spec_from_file_location('frozen_independent',BASE/'freeze-code-00/b570_llama_execution_v1/independent_qualification.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    results=[]
    for s in slots:
        p=root/'controls/native'/(s['id']+'.json')
        previous=module.record(old/'native'/(s['id']+'.json'));actual=module.record(p)
        assert previous['vectors']==actual['vectors'] and previous['endpoint']==actual['endpoint'] and previous['record']['cycles']==actual['record']['cycles']
        groups=collections.defaultdict(list)
        for g in read(p)['geometry']:
            if g['phase']=='VERIFY' and g['name'].startswith('hs_prefix_attention-'):
                assert g['scheduler_backend']=='Vulkan0'
                groups[g['caller_base'],int(g['name'].rsplit('-',1)[1])].append(g['ne'][1])
        if s['input']['id']=='CodeContests/valid/108':assert all(groups[765,layer]==[3,1] for layer in range(32))
        else:assert not groups
        results.append({'id':s['input']['id'],'saved_vectors':len(actual['vectors']),'cycles':len(actual['record']['cycles']),'all_equal_PR163':True,'grouped_bases':sorted({base for base,layer in groups})})
    write(root/'REGRESSION.json',dict(status='TWO_LLAMA_CONTROLS_PASS',cells=results));print(results,flush=True)
if __name__=='__main__':run(sys.argv[1])

