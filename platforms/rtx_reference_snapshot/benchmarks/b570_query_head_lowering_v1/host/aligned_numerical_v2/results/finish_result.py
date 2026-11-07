"""CPU-only closeout of the stopped frozen panel. Never starts a child/device.

This delivery tool does not change the frozen executor, analysis or F0. It keeps
observer-invalid output descriptive and never upgrades that slot's admission.
"""
import collections
import datetime
import hashlib
import itertools
import json
import math
import os
import pathlib
import struct
import sys
import time
import zipfile

HERE=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from panel_common import ROOT,RUN,MODES,STAGES,LIMITS,load,save,sha,need,modules
from controller import events,output_usage
from native_audit import audit_raw
from analyzer import analyze_files,compare
from reference import solve

DEST=HERE/'results'
APPROVED='332c5d5d309a97f5073b7fd3d8228a5ef46ade7b87315632165251fe89b7786c'

def main():
    started=time.monotonic();before=modules()
    need(sha(HERE/'F0.json')==APPROVED,'unchanged approved F0')
    f0=load(HERE/'F0.json');plan=load(HERE/'PLAN.json');inputs=load(HERE/'INPUTS.json')
    close=load(RUN/'CLOSEOUT.json');rec=load(RUN/'INDEPENDENT_RECONSTRUCTION.json')
    need(close['status']=='STOPPED_INCOMPLETE' and close['error']=='final observer gap','actual frozen stop')
    need(rec['attempts']==37 and rec['observed_graph_calls']==36 and len(rec['failed_or_invalid'])==1 and len(rec['unstarted'])==124,'actual denominator')
    checked=[]
    def check(path,expected,kind):
        actual=sha(path);need(actual==expected,'frozen byte drift '+str(path));checked.append(dict(path=str(path),sha256=actual,kind=kind))
    for p,h in f0['sources'].items():check(ROOT/p,h,'source')
    for p,h in f0['artifacts'].items():check(HERE/p,h,'frozen artifact')
    for item in [f0['executable'],f0['python']]+f0['dependencies']+f0['driver_files']:check(item['path'],item['sha256'],'runtime/driver')
    for item in f0['history_files']:check(ROOT/item['path'],item['sha256'],'immutable history')
    build=load(HERE/'BUILD_INPUTS.json')
    for item in build['files']+build['frozen_backend_sources']:check(item['path'],item['sha256'],'build/frozen source')
    for item in inputs:check(item['path'],item['sha256'],'original input')
    save(DEST/'FROZEN_BINDING_RECHECK.json',dict(approved_F0_sha256=APPROVED,all_match=True,files=checked,
        new_F0_generated=False,frozen_implementation_modified=False))

    # Fresh scalar recomputation from original stored operands, separate from
    # loading the prospective reference files. No GGML or candidate helper.
    refs={};reference_receipt=[];manifest=load(HERE/'REFERENCE_MANIFEST.json')
    for item in inputs:
        data=pathlib.Path(item['path']).read_bytes();ref=solve(data);refs[item['id']]=ref;stages={}
        for stage in STAGES:
            b=b''.join(struct.pack('<d',v) for v in ref[stage]);entry=manifest['inputs'][item['id']]['stages'][stage]
            need(b==(HERE/entry['path']).read_bytes(),'fresh FP64 reference byte mismatch')
            stages[stage]=dict(elements=len(ref[stage]),sha256=hashlib.sha256(b).hexdigest(),bitwise_to_frozen_reference=True)
        reference_receipt.append(dict(input_id=item['id'],geometry=item['cell']['geometry'],stages=stages))
    save(DEST/'FRESH_FP64_RECOMPUTATION.json',dict(origin='CPU_SCALAR_BINARY64_RECOMPUTATION_NOT_GPU',
        actual_stored_inputs=16,stage_vectors=64,all_exact_to_frozen_references=True,reference_source_sha256=sha(HERE/'reference.py'),inputs=reference_receipt))

    by_input={x['id']:x for x in inputs};expected=load(HERE/'EXPECTED_GRAPHS.json');good={};all_native={};native=[];lives={};all_events=[]
    records={r['slot']['id']:r for r in rec['records']}
    for slot in plan['slots']:
        folder=RUN/slot['id']
        if not folder.exists():continue
        life=load(folder/'LIFECYCLE.json');raw=events(folder/'raw.jsonl');lives[slot['id']]=life;all_events+=raw
        need(life['request_sha256']==sha(folder/'REQUEST.wire') and life['raw_sha256']==sha(folder/'raw.jsonl'),'lifecycle raw/wire hashes')
        audit=audit_raw(raw,load(folder/'REQUEST.wire'),life['pid'],expected)
        row=dict(slot=slot,lifecycle_status=records[slot['id']]['status'],pid=life['pid'],creation_FILETIME=life['creation_FILETIME'],
            returncode=life['returncode'],owned_wall_s=life['owned_wall_s'],observer_samples=len(life['watchdog_samples']),
            terminal_observer_gap_ms=(life['owned_wall_s']-life['watchdog_samples'][-1]['elapsed_s'])*1000,
            lifecycle_error=records[slot['id']].get('error'),native_audit=audit)
        if slot['kind']=='graph':
            item=by_input[slot['input_id']];analysis,vectors=analyze_files(load(folder/'REQUEST.wire'),audit['graph'],folder,
                pathlib.Path(item['path']).read_bytes(),refs[item['id']])
            key=(item['id'],slot['mode'],slot['repeat']);all_native[key]=vectors
            row['fresh_reference_analysis']=analysis
            if records[slot['id']]['status']=='COMPLETE_AUDITED':good[key]=vectors
            else:row['output_scope']='Descriptive complete raw output only; observer-invalid slot remains NOT_ADMITTED'
        native.append(row)
    save(DEST/'NATIVE_AND_CPU_REANALYSIS.json',dict(native_hosts=native,admitted_graphs=len(good),complete_native_graphs=len(all_native),
        observer_invalid_outputs_do_not_repair_admission=True,CPU_graph_computes=0,GPU_launches_by_this_tool=0))

    # Full coordinate denominator, ten mode pairs and each independent repetition.
    cells=[];pair_summary={f'{a}/{b}':dict(available=0,missing=0,all_four_equal=0,first_divergence=collections.Counter(),
        stages={s:dict(bit_mismatches=0,max_abs=0.,max_relative_defined=0.,max_ULP=0,nonfinite=0) for s in STAGES}) for a,b in itertools.combinations(MODES,2)}
    for item in inputs:
        ident=item['id'];cell=dict(input_id=ident,geometry=item['cell']['geometry'],representations={},pairs=[],independent_repeats=[])
        for mode in MODES:
            slots=[s for s in plan['slots'] if s.get('input_id')==ident and s.get('mode')==mode]
            cell['representations'][mode]=[dict(repeat=s['repeat'],slot=s['id'],status=records[s['id']]['status'],error=records[s['id']].get('error')) for s in slots]
            left,right=(ident,mode,0),(ident,mode,1);repeat=dict(mode=mode,status='MISSING_OR_INVALID')
            if left in good and right in good:
                a,b=(lives[s['id']] for s in slots);repeat.update(status='COMPLETE_ADMITTED',independent=(a['pid'],a['creation_FILETIME'])!=(b['pid'],b['creation_FILETIME']),relation=compare(good[left],good[right]))
            elif left in all_native and right in all_native:
                repeat.update(descriptive_relation=compare(all_native[left],all_native[right]),scope='NOT_ADMITTED: includes observer-invalid output')
            cell['independent_repeats'].append(repeat)
        for a,b in itertools.combinations(MODES,2):
            aggregate=pair_summary[f'{a}/{b}']
            for repeat in (0,1):
                left,right=(ident,a,repeat),(ident,b,repeat);row=dict(left=a,right=b,repeat=repeat,status='MISSING_OR_INVALID',first_divergence_stage='UNKNOWN')
                if left in good and right in good:
                    relation=compare(good[left],good[right]);row.update(status='COMPLETE_ADMITTED',relation=relation,first_divergence_stage=relation['first_bitwise_divergence_stage'])
                    aggregate['available']+=1;aggregate['all_four_equal']+=relation['all_stages_bitwise_equal'];aggregate['first_divergence'][relation['first_bitwise_divergence_stage'] or 'NONE']+=1
                    for s in STAGES:
                        metrics=relation['stages'][s];target=aggregate['stages'][s]
                        target['bit_mismatches']+=metrics['bit_mismatches'];target['nonfinite']+=metrics['nonfinite']
                        for k in ('max_abs','max_relative_defined','max_ULP'):target[k]=max(target[k],metrics[k])
                else:aggregate['missing']+=1
                cell['pairs'].append(row)
        cells.append(cell)
    save(DEST/'ALL_COORDINATE_STAGE_RELATIONS.json',dict(expected_inputs=16,expected_pair_comparisons=320,
        expected_independent_repeat_pairs=80,stages=list(STAGES),pair_summary=pair_summary,cells=cells,
        admitted_only=True,not_a_full_domain_PASS=True))

    census_slot=plan['slots'][0];census_life=lives[census_slot['id']];numerical=[x for x in native if x['slot']['kind']=='graph']
    admitted=[x for x in numerical if x['lifecycle_status']=='COMPLETE_AUDITED'];invalid=[x for x in numerical if x['lifecycle_status']!='COMPLETE_AUDITED']
    samples=[s for l in lives.values() for s in l['watchdog_samples']];checkpoints=[e for e in all_events if e['event']=='MEMORY_CHECKPOINT']
    q1=[s for s in plan['slots'][1:] if s['q']==1];q1_started=[s for s in q1 if s['id'] in lives]
    fp64={}
    for stage in STAGES:
        m=[x['fresh_reference_analysis']['FP64_error'][stage] for x in admitted]
        fp64[stage]={k:max(x[k] for x in m) for k in ('max_abs','max_relative_defined','max_ULP_against_F32_rounded_reference')}
        fp64[stage]['nonfinite_actual']=sum(x['nonfinite_actual'] for x in m)
        fp64[stage]['first_error_stages_by_host']=dict(collections.Counter(x['fresh_reference_analysis']['first_nonzero_FP64_error_stage'] or 'NONE' for x in admitted)) if stage=='QK' else None
    summary=dict(run_id=f0['run_id'],approved_F0_sha256=APPROVED,reviewed_commit='d12a82d38a438425b8a9a54c899e076fae64456c',
        status='STOPPED_INCOMPLETE_OBSERVER_VIOLATION',stop='final observer gap',
        census=dict(attempts=1,completed_admitted=1,failed=0,unstarted=0,graph_descriptions=80,all_supported=True,graph_calls=0,owned_seconds=census_life['owned_wall_s']),
        numerical=dict(planned=160,attempts=len(numerical),native_returned_output=len(all_native),completed_admitted=len(good),failed_or_invalid=len(invalid),unstarted=124,
            graph_start=sum(e['event']=='GRAPH_START' for e in all_events),graph_return=sum(e['event']=='GRAPH_RETURN' for e in all_events),graph_output=sum(e['event']=='GRAPH_OUTPUT' for e in all_events),
            owned_seconds=sum(x['owned_wall_s'] for x in numerical),crashes=0,nonzero_process_exits=0,observer_invalid=1),
        totals=dict(experiment_host_attempts=37,graph_calls=36,owned_seconds=rec['owned_wall_s'],max_host_owned_seconds=max(l['owned_wall_s'] for l in lives.values()),
            unique_process_creation_identities=len({(l['pid'],l['creation_FILETIME']) for l in lives.values()})),
        q1=dict(planned=40,started=len(q1_started),admitted=35,observer_invalid=1,unstarted=4,
            admitted_common_path_comparisons=35,all_admitted_common_four_stages_equal=True,
            admitted_independent_repeat_pairs=15,all_admitted_repeat_four_stages_equal=True,remaining_repeat_pairs=5,
            caveat='All q1 labels are the same original common graph; q>1 QH_CONT/mask_REPEAT/KV_REPEAT paths were never executed'),
        q_gt1=dict(planned=120,started=0,unstarted=120,all_numerical_relations='UNKNOWN',support_only=True),
        comparisons=dict(available_admitted_cross_representation=70,missing_or_invalid_cross_representation=250,pairs=pair_summary),
        independent_FP64=fp64,
        actual_alignment_bytes=sorted({e['actual_alignment'] for e in all_events if e['event']=='DEVICE'}),
        PQ_cost=dict(actual_extra_CPU_copy_bytes=0,actual_extra_API_upload_bytes=0,actual_extra_logical_storage_bytes=0,actual_extra_allocator_rounded_bytes=0,
            reason='No q>1 host started. This is missing repaired-PQ execution evidence, not a free PQ baseline; frozen future costs remain unchanged'),
        resource_observations=dict(max_actual_sample_gap_ms=max(s['gap_ms'] for s in samples),max_terminal_observer_gap_ms=max(x['terminal_observer_gap_ms'] for x in native),
            peak_worker_RSS_bytes=max(s['RSS'] for s in samples),min_host_available_bytes=min(s['host_available'] for s in samples),
            min_disk_free_bytes=min(s['disk_free'] for s in samples),GPU_checkpoint_min_free_bytes=min(e['free'] for e in checkpoints),
            GPU_checkpoint_count=len(checkpoints),continuous_GPU_residency=False),
        failed_slot=dict(slot=invalid[0]['slot'],pid=invalid[0]['pid'],returncode=invalid[0]['returncode'],
            terminal_observer_gap_ms=invalid[0]['terminal_observer_gap_ms'],output_preserved=True,numerical_qualification='NOT_ADMITTED'),
        original_S1=dict(attempts=2,owned_seconds=5.109,unstarted=159,unchanged=True),
        seven_diagnostics=dict(attempts=7,owned_seconds=13.172,successful_graphs=5,predeclared_negatives=2,unchanged=True),
        models=0,extra_probes=0,warmups=0,retries=0,additional_GPU_attempts_after_stop=0,S2_S3='NOT_ADMITTED',actor_execution=False,performance_claim=None)
    save(DEST/'RESULT.json',summary)

    # Freeze all stopped-run files without adding/replacing any file in RUN.
    entries=[]
    for path in sorted(RUN.rglob('*')):
        if path.is_file():entries.append(dict(path=str(path.relative_to(RUN)).replace('\\','/'),bytes=path.stat().st_size,sha256=sha(path)))
    archive=DEST/'RAW_EVIDENCE.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for entry in entries:z.write(RUN/entry['path'],entry['path'])
    with zipfile.ZipFile(archive) as z:
        need(set(z.namelist())=={e['path'] for e in entries},'complete archive names')
        for entry in entries:need(hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256'],'archive streaming readback hash')
    save(DEST/'RAW_MANIFEST.json',dict(run_root=str(RUN),files=entries,file_count=len(entries),raw_bytes=sum(e['bytes'] for e in entries),
        archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,streaming_readback_all_hashes_match=True,
        no_raw_file_modified=True,failed_observer_slot_output_preserved=True))
    actual,reserve=output_usage();need(actual+reserve<=LIMITS['output_bytes'],'whole v2 plus export reserve budget')
    save(DEST/'DELIVERY_PROCESS.json',dict(origin='PURE_CPU_DELIVERY_AUDIT',pid=os.getpid(),
        elapsed_seconds=time.monotonic()-started,subprocess_starts=0,experiment_hosts_started=0,device_queries=0,graph_computes=0,
        modules_before=before,modules_after=modules(),actual_v2_bytes=actual,additional_full_raw_export_reserve_bytes=reserve,
        combined_accounted_bytes=actual+reserve,ceiling_bytes=LIMITS['output_bytes']))
    print(json.dumps(dict(status=summary['status'],census=summary['census'],numerical=summary['numerical'],totals=summary['totals'],
        q1=summary['q1'],FP64=fp64,raw_files=len(entries),raw_archive_sha256=sha(archive),combined_artifact_bytes=actual+reserve),indent=2))

if __name__=='__main__':main()
