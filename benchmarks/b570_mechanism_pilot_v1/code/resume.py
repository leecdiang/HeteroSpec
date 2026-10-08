"""Persistent bounded StageA worker. Later GPU stages require their frozen manifests."""
from pathlib import Path
import json,traceback
import runner
R=Path(__file__).parent
def main():
 assert runner.read(R/'STAGE0.json')['status']=='PASS'
 f=runner.read(R/'A_FREEZE.json')
 for p,h in f['sources'].items():assert runner.sha(R/p)==h,p
 for p,h in f['binaries'].items():assert runner.sha(R/p)==h,p
 runner.acquire()
 try:runner.run_sessions('A',runner.read(R/'A_SCHEDULE.json'))
 except BaseException:
  runner.save(R/'WORKER_FAILURE.json',dict(traceback=traceback.format_exc()));raise
 finally:runner.release()
if __name__=='__main__':main()
