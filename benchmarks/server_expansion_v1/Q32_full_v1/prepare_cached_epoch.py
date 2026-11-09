"""Common observer-only correction, strict all-six gates and matched warmups.

No numerical archive or independent reference change. Preserve all earlier
epochs. Timing has not started; register this complete design before freezing.
"""
from pathlib import Path
import argparse,shutil
from build import read,sha,save
POLICY='Per request: immutable device type once per actual device; fresh tensor buffer device every callback'
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();w=a.root/'q32-q4-full-20261109-01'
 for name in ['build.py','resource_guard.py','geometry_journal.py']:shutil.copy2(a.source/name,a.out/name)
 s=(a.source/'qualification.py').read_text().replace('qualification-06','qualification-07').replace("self.w/'runtime-04'","self.w/'runtime-05'")
 anchor='greedy=True,cuda_graphs=False,';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'observer_device_type_policy='+repr(POLICY)+',',1)
 # Same512 cumulative cap; exact-root warmups need48 additional reservations.
 s=s.replace('total>352','total>304').replace('entire144-request panel','entire192-request panel')
 (a.out/'qualification.py').write_text(s)
 s=(a.source/'finish.py').read_text().replace('qualification-06','qualification-07').replace('closure-06','closure-07').replace('FINISH_NOT_ADMITTED-06','FINISH_NOT_ADMITTED-07')
 assert s.count("'target_output_reserve':8")==3;s=s.replace("'target_output_reserve':8","'target_output_reserve':32")
 s=s.replace("z['two_primers_s']", "z['matched_warmup_s']").replace('two_primers_s=3*max(root_service)','matched_warmup_s=sum(root_service)')
 s=s.replace('enumerate(s.roots)','enumerate(s.roots[:4])').replace("roots=[x['id']for x in s.roots]","roots=[x['id']for x in s.roots[:4]]")
 anchor="tests=tests if rnd%2==0 else tests[::-1]";assert s.count(anchor)==1
 s=s.replace(anchor,"root_orders=[[0,1,3,2],[1,2,0,3],[2,3,1,0],[3,0,2,1]];tests=[tests[i]for i in root_orders[rnd]];paired=[]\n   for test in tests:\n    warm=copy.deepcopy(test);warm['name']='warm-'+test['name'];paired.extend([warm,test])\n   tests=paired",1)
 assert s.count("'inputs':copy.deepcopy(entries)+tests")==1;s=s.replace("'inputs':copy.deepcopy(entries)+tests","'inputs':tests",1)
 s=s.replace('measured=96,primers=48','measured=96,primers=96').replace('measurements=96,primers=48','measurements=96,primers=96')
 s=s.replace("'heterospec.q32.descriptive-six-arm.v1'","'heterospec.q32.descriptive-six-arm.matched-warmup.v2'")
 anchor="want=primer_endpoints[entry['name']]if entry['name'].startswith('primer-')else expected[entry['input']['id']]";assert s.count(anchor)==1;s=s.replace(anchor,"want=expected[entry['input']['id']]",1)
 s=s.replace("primer_endpoints=primer_endpoints)","primer_endpoints=primer_endpoints,warmup_policy='One complete exact same root/cap/live path immediately before each measured request; all96 warmups charged and retained; every worker fresh; four-round root positions and directed adjacencies balanced',measurement_selector='name starts root-; warm-root- is excluded from timing comparisons')",1)
 s=s.replace("'test_burst_wall_s'","'legacy_test_burst_wall_s'")
 (a.out/'finish.py').write_text(s)
 s=(a.source/'archive.py').read_text().replace('qualification-06','qualification-07').replace('closure-06','closure-07').replace('LAUNCH_06','LAUNCH_07').replace('CLOSED06','CLOSED07').replace('export-08','export-09')
 assert s.count("for x in job['inputs'][2:]:")==1;s=s.replace("for x in job['inputs'][2:]:","for x in job['inputs']:\n            if not x['name'].startswith('root-'):continue",1)
 s=s.replace('old_Q32_diagnostics_included=inherited','old_Q32_diagnostics_included=json.loads(sanitize(json.dumps(inherited)))')
 (a.out/'archive.py').write_text(s)
 rt=w/'runtime-05';shutil.copytree(w/'runtime-04',rt)
 p=rt/'host.py';s=p.read_text();anchor="save(out/'CLOCKS.json',{'markers':markers";i=s.index(anchor);end=s.index("            status='COMPLETE'",i)
 # Retain original development clocks; specialize only the new formal schema.
 block=s[i:end];indent='                '
 replacement="if freeze and read(freeze['plan']['path']).get('schema')=='heterospec.q32.descriptive-six-arm.matched-warmup.v2':\n                    save(out/'CLOCKS.json',dict(markers=markers,launch_to_first_result_s=markers[0]['seconds_after_launch'],launch_to_first_measured_result_s=markers[1]['seconds_after_launch'],launch_to_final_result_s=markers[-1]['seconds_after_launch'],boundary='Fresh native worker through interleaved exact-root warmup/measurement pairs; no unprimed or legacy two-primer burst estimate; full worker exit and caller SHA costs separate'))\n                else:\n"+''.join('    '+line+'\n'for line in block.rstrip().splitlines())
 # First line of block starts after existing indentation, subsequent lines
 # already carry it. Normalize the nested block explicitly.
 lines=block.rstrip().splitlines();replacement=replacement[:replacement.index('                else:\n')+len('                else:\n')]+indent+'    '+lines[0]+'\n'+''.join('    '+line+'\n'for line in lines[1:])
 s=s[:i]+replacement+s[end:];compile(s,str(p),'exec');p.write_text(s)
 shutil.copy2(Path(__file__).parent/'cached_coordinator.py',a.out/'coordinator.py')
 for p in a.out.glob('*.py'):compile(p.read_text(),str(p),'exec')
 save(a.out/'ADAPTER_BINDING.json',dict(original_sources={p.name:sha(p)for p in a.source.glob('*.py')},new_sources={p.name:sha(p)for p in a.out.glob('*.py')},observer_device_type_policy=POLICY,numerical_archives_changed=False,reference_changed=False,measured_requests=96,matched_warmup_requests=96,panel_total=192,cumulative_request_ceiling=512,all_six_required=True,no_formal_measurements_started=True))
if __name__=='__main__':main()
