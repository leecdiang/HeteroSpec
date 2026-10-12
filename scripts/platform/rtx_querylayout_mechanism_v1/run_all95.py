"""Single controller: freeze -> diagnostic -> qualification -> freeze -> formal -> CPU delivery."""
from common95 import *
from runner95 import Ledger95,native
from freeze95 import freeze
from stages95 import run_p1,engineering,formal
from delivery95 import closeout
import ctypes,traceback

def main():
    lock=LOCAL/'controller.lock';handle=lock.open('xb');handle.write(str(os.getpid()).encode());handle.flush()
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000003)
    try:
        ledger=Ledger95();assert not ledger.events,'Only a fresh controller may initiate GPU stages; delivery95 handles CPU-only continuation'
        h=native.host();save(PUB/'LIVE_PREFLIGHT.json',dict(utc=now(),sample=h,no_hidden_load=True,ancestry_receipt_sha256=sha(PUB/'ANCESTRY_RESTORE.json')))
        expected=read(PUB/'HOST_ADMISSION.json')['sample']
        assert h['AC']==1 and h['total_MiB']-h['used_MiB']>=512 and h['util']<=5
        assert all(h[k]==expected[k] for k in ['gpu','driver','total_MiB','power_scheme_guid'])
        for name,v in read(PUB/'MODEL_CONTRACT.json')['families'].items():
            for role,model in v['models'].items():assert sha(model['path'])==model['sha256']
        for name,hsh in read(PUB/'NATIVE_BUILD.json')['numerical_DLL_sha256'].items():assert sha(LOCAL/'native/build/bin'/name)==hsh
        freeze('F0A')
        try:run_p1(ledger)
        except (AssertionError,RuntimeError,OSError,TimeoutError) as e:
            save(PUB/'P1_STAGE_FAILURE.json',dict(utc=now(),error=repr(e),traceback=traceback.format_exc(),started_not_retried=True,scope='diagnostic stage blocked; independent full-output comparator qualification can proceed'))
        engineering(ledger)
        freeze('F0B');formal(ledger);closeout()
    except BaseException as e:
        p=LOCAL/('CONTROLLER_FAILURE-'+str(time.time_ns())+'.json');save(p,dict(utc=now(),error=repr(e),traceback=traceback.format_exc(),no_automatic_started_slot_retry=True))
        status('CONTROLLER_STOPPED',error=repr(e),failure=str(p));raise
    finally:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000);handle.close()
if __name__=='__main__':main()
