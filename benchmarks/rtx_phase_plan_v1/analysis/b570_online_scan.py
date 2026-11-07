#!/usr/bin/env python3
"""Read-only cost scan. No imports of platform runners; no GPU/model/network work.
With --runs, point ONLY to the restored secondary-smol/campaign02/runs directory.
Absent per-operation timers remain null, never inferred from a total residual.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path

ARMS=('M','H1','C1U1','C4U1','C4U2','C4U4')
PROMPTS=(154,833,555,331,346,446,748,188,508,276,484,531)
# Transcribed from PR187 RESULTS.md; six repetitions, 72 measures/arm.
TOTALS={'M':86.478166,'H1':832.191137,'C1U1':832.632691,
        'C4U1':831.493408,'C4U2':839.122671,'C4U4':808.976532}
PREFIX='https://github.com/leecdiang/HeteroSpec/blob/'
SOURCES={
 'result':PREFIX+'b01040d3b303abfc31c5ce2dbcb100cac7490b27/benchmarks/b570_decisive_v1/RESULTS.md',
 'campaign':PREFIX+'b01040d3b303abfc31c5ce2dbcb100cac7490b27/benchmarks/b570_decisive_v1/smol_campaign.py',
 'state_profile':PREFIX+'b01040d3b303abfc31c5ce2dbcb100cac7490b27/benchmarks/b570_decisive_v1/smol_state.py',
 'bulk_observer':PREFIX+'b01040d3b303abfc31c5ce2dbcb100cac7490b27/benchmarks/b570_decisive_v1/smol_bulk.hpp',
 'inherited_move':PREFIX+'66594b349955e66146702325559c26019ea16485/benchmarks/b570_closeout_overnight_v1/code/src/observer.h',
 'inherited_timer':PREFIX+'66594b349955e66146702325559c26019ea16485/benchmarks/b570_closeout_overnight_v1/code/src/native.cpp'}

def scan_published():
    # Work-volume model: three full exports plus one full import at transition.
    # Uses active K/V only, excludes framing/logits/sampler and transport retries.
    per_token=24*(2048+2048)*2
    one_pass=sum(PROMPTS)*6*per_token
    c,m=TOTALS['C4U4'],TOTALS['M']
    return {
      'status':'PUBLISHED_TOTALS_AND_SOURCE_WORK_SCAN',
      'new_model_requests':0,'raw_slot_metrics_scanned':False,'sources':SOURCES,
      'inputs_are_transcribed_report_values':True,
      'mean_request_seconds':{a:t/72 for a,t in TOTALS.items()},
      'fastest_speculative_over_M':c/m,
      'seconds_per_request_to_remove_for_parity':(c-m)/72,
      'fraction_of_spec_service_to_remove_for_parity':1-m/c,
      'width4_reduction_vs_H1':1-c/TOTALS['H1'],
      'source_transition':{'exports':3,'imports':1,'host_full_equality_comparisons':2,
        'new_continuation_context':1,'sampler_clone':1,
        'executes_with_trace_off':True,'offline_bulk_observer_does_not_optimize_move':True},
      'active_payload_lower_bound':{'basis':'source-derived work volume, NOT measured traffic or time',
        'layers':24,'k_elements_per_layer':2048,'v_elements_per_layer':2048,
        'bytes_per_element':2,'bytes_per_active_token':per_token,
        'mean_prompt_tokens':sum(PROMPTS)/len(PROMPTS),
        'mean_single_active_KV_MiB':(sum(PROMPTS)/len(PROMPTS))*per_token/2**20,
        'mean_three_exports_plus_one_import_MiB':4*(sum(PROMPTS)/len(PROMPTS))*per_token/2**20,
        'single_pass_bytes_72_measures':one_pass,
        'three_exports_plus_one_import_GiB_72_measures':4*one_pass/2**30,
        'all_five_spec_arms_measured_GiB':5*4*one_pass/2**30},
      'unmeasured_seconds':{k:None for k in ['export','import','context_create_destroy','host_comparison','sampler_clone']},
      'interpretation':'The transition has removable-looking work, but its duration and the benefit of removal require controlled native evidence. Keeping R does not require freezing this candidate lifecycle.'}

def number(record,key):
    value=record.get(key)
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError('missing/invalid metric: '+key)
    return float(value)

def partitions(record):
    service=number(record,'service_ms')
    whole=number(record,'whole_request_ms')
    prefill=number(record,'prefill_ms')
    generation=number(record,'generation_ms')
    residual=whole-prefill-generation
    close=service-whole
    if residual < -0.01 or close < -0.01:
        raise ValueError('interval nesting differs from the pinned source')
    return {'service_ms':service,'prefill_ms':prefill,
      'generation_including_transfer_ms':generation,
      'host_reset_setup_cleanup_residual_ms':max(0.,residual),
      'capture_finish_ms':max(0.,close)}

def scan_raw(runs:Path):
    if not runs.is_dir():raise ValueError('runs directory missing')
    rows=[];seen=set();hashes={}
    pattern=re.compile(r'^main-s([0-5])-r([0-9]+)-(M|H1|C1U1|C4U1|C4U2|C4U4)$')
    for folder in sorted(runs.iterdir()):
        match=pattern.fullmatch(folder.name)
        if not match or not folder.is_dir():continue
        session,root,arm=int(match[1]),int(match[2]),match[3]
        if root not in range(12):raise ValueError('unexpected root')
        for index,kind in ((0,'warmup'),(1,'measure')):
            path=folder/f'{index}.json.metrics.json'
            if not path.is_file():continue
            raw=path.read_bytes();metric=json.loads(raw);key=(session,root,arm,kind)
            if key in seen:raise ValueError('duplicate slot')
            seen.add(key);row=dict(session=session,root=root,arm=arm,kind=kind,**partitions(metric))
            capture=folder/f'{index}.json'
            if capture.is_file() and capture.stat().st_size<4*1024*1024:
                cap=json.loads(capture.read_bytes());transfer=cap.get('transfer')
                row['transfer_state_bytes']=transfer.get('state_bytes') if isinstance(transfer,dict) else None
            rows.append(row);hashes[str(path.relative_to(runs))]=hashlib.sha256(raw).hexdigest()
    complete=len(rows)==864
    sums={}
    for arm in ARMS:
        measured=[r for r in rows if r['arm']==arm and r['kind']=='measure']
        sums[arm]={'count':len(measured),**{k:sum(r[k] for r in measured)/1000 for k in
            ['service_ms','prefill_ms','generation_including_transfer_ms','host_reset_setup_cleanup_residual_ms','capture_finish_ms']}}
        if complete and abs(sums[arm]['service_ms']-TOTALS[arm])>1e-5:
            raise ValueError('complete measured total disagrees with published panel: '+arm)
    return {'status':'COMPLETE_SAVED_METRIC_SCAN' if complete else 'INCOMPLETE_SAVED_METRIC_SCAN',
       'complete':complete,'slots':len(rows),'rows':rows,'source_metric_sha256':hashes,
       'sums_seconds':sums,'generation_is_not_pure_decode':True,
       'transfer_ms':None,'no_new_model_requests':True}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result=scan_published()
    if args.runs:result['saved_metrics']=scan_raw(args.runs)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8')as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
if __name__=='__main__':main()
