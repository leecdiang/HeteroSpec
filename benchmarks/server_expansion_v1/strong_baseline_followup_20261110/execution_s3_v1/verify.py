"""Reuse complete S1 numeric readers; distinct clean/formal checking depth."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent/'execution_v1'))
from support import need,read,sha,fresh
from check_numeric import state,vectors
from qualify import reference_services_pair,service_pair


def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def repeated_R(first,second,service,profile):
    return reference_services_pair(second,first,dict(services=[service]),profile)


def complete_bridge(heavy_native,heavy_name,clean_native,clean_name,reference,service,profile,arm,view):
    """A read-only linked view adapts names, never data or original receipts.

    The original strict checker expects heavy/clean in one native directory.
    Fresh clean calibration workers deliberately keep a separate process. All
    actual paths/bytes are retained and their exact links are in the proof.
    """
    need(not view.exists(),'Fresh CPU checker view');view.mkdir(parents=True)
    name=service['id'];heavy=Path(heavy_native)/heavy_name;clean=Path(clean_native)/clean_name
    for path in (heavy,clean):need(path.is_dir()and not path.is_symlink(),'Original actual request directory required')
    (view/(name+'-heavy')).symlink_to(heavy,target_is_directory=True)
    (view/(name+'-clean')).symlink_to(clean,target_is_directory=True)
    fresh(view/'result.json',read(Path(heavy_native)/'result.json'))
    result=service_pair(view,reference,dict(services=[service]),profile,arm)
    # New POSIX endpoint must exist on both the heavy and clean request; its
    # heavy duration is never used as a performance observation.
    for path in (heavy,clean):clock(read(path/'receipt.json'))
    return dict(full_S1_service_checker=result,heavy_native=str(heavy),clean_native=str(clean),
                heavy_receipt_sha256=sha(heavy/'receipt.json'),clean_receipt_sha256=sha(clean/'receipt.json'),
                link_view_changes_names_only=True)


def clock(receipt):
    x=receipt['S3_service'];need(x['clock']=='CLOCK_MONOTONIC'and x['unit']=='s','Explicit actual native monotonic endpoint')
    for key in ('start_ns','reset_end_ns','end_ns','fence_ns','owned_ready_ns'):
        need(type(x[key])is int and x[key]>0,'Actual positive native timestamp')
    need(x['start_ns']<=x['reset_end_ns']<=x['fence_ns']<=x['end_ns']and
         x['start_ns']<=x['owned_ready_ns']<=x['end_ns'],'Reset/fence/output clock ordering')
    need(abs((x['end_ns']-x['start_ns'])/1e9-x['elapsed_s'])<1e-8 and x['elapsed_s']>0,'Native seconds/ns mismatch')
    need(x['empty_after_reset_min']<0 and x['empty_after_reset_max']<0 and
         x['initial_reset_included']is True and x['all_required_outputs_owned']is True and
         x['post_service_receipt_state_export_serialization_excluded']is True,'Complete initial reset and owned-output boundary')
    need(x['stop_separate_s']is None,'Uninstrumented stop clock must not be invented')
    return x


def clean(receipt_directory,reference,service,profile,arm,qualified_tape_sha256):
    path=Path(receipt_directory);r=read(path/'receipt.json');rr=read(Path(reference)/service['id']/'receipt.json')
    need(not r['capture']and r['ids']==rr['ids']and r['eog']==rr['eog']and r['stop_reason']==rr['terminal_kind'],'Complete clean/R greedy endpoint')
    need(r['prompt_ids']==service['input']['prompt_ids']and not r['draft_enabled']and r['draft_calls']==0,'Exact clean input and target-only M')
    n=len(r['prompt_ids']);count=len(r['ids']);final=n+count-1
    need(1<=count<=128 and (r['stop_reason']=='EOG'or count==128),'Natural EOG or unmodified128 cap')
    need(r['target_final_kv']==dict(min=0,max=final-1),'Last output token remains pending')
    need(all(r['observed_API_calls_within_service'][key]==0 for key in ('state_exports','state_imports','context_creates','heavy_captures')),
         'Heavy export/import/context/observer entered clean request')
    need(r['online_reference_replays']==r['online_state_exports']==r['online_context_creates']==0,'Hidden online clean replay/state/context')
    need(r['semantic_tape_sha256']==qualified_tape_sha256 and
         hashlib.sha256(canonical(read(path/'semantic-tape.json'))).hexdigest()==qualified_tape_sha256,'Complete qualified clean trajectory differs')
    expected=Path(reference)/service['id']/'captures'/str(final)
    proof=dict(frontier=vectors(path/'post-service-terminal/frontier.f32',expected/'frontier.f32',1,151936),
               all64_active_KV=state(path/'post-service-terminal/sequence.bin',expected/'sequence.bin',final,profile))
    need(r['target_output_reserve']==32 and(r['application_work']['backend_loop_entries']>0)==(arm=='B'and n>1),'Actual native reserve/backend loop')
    clock(r)
    return dict(terminal=proof,complete_semantic_tape_sha256=qualified_tape_sha256,
                every_step_full_vector_KV_recheck='Not repeated in clean timing; full heavy/clean qualification previously passed',
                all_requested_vectors_materialized_and_scanned_finite_in_native=True)


def row(worker,ordinal,receipt_directory,job,host):
    r=read(Path(receipt_directory)/'receipt.json');x=clock(r)
    need(host['launch_begin_monotonic_ns']<=x['start_ns']<x['end_ns']<=host['exit_observed_monotonic_ns'],'Native/host POSIX clock binding')
    entry=job['inputs'][ordinal];tokens=r['ids'];count=len(tokens)
    need(entry['name']==('warm'if ordinal==0 else'measured'),'Actual registered clean warm/measured role')
    runtime={k:v for k,v in job.items()if k!='inputs'}
    return dict(operation_id=worker['operations'][ordinal]['operation_id'],worker_id=worker['worker_id'],
         arm=worker['arm'],slot=worker['slot'],block=worker['block'],ordinal=ordinal,role=entry['name'],phase='S3',unit='s',
         elapsed_s=x['elapsed_s'],start_ns=x['start_ns'],end_ns=x['end_ns'],fence_ns=x['fence_ns'],owned_ready_ns=x['owned_ready_ns'],
         input_sha256=hashlib.sha256(canonical(entry['input'])).hexdigest(),config_sha256=hashlib.sha256(canonical(runtime)).hexdigest(),
         output_sha256=sha(Path(receipt_directory)/'post-service-terminal/frontier.f32'),
         output_commitment_kind='Complete terminal frontier vector; earlier steps bound by qualified semantic tape, not a fabricated trajectory-vector hash',
         q=count,output_rows=count,all_outputs_owned=True,callback_continues=True,
         q_definition='Logical requested full-vector rows over this complete service; actual native per-call widths are recorded separately',
         tokens=tokens,generated_tokens=count,stop_reason=r['stop_reason'].lower(),
         work_counters=r['application_work'],actual_physical_width_histogram=r['target_physical_width_hist'],
         reset_s=x['reset_s'],prefill_s=r['target_phases'].get('PREFILL',0),decode_s=r['target_phases'].get('ORDINARY',0),
         planning_s=r['planning_s'],owned_output_copy_s=r['output_copy_s'],stop_separate_s=None,
         observer_scope='Instrumented shared implementation, common CUDA graphs off')
