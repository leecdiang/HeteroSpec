#!/usr/bin/env python3
"""Read-only scope/preservation checks for the literature-only v0.8.1 revision."""
from pathlib import Path
import hashlib, json, subprocess
ROOT = Path(__file__).resolve().parents[4]
START = '0e93dc93569ee091e48f2cd76327cfd8a9de3cde'
FREEZE = '1d3b556c93b477680788dfd1eb0737dfe9eee28c'
PAPER = 'paper/mlsys2027/'
ALLOWED = {PAPER+n for n in ['HANDOVER_CURRENT.md','MANUSCRIPT_STATUS.md','SUBMISSION_UPLOAD_CHECKLIST.md','reviews/AUTHOR_REVIEW_NOTE_V081.md']} | {PAPER+'manuscript/'+s for s in [
    'main.tex','appendix.tex','references.bib','README.md','sections/01_introduction.tex',
    'sections/05_diagnoses.tex','sections/06_synthesis.tex',
    'sections/08_related_work.tex','sections/10_conclusion.tex']}

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

assert git('rev-parse','mlsys2027-v0.8-author-freeze^{commit}').decode().strip()==FREEZE
changed=git('diff','--name-only',START).decode().splitlines()
tracked=set(git('ls-tree','-r','--name-only',START).decode().splitlines())
# New paths may be versioned review/QA/build outputs only, all under the paper tree.
new_allowed = lambda p: p.startswith(PAPER+'reviews/submission_v081/') or (p.startswith(PAPER+'evidence/') and 'V081' in p) or (p.startswith(PAPER+'manuscript/scripts/') and 'v081' in p) or (p.startswith(PAPER+'manuscript/output/') and 'v0.8.1' in p)
assert all(p in ALLOWED or (p not in tracked and new_allowed(p)) for p in changed),changed
protected=[p for p in tracked if not p.startswith(PAPER) or p.startswith(PAPER+'manuscript/figures/') or p.startswith(PAPER+'figures/') or p.startswith(PAPER+'manuscript/tables/') or p.startswith(PAPER+'manuscript/vendor/') or p.startswith(PAPER+'manuscript/output/') or p==PAPER+'manuscript/sections/09_limitations.tex']
assert not set(changed).intersection(protected)
# The byte-comparison explicitly covers every closed result macro and the canonical limitations.
explicit=[PAPER+'manuscript/'+n for n in ['tables/values.tex','tables/runtime_values.tex','tables/direct_id_values.tex','sections/09_limitations.tex','sections/07_runtime_codesign.tex']]
for name in explicit:
    assert (ROOT/name).read_bytes()==git('show',START+':'+name),name
before=git('show',START+':'+PAPER+'manuscript/appendix.tex').decode()
after=(ROOT/PAPER/'manuscript/appendix.tex').read_text()
assert after==before.replace('appendix v0.8}','appendix v0.8.1}').replace('manuscript v0.8. It','manuscript v0.8.1. It').replace('pdftitle={Supplement: Speculative Decoding Across Consumer Systems}', 'pdftitle={Supplement: Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems}').replace(r'\mlsystitle{Supplement: Speculative Decoding Across Consumer Systems}', r'\mlsystitle{Supplement: Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems}').replace(r'\mlsystitlerunning{Supplement: Speculative Decoding Across Consumer Systems}', r'\mlsystitlerunning{Supplement: Execution-Path Qualification in Speculative Decoding}')
main=(ROOT/PAPER/'manuscript/main.tex').read_text()
assert r'\mlsystitle{Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems}' in main
assert r'\RTGuard' in main and r'\RTAlways' in main and r'\RTExact' in main
report={'status':'PASS','starting_main':START,'author_freeze':FREEZE,
        'protected_tracked_paths':len(protected),'explicit_byte_comparisons':explicit,
        'changed_paths':changed,'all_closed_evidence_unchanged':True,
        'all_figure_bytes_unchanged':True,'canonical_limitations_unchanged':True,
        'appendix_only_title_and_version_labels_changed':True,'title_applied':True,
        'no_new_inference_timing_energy_sweeps':True,
        'execution_scope':'Only document builds, literature retrieval, rendering, read-only validation and git/PR operations were executed; no measurement runner or model was invoked.'}
(ROOT/PAPER/'evidence/PRESERVATION_FINALIZATION_V081_QA.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','protected_paths':len(protected),'closed_evidence_changed':False,'figure_bytes_changed':False}))
