"""Queue full packed-path native gates after a retained long-loop timeout.

This is a narrowed eligibility continuation, never an automatic replacement
performance panel. The unavailable loop controls keep the six-arm gate closed.
Compiled numerical/frontend ELFs, scalar R, comparisons and512/2M caps do not change.
"""
from pathlib import Path
import argparse,shutil
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir()
 for name in('build.py','resource_guard.py'):shutil.copy2(a.source/name,a.out/name)
 s=(a.source/'qualification.py').read_text();s=s.replace("self.w/'qualification-03'","self.w/'qualification-04'")
 line=next(x for x in s.splitlines()if x.startswith('ARMS='));s=s.replace(line,line.replace('ARMS=','ORIGINAL_ARMS=',1)+"\nARMS={k:v for k,v in ORIGINAL_ARMS.items()if v[0]=='packed'}\n",1)
 anchor='dict(passed=True,geometry=True,natural=True,controlled_transactions=True,remaining=';assert s.count(anchor)==1;s=s.replace(anchor,'dict(passed=True,all_six_arms_qualified=False,supported_arms=list(ARMS),unsupported_loop_arms=[k for k,v in ORIGINAL_ARMS.items()if v[0]=="loop4"],geometry=True,natural=True,controlled_transactions=True,remaining=',1);(a.out/'qualification.py').write_text(s)
 s=(a.source/'finish.py').read_text().replace('qualification-03','qualification-04').replace('closure-03','closure-04').replace('FINISH_NOT_ADMITTED-03','FINISH_NOT_ADMITTED-04')
 anchor=';panel(s,q,entries,eps)';assert s.count(anchor)==1;s=s.replace(anchor,';save(w/"PANEL_NOT_ADMITTED_UNSUPPORTED_LOOPS.json",dict(reason="Three loop-control paths did not finish long-prefix eligibility within the fixed900s worker window. Packed-path eligibility alone never admits the original six-arm performance panel.",supported_arms=list(q.ARMS),full_six_arm_qualification=False,descriptive_performance_measurements=0))',1)
 anchor='dict(passed=True,core_gates_sha256=';assert s.count(anchor)==1;s=s.replace(anchor,'dict(passed=True,all_six_arms_qualified=False,supported_arms=list(q.ARMS),scope="Finite full-model supported-path qualification; required loop controls remain unavailable, no performance panel",core_gates_sha256=',1);(a.out/'finish.py').write_text(s)
 s=(a.source/'archive.py').read_text().replace('PIPELINE_LAUNCH_03','PIPELINE_LAUNCH_04').replace('PIPELINE_COORDINATOR_CLOSED03','PIPELINE_COORDINATOR_CLOSED04').replace('qualification-03','qualification-04').replace('closure-03','closure-04').replace('finish-03','finish-04').replace("w/'export-03'","w/'export-04'")
 s=s.replace("if not f.is_file()or f.is_relative_to(out)or'__pycache__'in f.parts:continue","if not f.is_file()or any(x.startswith('export-')for x in f.relative_to(directory).parts)or'__pycache__'in f.parts:continue",1);(a.out/'archive.py').write_text(s)
 shutil.copy2(Path(__file__).parent/'supported_coordinator.py',a.out/'coordinator.py')
 save(a.out/'ADAPTER_BINDING.json',dict(original_source=str(a.source),original_files={n:sha(a.source/n)for n in('qualification.py','finish.py','archive.py','build.py','resource_guard.py')},new_files={p.name:sha(p)for p in a.out.iterdir()if p.is_file()},changes=['Only packed arms enter new gates after loop timeout; same compiled source04 numerical/frontends and R','Output directories04, all original numerical/state/physical/boundary checks retained','No six-arm performance panel; explicit unsupported-control gap','Archive waits terminal state, omits prior derived export directories to avoid recursive bundles'],full_six_arm_qualified=False))
if __name__=='__main__':main()
