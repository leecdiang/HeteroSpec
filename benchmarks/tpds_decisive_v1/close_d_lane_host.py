"""Close the invalidated frozen panel without aggregate or selective rescue."""
from native_adapter import *

def main():
    failure=json.loads((ROOT/'D-MAIN-INVALIDATION.json').read_bytes());diagnosis=json.loads((ROOT/'D-BOUNDARY-DIAGNOSIS.json').read_bytes());native=json.loads((RUNS/'D-boundary-diagnostic-v1/native/result.json').read_bytes())
    assert not diagnosis['rows'][0]['active_kv_equal'] and diagnosis['rows'][1]['active_kv_equal']
    assert all(not x['equal'] for x in diagnosis['rows'][0]['vectors']) and all(x['equal'] for x in diagnosis['rows'][1]['vectors'])
    f=json.loads((ROOT/'D-FREEZE.json').read_bytes());validated={}
    for path in RUNS.glob('D-main-s*-pair*/SLOT_VALIDATION.json'):
        for row in json.loads(path.read_bytes()):validated[row['slot']]=row
    failed={r['slot'] for r in failure['rows']};outcomes=[]
    for slot in f['schedule']['slots']:
        status='VALIDATED_BEFORE_PANEL_INVALIDATION' if slot['slot'] in validated else 'FAILED_TARGET_STATE' if slot['slot'] in failed else 'NOT_RUN_PANEL_INVALIDATED'
        outcomes.append(dict(slot,status=status))
    assert len(outcomes)==384 and len(validated)==8 and len(failed)==2
    geometry=[]
    for d in native['diagnostic']:
        geometry.append(dict(name=d['name'],before_used_max_p1=d['before']['used_max_p1'],before_attention_extent=d['before']['attention_key_extent'],physical_mapping_contiguous_identity=all(a==b for a,b in d['before']['cells']),calls=[dict(width=c['width'],used_max_p1=c['after']['used_max_p1'],attention_extent=c['after']['attention_key_extent']) for c in d['calls']]))
    put(ROOT/'D-LANE-CLOSURE.json',dict(status='CLOSED_NEGATIVE_FROZEN_PANEL_INVALIDATED',reason='Mandatory unchanged D1 produces identical greedy tokens but different active target KV and full frontier at a natural test head crossing the padded attention extent.',completed_main_requests=10,validated_main_requests=8,state_failed_main_requests=2,unstarted_main_requests=374,performance_aggregate=None,selective_retry=False,numerical_contract_changed=False,causal_probe=diagnosis,actual_probe_geometry=geometry,causal_scope='Independent scalar prefix at the actual failed logical position767 imports into contiguous physical cells0..766. Four-row verification expands attention extent to1024 immediately and fails; diagnostic split1+3 preserves extent768 for first row then1024 and matches all four vectors and final KV. This diagnostic is not a replacement arm, formal rerun, or timing result.',qualification_scope='Four exposed development roots and all16 exact priming checks passed; this finite qualification did not cover every natural test boundary.',prior_AUTO_null_preserved=True,outcomes=outcomes))

if __name__=='__main__':main()
