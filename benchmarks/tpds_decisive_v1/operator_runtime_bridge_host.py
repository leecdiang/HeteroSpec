"""Bounded full-runtime bridge after adding the host-buffer CPU plugin."""
from operator_host import *

def main():
    rows=[]
    for model in ('8B','0.6B'):
        for arm in ('graph_tiles','backend_loop4','packed'):
            old=json.loads((OP/(arm+'-driver-v4')/'RUNTIME_BINDING.json').read_bytes());new=json.loads((OP/(arm+'-driver-v5')/'RUNTIME_BINDING.json').read_bytes())
            assert old['exe']==new['exe'] and all(new['modules'][n]==h for n,h in old['modules'].items())
            assert set(new['modules'])-set(old['modules'])=={'ggml-cpu.dll'}
            for trace in ([False,True] if model=='8B' else [False]):
                out=execute_operator('O-replay-v5-'+model+'-'+arm+('-trace' if trace else '-clean'),arm,dict(replay='E:/rtx170/witness-'+model+'/native',route=arm,diagnostic=trace),model,OP/(arm+'-driver-v5'))
                oracle=RUNS/('O-replay-v4-'+model+'-original-clean');comparison=[]
                for p in out.glob('*/*.bin'):
                    ref=oracle/p.relative_to(out);comparison.append(dict(path=str(p),sha256=sha(p),reference_sha256=sha(ref),equal=sha(p)==sha(ref)))
                assert len(comparison)==72
                row=dict(model=model,arm=arm,diagnostic=trace,all_equal=all(x['equal'] for x in comparison),comparisons=comparison)
                put(out/'ORACLE_COMPARISON.json',row);rows.append(row);print('full runtime bridge',model,arm,trace,row['all_equal'],flush=True)
    put(ROOT/'O-RUNTIME-BRIDGE.json',dict(rows=rows,all_equal=all(x['all_equal'] for x in rows),operator_executions=2592,unchanged_gpu_modules=True,new_module='ggml-cpu.dll',scope='same executable/core/CUDA/base, added host-buffer CPU registration; all model layers remain GPU'))

if __name__=='__main__':main()
