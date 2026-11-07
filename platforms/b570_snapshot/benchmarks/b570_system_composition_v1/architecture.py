"""CPU-only architecture handoff metrics; never an occupancy/DRAM/cycle predictor."""
from __future__ import annotations
import argparse
from pathlib import Path
from study import load, write_new, require


def summarize(events: list[dict]) -> dict:
    """Input events must come from source-aligned S2 traces or labelled synthetic tests.

    A micrograph's occupied rows differ from QB's singleton attention-column axis.
    The two logical KV supply scenarios below are NOT measured memory traffic.
    """
    require(bool(events), 'no trace events')
    seen = set(); groups = {}; examples = []
    for e in events:
        key = (e['slot'], e['event_id'])
        require(key not in seen, 'duplicate graph event'); seen.add(key)
        require(e['source_kind'] in ('NATIVE_HEAVY_TRACE', 'SYNTHETIC_TEST'), 'trace provenance')
        require(e['role'] in ('TARGET', 'DRAFT') and e['phase'] in ('PREFILL','VERIFY','ORDINARY','PROPOSE','CATCHUP'), 'role/phase')
        q, cols, batches = (e[k] for k in ('occupied_rows', 'attention_query_columns', 'attention_query_batches'))
        require(all(type(v) is int and v > 0 for v in (q,cols,batches)), 'logical geometry')
        require(cols*batches == q, 'query representation does not account for occupied rows')
        require(e['layout'] in ('MQ','PQ','QB','SERIAL'), 'unknown layout')
        if e['layout'] == 'QB':
            require(cols == 1 and batches == q, 'QB axis mapping')
        if e['layout'] == 'SERIAL':
            require(q == 1, 'global serialized micrograph must contain one row')
        # This is a schema for one full attention layer, not per-PQ-subgraph records.
        n,hk,hq,dk,dv = (e[k] for k in ('key_extent','kv_heads','query_heads','key_dim','value_dim'))
        require(all(type(v) is int and v > 0 for v in (n,hk,hq,dk,dv)) and hq%hk == 0, 'GQA/dimensions')
        require(e['kv_dtype'] == 'F16' and e['q_dtype'] == 'F32', 'unsupported byte model')
        logical = 2*n*hk*(dk+dv)
        group = groups.setdefault((e['role'],e['phase'],e['layout']), {'events':0,'rows':0})
        group['events'] += 1; group['rows'] += q
        examples.append({'slot':e['slot'],'event_id':e['event_id'],'occupied_rows':q,
                         'attention_query_columns':cols,'attention_query_batches':batches,
                         'logical_KV_value_bytes':logical,
                         'supply_once_scenario_bytes':logical,
                         'supply_per_query_scenario_bytes':q*logical,
                         'actual_DRAM_bytes':None,'actual_XMX_occupancy':None,
                         'arithmetic_reduction_order':'UNKNOWN',
                         'source_kind':e['source_kind']})
    return {'groups':[{'role':k[0],'phase':k[1],'layout':k[2],**v,
                       'rows_per_event':v['rows']/v['events']} for k,v in sorted(groups.items())],
            'events':examples,'new_gpu_requests':0,
            'scope':'logical payload/data-supply scenarios; not DRAM bounds, kernel timings, cycle simulation or verified arithmetic DAG'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--events',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();write_new(a.output,summarize(load(a.events)))

if __name__ == '__main__': main()
