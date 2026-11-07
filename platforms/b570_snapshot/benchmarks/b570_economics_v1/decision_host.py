"""All exposed roots and controls retained; clean service determines the gate."""
from native_host import *
from costs import economic_identity
import math,importlib.util

def label(method,arm):return method+'_'+{'M':'M','H1':'D1','C4U4':'D4','C4U1':'C4U1'}[arm]

def decide():
 raw=read(ROOT/'PARALLEL_PILOT.json')['records'];measured=[x for x in raw if x['kind']=='measure']
 assert len(measured)==64 and len(raw)==128
 roots=read(ROOT/'EXPOSED_INPUTS.json')['inputs'];groups={}
 for x in measured:groups.setdefault(label(x['method'],x['arm']),[]).append(x)
 assert set(groups)=={'S_M','L_M','S_D1','L_D1','S_D4','L_D4','S_C4U1','L_C4U1'}
 totals={a:sum(r['service_s'] for r in rows) for a,rows in groups.items()};byroot={}
 for a,rows in groups.items():
  assert len(rows)==8
  byroot[a]=[sum(r['service_s'] for r in rows if r['root']==i) for i in range(4)]
  assert all(sum(r['root']==i for r in rows)==2 for i in range(4))
 best_m=min(('S_M','L_M'),key=totals.get)
 diag=read(ROOT/'PARALLEL_DIAGNOSTICS.json')['records'];identities=[]
 for i in range(4):
  for method in ('S','L'):
   window={x['arm']:x['cost'] for x in diag if x['root']==i and x['method']==method}
   for arm in ('H1','C4U4','C4U1'):identities.append(dict(root=i,method=method,arm=arm,mode=1,**economic_identity(window['M'],window[arm])))
 sync=read(ROOT/'PARALLEL_SYNCHRONIZED.json')['records']
 for i in (0,2):
  for method in ('S','L'):
   window={x['arm']:x['cost'] for x in sync if x['root']==i and x['method']==method}
   for arm in ('H1','C4U4'):identities.append(dict(root=i,method=method,arm=arm,mode=2,**economic_identity(window['M'],window[arm])))
 spec=importlib.util.spec_from_file_location('b570_economics_design',HERE/'design.py');design=importlib.util.module_from_spec(spec);spec.loader.exec_module(design)
 quality=read(ROOT/'PARALLEL_QUALIFIED.json')['status']=='COMPLETE_T_CONTRACT_PASS'
 assert quality and (ROOT/'KNOWN_PROBE_RESULTS.json').exists() and (ROOT/'CAP1_RESULTS.json').exists() and (ROOT/'K3_PROTOCOL_RESULTS.json').exists()
 decisions={}
 for a in groups:
  if a.endswith('_M'):continue
  ratios=[byroot[best_m][i]/byroot[a][i] for i in range(4)]
  total=totals[best_m]/totals[a]
  d=design.gate(quality,ratios,dict(source='separate mode1 cost-only and mode2 blocking windows',identity_is_not_causal=True),total_ratio=total,meaningful_target_capability=False)
  decisions[a]=dict(**d,best_fixed_M=best_m,total_ratio=total,root_ratios=ratios,beats_both_M_totals=all(totals[m]>totals[a] for m in ('S_M','L_M')),caller_only_control='C4U1' in a)
 provisional=[a for a,d in decisions.items() if d['action']=='FREEZE_JOINT_CONFIRMATION']
 result=dict(status='EXPOSED_DEVELOPMENT_GATE',complete_clean_service_totals_s=totals,root_service_totals_s=byroot,decisions=decisions,provisional_joint_opportunities=provisional,independent_roots=4,blocks=2,all_controls_retained=True,all_warmups_retained=True,no_unseen_claim=True,descriptive_cost_identities=identities,physical_work=diag,acceptance={a:dict(proposed=sum(r['drafted'] for r in rows),accepted=sum(r['accepted'] for r in rows)) for a,rows in groups.items()},target_only_panel_rule='No new natural S_M/L_M capability is tested by an unchanged original producer and single-row ordinary continuation alone; physical q2/q4/q32 evidence remains separate',frozen_confirmation_started=False)
 write(ROOT/'DEVELOPMENT_DECISION.json',result);print(json.dumps(dict(totals=totals,decisions=decisions),indent=2),flush=True)
 return result

if __name__=='__main__':decide()
