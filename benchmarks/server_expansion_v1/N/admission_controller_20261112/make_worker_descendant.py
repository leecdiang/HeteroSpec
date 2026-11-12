"""Derive a full worker by exact bounded replacements, never execute it."""
import argparse
import hashlib
import json
from pathlib import Path

PINNED_WORKER_SHA256 = 'd92280465ec60d52a24d6f8742117e2b7541e92ed411e3a70cbf3ea6fd4f54fa'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def derive(pinned_worker):
    raw = Path(pinned_worker).read_bytes()
    if sha(raw) != PINNED_WORKER_SHA256:
        raise ValueError('Complete PR228 worker source identity mismatch; stop')
    text = raw.decode('utf-8')
    substitutions = [
        ('include-controller-client', '#include "../budget_writer/accounting_ipc.hpp"',
         '#include "../budget_writer/accounting_ipc.hpp"\n#include "native_client.hpp"'),
        ('receipt-IO', 'auto root=absolute_dir(job.at("capture_root"));IO io;',
         'auto root=absolute_dir(job.at("capture_root"));auto io=controller_io(account);'),
        ('receipt-directory-fsync', 'checked(::fsync(root.n),"native receipt directory sync");',
         'checked(io.sync(root.n),"native receipt directory sync");'),
        ('owned-writer-IO', 'StreamCapture writer(job.at("capture_root"),capture,ci,{2*1024*1024,8,1024*1024},account);',
         'StreamCapture writer(job.at("capture_root"),capture,ci,{2*1024*1024,8,1024*1024},account,controller_io(account));'),
        ('state-writer-IO', 'StreamCapture writer(job.at("capture_root"),id,transport,{700000000,12,1024*1024},account);',
         'StreamCapture writer(job.at("capture_root"),id,transport,{700000000,12,1024*1024},account,controller_io(account));'),
        ('owner-bound-controller-client',
         'hs::n1chain::NativeAccountingClient account(job.at("accounting_socket"),job.at("run_id"),job.at("accounting_manifest_sha256"),job.at("worker_id"),5000);',
         'hs::n1chain::ControlledNativeClient account(job.at("accounting_socket"),job.at("run_id"),job.at("accounting_manifest_sha256"),job.at("worker_id"),5000,hs::n1chain::ControllerPeer{job.at("controller_owner").at("pid").get<pid_t>(),job.at("controller_owner").at("start_ticks").get<std::string>(),job.at("controller_owner").at("boot_id").get<std::string>()},job.at("owner_lease_sha256"),job.at("capture_root"));'),
    ]
    applied = []
    for name, old, new in substitutions:
        if text.count(old) != 1:
            raise ValueError('Exact full-worker derivation site changed: ' + name)
        text = text.replace(old, new)
        applied.append({'id': name, 'matches': 1,
                        'old_fragment_sha256': sha(old.encode()),
                        'new_fragment_sha256': sha(new.encode())})
    guard = 'ProductionGate gate;gate.before_backend_init("main-entry");'
    if text.count(guard) != 1 or text.index(guard) > text.index('const auto job='):
        raise ValueError('Original permanent deny must precede JSON/IPC/native objects')
    value = text.encode()
    return value, {'schema': 'hs.N1a.controller-worker-derivation.v1',
                   'status': 'FULL_SOURCE_DERIVED_COMPILE_ONLY_NOT_ADMITTED',
                   'original_worker_sha256': sha(raw),
                   'original_worker_bytes': len(raw),
                   'descendant_worker_sha256': sha(value),
                   'descendant_worker_bytes': len(value),
                   'exact_substitutions': applied,
                   'original_numerical_and_lifecycle_code_unchanged': True,
                   'permanent_main_gate_preserved': True,
                   'GPU_execution_authorized': False,
                   'native_executables_started': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pinned-worker', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Fresh output directory required; preserve all epochs')
    value, receipt = derive(args.pinned_worker)
    args.out.mkdir(parents=True)
    (args.out / 'worker.cpp').write_bytes(value)
    (args.out / 'DERIVATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
