#!/usr/bin/env python3
"""Bounded source/evidence checks for this author revision, not a review vote."""
import csv,hashlib,json,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];P=ROOT/'paper/mlsys2027';M=P/'manuscript';E=P/'evidence';OUT=M/'output'
def sha(b):return hashlib.sha256(b).hexdigest()
def extract(archive,dest):
    dest.mkdir()
    with zipfile.ZipFile(archive) as z:z.extractall(dest)
def run(root,expected):
    p=subprocess.run([sys.executable,'-B','verify.py'],cwd=root,capture_output=True,text=True)
    assert (p.returncode==0)==expected,(root,p.stderr)
    return p
def main():
    with zipfile.ZipFile(OUT/'overleaf-rtx-integration-v0.8.7.zip') as z:old_source={n:z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(OUT/'overleaf-system-revision-v0.8.8.zip') as z:new_source={n:z.read(n) for n in z.namelist()}
    protected=['tables/values.tex','tables/runtime_values.tex','tables/direct_id_values.tex','tables/followup_values_v085.tex','tables/derived_values_v086.tex','tables/rtx_v4_values_v087.tex','figures/03_verification.tex','figures/presentation_v07/pdf/verification.pdf','mlsys2025.sty','mlsys2025.bst','references.bib']
    assert all(new_source[n]==old_source[n] for n in protected)
    # The historical figure is relocated, with the original source and width intact.
    assert b'width=\\textwidth' in new_source['figures/03_verification.tex']
    assert b'figures/03_verification.tex' not in new_source['sections/04_outcomes.tex']
    assert b'figures/03_verification.tex' in new_source['appendix.tex']
    with zipfile.ZipFile(OUT/'anonymous-evidence-index-v0.8.7.zip') as z:old={n:z.read(n) for n in z.namelist()}
    archive=OUT/'anonymous-evidence-index-v0.8.8.zip'
    with zipfile.ZipFile(archive) as z:new={n:z.read(n) for n in z.namelist()}
    keep=[n for n in old if n not in ('INDEX.json','README.md','SHA256SUMS.json','verify.py')]
    assert all(new[n]==old[n] for n in keep) and new['verify_v087.py']==old['verify.py']
    j=json.loads(new['evidence/RTX_V4.json']);assert j['reported_B']['B_BATCHED_K2_UB2']['speedup'] is None and j['reported_B']['B_BATCHED_K2_UB2']['CI'] is None
    result=json.loads(new['derived/GLOBAL_ANALYSIS_V088.json']);assert result['frozen_B_report']==j['reported_B']
    plan=P/'reviews/system_revision_v088/ANALYSIS_PLAN_V088.md';assert result['plan_sha256']==sha(plan.read_bytes())
    assert json.loads((E/'GLOBAL_ANALYSIS_V088_QA.json').read_text())['max_absolute_difference_s']==0
    temp=ROOT/'tmp/qa-v088';temp.mkdir(parents=True,exist_ok=True);work=Path(tempfile.mkdtemp(prefix='evidence-',dir=temp))
    executions=[]
    for name in ['clean-one','clean-two']:
        d=work/name;extract(archive,d);r=run(d,True);(d/'execution.stdout').write_text(r.stdout)
        executions.append({'directory':str(d),'status':'PASS','final':json.loads(r.stdout.strip().splitlines()[-1])})
    # Change data and rehash the manifest: the calculator must still reject it.
    negatives=[]
    for name in ['changed-quantile','changed-prompt-median']:
        d=work/name;extract(archive,d)
        if name=='changed-quantile':
            f=d/'derived/GLOBAL_ANALYSIS_V088.json';q=json.loads(f.read_text());q['distribution']['B_TARGET_REFERENCE_UB1']['q25_s']+=.1;f.write_text(json.dumps(q))
        else:
            f=d/'derived/RTX_V4_PROMPT_MEDIANS_V088.csv';rows=list(csv.DictReader(f.open()));rows[0]['B_TARGET_REFERENCE_UB1']=str(float(rows[0]['B_TARGET_REFERENCE_UB1'])+.1)
            with f.open('w',newline='') as stream:w=csv.DictWriter(stream,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
        mm=json.loads((d/'SHA256SUMS.json').read_text());mm[f.relative_to(d).as_posix()]=sha(f.read_bytes());(d/'SHA256SUMS.json').write_text(json.dumps(mm))
        r=run(d,False);negatives.append({'case':name,'status':'REJECTED','returncode':r.returncode})
    build=json.loads((E/'CLEAN_ZIP_REBUILD_V088_QA.json').read_text());pdf=json.loads((E/'PDF_AND_ANONYMITY_V088_QA.json').read_text())
    assert all(x['raw_extracted_page_text_exact_equal'] for x in build['comparison'].values())
    assert pdf['pdfs']['main']['body_pages']<=10
    assert all(x['overfull_boxes']==x['undefined_references_citations']==0 for x in pdf['pdfs'].values())
    report={'status':'PASS','scope':'Author revision validation; no fresh six-reviewer vote or model execution','source_invariants':{n:sha(new_source[n]) for n in protected},'historical_figure':'Relocated into appendix; original source, asset and textwidth inclusion preserved','prior_evidence_members_unchanged':len(keep),'prior_verifier_unchanged':True,'clean_executions':executions,'new_descriptor_negative_cases':negatives,'original_V4_denominators_and_report':'unchanged; preserved verifier rerun','new_numeric_independent_check':'zero discrepancy across five descriptors per condition from 171 original QPC intervals','pdfs':{k:{f:v[f] for f in ['pages','body_pages','sha256','overfull_boxes','undefined_references_citations']} for k,v in pdf['pdfs'].items()},'manual_visual_review':pdf['manual_visual_review'],'historical_raw_audit':'Prior nine-capsule receipt reused; no re-download or GPU rerun'}
    (E/'REVISION_V088_QA.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_invariants','clean_executions')}))
if __name__=='__main__':main()
