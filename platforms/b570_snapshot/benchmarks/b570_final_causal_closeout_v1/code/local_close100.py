"""CPU-only fresh full archive restore and independent byte rederivation."""
import json,hashlib,subprocess,sys,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_bytes())
def step(name,argv):
 p=subprocess.run(argv,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=240)
 (R/'receipts'/f'{name}.stdout.log').write_bytes(p.stdout);(R/'receipts'/f'{name}.stderr.log').write_bytes(p.stderr)
 assert p.returncode==0,p.stderr.decode(errors='replace');return p
def main():
 dest=R/'receipts/local_restore';out=R/'receipts/local_rederived';out.mkdir(exist_ok=False)
 step('LOCAL_RESTORE',[sys.executable,'-B','-X','utf8',str(R/'code/restore98.py'),'--cas',str(R/'COMPLETE_CAS.zip'),'--dest',str(dest)])
 step('LOCAL_AUDIT',[sys.executable,'-B','-X','utf8',str(dest/'code/verify100.py'),'--root',str(dest),'--output',str(out)])
 step('LOCAL_SYNTHETIC',[sys.executable,'-B','-X','utf8',str(dest/'code/test_verify100.py'),str(dest)])
 # Re-run entire old independent audit on archived full historical bytes, not trust original JSON.
 inherited=R/'receipts/local_rederived99';inherited.mkdir()
 step('LOCAL_INHERITED_AUDIT',[sys.executable,'-B','-X','utf8',str(dest/'baseline/pr99/code/verify98.py'),'--root',str(dest/'baseline/pr99'),'--output',str(inherited)])
 files=['PARTITION_MATRIX','OPERATOR_FIRST_DIFF','FIXED_INPUT_REPLAY','STATE_RESTORE_ADMISSION','KV_LOGITS_CROSS','GPU_TIMELINE','QUALIFICATION','RAW_EVIDENCE','RESULTS','INDEPENDENT_VERIFICATION']
 exact={}
 for n in files:
  assert (out/f'{n}.json').read_bytes()==(R/f'{n}.json').read_bytes(),n;exact[n+'.json']=sha(out/f'{n}.json')
 for n in ['RESULTS','QUALIFICATION','WORK_WITNESSES','NUMERICAL_STATE_LAYOUTS','INDEPENDENT_VERIFICATION']:assert (inherited/f'{n}.json').read_bytes()==(R/'baseline/pr99'/f'{n}.json').read_bytes()
 receipt=dict(status='PASS_FRESH_LOCAL_COMPLETE_BYTES_AND_INDEPENDENT_EXACT_REDERIVATION',**load(R/'COMPLETE_CAS.json'),exact_artifacts=exact,full_target_rehashed=True,inherited_PR99_full_independent_audit=True,synthetic_rejections=load(dest/'SYNTHETIC_REJECTION.json')['tests'],new_GPU_forwards=0)
 (R/'LOCAL_RESTORE.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
