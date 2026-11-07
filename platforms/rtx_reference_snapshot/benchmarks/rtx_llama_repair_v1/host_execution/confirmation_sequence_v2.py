"""Continue the authorized registered gates after successful new regressions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

REPO=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160')
ROOT=Path('E:/rtx160');BUNDLE=ROOT/'research/epoch06'
CODE=REPO/'scripts/experiments/rtx_llama_repair_v1'
HELPERS=REPO/'benchmarks/rtx_llama_repair_v1/host_execution'
OPERATIONS=Path('D:/rtx160/operations')


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,script,args):
    subprocess.run([sys.executable,'-B',str(OPERATIONS/'run_logged.py'),name,sys.executable,'-B',str(script),*map(str,args)],cwd=REPO,check=True)


def main():
    deadline=time.monotonic()+10800
    coverage=ROOT/'exposure04/COVERAGE_REVIEW.json'
    while not ((OPERATIONS/'QWEN_SEQUENCE01.json').exists() and coverage.exists()):
        assert time.monotonic()<deadline,'finite regression wait expired'
        time.sleep(10)
    assert read(OPERATIONS/'QWEN_SEQUENCE01.json')['exit_code']==0,'regression continuation failed'
    reg=ROOT/'research/CROSS_MODEL_REGRESSION.json'
    assert read(reg)['status']=='CROSS_MODEL_REGRESSION_PASS'
    exposure=ROOT/'exposure04';prep=ROOT/'preparation01'
    review=read(coverage)
    assert review['status']=='ALL_REMOTE_HEADS_TAGS_AND_PR_HISTORY_REVIEWED'
    for path,digest in review['evidence'].items():assert sha(Path(path))==digest
    report=read(exposure/'REPORT.json')
    assert report['coverage_review_complete'] and not report['errors']
    receipt=read(prep/'TOKENIZATION_RECEIPT.json')
    assert receipt['status']=='EXACT_ORIGINAL_TOKENIZER_ROUNDTRIP' and receipt['historical_items']==12 and receipt['forward_calls']==0
    assert not (BUNDLE/'CANDIDATE_FREEZE.json').exists()
    provenance={'status':'PRE_OUTPUT_SELECTION_INPUTS_BOUND',
      'n':24,'strata':'code/math x short/long; six each; original registered seed',
      'inputs':{str(p):sha(p) for p in [reg,coverage,exposure/'REPORT.json',exposure/'EXPOSURES.json',prep/'POOL.json',prep/'TOKENIZATION_RECEIPT.json',Path(__file__)]}}
    with (ROOT/'research/SELECTION_PROVENANCE.json').open('x') as f:json.dump(provenance,f,indent=2)
    panel=ROOT/'research/HELDOUT_SELECTION01.json'
    run('SELECT_HELDOUT01',CODE/'panel.py',['--pool',prep/'POOL.json','--exposures',exposure/'EXPOSURES.json','--n',24,'--out',panel])
    run('FREEZE06',CODE/'host.py',['seal','--bundle',BUNDLE,'--panel',panel,
      '--mechanism',BUNDLE/'MECHANISM_REVIEW.json','--development',BUNDLE/'DEVELOPMENT_AUDIT.json','--regression',reg])
    run('CONFIRM06',CODE/'host.py',['confirm','--bundle',BUNDLE])
    run('INDEPENDENT_COST06',HELPERS/'independent_cost.py',['--bundle',BUNDLE,'--out',BUNDLE/'INDEPENDENT_COST.json'])
    print('CONFIRMATION_AND_INDEPENDENT_COST_COMPLETE',flush=True)


if __name__=='__main__':main()
