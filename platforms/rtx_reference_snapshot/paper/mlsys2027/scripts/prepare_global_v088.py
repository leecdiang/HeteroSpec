#!/usr/bin/env python3
"""Preserve v087 evidence bytes and add bounded post-study descriptors."""
import hashlib, json, zipfile
from pathlib import Path
from analyze_global_v088 import compute

ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'paper/mlsys2027'; OUT=P/'manuscript/output'; E=P/'evidence'
def digest(b): return hashlib.sha256(b).hexdigest()

def main():
    old=OUT/'anonymous-evidence-index-v0.8.7.zip'
    assert digest(old.read_bytes())=='36609ad6579775deeb7edccc70f89bd9a242346b7446cc28575703ee7a8e3a04'
    with zipfile.ZipFile(old) as z: prior={n:z.read(n) for n in z.namelist()}
    manifest=json.loads(prior['SHA256SUMS.json'])
    assert set(manifest)==set(prior)-{'SHA256SUMS.json'}
    assert all(digest(prior[n])==h for n,h in manifest.items())
    files=dict(prior)
    files['prior/INDEX_V087.json']=prior['INDEX.json']
    files['prior/README_V087.md']=prior['README.md']
    files['prior/SHA256SUMS_V087.json']=prior['SHA256SUMS.json']
    files['verify_v087.py']=prior['verify.py']
    for n in ['GLOBAL_ANALYSIS_V088.json','RTX_V4_PROMPT_MEDIANS_V088.csv']:
        files['derived/'+n]=(E/n).read_bytes()
    plan=(P/'reviews/system_revision_v088/ANALYSIS_PLAN_V088.md').read_text()
    # Only the pre-written numerical-input/operation portion is exported.
    plan=plan[plan.index('## Quantitative inputs and operations'):plan.index('## Revision and completion')]
    files['derived/PLAN_V088.md']=('POST-STUDY V0.8.8 DERIVED PLAN\nOriginal outcomes were known before this plan and computation.\n'+plan).encode()
    files['global_analysis.py']=(P/'scripts/analyze_global_v088.py').read_bytes()
    files['verify.py']=b'''#!/usr/bin/env python3
"""Preserved v087 assertions plus v088 post-study descriptor replay."""
import csv,hashlib,json
from pathlib import Path
from verify_v087 import main as prior_main
from global_analysis import compute,CONDITIONS
ROOT=Path(__file__).resolve().parent
def main():
    prior_main()
    raw=(ROOT/'evidence/RTX_V4.json').read_bytes()
    actual,rows=compute(json.loads(raw));expected=json.loads((ROOT/'derived/GLOBAL_ANALYSIS_V088.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==expected['source_member_sha256']
    assert actual=={k:v for k,v in expected.items() if k not in ('source_member_sha256','plan_sha256')}
    with (ROOT/'derived/RTX_V4_PROMPT_MEDIANS_V088.csv').open(newline='') as f: csv_rows=list(csv.DictReader(f))
    assert len(csv_rows)==len(rows)==19
    for a,b in zip(csv_rows,rows):
        assert a['task_id']==b['task_id']
        assert all(float(a[c])==b[c] for c in CONDITIONS)
    print(json.dumps({'status':'PASS','v088_descriptors':'POST_STUDY_PASS','prompt_rows':19,'conditions':3,'primary_estimates':'unchanged; prior verifier executed','limits':actual['limits']}))
if __name__=='__main__':main()
'''
    index=json.loads(files['INDEX.json']);index['version']='v0.8.8'
    index['v088_descriptors']={'status':'POST_STUDY','plan':'derived/PLAN_V088.md','results':'derived/GLOBAL_ANALYSIS_V088.json','rows':'derived/RTX_V4_PROMPT_MEDIANS_V088.csv','calculator':'global_analysis.py','primary_estimates':'Unchanged; v087 verifier retained byte-for-byte as verify_v087.py'}
    files['INDEX.json']=(json.dumps(index,indent=2)+'\n').encode()
    files['README.md']=b'''# Anonymous evidence index v0.8.8
Extract into a clean directory and run `python3 -B verify.py`.
Requires only Python standard library; no model, GPU or network.
Retained original studies and v0.8.7 V4 arrays/timers/verifiers are unchanged.
New descriptors summarize 19 prompt medians per condition and cross failures.
They are post-study, with outcomes known, and do not change primary GM/CI.
The blocked batched speedup/CI remain null. Observation spread is not a CI.
Compact arrays/timer fields permit CPU recalculation, not raw state inspection.
Full capsule identities/entries remain in INDEX.json. Reported ordering is not
trusted external chronology; omitted runtime/model/driver bytes are unavailable.
The source ZIP reconstructs documents separately; no functional pass@k claim.
'''
    result,rows=compute(json.loads(prior['evidence/RTX_V4.json']))
    expected=json.loads(files['derived/GLOBAL_ANALYSIS_V088.json'])
    assert result=={k:v for k,v in expected.items() if k not in ('source_member_sha256','plan_sha256')}
    protected={n:digest(b) for n,b in prior.items() if n not in ('INDEX.json','README.md','SHA256SUMS.json','verify.py')}
    assert all(files[n]==prior[n] for n in protected)
    assert files['verify_v087.py']==prior['verify.py']
    files['SHA256SUMS.json']=(json.dumps({n:digest(b) for n,b in sorted(files.items()) if n!='SHA256SUMS.json'},indent=2)+'\n').encode()
    archive=OUT/'anonymous-evidence-index-v0.8.8.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,10,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    receipt={'status':'PASS','prior_zip_sha256':digest(old.read_bytes()),'new_zip_sha256':digest(archive.read_bytes()),'members':len(files),'preserved_members':protected,'prior_verifier_sha256':digest(files['verify_v087.py']),'scope':'Export only; new analysis is post-study; no primary input or estimate changed'}
    (E/'ANONYMOUS_EXPORT_V088_QA.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='preserved_members'}))

if __name__=='__main__':main()
