"""CPU-only reconstruction of producer preparation samples and honest phase sums."""
import argparse,collections,csv,math,statistics
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from export_rtx import rows_csv

def read(p):
    with Path(p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def run(out):
    r=root();out=Path(out);out.mkdir(exist_ok=False);cases=load(r/'INPUTS.json')
    if (r/'HOLDOUT_INPUTS.json').exists():cases.update(load(r/'HOLDOUT_INPUTS.json'))
    cpu=r/'CPU_PREPARATION';rows=[];frozen=load(cpu/'FREEZE.json');source=(r/'source_runtime/cpu_preparation.cpp') if (r/'source_runtime/cpu_preparation.cpp').exists() else V/'cpu_preparation.cpp';assert sha(source)==frozen['source_sha256']
    for cid,c in cases.items():
        for repeat in range(2):
            folder=cpu/(cid+f'-r{repeat}');result=load(folder/'native/CPU_PREPARATION.json');life=load(folder/'host.LIFETIME.json');assert result['GPU_calls']==result['CUDA_loads']==0 and life['exit_code']==0 and life['error'] is None;assert len(result['rows'])==65
            for role in ['Q','K','V','mask']:assert (folder/f'native/prepared_{role}.bin').read_bytes()==(r/'inputs'/cid/(role+'.bin')).read_bytes()
            last=0;values=[]
            for i,sample in enumerate(result['rows']):
                assert sample['index']==i and sample['warmup']==(i==0) and sample['all_full_bytes_exact'] and sample['begin']>=last and sample['end']>sample['begin'] and result['QPC_frequency']>0;last=sample['end']
                if i:values.append((sample['end']-sample['begin'])*1e6/result['QPC_frequency'])
            rows.append(dict(case_id=cid,storage=c['storage'],repeat=repeat,mean_us=statistics.mean(values),median_us=statistics.median(values),p95_us=sorted(values)[60],max_us=max(values),cold_output_allocation_us=result['cold_output_allocation_ticks']*1e6/result['QPC_frequency'],all_bytes_exact=True,GPU_calls=0))
    rows_csv(out/'CPU_HOSTS.csv',rows);assert (out/'CPU_HOSTS.csv').read_bytes()==(cpu/'HOSTS.csv').read_bytes(),'CPU preparation independent reconstruction'
    prep={cid:statistics.mean(x['mean_us'] for x in rows if x['case_id']==cid) for cid in cases};hosts=read(r/'analysis_final/HOSTS.csv');phase=[];paired=collections.defaultdict(dict)
    for h in hosts:
        if h['stage'] not in ['confirm','holdout'] or h['numerical_qualified']!='True' or h.get('environment_qualified')!='True':continue
        value=float(h['input_inclusive_first_call_phase_sum_us'])-float(h['CPU_materialize_us'])+prep[h['case_id']];row=dict(task_id=h['task_id'],stage=h['stage'],case_id=h['case_id'],block=int(h['block']),session_id=h['session_id'],arm=h['arm'],CPU_common_prepare_us=prep[h['case_id']],replaced_preformatted_copy_us=float(h['CPU_materialize_us']),common_producer_phase_sum_us=value,scope='separatelymeasuredCPUprepare+nativeupload/firstcall;notintegratedtransaction');phase.append(row);paired[h['stage'],h['case_id'],int(h['block'])][h['arm']]=row
    rows_csv(out/'COMMON_PRODUCER_PHASE_SUMS.csv',phase);plan=load(r/'plan.json');contrasts=[]
    for stage in ['confirm','holdout']:
        for subset in ['q1','q>1']:
            ids=[c['case_id'] for c in plan['cases'] if c['cohort']==('confirmation' if stage=='confirm' else 'holdout') and (c['q']==1 if subset=='q1' else c['q']>1)]
            if not ids:continue
            expected=len(ids)*8
            for label,x,y in [('AA','QB_A','QB_B'),('QB_QH','QB_A','QH_C'),('QB_QH_alt','QB_B','QH_C'),('PQ_QB','PQ','QB_A'),('PQ_QB_alt','PQ','QB_B')]:
                logs=[];diffs=[]
                for cid in ids:
                    for b in range(8):
                        arms=paired.get((stage,cid,b),{})
                        if set(arms)!=set(['PQ','QB_A','QH_C','QB_B']):continue
                        a,z=arms[x]['common_producer_phase_sum_us'],arms[y]['common_producer_phase_sum_us'];logs.append(math.log(a/z));diffs.append(a-z)
                complete=len(logs)==expected;contrasts.append(dict(stage=stage,stratum=subset,comparison=label,pairs=len(logs),expected_pairs=expected,complete=complete,geometric_ratio=math.exp(statistics.mean(logs)) if complete else None,mean_difference_us=statistics.mean(diffs) if complete else None,scope='descriptive phase sum;CPUcomponent shared across blocks;no newindependentGPUmeasurements'))
    rows_csv(out/'COMMON_PRODUCER_AGGREGATES.csv',contrasts);save(out/'AUDIT.json',dict(status='CPU_BYTES_AND_SAMPLES_RECONSTRUCTED',CPU_hosts=len(rows),preparation_occurrences=len(rows)*65,measured_preparations=len(rows)*64,GPU_calls=0,CUDA_loads=0,source='canonicalQ and already available fullKV;maskconstruct included;notdecoderoperandproduction',statistical_limit='CPU followup not simultaneous withGPU;2CPUprocesses/case;commonphase sums not actualtransactionwall'))
    print('CPU preparation reconstruction PASS',len(rows),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();run(a.out)
