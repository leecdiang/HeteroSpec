"""Describe actual CUPTI activity and API correlation, never clean latency."""
import argparse,collections,statistics as st
from pathlib import Path
from common import load,save
from prepare_rtx import root
from audit_rtx import csvwrite as csvfile
def summarize(out):
    r=root();out=Path(out);out.mkdir();calls=[];kernels=[];hosts=[]
    for a in sorted((r/'attempts').iterdir()):
        path=a/'native/CUDA_TRACE.json'
        if not path.exists():continue
        tr=load(path);job=load(a/'JOB.json');record=load(a/'native/RECORD.json');assert not tr['overflow'] and tr['dropped']==0
        bycorr=collections.defaultdict(set);begin={};api=[]
        for e in tr['API_events']:
            bycorr[e['correlation']].add(e['call'])
            token=e['domain'],e['correlation']
            if e['site']==0:begin[token]=e
            elif token in begin:
                b=begin[token];assert e['QPC']>=b['QPC'];api.append(dict(name=e['name'],call=e['call'],QPC_interval_us=(e['QPC']-b['QPC'])*1e6/record['QPC_frequency'],status=e['status']))
        groups=collections.defaultdict(list);unmapped=0
        for k in tr['activities']:
            if k['kind'] not in [10,1]:continue
            assert k['end_ns']>=k['start_ns']>0 and k['end_ns']-k['start_ns']<120*10**9,'invalid CUPTI time'
            indices=bycorr[k['correlation']]
            ci=next(iter(indices)) if len(indices)==1 else None
            if ci is None:unmapped+=1
            groups[ci].append(k)
            if k['kind']==10:kernels.append(dict(task_id=a.name,context=job['context']['id'],layout=job['layout'],mode=job['graph_mode'],call=ci,name=k['name'],start_ns=k['start_ns'],end_ns=k['end_ns'],duration_us=(k['end_ns']-k['start_ns'])/1000,stream=k['stream'],graph_id=k['graph_id'],graph_node_id=k['graph_node_id'],correlation=k['correlation']))
        for row in record['calls']:
            i=row['index'];ks=[x for x in groups[i] if x['kind']==10];cp=[x for x in groups[i] if x['kind']==1];apis=[x for x in api if x['call']==i]
            calls.append(dict(task_id=a.name,case_id=job['context']['id'],layout=job['layout'],mode=job['graph_mode'],index=i,warmup=row['warmup'],kernels=len(ks),distinct_kernel_names=len({k['name'] for k in ks}),kernel_duration_sum_us=sum(k['end_ns']-k['start_ns'] for k in ks)/1000,kernel_span_us=(max(k['end_ns'] for k in ks)-min(k['start_ns'] for k in ks))/1000 if ks else None,copies=len(cp),copy_bytes=sum(k['bytes'] for k in cp),copy_duration_sum_us=sum(k['end_ns']-k['start_ns'] for k in cp)/1000,graph_launch_API_intervals_us=[x['QPC_interval_us'] for x in apis if x['name'].startswith('cudaGraphLaunch')],profiled_completed_graph_us=(row['sync_return']-row['begin'])*1e6/record['QPC_frequency'],profiled_explicit_sync_us=(row['sync_return']-row['compute_return'])*1e6/record['QPC_frequency']))
        hosts.append(dict(task_id=a.name,layout=job['layout'],mode=job['graph_mode'],case_id=job['context']['id'],activity_records=len(tr['activities']),unmapped_kernel_or_copy_records=unmapped,CUDA_API_events=len(tr['API_events']),kernel_names=sorted({k['name'] for k in tr['activities'] if k['kind']==10}),activity_enable=tr['activity_enable']))
    csvfile(out/'TRACE_CALLS.csv',calls);csvfile(out/'TRACE_KERNELS.csv',kernels);save(out/'TRACE_HOSTS.json',hosts);save(out/'SCOPE.json',dict(profile_hosts_with_trace=len(hosts),kernel_records=len(kernels),timeline='actual CUPTI12.8 callbacks+activity;ns device intervals and QPC API intervals kept separate',cost_use='not pooled with clean estimates;no counter/occupancy/traffic/TensorCore utilization inference',API_submit='nested runtime/driver intervals must not be summed',kernel_sum='sum of kernel durations is not union busy time',trace_vs_clean='different host observer,overhead not subtracted',external_review=False));print('trace hosts',len(hosts),'kernel records',len(kernels))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();summarize(a.out)
