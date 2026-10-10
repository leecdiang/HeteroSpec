"""Commit/push concrete manifests and independently check the remote ref."""
from common import *
def freeze(label,manifest):
    subprocess.run(['git','add','--sparse','benchmarks/jsa_rtx_validation_v1','scripts/platform/jsa_rtx_validation_v1'],cwd=REPO,check=True)
    subprocess.run(['git','commit','-m',label],cwd=REPO,check=True)
    frozen=head();branch=subprocess.check_output(['git','branch','--show-current'],cwd=REPO,text=True).strip();subprocess.run(['git','push','origin','HEAD:'+branch],cwd=REPO,check=True)
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=REPO,text=True).split()[0];assert remote==frozen
    receipt={'utc':now(),'label':label,'manifest':manifest,'manifest_sha256':sha(PUB/manifest),'frozen_sha':frozen,'remote_sha':remote,'branch':branch,'independent_read':'git ls-remote separate process after push'}
    key=manifest.removesuffix('_F0.json') if manifest.endswith('_F0.json') else 'F_E_ENGINEERING';save(LOCAL/(key+'_REMOTE_RECEIPT.json'),receipt)
    p=LOCAL/'FREEZE_HISTORY.json';history=read(p) if p.exists() else [read(LOCAL/'S_REMOTE_RECEIPT.json')];history.append(receipt);save(p,history);save(PUB/'FREEZE_RECEIPTS.json',history);print('REMOTE FREEZE VERIFIED',label,frozen,flush=True)
if __name__=='__main__':
    import sys
    freeze(sys.argv[1],sys.argv[2])
