"""Architecture handoff and explicitly conditional sensitivity, NOT a GPU simulator.
No default vendor throughput, cache-hit, XMX utilization, area or energy is invented.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
from protocol import require, valid_hash, read_json, write_new
from contracts import physical_work, validate_endpoint


def architecture_record(record: dict) -> dict:
    require(record['evidence_origin']=='NATIVE','real architecture exports cannot use synthetic records')
    require(record['status']=='COMPLETED','cannot normalize incomplete native work as complete')
    endpoint=validate_endpoint(record['endpoint']);work=physical_work(record['work'],endpoint)
    require(valid_hash(record['request_sha256']) and valid_hash(record['runtime_manifest_sha256']),'source bindings')
    req=record['normalized_sent_request'];recipe=req['recipe'];continuation=record['work']
    return {'schema':1,'source_request_sha256':record['request_sha256'],
            'runtime_manifest_sha256':record['runtime_manifest_sha256'],
            'recipe':recipe,'reference_contract':'DEPLOYED_B570_FIXED_GGUF_RUNTIME_GREEDY_EOG_OR_CAP128',
            'numerical_contract':{'arithmetic_DAG':'UNKNOWN','reduction_order':'UNKNOWN','rounding_points':'UNKNOWN',
                                  'scalar_format_alone_is_not_a_complete_contract':True},
            'geometry':{'logical_maximum_query_rows':2 if recipe['draft'] else 1,
                        'observed_prefill_micrograph_widths':record['target_prefill_micrograph_widths'],
                        'observed_prefill_width_hist':record['target_prefill_width_hist'],
                        'observed_continuation_width_hist':continuation['target_continuation_width_hist'],
                        'local_attention_layout':recipe['continuation'],'state_origin':'NATURAL_PREFILL'},
            'measured_native_work':dict(continuation),'derived_work':work,
            'request_time':{'ms':record['request_wall_ms'],'channel':record['mode'],
                            'paid':record['mode']=='counts' and not record['warmup']},
            'unmeasured':{'dispatches':None,'XMX_utilization':None,'DRAM_bytes':None,'cache_hits':None,
                          'completed_kernel_times':None,'area':None,'power':None},
            'raw_artifacts':record['raw_artifacts'],
            'use_boundary':'Fixed native trace only. New numerical decisions require regenerated functional traces, not reuse of this endpoint.'}


def reuse_opportunity(q: int, kv_tile_bytes: int, contexts: int) -> dict:
    require(all(type(x) is int and x>0 for x in (q,kv_tile_bytes,contexts)),'positive integer capacities')
    groups=math.ceil(q/contexts)
    return {'scope':'HYPOTHETICAL_TILE_FETCH_COUNT_NOT_MEASURED_DRAM_TRAFFIC',
            'independent_query_fetch_bytes':q*kv_tile_bytes,
            'context_group_shared_fetch_bytes':groups*kv_tile_bytes,
            'strong_shared_baseline_fetch_bytes':kv_tile_bytes,
            'candidate_vs_strong_shared_baseline_ratio':groups,
            'missing_costs':['SRAM_capacity_ports','bank_conflicts','broadcast_bandwidth','context_state','reuse_across_groups'],
            'warning':'A baseline with the same feasible sharing may already attain the bound. This alone proves no hardware advantage.'}


def amdahl_sensitivity(fraction: float, component_speedup: float, added_fraction: float=0.) -> dict:
    require(all(type(x) in (int,float) and math.isfinite(x) for x in (fraction,component_speedup,added_fraction)),'finite assumptions')
    require(0<=fraction<=1 and component_speedup>0 and added_fraction>=0,'assumption range')
    denominator=1-fraction+fraction/component_speedup+added_fraction
    return {'basis':'ASSUMPTION_SENSITIVITY_NOT_HETEROSPEC_MEASUREMENT','fraction':fraction,
            'component_speedup':component_speedup,'added_serial_fraction':added_fraction,
            'whole_request_speedup_if_assumptions_hold':1/denominator,
            'limitation':'Non-overlapped critical-path decomposition and unchanged useful work assumed; unknown measured fractions must remain unknown.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();write_new(a.out,architecture_record(read_json(a.record)))
if __name__=='__main__':main()
