from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
for cohort in ('qwen_config01','config06'):
 old=Path('E:/rtx160')/cohort/'build'; new=Path('E:/rtx164/active03')/cohort
 (new/'core').mkdir(); (new/'bin').mkdir()
 for f in [*old.glob('*.hpp'),*old.glob('*.h'),old/'worker.cpp']:shutil.copyfile(f,new/f.name)
 for name in ('ar.cmd','ranlib.cmd'):shutil.copyfile(old/'core'/name,new/'core'/name)
 for f in (old/'bin').glob('*.dll'):shutil.copyfile(f,new/'bin'/f.name)
 receipt=[]
 for entry in json.loads((old/'BUILD.json').read_bytes())['commands']:
  cmd=[s.replace(str(old),str(new)).replace(old.as_posix(),new.as_posix()) for s in entry['argv']]
  with (new/(entry['label']+'.log')).open('xb') as log:
   t=time.monotonic();r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
  receipt.append(dict(label=entry['label'],argv=cmd,seconds=time.monotonic()-t,exit_code=r.returncode));(new/'COMMANDS.json').write_text(json.dumps(receipt,indent=2));assert r.returncode==0
 print(cohort,'compiled',flush=True)
