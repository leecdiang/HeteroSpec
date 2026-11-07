"""CPU-only followup to charge common-producer Q packing and mask construction.

Primary GPU boundaries/data remain unchanged. This is a separately measured phase
sum, not an integrated transaction or a timing qualification rerun.
"""
import argparse,statistics,subprocess,time
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from collect import Child,helper,env,git,cas
from export_rtx import rows_csv

def run():
    r=root();assert not (r/'WORKER.lock').exists(),'do not compile/measure beside clean timing';s=load(r/'RUN_SPEC.json');out=r/'CPU_PREPARATION';out.mkdir();source=V/'cpu_preparation.cpp';cmd=[s['compiler']['path'],'c++','-O3','-std=c++17','-I'+s['vendor_include'],str(source),'-lpsapi','-o',str(V/'build/cpu_preparation.exe')];t=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=600);save(out/'BUILD.json',dict(command=cmd,exit=p.returncode,stderr=p.stderr.decode(errors='replace'),seconds=time.monotonic()-t,GPU_calls=0));assert p.returncode==0
    save(out/'FREEZE.json',dict(source_sha256=sha(source),adapter_sha256=sha(V/'cpu_preparation.py'),native_sha256=sha(V/'build/cpu_preparation.exe'),commit=git('rev-parse','HEAD'),scope='two fresh CPU processes per available input;1warmup+64preparations;fulltargetbytes each occurrence',GPU_calls=0));cases=load(r/'INPUTS.json')
    if (r/'HOLDOUT_INPUTS.json').exists():cases.update(load(r/'HOLDOUT_INPUTS.json'))
    rows=[]
    for cid,c in cases.items():
        for rep in range(2):
            folder=out/(cid+f'-r{rep}');folder.mkdir();save(folder/'JOB.json',dict(context=c));worker=Child(helper());worker.run([str(V/'build/cpu_preparation.exe'),str(folder/'JOB.json'),str(folder/'native')],folder/'host',120,env(s),s['host_RAM_bytes']);result=load(folder/'native/CPU_PREPARATION.json');assert result['CUDA_loads']==0 and result['status']=='PASS'
            for role in ['Q','K','V','mask']:assert (folder/f'native/prepared_{role}.bin').read_bytes()==(Path(c['root'])/(role+'.bin')).read_bytes()
            cas(folder/'native')
            values=[(x['end']-x['begin'])*1e6/result['QPC_frequency'] for x in result['rows'] if not x['warmup']];rows.append(dict(case_id=cid,storage=c['storage'],repeat=rep,mean_us=statistics.mean(values),median_us=statistics.median(values),p95_us=sorted(values)[60],max_us=max(values),cold_output_allocation_us=result['cold_output_allocation_ticks']*1e6/result['QPC_frequency'],all_bytes_exact=True,GPU_calls=0));print('CPU preparation',cid,rep,flush=True)
    rows_csv(out/'HOSTS.csv',rows);save(out/'ENDED.json',dict(hosts=len(rows),GPU_calls=0,CUDA_loads=0,all_full_bytes_exact=True,source_available_state='canonical logicalQ and full frozenKV;KV production and decoder state not included',cost_view='CPU prep mean can replace preformatted CPU_materialize in a separately labeled phase sum;do not add both',cold_allocation='separate;preallocated resident targetbuffers during64preparations',occurrences='all65 byte-identical preparations perhost refer to complete retained prepared files;source matches frozen input'))
if __name__=='__main__':run()
