"""CPU fault injection into copies of actual new RTX raw; never GPU retries."""
import copy,json,shutil,tempfile
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from runner import audit
def main():
    r=root();source=r/'attempts/qualification-0004/native';job=load(source.parent/'JOB.json');c=job['context'];base,receipt=audit(source,c,job);assert receipt['numerical_qualified'];before=sha(source/'RECORD.json');results=[]
    cases=['input_mutation','ordinary_truncation','output_nonfinite','unsupported_node','wrong_placement','missing_IAT','graph_drift','clock_reversal','module_drift']
    for kind in cases:
        with tempfile.TemporaryDirectory() as folder:
            n=Path(folder)/'native';shutil.copytree(source,n)
            def update(name,fn):
                p=n/name;obj=load(p);fn(obj);p.write_text(json.dumps(obj),encoding='utf8')
            if kind=='input_mutation':
                p=n/'input_Q_before.bin';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
            elif kind=='ordinary_truncation':
                p=n/'ordinary_all.bin';p.write_bytes(p.read_bytes()[:-1])
            elif kind=='output_nonfinite':
                p=n/'ordinary_all.bin';b=bytearray(p.read_bytes());b[:4]=bytes.fromhex('0000807f');p.write_bytes(b)
            elif kind=='unsupported_node':update('GRAPH.json',lambda g:g['nodes'][0].update(CUDA_support=False))
            elif kind=='wrong_placement':update('GRAPH.json',lambda g:g['addresses'][0].update(CUDA_owned=False))
            elif kind=='missing_IAT':update('RECORD.json',lambda rec:rec['plugin_core_IAT'].pop())
            elif kind=='graph_drift':update('GRAPH.json',lambda g:g['nodes'][0]['op_params'].__setitem__(0,g['nodes'][0]['op_params'][0]^1))
            elif kind=='clock_reversal':update('RECORD.json',lambda rec:rec['calls'][0].update(sync_return=rec['calls'][0]['begin']-1))
            elif kind=='module_drift':update('RECORD.json',lambda rec:rec['modules_end'].append('wrong-module.dll'))
            try:audit(n,c,job)
            except (AssertionError,ValueError,KeyError) as exc:results.append(dict(case=kind,rejected=True,reason=str(exc)))
            else:raise AssertionError('corrupted retained evidence accepted:'+kind)
    assert sha(source/'RECORD.json')==before
    save(V/'RAW_AUDIT_TESTS.json',dict(status='PASS',baseline_actual_new_attempt='qualification-0004',baseline_evidence_sha256=sha(source.parent/'EVIDENCE.json'),tests=len(results),negative_cases=results,original_raw_unchanged=True,GPU_calls=0,fixture_copies='temporary CPU-only injected copies;reconstructible from code and retained actual raw'))
    print('raw negative tests',len(results),'PASS')
if __name__=='__main__':main()
