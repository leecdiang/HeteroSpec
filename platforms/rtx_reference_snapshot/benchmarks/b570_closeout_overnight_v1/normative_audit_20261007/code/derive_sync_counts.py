"""Source-derived explicit frontend API counts, not kernel or internal sync counts."""
from pathlib import Path
import json,hashlib,collections
ROOT=Path(__file__).parent;BASE=Path('C:/hs/b570-closeout-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
native=(BASE/'src/native.cpp').read_text(encoding='utf-8');target=(BASE/'src/target.cpp').read_text(encoding='utf-8');observer=(BASE/'src/observer.h').read_text(encoding='utf-8')
assert native.count('llama_synchronize(')==4 and target.count('llama_synchronize(')==3
assert observer.count('if(instrument)llama_synchronize(ctx);')==1 and observer.count('llama_synchronize(c);')==1
assert observer.count('=state(src)')==2 and observer.count('=state(dst)')==1
allowed={'66b07015a83f4c0d772fce408da0ff3e34139065','64aa7a54ffc5668faf487342ffa6772a216619e3','cae1528f48b9fc46c1a3944a7f8a510bd0633c4f'}
selected={'B','C','C_ANCHOR_LONG','D_RESET','D_TIMING','E_CAPTURE','E_PILOT'};rows=[];totals=collections.Counter()
for p in (BASE/'raw').glob('*/RESULT.json'):
 r=load(p);stage=r['unit_id'].split('/')[0]
 if stage not in selected:continue
 assert r['source_commit'] in allowed
 capture=next(BASE/f for f in r['files'] if f.endswith('/capture.json'));raw=load(capture);instrument=r['config'].get('capture',False);transfer=int(raw['transfer'] is not None);work=raw['work']
 counted_calls=work['target_calls']+work['draft_calls'];reset_terminal=4 if r['config']['native'] else 3
 count=reset_terminal+3*transfer+(counted_calls if instrument else 0)
 row=dict(unit_id=r['unit_id'],stage=stage,warm=r['warm'],source_commit=r['source_commit'],capture=instrument,raw_capture_sha256=sha(capture),recorded_observer_calls=counted_calls,explicit_reset_prefill_terminal_syncs=reset_terminal,explicit_transfer_state_syncs=3*transfer,explicit_capture_decode_syncs=counted_calls if instrument else 0,frontend_explicit_llama_synchronize_calls=count,runtime_internal_sync_calls='MISSING',kernel_dispatches='MISSING',derivation='Actual completed branch + frozen source call sites; source-derived, not measured dispatch telemetry')
 rows.append(row);totals[stage]+=count
result=dict(status='PASS_SOURCE_DERIVATION',source_sha256={n:sha(BASE/'src'/n) for n in ['native.cpp','target.cpp','observer.h']},rows=len(rows),formal_nonwarm=sum(not r['warm'] for r in rows),formal_warm=sum(r['warm'] for r in rows),totals_by_stage=dict(totals),derivation='Native reset2+terminal2; target reset1+prefill barrier1+terminal1; online move states3; instrumented observer.end one per recorded observer caller. Excludes initialization/teardown and internal API synchronization. Capture-off retains reset/state/final synchronization in formal costs. No raw rewriting, inference or undocumented subtraction.',records=sorted(rows,key=lambda r:r['unit_id']))
(ROOT/'EXPLICIT_SYNC_COUNTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print({k:result[k] for k in ['status','rows','formal_nonwarm','formal_warm','totals_by_stage']})
