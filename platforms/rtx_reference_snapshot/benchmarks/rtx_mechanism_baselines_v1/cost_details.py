"""CPU separation of real QPC setup/warmup and profiled capture API boundaries."""
import argparse,collections,statistics as st
from pathlib import Path
from common import load,save
from prepare_rtx import root
from export_measurements import csvfile
def main(out):
    out=Path(out);out.mkdir();rows=[];apirows=[]
    for a in sorted((root()/'attempts').iterdir()):
        p=a/'native/RECORD.json'
        if not p.exists():continue
        rr=load(p);t=load(a/'STARTED.json')['task'];f=1e6/rr['QPC_frequency'];warm=[x for x in rr['calls'] if x['warmup']];formal=[x for x in rr['calls'] if not x['warmup']]
        rows.append(dict(task_id=a.name,stage=t['stage'],case_id=t['case_id'],layout=t['layout'],mode=t['graph_mode'],profile=rr['profile'],warmups=len(warm),formal_calls=len(formal),warmup_completed_graph_sum_us=sum(x['sync_return']-x['begin'] for x in warm)*f,first_warmup_completed_graph_us=(warm[0]['sync_return']-warm[0]['begin'])*f if warm else None,second_warmup_completed_graph_us=(warm[1]['sync_return']-warm[1]['begin'])*f if len(warm)>1 else None,formal_completed_graph_mean_us=st.mean((x['sync_return']-x['begin'])*f for x in formal),formal_resident_call_mean_us=st.mean((x['readback_return']-x['begin'])*f for x in formal),integrated_q_update_mean_us=st.mean((x['readback_return']-x['transaction_begin'])*f for x in formal) if rr['integrated_q_update'] else None,unassigned_between_Q_upload_and_graph_mean_us=st.mean((x['begin']-x['Q_upload_complete'])*f for x in formal) if rr['integrated_q_update'] else None,**{k+'_us':v*f for k,v in rr['cost_ticks'].items()}))
        if rr['profile']:
            tr=load(a/'native/CUDA_TRACE.json');starts={}
            for e in tr['API_events']:
                if e['domain']!=2 or not any(e['name'].startswith(n) for n in ['cudaStreamBeginCapture','cudaStreamEndCapture','cudaGraphInstantiate','cudaGraphExecUpdate','cudaGraphLaunch']):continue
                key=e['domain'],e['correlation']
                if e['site']==0:starts[key]=e
                elif key in starts:
                    b=starts[key];assert e['QPC']>=b['QPC'];apirows.append(dict(task_id=a.name,case_id=t['case_id'],layout=t['layout'],mode=t['graph_mode'],call=e['call'],name=e['name'],status=e['status'],profiled_API_interval_us=(e['QPC']-b['QPC'])*f))
    csvfile(out/'WARMUP_AND_SETUP.csv',rows);csvfile(out/'PROFILED_GRAPH_API_COSTS.csv',apirows)
    save(out/'SCOPE.json',dict(setup='all actual warmup costs retained;first/second calls are NOT isolated clean capture latency',capture='actual CUPTI-observed capture/end/instantiate/update API costs include observer overhead;never pooled with clean distributions',amortization='No exact clean-only isolated capture counter;no exact amortization point asserted. Warmup and cold costs remain published.',resident='QPC graph entry->compute return->device sync',resident_call='same entry through full ordinary readback',P0='continuous preallocated complete Q copy/transpose->upload/sync->compute/sync->ordinary readback;resident KV/mask;Q producer UNKNOWN',CPU_GPU_phase_sum='not used as integrated P0 transaction'))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();main(a.out)
