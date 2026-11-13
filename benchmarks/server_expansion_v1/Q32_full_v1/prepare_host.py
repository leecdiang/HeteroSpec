"""New host adapter epoch: charge one explicit empty-input native contract probe."""
from pathlib import Path
import argparse,shutil
from build import sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);a=p.parse_args();old=a.work/'runtime';out=a.work/'runtime-04';shutil.copytree(old,out);f=out/'host.py';s=f.read_text();anchor='def reservation(job):';assert s.count(anchor)==1;s=s.replace(anchor,anchor+"\n    if 'inputs' in job and not job['inputs']:return 1,0 # one native invalid-contract probe, no forward rows",1);f.write_text(s)
 save(out/'Q32_HOST_ACCOUNTING_ADAPTER.json',dict(original_host_sha256=sha(old/'host.py'),new_host_sha256=sha(f),change='Empty-input actual native invalid-contract probes reserve one logical request and zero forward rows; all failed workers retained. No budget/refund/GPU/resource/timeout or numerical-reader change',runtime={p.name:sha(p)for p in out.glob('*.py')}))
if __name__=='__main__':main()
