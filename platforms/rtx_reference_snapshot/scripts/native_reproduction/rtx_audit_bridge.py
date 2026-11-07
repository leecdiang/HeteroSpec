"""Independent read-only raw reconstruction: no import of the frozen estimator."""
import argparse,collections,csv,hashlib,json,math,pathlib,statistics
P=pathlib.Path
def read(p):return json.loads(P(p).read_bytes())
def sha(p):
    with P(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);ap.add_argument('registration',type=P);ap.add_argument('analysis',type=P);ap.add_argument('out',type=P);a=ap.parse_args()
    freeze=read(a.registration/'FREEZE.json');state=read(a.root/'formal/CHECKPOINT.json');assert state['status']=='COMPLETE';seen=set();cells=collections.defaultdict(list);rawseconds={};processes=[];references={}
    for s in range(6):
        saved=state['sessions'][str(s)];p=P(saved['result']);assert sha(p)==saved['sha256'];data=read(p);plan=read(a.registration/f'SESSION_{s}.json');assert len(data['requests'])==len(plan)==156
        groups=collections.defaultdict(dict)
        for expected,row in zip(plan,data['requests']):
            assert row['slot']==expected;sid=expected['slot_id'];assert sid not in seen;seen.add(sid);rawseconds[sid]=row['service_seconds']
            assert row['service_seconds']>0 and row['request_seconds']>0 and row['request_seconds']<=row['service_seconds']
            if expected['reference'] not in references:
                full=read(expected['reference']);references[expected['reference']]={k:full[k] for k in ('ids','eog','length','terminal_id','stop_reason','cycles','target_final_kv','draft_final_kv')};del full
            ref=references[expected['reference']]
            for key in ('ids','eog','length','terminal_id','stop_reason','cycles','target_final_kv','draft_final_kv'):assert row[key]==ref[key],sid+' differs '+key
            if expected['category']=='measurement':groups[(expected['task'],expected['k'],expected['lifecycle'])][expected['label']]=row['service_seconds']
        assert len(groups)==48
        for (task,k,life),values in groups.items():
            assert set(values)=={'PQ_A','PQ_B','QB'}
            cells[k,life,s].append(math.log(values['QB']/((values['PQ_A']+values['PQ_B'])/2)))
        expected_dlls=freeze['files'];loaded={}
        for module in data['modules']:
            path=P(module)
            if path.name.lower() in {'ggml-cuda.dll','ggml-base.dll','cublas64_12.dll','cublaslt64_12.dll','cudart64_12.dll'}:
                expected_path=next(x for x in expected_dlls if P(x).name.lower()==path.name.lower());assert path.resolve()==P(expected_path).resolve();assert sha(path)==expected_dlls[expected_path];loaded[path.name]=sha(path)
        assert len(loaded)==5
        receipt=read(a.root/(p.parent.name+'-PROCESS.json'));assert receipt['cleanup'] and receipt['status']=='COMPLETE' and receipt['exit_code']==0
        processes.append(dict(session=s,pid=data['pid'],requests=156,loaded_required_modules=loaded,cleanup=True))
    summary=read(a.analysis/'ANALYSIS.json');compares=[]
    for c in summary['cells']:
        per_session=[math.fsum(cells[c['k'],c['lifecycle'],s])/12 for s in range(6)];value=math.exp(math.fsum(per_session)/6)
        assert abs(value-c['ratio'])<1e-12
        for actual,reported in zip(per_session,c['session_ratios']):assert abs(math.exp(actual)-reported)<1e-12
        compares.append(dict(k=c['k'],lifecycle=c['lifecycle'],ratio=value))
    with (a.analysis/'TIMING.csv').open(newline='',encoding='utf-8') as f:table=list(csv.DictReader(f))
    assert len(table)==936 and {x['slot_id'] for x in table}==seen
    for row in table:assert float(row['service_seconds'])==rawseconds[row['slot_id']]
    result=dict(status='PASS',requests=936,measurements=864,warmups=72,processes=processes,independently_reconstructed_ratios=compares,scope='Independent Python raw endpoint/state/time/module/point-estimate reconstruction. Bootstrap computed by frozen estimator, not independently reimplemented. No external auditor or full CUDA library source certification.')
    assert not a.out.exists();a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('INDEPENDENT_RAW_AUDIT_PASS',936)
if __name__=='__main__':main()
