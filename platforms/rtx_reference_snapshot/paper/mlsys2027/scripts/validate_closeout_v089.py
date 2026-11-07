#!/usr/bin/env python3
"""Verify the bounded review closeout against frozen v088 artifacts; no models."""
import hashlib,json,zipfile
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'paper/mlsys2027';M=P/'manuscript';E=P/'evidence';OUT=M/'output'
def sha(b):return hashlib.sha256(b).hexdigest()
def read_json(p):return json.loads(p.read_bytes())
def archived(p):
    with zipfile.ZipFile(p) as z:return {n:z.read(n) for n in z.namelist()}
def main():
    baseline=read_json(E/'FINAL_ARTIFACT_MANIFEST_V088.json')
    frozen=baseline['artifacts']+baseline['QA_receipts']
    for x in frozen:
        b=(ROOT/x['path']).read_bytes()
        assert len(b)==x['bytes'] and sha(b)==x['sha256'],x['path']
    old=archived(OUT/'overleaf-system-revision-v0.8.8.zip')
    new=archived(OUT/'overleaf-system-revision-v0.8.9.zip')
    protected=['tables/values.tex','tables/runtime_values.tex','tables/direct_id_values.tex',
        'tables/followup_values_v085.tex','tables/derived_values_v086.tex','tables/rtx_v4_values_v087.tex',
        'figures/03_verification.tex','figures/presentation_v07/pdf/verification.pdf',
        'mlsys2025.sty','mlsys2025.bst','references.bib']
    assert all(old[n]==new[n] for n in protected)
    assert set(new)-set(old)=={'sections/appendix_followups_v089.tex','tables/b570_prediction_commitment_v089.tex'}
    assert set(old)-set(new)=={'sections/appendix_followups_v088.tex','tables/b570_prediction_commitment_v083.tex'}
    expected_main=old['main.tex'].replace(b'v0.8.8',b'v0.8.9')
    expected_app=old['appendix.tex'].replace(b'v0.8.8',b'v0.8.9').replace(
        b'b570_prediction_commitment_v083.tex',b'b570_prediction_commitment_v089.tex').replace(
        b'appendix_followups_v088.tex',b'appendix_followups_v089.tex')
    assert new['main.tex']==expected_main and new['appendix.tex']==expected_app
    common=set(new)&set(old)-{'main.tex','appendix.tex','README.txt','SHA256SUMS.json'}
    assert all(new[n]==old[n] for n in common)
    b570=(M/'tables/b570_prediction_commitment_v083.tex').read_bytes()
    assert b570.count(b'primary mechanism-validation endpoint')==1
    assert (M/'tables/b570_prediction_commitment_v089.tex').read_bytes()==b570.replace(
        b'primary mechanism-validation endpoint',b'primary prospective path-prediction endpoint')
    earlier=(M/'sections/appendix_followups_v088.tex').read_bytes()
    expected=earlier.replace(b"The original studies' references remain unchanged.}",
        b"The original studies' references remain unchanged. V4 is documented separately in Section~\\ref{app:rtxv4}.}").replace(
        b'overleaf-system-revision-v0.8.8.zip',b'overleaf-system-revision-v0.8.9.zip')
    assert (M/'sections/appendix_followups_v089.tex').read_bytes()==expected
    unchanged_canonical=[]
    for n,h in baseline['source_files'].items():
        if n in ('paper/mlsys2027/manuscript/main.tex','paper/mlsys2027/manuscript/appendix.tex'):continue
        assert sha((ROOT/n).read_bytes())==h,n
        unchanged_canonical.append(n)
    included='\n'.join(b.decode() for n,b in new.items() if n.endswith('.tex'))
    assert 'mechanism-validation' not in included
    assert 'primary prospective path-prediction endpoint' in included
    assert 'anonymous-evidence-index-v0.8.8.zip' in included
    assert 'overleaf-system-revision-v0.8.9.zip' in included
    build=read_json(E/'CLEAN_ZIP_REBUILD_V089_QA.json')
    pdf=read_json(E/'PDF_AND_ANONYMITY_V089_QA.json')
    visual=read_json(E/'VISUAL_QA_V089.json')
    assert build['status']==pdf['status']==visual['status']=='RERUN_PASS'
    assert build['zip_sha256']==sha((OUT/'overleaf-system-revision-v0.8.9.zip').read_bytes())
    assert all(x['raw_extracted_page_text_exact_equal'] and not x['normalization_applied'] for x in build['comparison'].values())
    assert pdf['pdfs']['main']['body_pages']==10 and pdf['pdfs']['main']['pages']==12
    assert pdf['pdfs']['appendix']['pages']==16
    assert pdf['pdfs']['hardware-only']['body_pages']==9 and pdf['pdfs']['hardware-only']['pages']==11
    assert all(x['overfull_boxes']==x['undefined_references_citations']==0 for x in pdf['pdfs'].values())
    assert pdf['manual_visual_review'].startswith('RERUN_PASS')
    assert pdf['manual_visual_receipt_sha256']==sha((E/'VISUAL_QA_V089.json').read_bytes())
    assert visual['prior_receipt_sha256']==sha((E/'VISUAL_QA_V088.json').read_bytes())
    assert visual['total_pages']==39 and visual['current_manual_pages']==3 and visual['exact_pixel_reuse_pages']==36
    for name,x in pdf['pdfs'].items():
        stem={'main':'manuscript','appendix':'appendix','hardware-only':'hardware-only'}[name]
        assert visual['pdf_sha256'][name]==x['sha256']==sha((OUT/(stem+'-v0.8.9.pdf')).read_bytes())
    for name in ['main','hardware-only']:
        stem={'main':'manuscript','hardware-only':'hardware-only'}[name]
        a=PdfReader(OUT/(stem+'-v0.8.8.pdf'));b=PdfReader(OUT/(stem+'-v0.8.9.pdf'))
        assert [p.extract_text() for p in a.pages]==[p.extract_text() for p in b.pages]
    report={'status':'PASS','scope':'Targeted author review closeout; no new vote, study, model or scientific CPU replay',
        'requests_completed':['R4 P1-1 / R6-1: A6 prospective endpoint','R6-3: A9 Section Q entry','A13 current document source ZIP'],
        'protected_source_ZIP_members':{n:sha(new[n]) for n in protected},
        'all_other_common_ZIP_members_unchanged':len(common),'unchanged_canonical_v088_sources':unchanged_canonical,
        'prior_artifacts_and_QA_receipts_hash_verified':frozen,
        'evidence_execution':'Unchanged v088 scientific package and prior global-analysis/CPU receipts reused after hash check; no re-execution',
        'scientific_numeric_and_digest_changes':0,'fresh_builds':2,'raw_per_page_text_exact_between_fresh_builds':True,
        'main_and_hardware_text_exact_equal_to_v088':True,
        'visual':{'changed_pages_manually_inspected':[6,8,11],'other_pages_exact_pixel_reuse':36,'receipt_sha256':sha((E/'VISUAL_QA_V089.json').read_bytes())},
        'pdfs':{k:{f:v[f] for f in ['pages','body_pages','sha256','overfull_boxes','undefined_references_citations']} for k,v in pdf['pdfs'].items()},
        'B570_RTX_358H_M4':'CLOSED','merge_release_submission':False}
    (E/'REVIEW_CLOSEOUT_V089_QA.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','frozen_files_verified':len(frozen),'unchanged_canonical_sources':len(unchanged_canonical),'current_manual_pages':3,'exact_pixel_reuse_pages':36}))
if __name__=='__main__':main()
