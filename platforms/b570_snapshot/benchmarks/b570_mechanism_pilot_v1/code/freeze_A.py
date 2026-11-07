from pathlib import Path
import json,hashlib,subprocess
from datetime import datetime,timezone
R=Path(__file__).parent
G='C:/Users/DIANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert json.loads((R/'STAGE0.json').read_text())['status']=='PASS'
x=dict(utc=datetime.now(timezone.utc).isoformat(),sources={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in list((R/'src').glob('*'))+[R/n for n in ['runner.py','resume.py','PROTOCOL.json','A_SCHEDULE.json','DEV_INPUTS.json','UNIT_MANIFEST.json','HISTORICAL_PARENTS.json']]},binaries={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in (R/'build/Release').glob('*') if p.suffix in ['.exe','.dll']},build='MSVC19.44.35228 x64 Release, CMake VS17; pinned b10839 published libraries, new private executable names',capture='on first round/off second; bounded natural checkpoints both rounds diagnostic cost only',budget='A48 +10 warm; failures counted; no scientific retry',gates='all available historical raw arrays/endpoints and switch stability; known failures must remain')
(R/'A_FREEZE.json').write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
subprocess.run([G,'add','.'],cwd=R,check=True);subprocess.run([G,'commit','-m','Freeze CPU feasibility and natural checkpoint bridge before StageA outputs'],cwd=R,check=True)
print('FROZEN',flush=True)
