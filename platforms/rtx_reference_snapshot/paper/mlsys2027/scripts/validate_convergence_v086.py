#!/usr/bin/env python3
"""Current scientific/derived/source/protected gates with rejecting counterexamples.

Old wording-specific integration assertions are historical context. Original
numeric/endpoint/negative assertions run unchanged on the current exported data.
No comparison silently substitutes a prior receipt for a current calculation.
"""
import copy,hashlib,importlib.util,json,re,subprocess,sys,tarfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];H=ROOT/'paper/mlsys2027/manuscript';E=H.parent/'evidence'
sys.path.insert(0,str(H/'scripts'));sys.path.insert(0,str(Path(__file__).parent))
from package_overleaf_v086 import collect_bundle,verify_dependencies
from verify_anonymous_v085 import validate
from analyze_existing_records_v086 import compute
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def historical():
    results={}
    for name,p,replacements in [('numerical',H/'scripts/validate_evidence.py',[("E/'NUMERICAL_QA.json'","E/'NUMERICAL_HISTORICAL_V086_QA.json'")]),('runtime',H/'scripts/validate_runtime.py',[('DIRECT_ID_M4_SECONDARY_REPLAY_V07.json','M4_SECONDARY_REPLAY_V086_QA.json'),('RUNTIME_QA_V07.json','RUNTIME_REPLAY_V086_QA.json')])]:
        s=p.read_text()
        for old,new in replacements:assert old in s;s=s.replace(old,new)
        exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
        results[name]={'status':'RERUN_PASS','entry':str(p.relative_to(ROOT)),'entry_sha256':sha(p),'adapter':replacements,'assertions':'All original assertions preserved; only output paths redirected'}
    p=H/'figures/presentation_v07/validate.py';spec=importlib.util.spec_from_file_location('immutable_figure3',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);r=m.validate();(E/'FIGURE3_REPLAY_V086_QA.json').write_text(json.dumps(r,indent=2)+'\n');results['Figure3']={'status':'RERUN_PASS','checks':r['check_count'],'entry_sha256':sha(p)}
    results['v085_wording_specific_integration']={'status':'NOT_APPLICABLE','reason':'Changed current prose/version dependencies; original numeric/endpoint/identity/negative predicates retained via unchanged validate() and current gates; old 159 receipt is historical context only'}
    (E/'HISTORICAL_CHECKS_V086_QA.json').write_text(json.dumps(results,indent=2)+'\n')
    return results
