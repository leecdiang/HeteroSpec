"""Explicit pinned PR62/195/209 overlap check; an empty read cannot pass."""
from pathlib import Path
import hashlib,json,subprocess
from admission import ROOT,REPO,put,sha
from select_inputs import visit

def main():
    cohort=json.loads((ROOT/'cohort/COHORT_ADMISSION.json').read_bytes())['selected']
    old209=json.loads((ROOT/'reference_209/m2-run-03/ROOT_SELECTION.json').read_bytes())
    old195=json.loads(Path('D:/rtx192-review-v2/R2/NATIVE_INPUTS.json').read_bytes())['inputs']
    pin='8dfa60a2492e0639a0774f7bac842273485ca26a'
    names=subprocess.check_output(['git','-C',str(REPO),'ls-tree','-r','--name-only',pin,'benchmarks/rtx_closeout_bcd']).decode().splitlines()
    names=[n for n in names if n.endswith('.json')];assert names,'No pinned PR62 exposure records found'
    blocked=set();pins={}
    for name in names:
        raw=subprocess.check_output(['git','-C',str(REPO),'show',pin+':'+name]);pins[name]=hashlib.sha256(raw).hexdigest();visit(json.loads(raw),blocked)
    overlap62=[r['id'] for r in cohort if {r['id'],r['text_sha256'],r['raw_prompt_sha256'],r['formatted_prompt_sha256']}&blocked]
    selected={r['id'] for r in cohort};overlap195=sorted(selected&{r['id'] for r in old195});overlap209=sorted(selected&set(old209['roots']))
    proof=dict(passed=not(overlap62 or overlap195 or overlap209),pr62_pin=pin,pr62_files=len(names),pr62_pins=pins,
        overlap_pr62=overlap62,overlap_pr195=overlap195,overlap_pr209=overlap209,
        scope='Project exposure identities and content hashes only; no training-unseen assertion',
        prior_reader_failure='EXPOSURE_FAILED_READER_01.json retained: sparse local path returned zero records; it is invalid evidence. No formal reference/timing was run under that empty-read result.',model_forwards=0)
    put(ROOT/'cohort/EXPOSURE_COMPLETE.json',proof);assert proof['passed']
    print('Pinned PR62 files',len(names),'all explicit overlap checks pass',flush=True)

if __name__=='__main__':main()
