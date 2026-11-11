"""Stopped-task raw reconstruction only. Portable, read-only; cannot grant CPU8 acceptance."""
import sys,json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'source'),str(ROOT/'src/rev2')]
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def audit(root):
 root=Path(root).resolve();stop=load(root/'STOP_CONTEXT.json');need(stop['status']=='ENGINEERING_BLOCKED','stopped identity')
 need(not (root/'CAPABILITY_FREEZE.json').exists() and not (root/'source/FINAL_REVIEW_BINDING.json').exists(),'unexpected execution freeze')
 plan=load(root/'CPU8_PLAN.json');need(len(plan['cases'])==8,'original eight')
 formal=list((root/'formal').glob('*/WATCHDOG.jsonl'));need(not formal,'unexpected formal execution')
 import native_gate_audit,integration_gates,campaign_budget
 native=native_gate_audit.check(root)
 d0=snapshot=root/'D0_EVIDENCE_SNAPSHOT';m=snapshot/'legacy/AUDIT_INPUT_MANIFEST-normal-readonly-final.json'
 binding=dict(d0_snapshot='D0_EVIDENCE_SNAPSHOT',d0_manifest=m.name,d0_manifest_sha256=sha(m),d0_expected_sha256=sha(snapshot/'EXPECTED.json'))
 rebuilt=integration_gates.d0_reconstruct(root,binding)
 known={};closed={};commands=[];job_proofs=[]
 for folder in sorted((root/'processes').iterdir()):
  p=folder/'OS_EVENTS.jsonl'
  if not p.exists():continue
  b=p.read_bytes();need(b.endswith(b'\n'),'partial OS journal')
  rs=[json.loads(x) for x in b.splitlines()];need(all(x['seq']==i+1 for i,x in enumerate(rs)),'OS raw sequence')
  creates={};exits={}
  for x in rs:
   if x['event']=='PROCESS_CREATE':
    k=(x['pid'],x['created_filetime']);need(k not in creates,'duplicate actual identity');creates[k]=x;known[k]=x
   if x['event']=='PROCESS_CLOSED':
    k=(x['pid'],x['created_filetime']);need(k not in exits,'duplicate OS closure');exits[k]=x;closed[k]=x
  need(creates and set(creates)==set(exits),'unclosed observed command identities')
  for k,e in exits.items():
   need(int(e['exit_filetime'])>int(k[1]),'actual OS lifetime')
   need(len([x for x in rs if x['event']=='HANDLE_CLOSED' and x.get('pid')==k[0] and x.get('created_filetime')==k[1] and x.get('handle_kind')=='retained_process'])==1,'actual retained handle closure')
  end=[x for x in rs if x['event']=='OBSERVER_END']
  if folder.name in ('case-smoke-limit','review-smoke-limit'):
   import check_observer_smoke
   check_observer_smoke.check(folder,'case' if folder.name=='case-smoke-limit' else 'review',True)
   failure=load(folder/'INCOMPLETE.json');root_exit=[x for x in rs if x['event']=='ROOT_OS_EXIT_AFTER_FAILURE'];need(len(root_exit)==1,'resource negative root exit')
   commands.append(dict(id=folder.name,observed=len(creates),closed=len(exits),root_exit_code=root_exit[0]['exit_code'],observer_error=failure['error'],raw_sha256=sha(p),lifetime_seconds=sum((int(x['exit_filetime'])-int(x['created_filetime']))/1e7 for x in exits.values()),command_wall_seconds=None,observed_raw_interval_seconds=(rs[-1]['at_ns']-rs[0]['at_ns'])/1e9,terminal_format='Original expected resource failure cleanup, no fabricated OBSERVER_END/receipt'))
   continue
  need(len(end)==1,'observer final raw event')
  rc=load(folder/'RECEIPT.json');need(end[0]['receipt']==rc and rc['all_observed_closed'] is True,'raw/receipt closure mismatch')
  empty=[x for x in rs if x['event']=='JOB_EMPTY' and x['active_pids']==[]];need(empty,'no raw empty Job')
  commands.append(dict(id=folder.name,observed=len(creates),closed=len(exits),root_exit_code=rc['root_exit_code'],observer_error=rc['error'],raw_sha256=sha(p),lifetime_seconds=rc['lifetime_seconds'],command_wall_seconds=(rc['end_ns']-rc['begin_ns'])/1e9))
 metrics=campaign_budget.process_check(root,now=datetime.datetime.fromisoformat(stop['observed_utc'].replace('Z','+00:00')),read_only=True)
 need(metrics['known_closed']==metrics['known_identities'],'current raw identity closure incomplete')
 first=load(root/'review/FINAL_REVIEW.json');need(first['status']=='findings' and len(first['findings'])==4,'actual review1 findings')
 reviews=[]
 for name in ['full-review','full-review-2','full-review-3']:
  rc=load(root/'processes'/name/'RECEIPT.json')
  reviews.append(dict(id=name,root_exit_code=rc['root_exit_code'],error=rc['error'],observed=rc['observed'],closed=rc['closed'],all_observed_closed=rc['all_observed_closed'],wall_seconds=(rc['end_ns']-rc['begin_ns'])/1e9,lifetime_seconds=rc['lifetime_seconds']))
 need(not (root/'review/FINAL_REVIEW_2.json').exists() and not (root/'review/FINAL_REVIEW_3.json').exists(),'unexpected final review')
 rej=root/'processes/review2-regressions/stderr.log';need(b'CAMPAIGN_LIFETIME_LIMIT' in rej.read_bytes(),'original budget rejection missing')
 return dict(status='ENGINEERING_BLOCKED',uuid=stop['uuid'],protocol_commit=load(root/'ACQUISITION.json')['protocol_commit'],formal_cases=[dict(case_id=s['id'],status='UNSTARTED') for s in plan['cases']],execution_freeze=None,formal_started=0,final_scoped_clean=False,native_gates=native,d0_raw_reconstruction=rebuilt,commands=commands,known_raw_budget_at_stop=metrics,reviews=reviews,review1_findings=first['findings'],partial_review3_findings=stop['partial_review3_findings'],budget_rejection=dict(path=rej.relative_to(root).as_posix(),sha256=sha(rej),classification='Original conservative guard rejection retained; later NTFS terminal-file upper charge does not create missing API/OS time'),engineering_wall_at_stop_seconds=stop['engineering_wall_seconds'],source_auditor_sha256=sha(root/'source/reconstruct_stopped.py'),forbidden_counts=stop['forbidden_counts'],task_total_os_ledger='UNKNOWN',missing=['final complete scoped-clean deployment review','formal execution freeze','all eight formal cases','outer observer/watchdog/shell/tool-host exact OS lifetimes','churn tool API observation UTC'],scope='Authenticates the stopped CPU prefix, actual known identities, native prerequisites and D0 raw results. Not CPU8_INTEGRATION_PASS, ENGINEERING_READY or paper/scientific evidence. Delivery tail is separately charged.')
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);p.add_argument('--manifest');a=p.parse_args()
 root=Path(a.root).resolve();out=Path(a.output).resolve();need(root not in out.parents and out!=root,'output must be external')
 if a.manifest:
  from evidence_contract import manifest_check
  manifest_check(root,a.manifest)
 data=(json.dumps(audit(root),sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with out.open('xb') as f:f.write(data)
 print(json.dumps(dict(status='STOPPED_PREFIX_RECONSTRUCTED',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)),sort_keys=True))
if __name__=='__main__':main()
