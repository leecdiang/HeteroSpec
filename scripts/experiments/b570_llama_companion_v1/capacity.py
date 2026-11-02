"""Output-blind, fixed-order placement admission. Never change model or quantization."""
import argparse
from pathlib import Path
from common import need, read, write
import host

PROFILES = [(999, 999), (999, 0), (28, 0), (24, 0)]


def admit(config_path, out):
    c = read(config_path);out = Path(out).resolve();need(not out.exists(), 'fresh capacity root')
    out.mkdir(parents=True);history = []
    for i, (target, draft) in enumerate(PROFILES):
        current = dict(c, target_gpu_layers=target, draft_gpu_layers=draft)
        cfg = out / f'profile-{i}.json';write(cfg, current)
        epoch = out / f'profile-{i}-epoch';host.prepare(cfg, epoch)
        try:
            host.execute(epoch, 'capacity', [], admit=True)
        except Exception as e:
            raw = epoch / 'units/capacity/native/result.json'
            result = read(raw) if raw.exists() else {}
            history.append({'profile': i, 'target_gpu_layers': target, 'draft_gpu_layers': draft,
                            'status': 'FAILED', 'error': repr(e), 'native': result})
            write(out / f'failure-{i}.json', history[-1])
            message = result.get('error', '')
            resource = message in ('device-memory reserve', 'RAM reserve', 'target load', 'draft load', 'context initialization')
            cleanup = read(epoch / 'units/capacity/RECEIPT.json').get('cleanup_verified')
            if not resource or not cleanup:
                raise ValueError('Inspect/setup-repair before trying another placement; unknown failure is not automatically an OOM') from e
            continue
        result = {'status': 'CAPACITY_ADMITTED_ZERO_FORWARD', 'selected_epoch': str(epoch),
                  'target_gpu_layers': target, 'draft_gpu_layers': draft, 'trials': history,
                  'model_requests': 0, 'selection_basis': 'fixed-order allocation/headroom, never outputs or speed',
                  'placement_matches_RTX': target == 999 and draft == 999,
                  'continuously_measured_residency': False}
        write(out / 'SELECTED.json', result);return result
    write(out / 'BLOCKED.json', {'status': 'RESOURCE_BLOCKED', 'trials': history, 'model_requests': 0})
    return {'status': 'RESOURCE_BLOCKED'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('--config', required=True);p.add_argument('--out', required=True)
    a = p.parse_args();print(admit(a.config, a.out))
