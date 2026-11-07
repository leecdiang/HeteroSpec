#!/usr/bin/env python3
"""Audit preserved anonymous bytes, V4 projection, negative gates and current build."""
import copy, hashlib, importlib.util, json, subprocess, sys, tempfile, zipfile
from pathlib import Path
from verify_rtx_v4_projection_v087 import validate, digest_ids
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'paper/mlsys2027';H=P/'manuscript';E=P/'evidence'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
    archive=H/'output/anonymous-evidence-index-v0.8.7.zip';negative=[];executions=[]
    with zipfile.ZipFile(archive) as z:
        data=json.loads(z.read('evidence/RTX_V4.json'));names=set(z.namelist());manifest=json.loads(z.read('SHA256SUMS.json'))
        assert names==set(manifest)|{'SHA256SUMS.json'}
        for n,h in manifest.items(): assert hashlib.sha256(z.read(n)).hexdigest()==h,n
        with zipfile.ZipFile(H/'output/anonymous-evidence-index-v0.8.6.zip') as old:
            preserved=[n for n in old.namelist() if n not in ('SHA256SUMS.json','INDEX.json','README.md','verify.py')]
            assert all(z.read(n)==old.read(n) for n in preserved)
            assert z.read('verify_v086.py')==old.read('verify.py')
        for i in (1,2):
            with tempfile.TemporaryDirectory(prefix='v087-anon-') as temp:
                d=Path(temp);z.extractall(d)
                result=json.loads(subprocess.check_output([sys.executable,'-B','verify.py'],cwd=d,text=True));assert result['status']=='PASS'
                executions.append(result)
        assert executions[0]==executions[1]
        for n in names:
            s=z.read(n).decode(errors='replace')
            assert not any(x.lower() in s.lower() for x in ('leecdiang','/Users/','/home/','C:\\Users','D:\\HeteroSpec','github.com/leecdiang')),(n,'identifying export')
    result=validate(data)
    def reject(name, mutate):
        bad=copy.deepcopy(data);mutate(bad)
        try: validate(bad)
        except (AssertionError,KeyError,ValueError,TypeError):negative.append(name);return
        raise AssertionError('accepted invalid evidence: '+name)
    def wrong_id(d):
        row=d['A'][0]['conditions']['A_H2_P_R'];row['ids'][0]^=1;row['ids_sha256']=digest_ids(row['ids'])
    reject('changed full trajectory with rehashed array',wrong_id)
    reject('missing timed observation',lambda d:d['B'].pop())
    reject('blocked path reported as speedup',lambda d:d['reported_B']['B_BATCHED_K2_UB2'].update(speedup=1.2))
    reject('serialized ratio direction inverted',lambda d:d['reported_B']['B_SERIALIZED_K2_UB1'].update(speedup=1/d['reported_B']['B_SERIALIZED_K2_UB1']['speedup']))
    reject('duplicate task/repetition',lambda d:d['A'][1].update(repetition=1))
    reject('negative native timer interval',lambda d:d['B'][0]['timer'].update(qpc_delta=-1))
    reject('exposure denominator changed',lambda d:d['selection']['excluded'].pop())
    reject('conditions called independent prompts',lambda d:d['formal_counts'].update(independent_prompts=456))
    reject('endpoint ID hash damaged',lambda d:d['B'][0]['ids'].pop())
    reject('unbalanced condition schedule',lambda d:d['schedule'][0].update(order=list(reversed(d['schedule'][0]['order']))))
    build=read(E/'CLEAN_ZIP_REBUILD_V087_QA.json');pdf=read(E/'PDF_AND_ANONYMITY_V087_QA.json')
    assert all(v['raw_extracted_page_text_exact_equal'] and not v['normalization_applied'] for v in build['comparison'].values())
    assert pdf['pdfs']['main']['body_pages']<=10
    assert all(v['overfull_boxes']==v['undefined_references_citations']==0 for v in pdf['pdfs'].values())
    projection=read(E/'RTX_V4_PROJECTION_V087_QA.json')
    for n,v in projection['source_inputs'].items():assert sha(ROOT/n)==v['sha256'] and (ROOT/n).stat().st_size==v['bytes']
    text='\n'.join(p.read_text() for p in [H/'main.tex',*(H/'sections').glob('[0-9]*.tex')])
    assert 'Our three contributions are (1)' in text and '(4)' not in text
    assert 'predictor is sufficient for this path' in text and 'without proving history necessary' in text
    assert 'UB2 fails on /15 and /25, reference on /15 and /18' in text
    assert 'not a target-only causal intervention' in text and 'not 456 independent samples' in text
    assert 'not an optimization trend' in text and 'no speedup/CI' in text
    report={'status':'PASS','new_projection':result,'anonymous_clean_executions':len(executions),'anonymous_results_exact_equal':True,'prior_member_bytes_preserved':preserved,'prior_verifier_bytes_preserved':True,'negative_cases_rejected':negative,'build':'two independent source ZIP extractions; raw page text equal','limits':'CPU projection verification only; old nine-capsule replay receipt remains a prior completed independent raw audit, not a new GPU run'}
    (E/'SCIENTIFIC_INTEGRATION_V087_QA.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','negative_cases':len(negative),'independent_prompts':19,'A_arrays':285,'B_arrays':171,'prior_member_bytes_preserved':len(preserved)}))
if __name__=='__main__':check()
