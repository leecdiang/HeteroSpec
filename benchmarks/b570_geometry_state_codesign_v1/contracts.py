"""CPU contracts for normalized native evidence, not a replacement for raw-native auditing.
The host adapter must bind original REQUEST/RESULT/trace/lifecycle sources and hashes.
"""
from pathlib import Path
from collections import Counter
import math
from protocol import require, digest, file_sha, valid_hash, EOG, VOCAB


def validate_endpoint(e: dict) -> dict:
    require(set(e) == {'ids','eog','length','terminal_id','stop_reason','cap'}, 'endpoint schema')
    ids=e['ids']; flags=e['eog']
    require(e['cap']==128 and isinstance(ids,list) and 0 < len(ids) <= 128, 'cap/IDs')
    require(all(type(i) is int and 0<=i<VOCAB for i in ids), 'invalid output IDs')
    require(all(type(v) is bool for v in flags), 'EOG flag type')
    require(flags==[i in EOG for i in ids] and not any(flags[:-1]), 'EOG/trailing suffix mismatch')
    require(len(ids)==len(flags)==e['length'] and e['terminal_id']==ids[-1], 'complete endpoint mismatch')
    require(e['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==128), 'stop mismatch')
    return e


def physical_work(w: dict, output: dict) -> dict:
    """Micrographs are NOT dispatches, SM occupancy, or DRAM traffic."""
    h=w['target_continuation_width_hist']
    require(isinstance(h,dict), 'missing physical histogram')
    for k,v in h.items():
        require(str(int(k))==k and int(k)>0 and type(v) is int and v>=0, 'bad histogram')
    require(all(int(k)<=2 for k in h), 'continuation width exceeds k1/q2 scope')
    graphs=sum(h.values()); rows=sum(int(k)*v for k,v in h.items())
    require(graphs==w['target_continuation_graphs'] and rows==w['target_continuation_rows'], 'graph/row conservation')
    require(type(w['target_continuation_callers']) is int and w['target_continuation_callers']>=0, 'caller count')
    # A graph can include verification seed, rejected or uncommitted proposal rows.
    # Do not assert these rows all become visible tokens.
    committed=output['length']-1
    result={'mean_occupied_rows_per_graph': rows/graphs if graphs else None,
            'continuation_graphs_per_postfirst_output': graphs/committed if committed else None,
            'continuation_rows_per_postfirst_output': rows/committed if committed else None,
            'multirow_graphs': sum(v for k,v in h.items() if int(k)>1),
            'scope':'native micrograph work only; no kernel/traffic/occupancy claim'}
    for key in ('draft_proposed_rows','draft_catchup_rows','accepted_proposals','rollback_calls'):
        require(type(w[key]) is int and w[key]>=0, 'negative/noninteger work count')
    require(w['accepted_proposals']<=w['draft_proposed_rows'], 'acceptance conservation')
    return result


def verify_artifacts(root: Path, artifacts: list[dict]) -> None:
    require(bool(artifacts), 'missing original raw artifacts')
    roles={a['role'] for a in artifacts}
    require({'request','result','lifecycle','identity'}<=roles, 'incomplete source roles')
    base=root.resolve()
    for a in artifacts:
        require(valid_hash(a['sha256']), 'bad artifact hash')
        p=(base/a['path']).resolve(); require(p.is_relative_to(base), 'raw path escape')
        require(type(a['bytes']) is int and a['bytes']>=0, 'artifact size')
        require(p.is_file() and p.stat().st_size==a['bytes'] and file_sha(p)==a['sha256'], 'raw pin mismatch')


def validate_record(slot: dict, record: dict, frozen_runtime_sha256: str, root: Path | None=None) -> dict:
    require(record['slot']==slot['slot'] and record['request_sha256']==slot['request_sha256'], 'wrong logical request')
    require(digest(record['normalized_sent_request'])==slot['request_sha256'], 'actual normalized wire differs')
    require(record['runtime_manifest_sha256']==frozen_runtime_sha256 and valid_hash(frozen_runtime_sha256), 'runtime changed')
    require(record['status']=='COMPLETED', 'incomplete native record')
    require(type(record['pid']) is int and record['pid']>0, 'missing owned PID')
    require(record['mode']==slot['mode'] and record['warmup'] is slot['warmup'], 'observer/warmup mismatch')
    observation=record['observation']
    require(set(observation)=={'heavy_capture','added_sync','api_dump','gpu_queries'}, 'observation schema')
    require(all(type(v) is bool for v in observation.values()), 'observation flags must be boolean')
    if slot['mode']=='counts': require(not any(observation.values()), 'contaminated paid channel')
    require(record['external_state_imports']==0 and record['teacher_forced_tokens']==0, 'not natural whole request')
    require(record['phase_recipe']==slot['request']['recipe'], 'phase/recipe identity mismatch')
    expected_widths=slot['request']['producer_plan']['expected_micrograph_widths']
    expected_hist={str(k):v for k,v in Counter(expected_widths).items()}
    require(record['target_prefill_width_hist']==expected_hist,'prefill physical histogram mismatch')
    actual_widths=record['target_prefill_micrograph_widths']
    if actual_widths is not None:
        require(actual_widths==expected_widths,'observed ordered prefill partition mismatch')
    if slot['mode']=='diagnostic':
        require(actual_widths is not None,'diagnostic requires actual ordered trace; counts histogram cannot supply it')
    require(record['all_target_weights_offloaded'] is True and record['no_draft_offload_violation'] is True, 'placement mismatch')
    require(record['request_begin_empty_state'] is True and record['lifecycle_closed'] is True, 'reset/lifecycle incomplete')
    output=validate_endpoint(record['endpoint']); work=physical_work(record['work'], output)
    require(record['runtime_role']==slot['request']['recipe']['runtime'], 'wrong old/new runtime role')
    require(record['process_group']==slot['process_group'], 'wrong process group')
    if not slot['request']['recipe']['draft']:
        require(all(int(k)==1 or v==0 for k,v in record['work']['target_continuation_width_hist'].items()),'draft-free continuation must be width1')
        require(all(record['work'][k]==0 for k in ('draft_proposed_rows','draft_catchup_rows','accepted_proposals','rollback_calls')),'draft work in draft-free arm')
    t=record['request_wall_ms']; require(type(t) in (int,float) and math.isfinite(t) and t>0, 'invalid request wall time')
    require(record['timer_contract']=='RESIDENT_RESET_PREFILL_DECODE_RECONCILE_END_SYNC', 'wrong cost window')
    if root is not None: verify_artifacts(root,record['raw_artifacts'])
    require(record['evidence_origin'] in ('NATIVE','SYNTHETIC_TEST_ONLY'),'unknown evidence origin')
    return {'endpoint':output,'wall_ms':t,'work':work}
