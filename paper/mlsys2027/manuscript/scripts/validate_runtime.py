#!/usr/bin/env python3
"""Validate runtime paper claims against immutable evidence, never run timing."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from runtime_values import ROOT,HERE,values,tex,load
E=HERE.parent/'evidence'
checks=[]
def check(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(name)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((E/'RUNTIME_BASELINE_V04.json').read_text())
for p,h in baseline['protected_runtime_sha256'].items():check('frozen '+p,digest(ROOT/p)==h)
pin=json.loads((E/'RUNTIME_358H_PIN_V04.json').read_text())
check('exact diagnostic pin',pin['pinned_commit']=='12f387d117fb52cc0ecc688931b9925abb29e71e')
for n,item in pin['files'].items():
    data=(E/'runtime_v04'/n).read_bytes()
    check('358H snapshot '+n,hashlib.sha256(data).hexdigest()==item['sha256'])
    original=subprocess.check_output(['git','show',pin['pinned_commit']+':'+item['source']],cwd=ROOT)
    check('358H Git blob '+n,data==original)
d=json.loads((E/'runtime_v04/runtime_diagnostic_v0_3_evidence.json').read_text())
p=json.loads((E/'runtime_v04/runtime_protocol_v0_3.json').read_text())
check('358H no R2',not d['v0_2_r2_executed'] and not d['formal_performance_data_exist'] and p['stage_gates']['r2_authorized'] is False)
check('358H diagnostic scope',d['claim_status']=='DIAGNOSTIC / INVALID_FOR_PERFORMANCE_CLAIMS' and d['scientific_verdict']=='UB2_INTRINSICALLY_BLOCKED_IN_TESTED_STACK')
check('358H no rollback bug proven',not d['correctness_bug_identified'] and not d['target_verification_semantics_changed'])
t=d['target54'];check('358H repeat and isolated controls',all(t[k] for k in ['reproduction_pass','ub1_repeat_exact','ub2_repeat_exact','order_independent','ub1_isolated_pass','ub2_isolated_pass']))
rows=[x for x in t['fresh_prefix_rows'] if x['output_index']==t['first_divergence_index']]
check('358H same exact prefix divergence',len(rows)==2 and all(x['teacher_forced_reference_prefix'] for x in rows) and rows[0]['input_prefix_length']==rows[1]['input_prefix_length'] and rows[0]['next_token']!=rows[1]['next_token'])
check('358H playback no live draft',d['verify48']['ub2_proposal_playback_reproduced'] and d['verify48']['draft_inference_executed'] is False)
# Validate selection membership/disjointness and regenerate the preregistered rank, without using timing.
inv=load('WORKLOAD_INVENTORY.json');seen=set();splits={}
for name,count in [('QUALIFICATION',16),('CALIBRATION',40),('HELDOUT',60)]:
    split=load(name+'_SPLIT.json');tasks=split['tasks'];ids={(t['workload_family'],t['task_id']) for t in tasks}
    check(name+' count/disjoint',len(ids)==count and not ids&seen);seen|=ids;splits[name]=ids
    check(name+' inventory hash',split['inventory_sha256']==digest(ROOT/'benchmarks/m4_runtime/WORKLOAD_INVENTORY.json'))
for family in ['HumanEval','Spec-Bench']:
    eligible=[t for t in inv['candidates'] if t['workload_family']==family and t['eligible_for_calibration'] and t['eligible_for_heldout']]
    check(family+' no exposure',all(not t['seen_in_historical_m4_execution'] and not t['historical_outcome_exposed'] for t in eligible))
    ranked=sorted(eligible,key=lambda t:hashlib.sha256(f"20260924|{family}|{t['task_id']}".encode()).hexdigest())
    for name,lo,hi in [('QUALIFICATION',0,8),('CALIBRATION',8,28),('HELDOUT',28,58)]:
        check(family+' '+name+' rank',{(family,t['task_id']) for t in ranked[lo:hi]}=={x for x in splits[name] if x[0]==family})
a=load('FORMAL_ANALYSIS.json');f=load('CALIBRATION_FREEZE.json');protocol=load('runtime_policy_protocol_v0.json')
check('policy freeze before heldout',f['formal_heldout_data_seen'] is False and f['selected']['candidate_id']=='E8_M000' and f['selected']['E']==8 and f['selected']['margin']==0)
check('M4 no energy',a['energy']==protocol['energy']=='NOT_CLAIMED')
check('M4 frozen bootstrap',a['bootstrap_resamples']==10000 and a['bootstrap_seed']==20260924 and a['bootstrap_unit']=='prompt')
archive=ROOT/'artifacts/m4_runtime/runtime-profitability-control-20260925'
descriptor=json.loads((archive/'archive_descriptor.json').read_text())
result=json.loads(subprocess.check_output([sys.executable,str(ROOT/'scripts/platform/m4_runtime/recompute_evidence_bundle.py'),str(archive/descriptor['archive']),'--expected-sha256',descriptor['sha256']],text=True))
check('M4 independent full archive recomputation',result==descriptor['independent_recomputation'])
check('M4 sidecar manifest',digest(archive/'bundle_manifest.json')==descriptor['bundle_manifest_sha256'])
check('runtime TeX exact source formatting',(HERE/'tables/runtime_values.tex').read_text()==tex())
vals,sources=values()
texts={str(p.relative_to(HERE)):p.read_text() for p in [HERE/'main.tex',HERE/'appendix.tex',*sorted((HERE/'sections').glob('*.tex')),HERE/'tables/07_runtime.tex']}
alltext='\n'.join(texts.values())
for n,v in vals.items():check('runtime macro '+n,re.search(r'\\'+n+r'\b',alltext) is not None)
for stale in ['proposed design only','implementation and measured results pending','No measured runtime intervention exists','hardware-complete / runtime-reserved','final conclusion awaits','final paper conclusion remains provisional']:
    check('no stale '+stale,stale.casefold() not in alltext.casefold())
s=texts['sections/07_runtime_codesign.tex']
for phrase in ['Fixed speculation has the higher aggregate speedup point estimate','No formal R2 performance run occurred','No runtime energy claim','offline oracle','no position drift or specific rollback-boundary bug','frozen tested target stack']:
    check('required boundary '+phrase,phrase in s)
# Runtime empirical values must use RT macros; raw decimals in its prose/table are model/revision identities only.
for n in ['sections/07_runtime_codesign.tex','tables/07_runtime.tex']:
    check(n+' no raw empirical decimals',set(re.findall(r'\d+\.\d+',texts[n])) <= {'0.6'})
report={'status':'PASS','checks':checks,'archive_recomputation':result,'macro_values':vals,'macro_sources':sources,'358h_pin':pin['pinned_commit'],'limits':['358H compact diagnostic findings verified; local raw traces not replayed.','Historical exposure exclusion verified against frozen inventory, not re-established from unavailable measurement-machine files.','Semantic prose and causal scope require human review.']}
(E/'RUNTIME_QA_V05.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Runtime PASS: {len(checks)} checks, {len(vals)} sourced macros, complete M4 archive recomputation, pinned 358H controls.')
