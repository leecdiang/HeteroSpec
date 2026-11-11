"""Correct offline sampling, keep passed core gates and register full costs.

The main qualified/timing ELF, own R, original cases and96 measurements do not
change. A prospective640-request independent32B envelope includes all previous
attempts plus96 matched warmups. The old512 registration remains in history.
"""
from pathlib import Path
import argparse,shutil
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();w=a.root/'q32-q4-full-20261109-01'
 for name in ['build.py','resource_guard.py','geometry_journal.py']:shutil.copy2(a.source/name,a.out/name)
 s=(a.source/'qualification.py').read_text().replace("self.w/'runtime-05'","self.w/'runtime-06'").replace('total>304','total>432').replace('total<=496','total<=624').replace('unchanged512 ceiling','registered640 ceiling').replace('unchanged512 Q32 ceiling','registered640 Q32 ceiling')
 (a.out/'qualification.py').write_text(s)
 s=(a.source/'finish.py').read_text().replace('closure-08','closure-09').replace('FINISH_NOT_ADMITTED-08','FINISH_NOT_ADMITTED-09')
 anchor=" assert not(a.work/'PANEL_NOT_ADMITTED_QUOTA.json').exists(),'Full eligibility used provisional panel quota; no partial panel'";assert s.count(anchor)==1
 replacement=" registry=read(a.work/'BUDGET_REGISTRATION_V2.json');assert registry['new_request_ceiling']==640 and registry['original_request_ceiling']==512 and registry['row_ceiling']==2000000\n assert registry['R_freeze_sha256']==sha(a.work/'reference/REFERENCE_FREEZE.json')\n while not(a.work/'PUBLIC_REMAINING_SOURCE_BINDING.json').exists():\n  assert now()<ADMIT,'Public source/budget readback not ready before whole-panel boundary';time.sleep(5)\n binding=read(a.work/'PUBLIC_REMAINING_SOURCE_BINDING.json');assert binding['passed']and binding['budget_registration_sha256']==sha(a.work/'BUDGET_REGISTRATION_V2.json')\n for x in binding['sources']:assert sha(x['path'])==x['sha256']\n entries_reserved=[json.loads(x)for x in(a.work/'ledger.jsonl').read_text().splitlines()if json.loads(x)['event']=='RESERVE'];inherited=read(a.work/'INHERITED_ACCOUNTING.json');assert inherited['requests']+sum(x['requests']for x in entries_reserved)+192+16<=640,'Full panel plus closure reserve cannot fit registered640 ceiling'"
 s=s.replace(anchor,replacement,1)
 anchor="primer_endpoints=primer_endpoints,warmup_policy=";assert s.count(anchor)==1;s=s.replace(anchor,"budget_registration_sha256=sha(a.work/'BUDGET_REGISTRATION_V2.json'),request_ceiling=640,primer_endpoints=primer_endpoints,warmup_policy=",1)
 (a.out/'finish.py').write_text(s)
 s=(a.source/'archive.py').read_text().replace('LAUNCH_08','LAUNCH_09').replace('CLOSED08','CLOSED09').replace('export-10','export-11').replace("('qualification-08', 'finish-08')","('finish-09',)").replace("('qualification-08', 'closure-08')","('qualification-08', 'closure-09')").replace('request_ceiling=512','request_ceiling=640')
 assert "('qualification-08', 'finish-08')"not in s;(a.out/'archive.py').write_text(s)
 runtime=w/'runtime-06';shutil.copytree(w/'runtime-05',runtime);p=runtime/'host.py';s=p.read_text();anchor="+req<=512";assert s.count(anchor)==1;s=s.replace(anchor,'+req<=640',1).replace('Cumulative PR197 envelope exhausted','Registered independent32B envelope exhausted');compile(s,str(p),'exec');p.write_text(s)
 for name in ['remaining_coordinator.py','delivery_audit.py','postprocess_delivery.py']:shutil.copy2(Path(__file__).parent/name,a.out/('coordinator.py'if name=='remaining_coordinator.py'else name))
 for p in a.out.glob('*.py'):compile(p.read_text(),str(p),'exec')
 save(a.out/'ADAPTER_BINDING.json',dict(original_sources={p.name:sha(p)for p in a.source.glob('*.py')},new_sources={p.name:sha(p)for p in a.out.glob('*.py')},main_native_ELF_changed=False,reference_changed=False,core_gate_epoch='qualification-08',remaining_gate_epoch='closure-09',offline_observer_corrected_in_fresh_build=True,new_independent_Q32_request_ceiling=640,prior_counters_and_failures_retained=True,measured_requests=96,matched_warmups=96,old_8B_budget_unchanged=True,whole_panel_before_03_BJT_and_new_worker_before_05_unchanged=True))
if __name__=='__main__':main()
