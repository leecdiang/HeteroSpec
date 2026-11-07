#!/usr/bin/env python3
"""Run original CPU auditors against restored raw bytes; never load models or native code."""
import argparse,hashlib,importlib.util,json,math,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];STAGE=ROOT/'output/raw_restore'
class WindowsEvidencePath(type(Path())):
    def __new__(cls,*args,**kwargs):return super().__new__(cls,*[str(x).replace('\\','/') for x in args],**kwargs)
    def __truediv__(self,key):return WindowsEvidencePath(str(self),str(key).replace('\\','/'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def differences(a,b,path=''):
    if type(a)!=type(b):return [dict(path=path,expected=a,actual=b)]
    if isinstance(a,dict):
        if set(a)!=set(b):return [dict(path=path,keys_expected=sorted(a),keys_actual=sorted(b))]
        return [d for k in a for d in differences(a[k],b[k],path+'/'+k)]
    if isinstance(a,list):
        if len(a)!=len(b):return [dict(path=path,length_expected=len(a),length_actual=len(b))]
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [dict(path=path,expected=a,actual=b)]

def compare(actual,expected,skipped_model_checks=0):
    a=json.loads(expected.read_bytes());b=json.loads(actual.read_bytes());allowed=[]
    if actual.name=='RAW_EVIDENCE.json' and a['files']!=b['files']:
        assert len({x['path'] for x in a['files']})==len(a['files'])
        assert len({x['path'] for x in b['files']})==len(b['files'])
        aa=sorted(a['files'],key=lambda x:x['path']);bb=sorted(b['files'],key=lambda x:x['path'])
        assert aa==bb,'Raw manifest contains a changed path, length or hash'
        a['files']=aa;b['files']=bb
        allowed.append(dict(path='/files',reason='Manifest file order only: Windows and POSIX path collation; identical path/size/SHA256 mapping',entries=len(aa)))
    diff=differences(a,b)
    fields={'external_model_bytes_verified','full_target_model_rehashed','models_full_rehashed','models_rehashed'}
    for d in diff:
        if skipped_model_checks and d['path']=='/checks' and d.get('expected')-d.get('actual')==skipped_model_checks:d['reason']=f'{skipped_model_checks} external model weight checks intentionally omitted'
        elif d['path'].split('/')[-1] in fields and d.get('expected') is True and d.get('actual') is False:d['reason']='external model weights intentionally not rehashed'
        elif type(d.get('expected')) is float and type(d.get('actual')) is float and math.isclose(d['expected'],d['actual'],rel_tol=1e-12,abs_tol=1e-12):d['reason']='platform floating-point rounding below 1e-12 comparison tolerance'
        else:raise AssertionError(json.dumps(d)[:1200])
        allowed.append(d)
    return dict(file=actual.name,expected_sha256=sha(expected),actual_sha256=sha(actual),byte_equal=actual.read_bytes()==expected.read_bytes(),allowed_differences=allowed)

def run(cmd,base,name):
    p=subprocess.run(cmd,capture_output=True,timeout=900,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    (base/(name+'.stdout.txt')).write_bytes(p.stdout);(base/(name+'.stderr.txt')).write_bytes(p.stderr)
    if p.returncode:raise RuntimeError((p.stderr+p.stdout)[-6000:].decode(errors='replace'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True,choices=['b57092','b57097','b57099','b570101','rtx98','rtx91']);ap.add_argument('--compare-existing',action='store_true');a=ap.parse_args()
    aid=a.archive;base=STAGE/aid;root=base/'restored';out=base/'rederived';out.mkdir(exist_ok=True)
    assert (base/'RESTORE_VERIFICATION.json').exists(),'complete byte restoration first'
    if aid=='b57092':
        script=root/'code/independent_verify.py'
        class EvidencePath(type(Path())):
            def __new__(cls,*args,**kwargs):return super().__new__(cls,*[str(x).replace('\\','/') for x in args],**kwargs)
            def __truediv__(self,key):return EvidencePath(str(self),str(key).replace('\\','/'))
        spec=importlib.util.spec_from_file_location('original_b57092',script)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.Path=EvidencePath
        data=module.verify(root,False);actual=out/'INDEPENDENT_VERIFICATION.json'
        actual.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        compared=[compare(actual,root/'INDEPENDENT_VERIFICATION.json',skipped_model_checks=2)]
    elif aid=='rtx91':
        pub=root/'repository/benchmarks/rtx_evidence_closeout_v1';code=root/'repository/scripts/platform/rtx_evidence_closeout_v1'
        rows=json.loads((pub/'FORMAL_RECORDS.json').read_bytes());index=json.loads((pub/'RAW_RECORD_INDEX.json').read_bytes());raw=[]
        assert len(rows)==len(index)==3600 and len({r['slot'] for r in index})==3600
        for item in index:
            p=root/'closeout'/item['path'];assert sha(p)==item['sha256']
            r=json.loads(p.read_bytes());done=json.loads(p.with_name('COMPLETED.json').read_bytes())
            assert done['record_sha256']==sha(p) and r['slot']==item['slot']
            assert r['wall_ms']==(r['request_end_ns']-r['request_start_ns'])/1e6
            assert r['response']['tokens']==r['output']['ids'] and r['response']['tokens_predicted']==r['output']['length']
            assert r['response']['hs_closeout']['workload']==r['workload']
            raw.append({k:v for k,v in r.items() if k not in ['response','trace_range']})
        assert raw==rows,'Export does not match the immutable native records'
        rawfile=out/'FORMAL_RECORDS.raw.json';rawfile.write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        compared=[]
        for stem,name in [('closeout','RESULTS.json'),('mechanism','MODEL_VALIDATION.json')]:
            script=code/(stem+'.py');actual=out/name
            cmd=[sys.executable,'-B',str(script),'--design',str(root/'repository/docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json'),'analyse','--plan',str(pub/'FORMAL_PLAN.json'),'--inputs',str(pub/'CONFIRMATION_INPUTS.json'),'--records',str(rawfile),'--freeze',str(root/'closeout/F0B_REMOTE_RECEIPT.json'),'--out',str(actual)]
            if stem=='mechanism':cmd+=['--model',str(pub/'BREAK_EVEN_MODEL.json')]
            run(cmd,base,stem);compared.append(compare(actual,pub/name))
    elif aid=='rtx98':
        script=root/'repository/scripts/platform/rtx_querylayout_mechanism_v1/audit95_v02.py'
        actual=out/'RESULTS.json';assert not actual.exists(),'fresh audit output required'
        run([sys.executable,'-B',str(script),'--repo',str(root/'repository'),'--local',str(root/'local'),'--out',str(actual)],base,'audit')
        expected=root/'repository/benchmarks/rtx_querylayout_mechanism_v1/RESULTS.json'
        if not expected.exists():expected=next((ROOT/'output/review_access_stage/evidence/rtx98').rglob('RESULTS.json'))
        compared=[compare(actual,expected)]
        test=script.with_name('test_audit95_v02.py');run([sys.executable,'-B',str(test)],base,'synthetic')
    else:
        script=root/({'b57097':'code/verify96.py','b57099':'code/verify98.py','b570101':'code/verify100.py'}[aid])
        if aid=='b570101':
            sys.path.insert(0,str(script.parent))
            spec=importlib.util.spec_from_file_location('original_b570101',script)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.Path=WindowsEvidencePath
            if a.compare_existing:
                assert json.loads((base/'audit.stdout.txt').read_text())['status']=='EXECUTED_AUDITED'
            else:
                data=module.audit100(WindowsEvidencePath(root),WindowsEvidencePath(out),False)
                (base/'audit.stdout.txt').write_text(json.dumps(data)+'\n');(base/'audit.stderr.txt').write_text('')
        else:run([sys.executable,'-B',str(script),'--root',str(root),'--output',str(out),'--skip-external-model-rehash'],base,'audit')
        compared=[]
        for p in sorted(out.glob('*.json')):
            expected=root/p.name
            if not expected.exists():expected=root/'analysis'/p.name
            assert expected.exists(),p.name
            compared.append(compare(p,expected))
    result=dict(id=aid,status='PASS_ORIGINAL_CPU_AUDITOR_REDERIVATION',original_auditor_sha256=sha(script),external_model_weights_rehashed=False,new_GPU_forwards=0,artifacts=compared)
    if aid in ['rtx98','b57097','b57099']:
        if aid!='rtx98':run([sys.executable,'-B',str(script.with_name('test_verify96.py' if aid=='b57097' else 'test_verify98.py'))],base,'synthetic')
        testlog=(base/'synthetic.stderr.txt').read_text()
        count=int(re.search(r'Ran (\d+) tests',testlog).group(1));assert testlog.strip().endswith('OK')
        result['synthetic_rejection']=dict(status='PASS',tests=count)
    if aid=='rtx91':result['raw_records_crosschecked']=3600;result['scope']='All native record hashes, completion seals, full IDs, workload and timer endpoints crosschecked; original CPU qualification/cost and model-availability analyses rerun. Not a new execution of the separate PR94 audit.'
    if aid in ['b57092','b570101']:result['path_adapter']='Runtime Path binding converts Windows backslashes to POSIX separators only; original source and data bytes unchanged.'
    if aid=='b570101':
        inherited=out/'inherited99';inherited.mkdir(exist_ok=True)
        inherited_root=root/'baseline/pr99'
        run([sys.executable,'-B',str(inherited_root/'code/verify98.py'),'--root',str(inherited_root),'--output',str(inherited),'--skip-external-model-rehash'],base,'inherited99')
        result['inherited_PR99_artifacts']=[compare(p,inherited_root/p.name) for p in sorted(inherited.glob('*.json'))]
        # The original test writes a result file. Give it a separate minimal fixture
        # so the immutable restored evidence stays unchanged.
        with tempfile.TemporaryDirectory(prefix='b570101-rejections-') as t:
            fixture=Path(t);rows=json.loads((root/'STUDY_RECORDS.json').read_bytes())
            r=next(r for r in rows if r['phase']=='P1A' and r['observation_mode']=='heavy')
            x=json.loads((root/r['raw_path']).read_bytes());p=x['partition98']['full_payloads']['0']
            names=['STUDY_RECORDS.json',r['raw_path'],r['evidence_path'],p['sequence_KV']['path'],p['logits']['path']]
            for n in names:q=fixture/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/n,q)
            run([sys.executable,'-B',str(script.with_name('test_verify100.py')),str(fixture)],base,'synthetic')
            result['synthetic_rejection']=json.loads((fixture/'SYNTHETIC_REJECTION.json').read_bytes())
    (base/'SCIENTIFIC_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
