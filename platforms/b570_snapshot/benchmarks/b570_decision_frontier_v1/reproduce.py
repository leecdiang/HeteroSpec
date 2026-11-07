"""CPU-only new archive restore and independent same-host raw reanalysis entry point."""
import argparse,json,subprocess,sys,zipfile
from pathlib import Path
from contracts import *

def restore(archive,manifest,fresh):
 m=read(manifest);require(sha(archive)==m['archive_sha256'],'new archive SHA mismatch');require(not fresh.exists(),'fresh destination must not exist');fresh.mkdir(parents=True)
 with zipfile.ZipFile(archive) as z:
  rows=m['files'];require(len(z.infolist())==len(rows) and set(z.namelist())=={r['path'] for r in rows},'ZIP/member manifest mismatch')
  for r in rows:
   p=(fresh/r['path']).resolve();require(p.is_relative_to(fresh.resolve()),'ZIP path escape');p.parent.mkdir(parents=True,exist_ok=True)
   with z.open(r['path']) as src,p.open('xb') as dest:
    while b:=src.read(1024*1024):dest.write(b)
   require(p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'restored member hash mismatch')
 return {'status':'PASS_LOCAL_FRESH_RESTORE','archive_sha256':sha(archive),'files_verified':len(rows),'restored_root':str(fresh),'independent_machine_recomputation':'NOT_PERFORMED','remote_raw_availability':'REMOTE_PENDING'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--fresh',type=Path,required=True);ap.add_argument('--pr103-fresh',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();receipt=restore(a.archive,a.manifest,a.fresh);code=a.fresh/'frozen-code';run=a.fresh/'native-run';audit=a.fresh/'cpu-evidence/RAW_AUDIT.json';plan=run/'PLAN.json';a.out.mkdir(parents=True,exist_ok=False)
 commands=[['analyze_frontier.py','--plan',str(plan),'--audit',str(audit),'--fresh',str(a.pr103_fresh),'--out',str(a.out/'historical')],['analyze_frontier.py','--plan',str(plan),'--audit',str(audit),'--fresh',str(a.pr103_fresh),'--new-run',str(run),'--out',str(a.out/'new-batch')],['review_after_stop.py','--run',str(run),'--baseline',str(a.baseline),'--repo',str(a.repo),'--output',str(a.out/'post-stop-review.json')]]
 for i,cmd in enumerate(commands):
  result=subprocess.run([sys.executable,'-B','-X','utf8',str(code/cmd[0]),*cmd[1:]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);(a.out/(str(i)+'.stdout')).write_bytes(result.stdout);(a.out/(str(i)+'.stderr')).write_bytes(result.stderr);require(result.returncode==0,'fresh-path CPU recomputation failed')
 old=read(a.out/'historical/FRONTIER_ANALYSIS.json');new=read(a.out/'new-batch/FRONTIER_ANALYSIS.json');require(len(old['rows'])==44 and len(new['rows'])==0 and new['accounting']['native_process_starts']==new['accounting']['native_request_starts']==1,'restored analysis scope changed');receipt['historical_comparisons']=len(old['rows']);receipt['new_batch_comparisons']=len(new['rows']);receipt['accounting']=new['accounting'];receipt['new_run_raw_read_scope']=str(run);receipt['PR103_raw_read_scope']=str(a.pr103_fresh);receipt['external_model_runtime']='explicit frozen external files; same-host verification only';write(a.out/'RESTORE_RECEIPT.json',receipt);print(json.dumps(receipt))
