"""Shared identities and atomic evidence writes for the RTX closeout."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
PHASE2=Path(os.environ.get('HETEROSPEC_PHASE2_ROOT',str(HERE.parent/'rtx-consistency-phase2')))
PHASE1=Path(os.environ.get('HETEROSPEC_PHASE1_ROOT',str(HERE.parent/'continuity-state-v1')))
ASSET=Path(os.environ.get('HETEROSPEC_ASSET_ROOT','D:/HeteroSpec-PC'))
OLDROOT=Path(os.environ.get('HETEROSPEC_RTX_STUDY_ROOT','D:/HeteroSpec-RTX-Target-V1'))
REPO=HERE.parent/'feasibility'
EOG={128247,151643,151645,151662,151663,151664}
SEED='HeteroSpec-RTX-Phase2-B-v1'
sys.path.insert(0,str(PHASE2))

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n');q.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def head():
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=HERE,text=True).strip()
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip()
def formatted(text):
    if text.endswith('\n'):text=text[:-1]
    return '<|im_start|>user\n'+text+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
def rank(task):return hashlib.sha256((task+SEED).encode()).hexdigest()
