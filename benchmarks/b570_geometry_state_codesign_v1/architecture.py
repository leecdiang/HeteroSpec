"""Read-only architecture handoff, NOT a GPU simulator or hardware admission gate.
Schema 2 requires the source plan, separately supplied runtime pin and raw files.
Hash-checked normalized fields still require independent raw semantic auditing.
"""
from __future__ import annotations
import argparse
import copy
import math
from pathlib import Path
from protocol import require, valid_hash, read_json, write_new, digest, validate_plan
from contracts import validate_record

WORK_COUNTS = (
    'target_continuation_graphs', 'target_continuation_rows',
    'target_continuation_callers', 'draft_proposed_rows', 'draft_catchup_rows',
    'accepted_proposals', 'rollback_calls',
)


def architecture_record(record: dict, *, plan: dict | None = None,
                        frozen_runtime_sha256: str | None = None,
                        raw_root: Path | None = None,
                        reference_record: dict | None = None) -> dict:
    """Export one completed observation; mismatches are retained, not speedups.

    A reference, when supplied, must be the original R from the same task/session
    in this plan. A single matching pair does not qualify the full panel, establish
    observer invariance, authenticate an execution F0, or identify an arithmetic DAG.
    """
    require(record.get('evidence_origin') == 'NATIVE', 'synthetic evidence is not native')
    require(plan is not None and valid_hash(frozen_runtime_sha256) and raw_root is not None,
            'source plan, independent runtime pin and raw root are required')
    validate_plan(plan)
    slots = {s['slot']: s for s in plan['slots']}
    root = Path(raw_root)

    def checked(rec: dict) -> tuple[dict, dict]:
        require(rec.get('evidence_origin') == 'NATIVE', 'synthetic evidence is not native')
        require(rec.get('slot') in slots, 'record is outside the supplied plan')
        slot = slots[rec['slot']]
        value = validate_record(slot, rec, frozen_runtime_sha256, root)
        require(type(slot['warmup']) is bool, 'warmup must be boolean')
        require(isinstance(rec.get('lifecycle_id'), str) and bool(rec['lifecycle_id']),
                'missing lifecycle identity')
        for name in WORK_COUNTS:
            require(type(rec['work'][name]) is int and rec['work'][name] >= 0,
                    'noninteger work count: ' + name)
        return slot, value

    slot, value = checked(record)
    req = record['normalized_sent_request']
    recipe = req['recipe']
    case = next(c for c in plan['panel'] if c['id'] == slot['task'])
    endpoint_status = 'NOT_CHECKED'
    reference = None
    if reference_record is not None:
        ref_slot, ref_value = checked(reference_record)
        require(ref_slot['arm'] == 'R' and ref_slot['mode'] == 'counts'
                and ref_slot['warmup'] is False, 'reference must be original non-warmup R')
        require((ref_slot['task'], ref_slot['session']) == (slot['task'], slot['session']),
                'reference task/session mismatch')
        require(reference_record['normalized_sent_request']['prompt_ids'] == req['prompt_ids'],
                'reference prompt mismatch')
        endpoint_status = 'MATCH' if value['endpoint'] == ref_value['endpoint'] else 'MISMATCH'
        reference = {'slot': ref_slot['slot'], 'record_sha256': digest(reference_record),
                     'endpoint_sha256': digest(ref_value['endpoint']),
                     'raw_artifacts': reference_record['raw_artifacts']}

    clean_counts = slot['mode'] == 'counts' and slot['warmup'] is False
    time_class = ('WARMUP_EXCLUDED' if slot['warmup'] else
                  'DIAGNOSTIC_ONLY' if slot['mode'] == 'diagnostic' else
                  'PILOT_DESCRIPTIVE_ONLY' if plan['phase'] == 'pilot' else
                  'CONFIRM_COUNTS_PENDING_PANEL_AND_RAW_AUDIT')
    result = {
        'schema': 2,
        'evidence_level': 'NORMALIZED_NATIVE_HASH_CHECKED_PENDING_RAW_SEMANTIC_AUDIT',
        'source': {'plan_sha256': digest(plan), 'record_sha256': digest(record),
                   'request_sha256': record['request_sha256'],
                   'runtime_manifest_sha256': frozen_runtime_sha256,
                   'slot': slot['slot'], 'task': slot['task'], 'arm': slot['arm'],
                   'phase': plan['phase'], 'session': slot['session'],
                   'pid': record['pid'], 'lifecycle_id': record['lifecycle_id'],
                   'process_group': record['process_group'],
                   'raw_bytes_checked': True, 'independent_raw_semantics_verified': False,
                   'execution_f0_authenticated_by_this_exporter': False},
        'input_bindings': {k: case[k] for k in
                          ('tokenizer_sha256', 'template_sha256', 'source_sha256')},
        'recipe': recipe,
        'reference_contract': 'DEPLOYED_B570_FIXED_GGUF_RUNTIME_GREEDY_EOG_OR_CAP128',
        'qualification': {'paired_original_reference_endpoint': endpoint_status,
                          'paired_reference': reference,
                          'panel_qualification': 'NOT_ESTABLISHED_BY_SINGLE_RECORD',
                          'observer_invariance': 'NOT_ESTABLISHED_BY_SINGLE_RECORD',
                          'reference_KV_identity': 'UNKNOWN'},
        'numerical_contract': {'arithmetic_DAG': 'UNKNOWN', 'reduction_order': 'UNKNOWN',
                               'rounding_points': 'UNKNOWN',
                               'scalar_format_alone_is_not_a_complete_contract': True},
        'geometry': {'declared_maximum_query_rows': recipe['k'] + 1 if recipe['draft'] else 1,
                     'actual_caller_query_rows': None,
                     'observed_prefill_micrograph_widths': record['target_prefill_micrograph_widths'],
                     'observed_prefill_width_hist': record['target_prefill_width_hist'],
                     'observed_continuation_width_hist': record['work']['target_continuation_width_hist'],
                     'verify_transaction_width_witness': None,
                     'ordered_transaction_trace': None,
                     'attention_query_columns_and_batch': None,
                     'physical_compute_resource_width': None,
                     'local_attention_layout': recipe['continuation'],
                     'prompt_tokens': len(req['prompt_ids']), 'prompt_sha256': req['prompt_sha256'],
                     'operator_key_extent': None, 'GQA_heads_strides_masks': None,
                     'declared_KV_dtype': req['kv_dtype'], 'operator_operand_dtype': None,
                     'state_origin': 'NATURAL_PREFILL', 'state_payload_sha256': None},
        'measured_native_work': {k: record['work'][k] for k in WORK_COUNTS},
        'derived_work': value['work'],
        'endpoint': {'length': value['endpoint']['length'], 'sha256': digest(value['endpoint'])},
        'request_time': {'ms': value['wall_ms'], 'channel': record['mode'],
                         'warmup': slot['warmup'], 'classification': time_class,
                         'timer_contract': record['timer_contract'],
                         'observation': record['observation'],
                         'clean_counts_nonwarmup': clean_counts,
                         'panel_qualified_cost': None, 'hardware_speedup': None,
                         'continuous_physical_residency': 'UNKNOWN'},
        'unmeasured': {k: None for k in ('dispatches', 'XMX_utilization', 'DRAM_bytes',
                                        'cache_hits', 'completed_kernel_times', 'area', 'power')},
        'raw_artifacts': record['raw_artifacts'],
        'hardware_stage1': {'admission': 'NOT_DECIDED_BY_EXPORTER',
                             'residual_bottleneck': 'UNKNOWN',
                             'strong_software_baseline_exhausted': 'NOT_ESTABLISHED'},
        'use_boundary': ('Request summary, not an ordered simulator trace. Matching endpoints do not '
                         'prove equal intermediate states or verification schedules. Changed numerical '
                         'decisions require new functional traces; no full-panel or hardware speedup here.'),
    }
    # Do not let later mutation of a caller-owned record alter an exported observation.
    return copy.deepcopy(result)


