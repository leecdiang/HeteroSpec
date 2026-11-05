"""Fixed real-operand qualification, separate tracing, and clean replay costs."""
from operator_host import *
import sys,collections,gzip
def main():
    # Do not contaminate clean microbenchmarks with the preceding bulk archive.
    if Path('D:/rtx184-qualification/M-root3/QUALIFICATION.json').exists():
        barrier=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx184-evidence/root3-retirement.json');began=time.monotonic()
        while not barrier.exists():
            assert time.monotonic()-began<1800,'archive barrier not completed';time.sleep(2)
    comparisons=[];traces=[]
    published=json.loads(gzip.decompress((Path(__file__).resolve().parent.parent/'rtx_operator_frontier_v1/execution/evidence/operands.json.gz').read_bytes()))
    for row in published:
        p=Path('E:/rtx170')/('witness-'+row['model'])/'native'/row['descriptor']['weight']['name']
        for name,h in row['inputs'].items():assert sha(p/(name+'.bin'))==h,('saved operand provenance',p,name)
    for model in ('8B','0.6B'):
        for arm in ('original','graph_tiles','backend_loop4','packed'):
            for diagnostic in ([False] if arm=='original' else [False,True]):
                label='O-replay-v4-'+model+'-'+arm+('-trace' if diagnostic else '-clean')
                manifest=dict(replay='E:/rtx170/witness-'+model+'/native',route='scalar' if arm=='original' else arm,diagnostic=diagnostic)
                existing=RUNS/label
                if (existing/'RECOVERED_COMPLETED_NATIVE.json').exists():
                    recovery=json.loads((existing/'RECOVERED_COMPLETED_NATIVE.json').read_bytes());assert json.loads((existing/'input.json').read_bytes())==manifest
                    for name,h in recovery['file_pins'].items():assert sha(existing/name)==h
                    out=existing
                else:out=execute_operator(label,arm,manifest,model)
                if arm=='original':
                    for row in published:
                        if row['model']!=model:continue
                        for route in row['routes']:
                            if route['route']=='scalar' and route['q'] in (4,8,16,32):assert sha(out/row['descriptor']['weight']['name']/(str(route['q'])+'.bin'))==route['sha'],'old scalar replay changed'
                    continue
                oracle=RUNS/('O-replay-v4-'+model+'-original-clean')
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
