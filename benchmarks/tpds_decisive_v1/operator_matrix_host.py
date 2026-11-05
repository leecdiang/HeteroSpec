"""Fixed real-operand qualification, separate tracing, and clean replay costs."""
from operator_host import *
import sys,collections
def main():
    comparisons=[];traces=[]
    for model in ('8B','0.6B'):
        for arm in ('original','graph_tiles','backend_loop4','packed'):
            for diagnostic in ([False] if arm=='original' else [False,True]):
                label='O-replay-v3-'+model+'-'+arm+('-trace' if diagnostic else '-clean')
                manifest=dict(replay='E:/rtx170/witness-'+model+'/native',route='scalar' if arm=='original' else arm,diagnostic=diagnostic)
                out=execute_operator(label,arm,manifest,model)
                if arm=='original':continue
                oracle=RUNS/('O-replay-v3-'+model+'-original-clean')
                for p in out.glob('*/*.bin'):
                    expected=oracle/p.relative_to(out);equal=sha(p)==sha(expected)
                    comparisons.append(dict(model=model,arm=arm,diagnostic=diagnostic,path=str(p),oracle=str(expected),equal=equal,sha256=sha(p),oracle_sha256=sha(expected)))
                if diagnostic:
                    for p in out.glob('*/*-gpu.json'):
                        events=json.loads(p.read_bytes());kernels=collections.Counter(x['name'] for x in events if x['kind']=='kernel')
                        assert kernels,'no actual GPU trace';traces.append(dict(model=model,arm=arm,path=str(p),kernels=dict(kernels),copies=sum(x['kind']=='copy' for x in events)))
                put(out/'ORACLE_COMPARISON.json',[x for x in comparisons if x['model']==model and x['arm']==arm and x['diagnostic']==diagnostic])
                print('operator complete',model,arm,'trace' if diagnostic else 'clean','equal',all(x['equal'] for x in comparisons if x['model']==model and x['arm']==arm and x['diagnostic']==diagnostic),flush=True)
    put(ROOT/'O-REAL-OPERAND-QUALIFICATION.json',dict(comparisons=comparisons,traces=traces,all_equal=all(x['equal'] for x in comparisons),scope='isolated saved real operands only; whole-model active state and natural service still require independent qualification',clean_profiler_initialized=False))
if __name__=='__main__':main()
