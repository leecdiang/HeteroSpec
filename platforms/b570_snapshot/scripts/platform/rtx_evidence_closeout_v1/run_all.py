"""No AI/API polling: one local controller through fixed experiment and result Draft PR."""
from run_common import *
import msvcrt, traceback
import stages, freeze_stage, history_inputs, deliver

def main():
    LOCAL.mkdir(exist_ok=True);lock=(LOCAL/'SINGLE_WRITER.lock').open('a+b');lock.seek(0);lock.write(b'1');lock.flush();lock.seek(0)
    msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    assert ctypes.windll.kernel32.SetThreadExecutionState(0x80000001),'sleep inhibitor failed'
    try:
        ledger=stages.Ledger()
        if not (LOCAL/'F0A_REMOTE_RECEIPT.json').exists():freeze_stage.prepare_f0a()
        if not (PUB/'ENGINEERING_QUALIFICATION.json').exists():stages.run_engineering(ledger)
        if not (PUB/'BREAK_EVEN_MODEL.json').exists():stages.run_profile(ledger)
        if not (PUB/'FORMAL_PLAN.json').exists():history_inputs.main()
        if not (PUB/'CONFIRMATION_BUDGET_PROJECTION.json').exists():freeze_stage.projection()
        if not (LOCAL/'F0B_REMOTE_RECEIPT.json').exists():freeze_stage.freeze('F0B')
        stages.run_formal(ledger);deliver.complete()
    except BaseException as e:
        status('STOPPING_WITH_EVIDENCE',reason=repr(e))
        stop=dict(utc=now(),reason=repr(e),traceback=traceback.format_exc(),formal_retry_limit=0,model_forwards_not_fabricated=True,paid_events=len(stages.Ledger().events),owned_lifetime_seconds=stages.Ledger().lifetime())
        save(LOCAL/'CONTROLLER_STOP.json',stop)
        try:
            if (PUB/'SOURCE_RUNTIME.zip').exists():deliver.publish(stop)
        except BaseException as delivery_error:
            save(LOCAL/'DELIVERY_FAILED.json',dict(utc=now(),error=repr(delivery_error),traceback=traceback.format_exc()));status('DELIVERY_NEEDS_REPAIR',experiment_stop=repr(e),delivery_error=repr(delivery_error))
        raise
    finally:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000);lock.close()

if __name__=='__main__':main()