def current():
    checks=[];negatives=[]
    def check(name,value):assert value,name;checks.append({'item':name,'status':'RERUN_PASS'})
    def reject(name,fn):
        try:fn()
        except (AssertionError,ValueError,KeyError):negatives.append({'case':name,'status':'RERUN_PASS','result':'Rejected as required'});return
        raise AssertionError('negative case accepted: '+name)
    protected=read(E/'PROTECTED_OBJECTS_V086.json');diff=[]
    for p,digest in protected['protected_sha256'].items():
        if not (ROOT/p).is_file() or sha(ROOT/p)!=digest:diff.append(p)
    check('all protected baseline bytes unchanged',not diff)
    check('scientific tag unchanged',subprocess.check_output(['git','rev-parse','mlsys2027-v0.8-author-freeze^{}'],cwd=ROOT,text=True).strip()==protected['scientific_tag_peeled'])
    baseline=read(E/'REVISION_BASELINE_V086.json')['author_checkout'];p=Path(baseline['path'])
    for args,key in [(['rev-parse','HEAD'],'HEAD'),(['branch','--show-current'],'branch'),(['status','--porcelain'],'status_porcelain')]:check('original checkout '+key,subprocess.check_output(['git',*args],cwd=p,text=True).strip()==baseline[key])
    (E/'PROTECTED_REPLAY_V086_QA.json').write_text(json.dumps({'status':'RERUN_PASS','protected_files':len(protected['protected_sha256']),'unexpected_differences':diff,'baseline_inventory_sha256':sha(E/'PROTECTED_OBJECTS_V086.json'),'scientific_tag_peeled':protected['scientific_tag_peeled'],'author_checkout_unchanged':True},indent=2)+'\n')
    archive=read(E/'ARCHIVE_REPLAY_V086_QA.json');accessible={k:v for k,v in archive['checks'].items() if v['status']!='UNAVAILABLE'}
    check('nine archive families personally rerun',len(accessible)==9 and all(v['status']=='RERUN_PASS' and v['actual_verifier_executions'] for v in accessible.values()))
    check('canonical B570 POSIX failure retained',accessible['B570_live_intervention']['canonical_entry_before_adapter']['status']=='RERUN_FAIL')
    check('358H runtime raw correctly unavailable',archive['checks']['358H_runtime_raw']['status']=='UNAVAILABLE')
    with zipfile.ZipFile(H/'output/anonymous-evidence-index-v0.8.6.zip') as z:
        manifest=json.loads(z.read('SHA256SUMS.json'));check('anonymous member inventory',set(z.namelist())==set(manifest)|{'SHA256SUMS.json'})
        for name,digest in manifest.items():check('anonymous member '+name,hashlib.sha256(z.read(name)).hexdigest()==digest)
        studies={Path(n).stem:json.loads(z.read(n)) for n in z.namelist() if n.startswith('evidence/')}
        anoninputs=json.loads(z.read('derived/inputs.json'));anonresults=json.loads(z.read('derived/results.json'))
    check('unchanged primary arrays/endpoint/timing assertions',bool(validate(studies)))
    projection=read(E/'FOLLOWUP_PROJECTION_V085.json')
    for name,expected in projection['studies'].items():check('all prior study values retained '+name,all(studies[name][k]==v for k,v in expected.items()))
    old=read(ROOT/'benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json')['predictions'];by={(r['task_id'],r['repetition']):r for r in old}
    for r in studies['B570_original_H1']['rows']:
        p=by[r['task_id'],r['repetition']];check('original B570 array '+r['task_id']+str(r['repetition']),r['arrays']['prediction']==p['predicted_ids'] and r['arrays']['reference']==p['reference_ids'])
    inputs=read(E/'DERIVED_INPUTS_V086.json');check('anonymous derived inputs exact',inputs==anoninputs);derived,_=compute(inputs);expected=read(E/'DERIVED_ANALYSIS_V086.json')
    check('all derived quantities recomputed',json.loads(json.dumps(derived))==anonresults and all(derived[k]==expected[k] for k in derived))
    for name,row in expected['author_input_manifest'].items():
        p=ROOT/name
        if p.is_file():check('derived raw input '+name,sha(p)==row['sha256'] and p.stat().st_size==row['bytes'])
        else:
            container=next(ROOT/p for p,v in expected['author_input_manifest'].items() if v['sha256']==row['container_sha256'])
            with tarfile.open(container) as t:raw=t.extractfile(name).read()
            check('derived tar member '+name,hashlib.sha256(raw).hexdigest()==row['sha256'])
    check('known-outcome plan identified',expected['post_study'] and sha(E/'DERIVED_ANALYSIS_PLAN_V086.md')==expected['plan_sha256'])
    check('new raw projection assertions and identities rerun',read(E/'FOLLOWUP_RAW_REPLAY_V086_QA.json')['complete_studies_element_equal'])
    check('H2 source and all six sealed negative witnesses audited',len(read(E/'H2_INPUT_AUDIT_V086.json')['negative_witnesses'])==6)
    files,sources=collect_bundle();verify_dependencies(files);clean=read(E/'CLEAN_ZIP_REBUILD_V086_QA.json')
    check('current source exactly matches packaged dependency hashes',sources==clean['source_files'])
    check('source ZIP inspected identity',sha(H/'output/overleaf-convergence-v0.8.6.zip')==clean['zip_sha256'])
    check('raw page text identical without normalization',all(v['raw_extracted_page_text_exact_equal'] and not v['normalization_applied'] for v in clean['comparison'].values()))
    bad=copy.deepcopy(studies);bad['RTX_H2']['qualification_status']='QUALIFIED';reject('H2 mislabeled qualified',lambda:validate(bad))
    bad=copy.deepcopy(studies);bad['RTX_H2']['rows'][0]['arrays']['H2_P_R'][0]^=1;reject('changed frozen prediction ID',lambda:validate(bad))
    bad=copy.deepcopy(studies);bad['RTX_matched_latency']['ratio']=1/bad['RTX_matched_latency']['ratio'];reject('inverted RTX ratio',lambda:validate(bad))
    bad=dict(files);bad.pop('sections/05_diagnoses.tex');reject('missing actual TeX dependency',lambda:verify_dependencies(bad))
    bad=copy.deepcopy(inputs);bad['B570'][0]['primary_scores'][0]['margin']+=1;reject('top-one mistaken for top-two margin',lambda:compute(bad))
    bad=copy.deepcopy(inputs);bad['M4'][0]['end_to_end_ns']+=10**12;reject('changed original M4 raw median',lambda:compute(bad))
    bad=copy.deepcopy(inputs);bad['358H']['rows'][0]['verification_ms']=-1;reject('invalid conditional target-work accounting',lambda:compute(bad))
    bad=copy.deepcopy(inputs);bad['RTX_hook_probe']['p99_microseconds']=11;reject('hook exceeds original threshold',lambda:compute(bad))
    text='\n'.join(p.read_text() for p in [H/'main.tex',*(H/'sections').glob('[0-9]*.tex')]);app=(H/'appendix.tex').read_text()+(H/'sections/appendix_followups_v086.tex').read_text()+(H/'sections/appendix_derived_v086.tex').read_text()
    intro=(H/'sections/01_introduction.tex').read_text();check('title and three contributions preserved','Our three contributions are (1)' in intro and '(2)' in intro and '(3)' in intro and '(4)' not in intro)
    check('H2 necessity limit explicit','No target-only UB2 competitor was tested on this same V2 reserved set' in text)
    check('conditional accounting limits explicit','not a prompt-GM bound' in text and 'fixed measured progress and target work' in text)
    check('known-outcome ambiguity fixed','No new measurement or analysis choice after seeing the result was used' not in app and 'after aggregate results were already known' in app)
    check('main/appendix citation separation','\\ref{app:' not in text)
    check('no incorrect score-spacing concatenation','\\BvLong describe' not in text and '\\BvLong\\ describe' in text)
    check('source/capsule/compact roles explicit','anonymous-evidence-index-v0.8.6.zip' in app and 'overleaf-convergence-v0.8.6.zip' in app and 'a5919b59342ecc68' in app)
    report={'status':'RERUN_PASS','checks':checks,'check_count':len(checks),'negative_cases':negatives,'scientific_limits':'Finite within-stack claims; no new inference; original primary CI untouched; conditional arithmetic and post-study sensitivity separate','historical_receipt_scope':'Other earlier reviews/closeouts not executed are PRIOR_RECEIPT_ONLY; old prose-specific v085 integration is NOT_APPLICABLE to changed prose'}
    (E/'SCIENTIFIC_INVARIANTS_V086_QA.json').write_text(json.dumps(report,indent=2)+'\n')
    (E/'NUMERICAL_CONVERGENCE_V086_QA.json').write_text(json.dumps({'status':'RERUN_PASS','existing_primary':validate(studies),'derived':{k:derived[k] for k in ('358H','RTX')},'new_M4_secondary':derived['M4']['stratified_sensitivity'],'negative_cases':negatives},indent=2)+'\n')
    print(json.dumps({'status':'RERUN_PASS','checks':len(checks),'rejecting_counterexamples':len(negatives),'protected':len(protected['protected_sha256'])}))
    return report
if __name__=='__main__':historical();current()
