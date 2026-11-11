"""Version-two R2 coverage: include every legal distinct target-only strategy.

Evidence IDs are supplied by the native agent, never created by this helper.
A speed ranking on the R2 confirmation set cannot select or delete a control.
"""
from __future__ import annotations
import hashlib
import json
from design import FACTOR, require

TARGET_ARMS = {
    'W_L4': 'W_M_TARGET_ONLY',
    'W_P': 'W_P_M_TARGET_ONLY',
    'L_L4': 'L_L4_M_TARGET_ONLY',
    'L_P': 'L_M_TARGET_ONLY',
}


def evidence(row, names):
    for name in names:
        require(isinstance(row.get(name), str) and row[name].strip(),
                'Missing native evidence reference: ' + name)


def baseline_set(review):
    require(isinstance(review, dict) and review.get('schema') == 'phase1.r2-baselines.v2',
            'Explicit pre-R2 baseline review v2 is required')
    require(review.get('selection_scope') == 'development_before_R2',
            'R2 outcomes cannot select controls')
    evidence(review, ('reference_id', 'development_binding', 'reviewer'))
    rows = review.get('strategies', {})
    require(set(rows) == set(FACTOR), 'Account for all four factorial strategies')
    require(all(rows[x].get('status') == 'INCLUDE' for x in ('W_L4', 'L_P')),
            'Keep the original whole-loop4 and local-packed target-only controls')
    included = [x for x in FACTOR if rows[x].get('status') == 'INCLUDE']
    for name, row in rows.items():
        status = row.get('status')
        if status == 'INCLUDE':
            evidence(row, ('target_only_qualification', 'source_binding', 'trace_binding'))
        elif status == 'EQUIVALENT':
            representative = row.get('representative')
            require(representative in included and representative != name,
                    'Equivalence must point directly to an included control')
            evidence(row, ('same_reference_evidence', 'source_equivalence', 'native_trace_equivalence',
                           'frontend_and_cost_window_equivalence'))
        elif status == 'INAPPLICABLE':
            require(row.get('reason') in ('NUMERICAL_MISMATCH', 'UNSUPPORTED_NATIVE_PATH', 'CAPACITY_NOT_ADMITTED'),
                    'Slow timing, pending engineering, or missing effort is not an exclusion')
            evidence(row, ('failure_evidence', 'bounded_diagnosis', 'scope_consequence'))
        else:
            raise ValueError('Unresolved strategy '+name+': finish development before freezing R2')
    strongest = review.get('observed_development_best')
    require(strongest is None or strongest in FACTOR, 'Invalid development-best label')
    if strongest is not None:
        require(rows[strongest]['status'] in ('INCLUDE', 'EQUIVALENT'),
                'The observed strongest legal development strategy must be represented')
    raw = json.dumps(review, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return dict(schema='phase1.r2-baseline-set.v2',
                arms=[TARGET_ARMS[x] for x in included]+['L_M_MATCHED', 'L_D4'],
                target_only_arms=[TARGET_ARMS[x] for x in included],
                strategy_to_arm={x: TARGET_ARMS[x] for x in included},
                review_sha256=hashlib.sha256(raw).hexdigest(), review=review,
                note='All qualifying distinct controls; no confirmation-winner selection')


def adoption_action(previous):
    """Read a host observation; absence of a GitHub receipt is not NOT_STARTED."""
    require(isinstance(previous, dict), 'Host version observation required')
    status = previous.get('status')
    require(status in ('UNKNOWN', 'DEVELOPMENT_ONLY', 'FROZEN', 'STARTED', 'COMPLETE'), 'Unknown host state')
    if status == 'UNKNOWN':
        return 'CHECK_HOST_STATE_CONTINUE_ENGINEERING_NO_FORMAL_FREEZE'
    evidence(previous, ('code_commit', 'host_observation'))
    if status == 'DEVELOPMENT_ONLY':
        return 'ADOPT_V2_REQUALIFY_THEN_FREEZE'
    evidence(previous, ('panel_version', 'freeze_receipt'))
    return 'KEEP_PINNED_PANEL_SEPARATE_V2_VERSION_NO_MID_PANEL_CHANGE'
