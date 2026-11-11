"""Exclusive cold initialization: an absent predecessor is the normal state."""
import json


def initialize(task):
    registry=json.loads((task/'BOOTSTRAP_REGISTRY.json').read_text(encoding='utf-8'))
    if registry.get('mode')!='cold-win32-v1' or registry.get('ledger_parts')!=['task/PROCESS_LEDGER.jsonl']:
        raise ValueError('cold bootstrap registry required; no predecessor supported')
    if type(registry.get('task_begin_ns')) is not int or registry['task_begin_ns']<0:
        raise ValueError('invalid cold task boundary')
    journal=(task/'PROCESS_LEDGER.jsonl').open('xb',buffering=0)
    return registry,journal


def ready_receipt(pid,created_filetime,start_ns,source_path,source_sha256,ledger):
    return dict(pid=pid,created_filetime=str(created_filetime),mode='cold-win32-v1',
                start_ns=start_ns,source_path=source_path,source_sha256=source_sha256,ledger=ledger)
