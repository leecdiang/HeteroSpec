"""Bind inherited dedup evidence without probing processes/devices or old ledgers."""
from pathlib import Path
import json,hashlib,datetime
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=ROOT/'rtx223-round1-resume-20261112-e03'

def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))

def file_record(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

sources=[OLD/'e03/RESULT.json',OLD/'e03/dedup/DEDUP_E03_RESULT.json',OLD/'e03/dedup/OWNER_STEPS_ZH.md']
old_result=read_json(sources[0]);old_dedup=read_json(sources[1])
if old_result.get('usage',{}).get('GPU_kernel_launches')!=0:
    raise ValueError('Inherited e03 native usage changed; cannot reuse zero-use interpretation')
api_files=[HERE.parent/'thread_api_1.json',HERE.parent/'thread_api_2.json']
api_results=[]
for p in api_files:
    parsed=read_json(p)
    text=json.dumps(parsed)
    if '-32000' not in text:
        raise ValueError('Thread API result changed; inspect it before retaining blocked interpretation')
    api_results.append({'file':file_record(p),'result':'MCP -32000; no terminal state recovered'})

# Search only known relevant dedup directories and root filenames. No user-document crawl.
search_dirs=[ROOT/'rtx223-round1-resume-20261112-e02/continuation/dedup',OLD/'e03/dedup']
candidates=[]
for d in search_dirs:
    for p in d.rglob('*'):
        if p.is_file() and p.suffix.lower() in ('.json','.log','.txt') and any(t in p.name.lower() for t in ('host','readonly','read-only','smoke','process')):
            candidates.append(p)
for p in ROOT.iterdir():
    if p.is_file() and p.suffix.lower() in ('.json','.log','.txt') and any(t in p.name.lower() for t in ('host','readonly','read-only','dedup')):
        candidates.append(p)
classified=[]
normal_host_files=[]
for p in sorted(set(candidates)):
    rec=file_record(p)
    if p.suffix.lower()=='.json':
        try:
            item=read_json(p)
        except (ValueError,UnicodeError):
            rec['classification']='not a parseable JSON host receipt'
        else:
            if p.name=='RESTRICTED_SCRIPT_SMOKE.json':
                rec['classification']='restricted smoke; not normal-host evidence'
                rec['process_query_status']=item.get('Processes',{}).get('Status')
                if rec['process_query_status']!='READ_FAILED_UNKNOWN':
                    raise ValueError('Restricted smoke changed; inspect scope rather than silently reclassify')
            elif p.name=='FRESH_PROCESS_LOCK_LEDGER.json':
                rec['classification']='prior restricted process namespace snapshot'
            elif p.name in ('NT_PROCESSES.json','TOOLHELP_PROCESSES.json','PROCESS_LOCK_LEDGER.json'):
                rec['classification']='prior restricted process namespace snapshot'
            elif item.get('Schema')=='heterospec.owner-readonly-host-evidence.v1':
                rec['classification']='candidate saved owner host receipt; requires direct scope/time review'
                normal_host_files.append(rec)
            else:
                rec['classification']='not a known normal-host owner receipt'
    else:
        rec['classification']='not a known parsed host receipt'
    classified.append(rec)

statement='User reports one prior full-host readonly process view: no workers/knownlocks then, explicitly transient and NOT original-session termination.'
threads=old_dedup['fresh_small_catalog']['threads']
out={
    'schema':'heterospec.rtx223.e04.dedup.v1',
    'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'decision':'INCONCLUSIVE','native_gate':'BLOCKED_PENDING_USER_ORIGINAL_EXECUTION_TERMINAL_AND_QUEUED_LEASE_FACTS',
    'inherited_sources':[file_record(p) for p in sources],
    'thread_API_results':api_results,
    'user_prior_host_observation':{
        'source_kind':'user attestation as supplied in this task; relayed text, not an independently verified raw receipt',
        'statement_as_supplied':statement,
        'normal_host_no_related_workers_then':'USER_REPORTED',
        'known_locks_absent_then':'USER_REPORTED',
        'observation_time':None,
        'raw_independent_verification':False,
        'proves_original_execution_ended':False,
        'fresh_admission_now':False
    },
    'scoped_saved_host_receipt_search':{
        'scope':[str(d) for d in search_dirs]+[str(ROOT)+' (matching top-level filenames only)'],
        'normal_host_candidate_files':normal_host_files,
        'status':'CANDIDATE_REQUIRES_REVIEW' if normal_host_files else 'NOT_LOCATED_IN_SCOPED_DIRECTORIES',
        'existing_restricted_candidates':classified,
        'does_not_claim_no_host_receipt_exists_elsewhere':True
    },
    'pending_original_execution_facts':[{
        'thread_id':t['thread_id'],'candidate_title':t['title'],
        'execution_turn_terminal':'PENDING_USER',
        'last_related_task_and_end_reply':'PENDING_USER',
        'queued_or_running_older_GPU_workers':'PENDING_USER',
        'lease_holder_and_task_attribution':'PENDING_USER',
        'current_e04_turn_is_not_another_older_task':True
    } for t in threads],
    'owner_next_steps':'OWNER_STEPS_ZH.md',
    'do_not_request_duplicate_full_host_collection_now':True,
    'require_fresh_host_check_immediately_before_future_launch':True,
    'no_self_clearance_from_user_idle_snapshot_or_empty_cache':True,
    'native_initialization_or_numerical_DLL_loading':'NOT_ADMITTED',
    'new_model_requests':0,'new_target_draft_rows':0,'new_GPU_kernel_launches':0,'new_native_GPU_seconds':0,
    'process_GPU_lock_ledger_probes_repeated':False,
    'old_ledger_reads_or_writes':False,
    'old_supervision_tests_rerun':False,
    'file_bindings':{p.name:file_record(p) for p in HERE.iterdir() if p.is_file() and p.name not in ('DEDUP_E04_RESULT.json','PARSE_CHECK.json')}
}
(HERE/'DEDUP_E04_RESULT.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
check={'status':'PASS_PARSE_AND_SCOPE_BINDING_ONLY','json_sources_parsed':2+len(api_files),'API_errors_retained':len(api_results),'host_snapshot_self_clearance':False,'saved_normal_host_candidates':len(normal_host_files),'no_process_GPU_or_ledger_probe':True,'new_model_requests':0,'new_GPU_kernel_launches':0}
(HERE/'PARSE_CHECK.json').write_text(json.dumps(check,indent=2),encoding='utf8')
print(json.dumps({'gate':out['native_gate'],'prior_host_observation':'USER_REPORTED_TRANSIENT_NOT_INDEPENDENTLY_RAW_VERIFIED','saved_normal_host_receipt_candidates':len(normal_host_files),'required_next_fact':'Original execution-turn terminal state plus queued-worker/lease attribution','parse_check':check},indent=2))
