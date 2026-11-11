"""Recover only terminal archive/replay into fresh paths; never launch models.

This avoids the retained supervisor-v2 log-name collision. It deliberately does
not retry or change any measurement, frozen configuration, source or ledger.
"""
from pathlib import Path
import argparse,json,os,subprocess,sys
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2);f.write('\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--tools',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert json.loads((a.work/'COMPLETE.json').read_text())['passed'],'Native completion required; do not infer it from stale supervisor status'
 for task in Path('/proc').iterdir():
  if not task.name.isdigit():continue
  try:
   if(task/'comm').read_text().strip()=='transfer-worker':assert str(a.work).encode()not in(task/'cmdline').read_bytes(),'Wait for exact-study native worker'
  except OSError:pass
 a.out.mkdir();env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
 for script,args in [('archive.py',['--root',str(a.root),'--work',str(a.work),'--out',str(a.out/'export')]),('replay_archive.py',['--bundle',str(a.out/'export'),'--out',str(a.out/'replay')])]:
  with(a.out/(script+'.stdout.log')).open('xb')as so,(a.out/(script+'.stderr.log')).open('xb')as se:
   r=subprocess.run([sys.executable,'-B',str(a.tools/script),*args],stdout=so,stderr=se,env=env,timeout=900)
  if r.returncode:raise RuntimeError(script+' failed; all original data retained')
 checked=json.loads((a.out/'replay/CHECKED.json').read_text());assert checked['passed']
 save(a.out/'COMPLETE.json',dict(status='LOCAL_ARCHIVE_AND_REPLAY_PASS',GPU_requests=0,measurements_repeated=False,source_work=str(a.work),public_upload='separate authorized connector step'))
if __name__=='__main__':main()
