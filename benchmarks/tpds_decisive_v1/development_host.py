"""Prespecified single-root initial eligibility checks; failures retained."""
import os,traceback
from native_adapter import execute,draft_job,ROOT,put
import qualify_host,dedup_host
def main():
    os.environ['TPDS_EVIDENCE_CAS']='D:/rtx184-cas'
    dedup_host.main()
    for arm in ('D2','D4','M'):
        try:
            execute(draft_job('development-v3-'+arm,arm));qualify_host.main(arm)
        except Exception as e:
            put(ROOT/('DEVELOPMENT_FAILURE-'+arm+'.json'),dict(error=repr(e),traceback=traceback.format_exc(),no_main_claim=True));print(arm,'failure retained',flush=True)
        dedup_host.main()
if __name__=='__main__':main()
