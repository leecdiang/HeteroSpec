"""CPU-only delivery recovery: change local extraction destination, not frozen code."""
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
SCRIPTS = REPOSITORY / 'scripts/platform/jsa_third_family_v1'
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / 'control'))
import restore_check
import autorun
from common import LOCAL, PUB, read, save, sha, now


def main():
    autorun.validate(initial=False)
    assert (LOCAL / 'runs/formal/COMPLETE.json').exists()
    before = len(list((LOCAL / 'runs').rglob('REQUEST_STARTED.json')))
    short_parent = Path('D:/hsr')
    short_parent.mkdir(parents=True, exist_ok=True)
    # This module's REPO is used only to form its extraction destination.
    # PUB, head(), frozen analyser and common.REPO still refer to the real checkout.
    restore_check.REPO = short_parent / 'destination-anchor'
    autorun.state('LOCAL_REPRODUCTION', 'CPU-only recovery with a shorter extraction directory; no inference rerun.')
    if not (PUB / 'RESTORE_LOCAL.json').exists():
        restore_check.main('local')
    after = len(list((LOCAL / 'runs').rglob('REQUEST_STARTED.json')))
    assert before == after
    autorun.validate(initial=False)
    receipt = PUB / 'DELIVERY_RECOVERY.json'
    if not receipt.exists():
        save(receipt, {'status': 'LOCAL_RECOVERY_PASS', 'utc': now(),
            'original_failure': '2026-10-11T11:23:20Z Windows MAX_PATH during author archive extraction',
            'original_failure_retained': str(LOCAL / 'autorun/run.log'),
            'changed_variable': 'restore_check.REPO for extraction destination only',
            'short_restore_parent': str(short_parent),
            'recovery_script_sha256': sha(__file__), 'frozen_restore_script_sha256': sha(SCRIPTS / 'restore_check.py'),
            'frozen_code_payload_control_hashes': 'UNCHANGED_PASS',
            'paid_requests_started_before': before, 'paid_requests_started_after': after,
            'extra_model_forwards': 0, 'statistics_or_results_changed': False,
            'restored_local_receipt_sha256': sha(PUB / 'RESTORE_LOCAL.json'),
            'remote_and_PR_delivery': 'continues through unchanged autorun.py --resume-post'})
    print('SHORT_PATH_LOCAL_RECOVERY_PASS; no model forwards', flush=True)


if __name__ == '__main__':
    main()
