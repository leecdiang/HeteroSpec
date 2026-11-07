"""Resume A after a host interruption without accepting changes to its loaded programs."""
from pathlib import Path
import runner
R=Path(__file__).parent
f=runner.read(R/'A_FREEZE.json')
assert runner.read(R/'STAGE0.json')['status']=='PASS'
for p,h in f['sources'].items():
 if p=='src/cross.cpp':continue # not loaded by StageA; its pre-B observational extension is separately frozen
 assert runner.sha(R/p)==h,p
for p,h in f['binaries'].items():
 if p.endswith('/b570-pilot-cross.exe'):continue # no cross helper run during A
 assert runner.sha(R/p)==h,p
runner.acquire()
try:runner.run_sessions('A',runner.read(R/'A_SCHEDULE.json'))
finally:runner.release()
