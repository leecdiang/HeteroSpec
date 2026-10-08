from pathlib import Path
import json,shutil
R=Path(__file__).parent
s=(R/'runner.py').read_text()
s=s.replace("BIN=ROOT/'build/Release'","BIN=ROOT/'candidate-build/Release'")
if "BIN=ROOT/'candidate-build/Release'" not in s:
 import re
 s=re.sub(r"BIN\s*=\s*ROOT\s*/\s*'build'\s*/\s*'Release'", "BIN=ROOT/'candidate-build/Release'",s)
assert "BIN=ROOT/'candidate-build/Release'" in s
s=s.replace('b570-pilot-native.exe','b570-candidate-native.exe').replace('b570-pilot-target.exe','b570-candidate-target.exe').replace('time.monotonic()','time.perf_counter()')
(R/'candidate_runner.py').write_text(s,encoding='utf8')
for p in (R/'build/Release').glob('*.dll'):
 if p.name.lower()!='llama.dll':shutil.copyfile(p,R/'candidate-build/Release'/p.name)
units=[]
for round in [1,2]:
 config=dict(label='CANONICAL_PREFILL_INPLACE_PHASE_BINDING',native=True,k=2,ub=1,prefill=128,cap=128,capture=round==1,plain=True,round=round)
 for task in json.loads((R/'DEV_INPUTS.json').read_text(encoding='utf8')):units.append(dict(unit_id=f'C/{round}/{task["id"]}',task=task['id'],config=config))
(R/'C_MANIFEST.json').write_text(json.dumps(dict(units=units,stop_first_mismatch=True,reference='historical immutable R cap128 IDs/EOG offline only',candidate_family_count=1,host_clock='QueryPerformanceCounter via time.perf_counter; paid timings unadjusted'),indent=2)+'\n',encoding='utf8')
print('C runner and 12 fixed units prepared; zero forwards')
