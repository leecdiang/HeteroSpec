"""Seal new evidence, restore to a fresh directory, compare every byte hash, and audit."""
import argparse,hashlib,json,subprocess,sys,zipfile
from pathlib import Path

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--dest',type=Path,required=True);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--restore',type=Path,required=True);ap.add_argument('--experiment',type=Path,required=True);a=ap.parse_args()
 assert not (a.out/'EXECUTION.lock').exists(),'run still active'
 assert not a.archive.exists() and not a.restore.exists(),'fresh paths only'
 files=sorted(p for p in a.out.rglob('*') if p.is_file());manifest=[]
 for p in files:
  assert not p.is_symlink()
  manifest.append({'path':p.relative_to(a.out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
 write(a.dest/'ARCHIVE_MANIFEST.json',{'scope':'New PR103 evidence only; external PR101 baseline/model remain byte-pinned prerequisites','files':manifest})
 a.archive.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(a.archive,'x',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
  for item in manifest:z.write(a.out/item['path'],item['path'])
 archive_pin={'path':str(a.archive),'bytes':a.archive.stat().st_size,'sha256':sha(a.archive)}
 a.restore.mkdir(parents=True)
 with zipfile.ZipFile(a.archive) as z:
  assert {i.filename for i in z.infolist()}=={x['path'] for x in manifest}
  for item in z.infolist():
   assert (a.restore/item.filename).resolve().is_relative_to(a.restore.resolve())
   z.extract(item,a.restore)
 for item in manifest:
  q=a.restore/item['path'];p=a.out/item['path']
  assert q.stat().st_size==item['bytes'] and sha(q)==item['sha256'] and sha(p)==item['sha256'],item['path']
 freeze=json.loads((a.restore/'FREEZE.json').read_bytes())
 for item in freeze['inputs']:
  rel=Path(item['path']).relative_to(a.out)
  q=a.restore/rel
  assert q.stat().st_size==item['bytes'] and sha(q)==item['sha256']
 # The inherited absolute baseline/model and original-path FREEZE dependencies remain explicit external prerequisites.
 p=subprocess.run([sys.executable,'-B','-X','utf8',str(a.experiment),'analyze','--out',str(a.restore)],capture_output=True)
 (a.dest/'restored-analysis.stdout').write_bytes(p.stdout);(a.dest/'restored-analysis.stderr').write_bytes(p.stderr)
 assert p.returncode==0,p.stderr.decode(errors='replace')
 restored=json.loads(p.stdout);original=json.loads((a.out/'ANALYSIS-cross.json').read_bytes()) if (a.out/'ANALYSIS-cross.json').exists() else json.loads((a.out/'ANALYSIS-control.json').read_bytes())
 assert restored==original,'restored CPU analysis differs'
 write(a.dest/'RESTORATION.json',{'status':'PASS_LOCAL_FRESH_RESTORE_AND_CPU_REANALYSIS','archive':archive_pin,'restored_root':str(a.restore),'files_compared':len(manifest),'all_original_and_restored_bytes_match':True,'restored_frozen_input_bytes_match':True,'cpu_analysis_exit_code':p.returncode,'cpu_analysis_identical':True,'remote_raw_archive_publication':'NOT_PERFORMED','external_baseline_and_model':'Exact frozen original PR101 source/runtime/model remain prerequisites; absolute paths are retained rather than edited','projection_mediation':'NOT_ESTABLISHED'})
 print(json.dumps({'status':'PASS_LOCAL_FRESH_RESTORE_AND_CPU_REANALYSIS','files':len(manifest),'archive_bytes':archive_pin['bytes'],'analysis':restored['status']}))
if __name__=='__main__':main()