def reuse_opportunity(q: int, kv_tile_bytes: int, contexts: int) -> dict:
    require(all(type(x) is int and x > 0 for x in (q, kv_tile_bytes, contexts)),
            'positive integer capacities')
    groups = (q + contexts - 1) // contexts
    return {'scope': 'HYPOTHETICAL_TILE_FETCH_COUNT_NOT_MEASURED_DRAM_TRAFFIC',
            'independent_query_fetch_bytes': q * kv_tile_bytes,
            'context_group_shared_fetch_bytes': groups * kv_tile_bytes,
            'strong_shared_baseline_fetch_bytes': kv_tile_bytes,
            'candidate_vs_strong_shared_baseline_ratio': groups,
            'assumptions': ['same valid tile and KV ownership for all queries',
                            'tile fetched once per candidate group; no retention across groups',
                            'strong baseline can retain/share the tile across all queries'],
            'missing_costs': ['SRAM_capacity_ports', 'bank_conflicts', 'broadcast_bandwidth',
                              'context_state', 'reuse_across_groups'],
            'warning': 'Conditional supply scenarios, not a universal traffic bound or speedup. '
                       'With equal feasible sharing the strong baseline may match the candidate.'}


def amdahl_sensitivity(fraction: float, component_speedup: float, added_fraction: float = 0.) -> dict:
    require(all(type(x) in (int, float) and math.isfinite(x)
                for x in (fraction, component_speedup, added_fraction)), 'finite assumptions')
    require(0 <= fraction <= 1 and component_speedup > 0 and added_fraction >= 0, 'assumption range')
    denominator = 1 - fraction + fraction / component_speedup + added_fraction
    require(math.isfinite(denominator) and denominator > 0, 'unrepresentable cost denominator')
    speedup = 1 / denominator
    require(math.isfinite(speedup), 'unrepresentable sensitivity result')
    return {'basis': 'ASSUMPTION_SENSITIVITY_NOT_HETEROSPEC_MEASUREMENT', 'fraction': fraction,
            'component_speedup': component_speedup, 'added_serial_fraction': added_fraction,
            'whole_request_speedup_if_assumptions_hold': speedup,
            'limitation': 'Non-overlapped critical-path decomposition and unchanged useful work assumed; '
                          'unknown measured fractions must remain unknown.'}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('record', 'plan', 'raw-root', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--runtime-hash', required=True)
    p.add_argument('--reference-record', type=Path)
    a = p.parse_args()
    result = architecture_record(read_json(a.record), plan=read_json(a.plan),
                                 frozen_runtime_sha256=a.runtime_hash, raw_root=a.raw_root,
                                 reference_record=read_json(a.reference_record) if a.reference_record else None)
    write_new(a.out, result)


if __name__ == '__main__':
    main()
