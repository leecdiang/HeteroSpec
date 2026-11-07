"""Validate normalized receipt semantics, NOT Windows/raw evidence or readiness.

Only a separately reviewed raw auditor may construct real receipts. This tool
cannot establish that an evidence hash or a checked flag is truthful.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

MATRIX = json.loads(Path(__file__).with_name('ACCEPTANCE.json').read_text(encoding='utf-8'))
CASES = {row['id']: row for row in MATRIX['cases']}
SHA = re.compile(r'[0-9a-f]{64}\Z')
BASE_CHECKS = {'freeze_binding', 'raw_hashes', 'coverage_checked', 'process_ledger', 'cleanup_checked'}
EXTRA_CHECKS = {
    'normal_single': {'work_completed', 'post_audit_separated'},
    'normal_transition': {'eight_pairs', 'sixteen_unique_slots', 'sealed_guard_continuous', 'pending_io_closed'},
    'normal_late_panel': {'eight_thousand_files', 'active_scan_only', 'historical_guard_continuous'},
    'late_closed_slot_write': {'a_sealed_b_active', 'sealed_guard_continuous'},
    'terminal_pending_completion': {'pending_completion_observed', 'pending_io_closed'},
    'notification_loss': {'production_parser_injected'},
    'log_overflow': {'soft_limit_reached', 'ack_nonempty', 'all_ack_frames_retained', 'hard_limit_respected'},
    'watcher_stall': {'independent_watchdog'},
    'journal_write_failure': {'independent_outer_receipt'},
    'wrong_module': {'no_go', 'no_data_write'},
    'truncated_stdout': {'raw_tail_incomplete'},
    'abnormal_exit': {'actual_nonzero_exit'},
    'child_timeout': {'deadline_reached', 'subtree_terminated'},
    'quick_exit': {'actual_creation_exit', 'no_fabricated_coverage'},
}


def confirmation_order(round_id):
    names = list(CASES)
    if round_id == 0:
        return names
    if round_id == 1:
        return names[::-1]
    if round_id == 2:
        return sorted(names, key=lambda s: hashlib.sha256(s.encode()).hexdigest())
    raise ValueError('unknown round')


def valid_ref(ref):
    if not isinstance(ref, dict):
        return False
    path, digest = ref.get('path'), ref.get('sha256')
    if not isinstance(path, str) or not path or '\\' in path or ':' in path:
        return False
    p = PurePosixPath(path)
    return (not p.is_absolute() and '..' not in p.parts and p.parts
            and isinstance(digest, str) and SHA.fullmatch(digest) is not None)


def tick(value):
    return type(value) is int and value >= 0


def load_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON value: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def judge(receipt):
    """Return (status, reason); failures are not equivalent to a passed control."""
    if (not isinstance(receipt, dict) or not isinstance(receipt.get('case_id'), str)
            or receipt.get('case_id') not in CASES):
        return 'EVIDENCE_MISSING', 'unknown/malformed case'
    spec = CASES[receipt['case_id']]
    negative = spec['kind'] == 'negative'
    if receipt.get('fixture_ready') is not True or receipt.get('control_point_reached') is not True:
        return 'NOT_REACHED', 'fixture/control point not reached'
    if negative and receipt.get('trigger_observed') is not True:
        return 'NOT_REACHED', 'intended fault not observed'
    if receipt.get('early_failure') is True:
        return 'WRONG_FAILURE', 'unrelated earlier failure'
    if receipt.get('early_failure') is not False:
        return 'EVIDENCE_MISSING', 'missing early-failure audit'
    detector = receipt.get('detector')
    if not isinstance(detector, dict) or detector.get('code') != spec['detector']:
        return 'WRONG_FAILURE', 'wrong detector/completion reason'
    if not tick(detector.get('at_ns')):
        return 'EVIDENCE_MISSING', 'invalid detector time'
    if negative:
        trigger = receipt.get('trigger')
        if not isinstance(trigger, dict) or trigger.get('code') != spec['trigger']:
            return 'WRONG_FAILURE', 'wrong injected fault'
        fault_id = f"{receipt.get('round')}:{receipt['case_id']}"
        target = receipt.get('planned_target_id')
        if (not isinstance(target, str) or not target
                or any(x.get('fault_id') != fault_id or x.get('target_id') != target for x in (trigger, detector))):
            return 'WRONG_FAILURE', 'fault/object attribution mismatch'
        begin, end = trigger.get('begin_ns'), trigger.get('end_ns')
        if not tick(begin) or not tick(end) or end < begin:
            return 'EVIDENCE_MISSING', 'invalid operation interval'
        if detector['at_ns'] < begin:
            return 'WRONG_FAILURE', 'detector predates injection operation'
        if receipt.get('no_work_after_detection') is not True:
            return 'WRONG_FAILURE', 'work continued after rejection'
    if receipt.get('cleanup_complete') is not True:
        return 'EVIDENCE_MISSING', 'cleanup not established'
    if not tick(receipt.get('closed_ns')) or receipt['closed_ns'] < detector['at_ns']:
        return 'EVIDENCE_MISSING', 'invalid closure boundary'
    if negative and receipt['closed_ns'] < receipt['trigger']['end_ns']:
        return 'EVIDENCE_MISSING', 'injection still open after claimed closure'
    checks = BASE_CHECKS | EXTRA_CHECKS.get(spec['id'], set())
    if negative:
        checks |= {'trigger_side_effect', 'detector_object_match'}
    verified = receipt.get('verified', {})
    if not isinstance(verified, dict) or any(verified.get(k) is not True for k in checks):
        return 'EVIDENCE_MISSING', 'required independent raw check absent'
    keys = {'fixture', 'lifecycle', 'cleanup', 'watch', 'coverage'} | checks
    if negative:
        keys |= {'injection', 'detector'}
    evidence = receipt.get('evidence', {})
    if not isinstance(evidence, dict) or any(not valid_ref(evidence.get(k)) for k in keys):
        return 'EVIDENCE_MISSING', 'missing/invalid raw reference'
    return 'PASS', 'normalized contract satisfied; raw audit still required'


def validate(panel):
    errors, results = [], []
    if not isinstance(panel, dict):
        return {'status': 'RECEIPT_CONTRACT_FAIL', 'errors': ['panel must be object'], 'cases': []}
    freeze = panel.get('freeze_sha256')
    if not isinstance(freeze, str) or not SHA.fullmatch(freeze):
        errors.append('missing/invalid freeze hash')
    rows = panel.get('receipts')
    if not isinstance(rows, list):
        rows = []
        errors.append('receipts must be list')
    expected = [(r, name) for r in range(3) for name in confirmation_order(r)]
    actual = [(row.get('round'), row.get('case_id')) if isinstance(row, dict) else (None, None) for row in rows]
    if actual != expected or any(not isinstance(row, dict) or type(row.get('round')) is not int for row in rows):
        errors.append('complete fixed 3-round order required; no duplicate/retry/replacement')
    for row in rows:
        status, reason = judge(row)
        if not isinstance(row, dict):
            errors.append('malformed receipt')
            continue
        if row.get('freeze_sha256') != freeze:
            errors.append('receipt uses different freeze')
        results.append({'round': row.get('round'), 'case_id': row.get('case_id'), 'status': status, 'reason': reason})
        if status != 'PASS':
            errors.append(f"{row.get('round')}:{row.get('case_id')}: {status}")
    return {'status': 'RECEIPT_CONTRACT_FAIL' if errors else 'RECEIPT_CONTRACT_PASS',
            'scope': 'Normalized semantics only; no raw/Windows/ENGINEERING_READY attestation',
            'errors': errors, 'cases': results}


if __name__ == '__main__':
    report = validate(load_json(Path(sys.argv[1]).read_text(encoding='utf-8-sig')))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report['status'] == 'RECEIPT_CONTRACT_PASS' else 1)
