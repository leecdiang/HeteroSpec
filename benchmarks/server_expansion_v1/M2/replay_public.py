"""Recompute descriptive results from the complete public sanitized bundle.

Uses recorded scalar values and raw-to-derived SHA commitments. Does not execute
models, validate original private GPU allocation, or requalify numerical state.
"""
from pathlib import Path
from collections import Counter
import argparse,copy,gzip,hashlib,json,sys

def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def records(path):
    header='{"schema":"linux-transfer.public-text-bundle.v1","records":[';decoder=json.JSONDecoder();buffer=''
    with gzip.open(path,'rt',encoding='utf8')as f:
        assert f.read(len(header))==header
        while True:
            block=f.read(4*1024**2);eof=not block;buffer+=block
            while True:
                buffer=buffer.lstrip(' \t\r\n,')
                if buffer.startswith(']}'):
                    assert not(buffer[2:]+f.read()).strip();return
                if not buffer:break
                try:x,end=decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    assert not eof,'Incomplete public record';break
                buffer=buffer[end:];yield x
            assert not eof,'Truncated public bundle'

def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--work',default='m2-run-03');a=p.parse_args()
    base=a.bundle.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    scope=json.loads((base/'EXPORT_SCOPE.json').read_text());ti=json.loads((base/'TEXT_INDEX.json').read_text())
    for name,key in [('scientific-records.json.gz','bundle_sha256'),('TEXT_INDEX.json','text_index_sha256'),('BINARY_CAPTURE_INDEX.json','binary_index_sha256')]:assert sha(base/name)==scope[key]
    index={x['path']:x for x in ti['files']};seen=set();selected={};driver='m2-driver-source-'+a.work.rsplit('-',1)[1]
    for record in records(base/'scientific-records.json.gz'):
        key=record['path'];assert key not in seen and key in index;seen.add(key);b=record['text'].encode('utf8');item=index[key]
        assert len(b)==item['exported_bytes'] and hashlib.sha256(b).hexdigest()==item['exported_sha256']
        if key.startswith(a.work+'/panel-01/') or key==a.work+'/ROOT_SELECTION.json':
            if key.endswith('.json'):selected[key]=json.loads(record['text'])
            elif key.endswith('/resources.jsonl'):selected[key]=[json.loads(x)for x in record['text'].splitlines()if x]
        elif key in [driver+'/'+name for name in ('panel.py','harness.py','qualify.py')]:
            dest=out/'analysis-source'/Path(key).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(b)
    assert len(seen)==scope['text_files']==len(index)
    prefix=a.work+'/panel-01/';plan=selected[prefix+'PLAN.json'];checked=selected[prefix+'CHECKED.json'];oracle=selected[a.work+'/ROOT_SELECTION.json'];derived=[]
    def raw_sha(key,expected):assert index[key]['raw_sha256']==expected,'Different original raw commitment '+key
    for worker,prior in zip(plan['workers'],checked):
        assert worker['id']==prior['id'] and prior['status']=='COMPLETE';row=copy.deepcopy(prior)
        job_key=prefix+worker['job'];job=selected[job_key];raw_sha(job_key,worker['job_sha256'])
        dest=prefix+'runs/'+worker['id']+'/';meta=selected[dest+'native/result.json'];raw_sha(dest+'native/result.json',prior['native_result_sha256'])
        assert selected[dest+'HOST.json']==prior['actual_host'] and selected[dest+'CLOCKS.json']==prior['actual_result_clocks']
        assert meta['model_load_s']==prior['model_load_s'] and meta['pool_setup_s']==prior['pool_setup_s']
        telemetry=selected[dest+'resources.jsonl']
        assert max((float(x['gpu']['memory.total'])-float(x['gpu']['memory.free']))*1024**2 for x in telemetry)==prior['peak_sampled_total_minus_free_bytes']
        assert min(float(x['gpu']['memory.free'])*1024**2 for x in telemetry)==prior['minimum_sampled_free_bytes']
        calls=[]
        for i,(key,entry,old)in enumerate(zip(worker['primers']+worker['roots'],job['inputs'],prior['calls'])):
            receipt_key=dest+'native/'+entry['name']+'/receipt.json';r=selected[receipt_key];raw_sha(receipt_key,old['receipt_sha256'])
            expected=oracle['expected'][key]['receipt'];assert r['ids']==expected['ids'] and r['eog']==expected['eog'] and r['stop_reason']==expected.get('terminal_kind',expected.get('stop_reason'))
            assert r['proposal_mode']==worker['proposal_mode'] and r['k']==worker['k'] and r['target_output_reserve']==8
            assert all(v==0 for v in r['observed_API_calls_within_service'].values())
            if len(r['cycles'])>=2:assert r['graphs_reused']>0
            physical=copy.deepcopy(old['physical']);physical['verify_width_histogram']=dict(Counter(str(e['width'])for e in r['executions']if e['phase']=='VERIFY'))
            physical['target_histogram']=dict(Counter(str(e['width'])for e in r['executions']));physical['draft_histogram']=r['draft_physical_width_hist']
            physical['target_rows']=sum(int(k)*v for k,v in r['target_physical_width_hist'].items());physical['draft_rows']=sum(int(k)*v for k,v in r['draft_physical_width_hist'].items())
            physical.update(graphs_built=r['graphs_built'],graphs_reused=r['graphs_reused'],k=r['k'],reserve=r['target_output_reserve'],proposal_mode=r['proposal_mode'])
            assert physical==old['physical']
            call={**old,'service_s':r['service_seconds'],'request_s':r['request_seconds'],'target_phases':r['target_phases'],'draft_phases':r['draft_phases'],
                'physical':physical,'cycles':len(r['cycles']),'accepted_proposals':sum(c['accepted']for c in r['cycles']),
                'proposed':sum(len(c['proposals'])for c in r['cycles']),'rejected_cycles':sum(c['rejected']for c in r['cycles']),
                'output_tokens':len(r['ids']),'stop_reason':r['stop_reason']}
            assert call==old;calls.append(call)
        row['calls']=calls;derived.append(row)
    sys.path.insert(0,str(out/'analysis-source'));import panel
    result=panel.analyze(derived);assert canonical(result)==canonical(selected[prefix+'RESULTS.json'])
    assert result['live']['measurements']==64 and result['replay']['measurements']==32
    (out/'RESULTS_REPRODUCED.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    proof=dict(passed=True,public_text_records_checked=len(seen),native_request_receipts_recomputed=144,
        bundle_sha256=scope['bundle_sha256'],analyzer_exported_sha256=index[driver+'/panel.py']['exported_sha256'],
        raw_SHA_binding='Raw receipt commitments checked against TEXT_INDEX; source values unchanged, host paths/UUID remain redacted',
        new_native_jobs=0,model_forwards=0,scope='Exact fixed descriptive request statistics/memory from public derived receipts; directly recorded adapter/process clocks retained, not independently reconstructed monotonic timestamps. No numerical state/allocation requalification.')
    (out/'CHECKED.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
if __name__=='__main__':main()
