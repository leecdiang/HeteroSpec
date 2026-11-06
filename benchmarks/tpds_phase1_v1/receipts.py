"""Small host adapters for saved receipts, build inputs and branch dispositions.

No subprocess launch, cloud purchase, source patching or auto-stopping peer work.
Reuse each platform's existing supervisor and immutable request ledger.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from design import require, write_new


def signature(events):
    """A comparison aid, NOT an equivalence proof from counts/labels.

    The host normalizes actual trace events into these fields and keeps raw logs.
    Durations and output values intentionally do not enter structural signatures.
    """
    keys=('operator','phase','shape','stride','dispatch','placement','group_rows','extent','output_mask','copies','graph_reuse')
    require(events and all(set(e)==set(keys) for e in events),'Complete normalized native events required')
    raw=json.dumps(events,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def natural_decision(evidence):
    required={'four_arms_qualified','distinct_mechanism','unanswered_natural_question','source_review','trace_review','numerical_failure','engineering_open','budget_available'}
    require(set(evidence)==required,'Explicit branch facts required')
    require(all(type(evidence[k]) is bool for k in required),'Boolean facts required')
    if evidence['numerical_failure']:
        return 'REPAIR_DEVELOPMENT_VERSION_KEEP_ORACLE'
    if evidence['engineering_open']:
        return 'CONTINUE_HOST_INTEGRATION'
    if not evidence['budget_available']:
        return 'CLOSE_BRANCH_RESOURCE_LIMIT'
    if not evidence['four_arms_qualified']:
        return 'CONTINUE_QUALIFICATION_OR_DOCUMENT_STRUCTURAL_COUPLING'
    if not (evidence['source_review'] and evidence['trace_review']):
        return 'COMPLETE_NATIVE_ALIAS_REVIEW'
    if evidence['distinct_mechanism'] and evidence['unanswered_natural_question']:
        return 'FREEZE_NEW_R1_NATURAL_PANEL'
    return 'CLOSE_R1_NATURAL_ONLY_CONTINUE_R2_AND_PORTABILITY'


def normalize_receipt(path, slot, reference_id, qualified, *, window, coordinate=None):
    """Bind a timing to its declared window. Never substitute service for append."""
    raw=Path(path).read_bytes();r=json.loads(raw)
    require(type(qualified) is bool and isinstance(reference_id,str) and reference_id,'Explicit qualification binding required')
    if window == 'complete_resident_service':
        t=r.get('service_seconds');unit='service_seconds'
    elif window == 'append_after_valid_state':
        require(isinstance(coordinate,dict), 'Structural coordinate binding required')
        require(r.get('capacity_observed') == coordinate['capacity'], 'Native capacity not observed or mismatched')
        require(r.get('requested_mask') == coordinate['requested_outputs'], 'Requested mask mismatch')
        expected_rows=coordinate['width'] if coordinate['requested_outputs']=='all' else 1
        require(r.get('observed_copied_rows')==expected_rows, 'Requested output buffer/row coverage not observed')
        require(r.get('phase1_clean') is True and r.get('prefill_outside_append') is True and
                r.get('append_includes_phase_bind_sync_and_requested_copy') is True, 'Not the registered clean append window')
        counters=r.get('append_observer_calls')
        keys={'state_exports','state_imports','reference_replays','heavy_captures'}
        require(isinstance(counters,dict) and set(counters)==keys and all(type(v) is int and v==0 for v in counters.values()),
                'Real clean observer counters required; absence/flags alone is not zero work')
        require(isinstance(r.get('native_admission_receipt'),str) and r['native_admission_receipt'],
                'Bind actual allocation, output reserve, signed budget and clean-observer qualification')
        begin,end=r.get('append_begin_us'),r.get('append_end_us')
        require(type(begin) is int and type(end) is int and end>begin,'Native append begin/end clocks required')
        ms=r.get('append_ms')
        require(type(ms) in (int,float) and math.isfinite(ms) and math.isclose(ms,(end-begin)/1000.,rel_tol=1e-10,abs_tol=1e-9),
                'append_ms disagrees with native append clocks')
        t=ms/1000.;unit='append_ms/1000'
    else:raise ValueError('Unknown cost window')
    require(type(t) in (int,float) and math.isfinite(t) and t>0,'Missing native timing for '+window)
    return dict(slot_id=slot,status='COMPLETE',qualified=qualified,service_s=t,reference_id=reference_id,
                window=window,native_timing_field=unit,native_receipt_sha256=hashlib.sha256(raw).hexdigest())


def _coverage(values, expected):
    require(expected is None or type(expected) is int and expected>=len(values), 'Invalid expected request count')
    known=[]
    for v in values:
        if v is not None:
            require(type(v) in (int,float) and math.isfinite(v) and v>=0,'Invalid recorded cost')
            known.append(v)
    complete=expected is not None and expected>0 and len(values)==expected and len(known)==expected
    return dict(total_s=math.fsum(known) if complete else None,
                observed_sum_s=math.fsum(known) if known else None,
                measured_requests=len(known),present_requests=len(values),expected_requests=expected,
                status='COMPLETE' if complete else 'INCOMPLETE_OR_UNMEASURED')


def saved_costs(path, expected_sessions=6):
    """Read saved PR190-style records. Empty phase maps never imply measured zero.

    Whole-arm totals require a declared root/session matrix (or expected_requests).
    Partial observed sums are named as such. Missing rows and missing nested fields
    propagate null independently; this function does not repair historic records.
    """
    require(type(expected_sessions) is int and expected_sessions>0, 'Positive expected session count required')
    j=json.loads(Path(path).read_text());out={}
    defaults={'target_phases':('PREFILL','ORDINARY','VERIFY'),
              'draft_phases':('PREFILL','DRAFT_SYNC','PROPOSE')}
    for family,f in j['families'].items():
        out[family]={}
        for name,a in f['arms'].items():
            rows=a['rows'];require(isinstance(rows,list),'Missing published request rows')
            expected=a.get('expected_requests')
            if 'roots' in f:
                require(len(set(f['roots']))==len(f['roots']),'Duplicate expected root')
                matrix={(root,session) for root in f['roots'] for session in range(expected_sessions)}
                seen=set()
                for row in rows:
                    key=(row.get('root'),row.get('session'))
                    require(key in matrix and key not in seen,'Duplicate/unexpected request cannot complete coverage')
                    seen.add(key)
                expected=len(matrix)
            coverage={k:_coverage([r.get(k) for r in rows],expected)
                      for k in ('service_s','planning_s','output_copy_s','reset_s','teardown_s','other_service_s')}
            all_complete=all(row.get('status','COMPLETE')=='COMPLETE' for row in rows)
            if not all_complete:
                for value in coverage.values():value.update(total_s=None,status='INCOMPLETE_REQUEST_STATUS')
            phases={}
            for role,default_keys in defaults.items():
                keys=set(default_keys)
                for row in rows:
                    value=row.get(role)
                    require(value is None or isinstance(value,dict),'Phase mapping must be object/null')
                    if value:keys.update(value)
                phases[role]={}
                for key in sorted(keys):
                    values=[];unverified_zero=0;not_executed=0
                    for row in rows:
                        raw=row.get(role);value=None if raw is None else raw.get(key)
                        if value is not None:
                            require(type(value) in (int,float) and math.isfinite(value) and value>=0, 'Invalid nested phase cost')
                        marker=row.get('phase_measurement_status',{}).get(role,{}).get(key)
                        if marker=='NOT_EXECUTED':
                            require(value in (None,0),'NOT_EXECUTED conflicts with nonzero cost')
                            not_executed+=1;value=None
                        elif value==0 and marker!='MEASURED':
                            # Old default zeros are not silently certified timings.
                            unverified_zero+=1;value=None
                        values.append(value)
                    summary=_coverage(values,expected)
                    if not all_complete:summary.update(total_s=None,status='INCOMPLETE_REQUEST_STATUS')
                    summary.update(unverified_zero_requests=unverified_zero,not_executed_requests=not_executed)
                    if expected is not None and len(rows)==expected and not_executed==expected:
                        summary['status']='NOT_APPLICABLE';summary['total_s']=None
                    phases[role][key]=summary
            out[family][name]=dict(requests_present=len(rows),expected_requests=expected,
                totals={k:v['total_s'] for k,v in coverage.items()},coverage=coverage,
                target_phases_s={k:v['total_s'] for k,v in phases['target_phases'].items()},
                draft_phases_s={k:v['total_s'] for k,v in phases['draft_phases'].items()},phase_coverage=phases,
                note='Host envelopes only. Null means unmeasured, partial, or not applicable; see coverage. Observed sums are not full totals.')
    return out


def source_bundle(manifest, output):
    """Export explicit source/build recipe inputs, never weights or private secrets."""
    import zipfile
    root=Path(manifest['root']).resolve();output=Path(output)
    require(not output.exists(),'Do not overwrite a bundle')
    files={}
    for relative,expected in manifest['files'].items():
        rel=Path(relative);p=root/rel
        require(not rel.is_absolute() and '..' not in rel.parts and not p.is_symlink() and p.resolve().is_relative_to(root),'Unsafe bundle path')
        require(p.suffix.lower() not in ('.gguf','.dll','.exe','.bin','.key','.pem') and p.name not in ('.env','credentials'),'Not a source-only input')
        raw=p.read_bytes();require(hashlib.sha256(raw).hexdigest()==expected,'Bundle source hash mismatch')
        files[relative]=raw
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,11,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
    return dict(files=len(files),bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                status='SOURCE_BUNDLE_ONLY_BUILD_NOT_RUN')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('task',choices=['saved-costs','decision','source-bundle'])
    p.add_argument('input',type=Path);p.add_argument('out',type=Path);p.add_argument('--expected-sessions',type=int,default=6);a=p.parse_args()
    j=None if a.task=='saved-costs' else json.loads(a.input.read_text())
    if a.task=='source-bundle':print(json.dumps(source_bundle(j,a.out)))
    else: write_new(a.out,saved_costs(a.input,a.expected_sessions) if a.task=='saved-costs' else {'R1_natural':natural_decision(j)})
if __name__=='__main__': main()
