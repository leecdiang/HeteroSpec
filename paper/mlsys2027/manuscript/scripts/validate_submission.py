"""Submission-specific scope checks, supplementing every existing scientific gate."""
from pathlib import Path
import hashlib, json, re, subprocess, tarfile

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[2]
E=HERE.parent/'evidence'
SOURCE='b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae'
checks=[]
def check(label,condition):
    assert condition,label
    checks.append(label)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
# All modifications, including untracked delivery files, must remain in the paper workspace.
changed=git('diff','--name-only',SOURCE).decode().splitlines()
untracked=git('ls-files','--others','--exclude-standard').decode().splitlines()
check('no experiment/source/result edits',all(p.startswith('paper/mlsys2027/') for p in changed+untracked))
for p in ['scripts/build_assets.py','scripts/validate_evidence.py','scripts/runtime_values.py','tables/runtime_values.tex','tables/values.tex']:
    path='paper/mlsys2027/manuscript/'+p
    check('original generator/validator/values '+p,(ROOT/path).read_bytes()==git('show',SOURCE+':'+path))
overlays={
 '01_platforms': [('All campaigns use greedy generated-token equivalence to a matched target-only reference.','Greedy execution is compared with matched target-only references; historical M4/RTX/B570 use re-tokenized text, while 358H uses direct IDs.'),('exact serialized controls','text-path-qualified controls')],
 '02_headlines': [('Exact pairs and faster prompts are separate metrics.','Matching pairs and faster prompts are separate metrics. M4/RTX/B570 count re-tokenized-text agreement; 358H counts direct-ID agreement.'),('Exact pairs &','Matching pairs &')],
 '04_energy': [('Exact fixed-$k=2$ energy neutral within uncertainty','Fixed-$k=2$ package-energy interval includes parity')],
 '05_regimes': [('each 90/90 exact','each 90/90 text-path-equal'),('Fractions count generated-token equality, not functional correctness.','Historical M4/RTX/B570 equality labels in the frozen inventory denote re-tokenized-text agreement; 358H denotes direct-ID agreement. Neither establishes functional correctness.')],
 '06_verification_lookup': [('Qualification describes the associated execution path.','Qualification and equality labels refer to the historical text-path comparator for the associated execution path; they do not certify generated-ID equality.')]
}
for name,replacements in overlays.items():
    original=git('show',SOURCE+':paper/mlsys2027/manuscript/tables/'+name+'.tex').decode()
    check('historical table preserved '+name,(HERE/'tables'/f'{name}.tex').read_text()==original)
    expected=original
    for old,new in replacements:
        check('projection source phrase '+name+':'+old[:25],old in expected)
        expected=expected.replace(old,new)
    check('only reviewed wording projection '+name,(HERE/'tables'/f'{name}_v05.tex').read_text()==expected)
framework=(HERE/'sections/02_framework.tex').read_text()
check('early comparator distinction','not direct generated-ID equality' in framework and 'recorded comparator' in framework)
check('direct runtime preserved','direct-token exact' in (HERE/'sections/07_runtime_codesign.tex').read_text())
check('no universal direct-ID table claim','All campaigns use greedy generated-token equivalence' not in (HERE/'tables/01_platforms_v05.tex').read_text())
check('energy parity not equivalence','a package-energy improvement is not established' in (HERE/'sections/04_outcomes.tex').read_text())
runtime=(HERE/'sections/07_runtime_codesign.tex').read_text()
for phrase in ['Historical M4 outcomes informed the study design','generation-loop initialization','request executions','not the fraction of beneficial decisions','Fixed speculation has the higher aggregate speedup point estimate']:
    check('runtime scope '+phrase,phrase in runtime)
archive=ROOT/'artifacts/m4_runtime/runtime-profitability-control-20260925/m4_runtime_complete_evidence.tar.gz'
with tarfile.open(archive) as t:
    for name in ['CALIBRATION_FREEZE.json','QUALIFICATION_REPORT.json']:
        data=t.extractfile('m4-runtime-evidence/freeze/'+name).read()
        committed=git('show','202109717754bc62f889d19b5fbb141bfc3cc529:benchmarks/m4_runtime/'+name)
        check('archive equals formal-start Git '+name,data==committed)
fresh=json.loads((E/'NUMERICAL_QA_V05.json').read_text())
check('fresh historical numerical checks',fresh['status']=='PASS' and len(fresh['checks'])==228 and all(c['pass'] for c in fresh['checks']))
runtimeqa=json.loads((E/'RUNTIME_QA_V05.json').read_text())
check('fresh full runtime gate',runtimeqa['status']=='PASS' and len(runtimeqa['checks'])==117 and runtimeqa['archive_recomputation']['verified_payload_files']==62)
report={'status':'PASS','source_head':SOURCE,'checks':checks,'changed_tracked_files':changed,'limits':['Historical text-path agreement is not direct-ID proof.','Hash and Git-byte consistency do not certify every possible historical exposure or machine state.','358H compact diagnostics verified, not raw-trace replay.']}
(E/'SUBMISSION_QA_V05.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Submission PASS: {len(checks)} additional scope/projection/provenance checks.')
