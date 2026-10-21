"""Read-only PR136 admission audit. Never imports or starts a model runtime."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
REPO = HERE / 'HeteroSpec-rtx-closure'
OUT = REPO / 'benchmarks/rtx_platform_closure_v1/e0_20261020'
OLD = Path('D:/hs-qb-confirmation-v02')
RESTORE = Path('D:/hs104-authenticated-final-restore')
OLD_REPO = Path('C:/Users/ASUS/Documents/Codex/2026-10-14/heterospec-pr-104-rtx-implementation-pq/work/HeteroSpec-pr104')
OLD_RESULT = OLD_REPO / 'benchmarks/rtx_qb_confirmation_v1/final_20261015'
PROTOCOL_SHA = '65b938c19b9856c6c37af6c1d224989c22cd469f'

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(name, data):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')

def pin(p):
    p = Path(p)
    return dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p))

def compare(p, expected):
    p = Path(p)
    row = dict(path=str(p), expected_sha256=expected)
    if not p.is_file():
        return row | dict(status='MISSING')
    actual = pin(p)
    return row | actual | dict(status='KNOWN' if actual['sha256'] == expected else 'INCOMPATIBLE')

def main():
    start = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=False)
    study_uuid = str(uuid.uuid4())
    save('AUDIT_IDENTITY.json', dict(study_uuid=study_uuid, created_utc=datetime.now(timezone.utc).isoformat(),
         scope='E0 read-only admission; no native model, graph, replay, build or profiler invocation',
         execution_preregistration_frozen=False, audit_script=pin(__file__), python=pin(sys.executable),
         protocol_pr=136, protocol_head=PROTOCOL_SHA, result_base='ec6b97518a2f230330d79f1b0ba2ca97bc70cd6a'))

    for name in ('README.md', 'EXPERIMENT_PLAN.md', 'PREREGISTRATION_TEMPLATE.json', 'RUNBOOK.md'):
        p = OUT / 'protocol136' / name
        p.parent.mkdir(exist_ok=True)
        shutil.copyfile(HERE / 'protocol136' / name, p)

    runtime = read(OLD / 'RUNTIME_MANIFEST.json')
    contracts = read(OLD / 'MODEL_CONTRACT.json')
    plan = read(OLD / 'PLAN.json')
    qwen = contracts['families']['Qwen']
    rows = []
    route = next(x for x in runtime['routes'] if x['family'] == 'Qwen' and x['arm'] == 'C_QB')
    rows.append(compare(OLD / 'native/build/bin' / route['binary'], route['binary_sha256']))
    for name, expected in runtime['numerical_DLL_sha256'].items():
        rows.append(compare(OLD / 'native/build/bin' / name, expected))
    for spec in qwen['models'].values():
        rows.append(compare(spec['path'], spec['sha256']))
    f0 = read(OLD_REPO / 'benchmarks/rtx_qb_confirmation_v1/registration/E2_F0.json')
    driver = next(x for x in f0['files'] if Path(x['path']).name.lower() == 'nvcuda.dll')
    rows.append(compare(driver['path'], driver['sha256']))
    rows.append(compare(OLD / route['build_manifest'], route['build_manifest_sha256']))
    save('RUNTIME_MODEL_DLL_AUDIT.json', dict(checks=rows, status_counts=dict(collections.Counter(x['status'] for x in rows)),
         runtime_source_inventory_sha256=route['source_inventory_sha256'],
         tokenizer_binding='tokenizer GGUF metadata and vocabulary contract; model byte identity includes embedded tokenizer',
         qwen_contract=qwen, frozen_driver=f0['host_identity'], runtime_manifest=pin(OLD/'RUNTIME_MANIFEST.json'),
         model_contract=pin(OLD/'MODEL_CONTRACT.json')))

    # Hash every member against the authenticated combined PR104 restoration manifests.
    restoration = []
    for part in ('E2', 'E1', 'CONTROL'):
        root = RESTORE / part
        manifest = read(root / 'RAW_MANIFEST.json')
        members = []
        for item in manifest['files']:
            p = root / item['path']
            row = compare(p, item['sha256'])
            if p.is_file() and p.stat().st_size != item['bytes']:
                row['status'] = 'INCOMPATIBLE'
            members.append(row)
        save('restoration/' + part + '_MEMBER_CHECKS.json', members)
        restoration.append(dict(part=part, manifest=pin(root/'RAW_MANIFEST.json'), members=len(members),
                                status_counts=dict(collections.Counter(x['status'] for x in members))))
        print('Restoration checked:', part, len(members), flush=True)
    raw_manifest = read(OLD_RESULT / 'RAW_ARCHIVE_MANIFEST.json')
    archives = []
    for item in raw_manifest['E1']['parts']:
        archives.append(compare(OLD_RESULT / item['name'], item['sha256']))
    archives.append(compare(OLD_RESULT / raw_manifest['CONTROL']['name'], raw_manifest['CONTROL']['sha256']))
    archives.append(compare(OLD_REPO / raw_manifest['E2']['path'], raw_manifest['E2']['sha256']))
    save('HISTORICAL_RESTORATION.json', dict(restoration=restoration, archives=archives,
         original_archive_descriptor=raw_manifest, original_final_seal='f997262d6b0accb126a1217c9356745cc8bbf708',
         scope='Local byte verification of previously authenticated restoration, not a new external review'))

    # Exhaustively inspect retained reference schemas; top scores are not full logits.
    coverage = []
    for part in ('E1', 'E2'):
        root = RESTORE / part
        events = collections.Counter()
        keys = collections.defaultdict(set)
        sample_count = 0
        full_logits_events = 0
        for p in sorted(root.rglob('trace.jsonl')):
            for line in p.read_text(encoding='utf-8').splitlines():
                if not line.strip():
                    continue
                event = json.loads(line)
                kind = event.get('event', 'NO_EVENT')
                events[kind] += 1
                keys[kind].update(event)
                sample_count += kind == 'sample'
                full_logits_events += any(isinstance(event.get(k), list) and len(event[k]) == 151936 for k in ('logits', 'target_logits', 'draft_logits'))
        records = [read(p) for p in sorted((root/'data/runs').rglob('RECORD.json'))]
        qrecords = [r for r in records if r.get('family') == 'Qwen']
        coverage.append(dict(part=part, records=len(records), qwen_records=len(qrecords),
             qwen_condition_counts=dict(collections.Counter(r.get('condition') for r in qrecords)),
             trace_files=len(list(root.rglob('trace.jsonl'))), event_counts=dict(events),
             event_field_names={k:sorted(v) for k,v in keys.items()}, sample_events=sample_count,
             full_vocab_logits_events=full_logits_events,
             f32_files=[str(p.relative_to(root)) for p in root.rglob('*.f32')],
             binary_tensor_basenames=sorted({p.name for p in root.rglob('*.bin')}),
             zero_trace_ranges=sum(r.get('trace_range',{}).get('start') == r.get('trace_range',{}).get('end') == 0 for r in records)))
    save('REFERENCE_COVERAGE.json', dict(coverage=coverage, conclusion='MISSING_FULL_REQUEST_LOGITS_REFERENCE',
         exact_limit='PR104 E1 retains operator tensors and heavy traces with selected/top1/top2 scores, not every raw target/draft vocabulary vector including rejected verification rows. E2 retains counts and endpoints without full cycle traces.',
         complete_reference_binding_verified=False,
         historical_policy=dict(cap=128, C_maximum_k=3, C_target_ub=4, R_target_ub=1),
         proposed_policy=dict(cap='must remain 128', maximum_k=1),
         k1_historical_full_reference='NOT_BOUND; k1 cannot inherit k3 complete workload/cycle reference by name'))

    save('EXPOSED_INPUT_INVENTORY.json', dict(selection_status='NOT_FROZEN_E0_STOP',
         historical_plan=pin(OLD/'PLAN.json'), all_qwen_inputs=plan['panel']['Qwen'],
         cap=128, new_output_cap_authorized=False, selected_four=None,
         reason='No candidate panel or execution schedule is represented as frozen after failed E0'))

    # Old ledgers retain their own units and caps. Never sum overlapping restorations or reset allowance.
    ledger = sorted((OLD/'ledger').glob('*.json'))
    entries = [read(p) for p in ledger]
    slot_counter = collections.Counter(e['slot'] for e in entries)
    save('ledgers/PR104_LEDGER_MEMBER_HASHES.json', [pin(p) for p in ledger])
    save('ledgers/PR104_LEDGER.json', entries)
    lifetimes = [dict(receipt=pin(p), **read(p)) for p in sorted((RESTORE/'E2/data/runs').rglob('LIFETIME.json'))]
    save('ledgers/PR104_PROCESS_LIFETIMES.json', lifetimes)
    ledger_summary = dict(root=str(OLD), events=len(entries),
         kind_counts=dict(collections.Counter(e['kind'] for e in entries)),
         duplicate_slots=[s for s,n in slot_counter.items() if n > 1],
         process_receipts=len(lifetimes), owned_seconds=sum(x['seconds'] for x in lifetimes),
         ledger_entry_snapshots='ledgers/PR104_LEDGER.json', ledger_hashes='ledgers/PR104_LEDGER_MEMBER_HASHES.json')

    # Reconcile each later RTX scope with its exact raw root; keep receipts and original units intact.
    followups = []
    for pr in (120, 121, 122, 123):
        roots = sorted(p for p in Path('D:/').glob('hs' + str(pr) + '-*')
                       if (p/'RESOURCE_SUMMARY.json').is_file() and (p/'RUN_SPEC.json').is_file())
        for root in roots:
            docs = {}
            for name in ('RESOURCE_SUMMARY.json', 'RUN_SPEC.json', 'QUERY_AND_FAILURE_ACCOUNTING.json', 'EXECUTION_POLICY.json', 'GPU_EXECUTION_CLOSED.json', 'PROCESS_GPU_CLOSURE.json'):
                p = root / name
                if p.is_file():
                    dest = 'ledgers/PR'+str(pr)+'/'+name
                    save(dest, read(p))
                    docs[name] = pin(p)
            followups.append(dict(pr=pr, root=str(root), documents=docs,
                             resource_summary=read(root/'RESOURCE_SUMMARY.json')))
    # Inventory all retained study-specific ledger/accounting records across earlier RTX roots.
    index = []
    names = {'BUDGET.json','BUDGET_FINAL.json','BUDGET_ACCOUNTING.json','FINAL_ACCOUNTING.json',
             'CLOSURE_ACCOUNTING.json','RESOURCE_SUMMARY.json','WORK_ACCOUNTING.json',
             'S0_ACCOUNTING.json','ACCOUNTING.json','CPU_DELIVERY_ACCOUNTING.json',
             'QUERY_AND_FAILURE_ACCOUNTING.json','PAID_LEDGER.json'}
    for root in [p for p in Path('D:/').iterdir() if p.is_dir() and
                 (p.name.startswith(('hs104','hs110','hs113','hs114','hs116','hs120','hs121','hs122','hs123','hsc95','hs-qb')))
                 and not any(w in p.name for w in ('fresh','restore','archive','download','authenticated','package','control-history'))]:
        for p in root.rglob('*.json'):
            if p.name in names:
                index.append(pin(p))
    save('RTX_LEDGER_RECONCILIATION.json', dict(PR104=ledger_summary, later_RTX_scopes=followups,
         retained_accounting_index=index,
         restored_copies_are_not_new_charges=True, common_global_remaining_allowance=None,
         resource_status='SCOPED_LEDGERS_RECOVERED; NO_COMMON_REMAINING_ALLOWANCE_ASSERTED',
         reconciliation_limit='Historical studies use different caps and charge units. Listed source receipts preserve them; no synthetic cumulative balance and no B570 budget transfer.',
         new_study_reserved_native_processes=0, new_study_reserved_request_slots=0,
         new_study_reserved_owned_process_seconds=0))

    source = Path('D:/hsc95/native/source')
    evidence_paths = {
        'native_hs_observer.h':source/'common/hs_observer.h',
        'native_capture95.h':source/'common/capture95.h',
        'native_live_capture.h':source/'common/live_capture.h',
        'historical_resident.py':Path(plan['legacy'])/'resident.py',
        'PR104_experiment.py':OLD_REPO/'benchmarks/rtx_qb_confirmation_v1/experiment.py',
        'PR104_COUNTER_SEMANTICS.md':OLD/'COUNTER_SEMANTICS.md',
        'PR104_COUNTS.json':OLD_RESULT/'COUNTS.json',
        'PR104_RESULT.md':OLD_RESULT/'RESULT.md',
        'PR104_RUNTIME_MANIFEST.json':OLD/'RUNTIME_MANIFEST.json',
        'PR104_MODEL_CONTRACT.json':OLD/'MODEL_CONTRACT.json',
    }
    bindings=[]
    for name,p in evidence_paths.items():
        dest=OUT/'historical_evidence'/name
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(p,dest)
        bindings.append(dict(copied_to=str(dest.relative_to(OUT)), **pin(p)))
    save('SOURCE_EVIDENCE_BINDINGS.json', dict(files=bindings,
         scope='Retained source inspection; manifest and binary identities independently hashed. No fresh compiler/link or deployed-kernel source correspondence claim.'))

    stop_reasons = ['No bound complete historical R/PQ/QB target/draft logits reference for the proposed k1 requests',
                    'Retained native capture records top scores and selected operator snapshots, not full-request raw logits',
                    'PR104 resident timer and arm contexts do not implement the proposed fresh-context complete-service window']
    save('E0_DISPOSITION.json', dict(status='ENGINEERING_STOP_REFERENCE_BINDING',
         E0='AUDIT_COMPLETED_NOT_ADMITTED', E1='NOT_STARTED_E0_GATE', E2='NOT_STARTED_E0_GATE',
         E3='UNAVAILABLE_E0_GATE; no clean E2 data on which to assess need', E4='E0_STOP_ARCHIVED; scientific questions unresolved',
         stop_reasons=stop_reasons,
         scientific_ratios=None, scientific_screen='NOT_EVALUATED', speculative_economics='NOT_EVALUATED',
         actual_q_gt_1_this_study='NOT_OBSERVED_NO_EXECUTION',
         historical_q_is_not_new_qualification=True, native_execution_allowed=False,
         paper_reconstruction_started=False, no_time_deadline=True))
    save('PREREGISTRATION_NOT_FROZEN.json', dict(study='RTX_PLATFORM_CLOSURE_V1', study_uuid=study_uuid,
         status='NOT_FROZEN_E0_ENGINEERING_STOP', protocol_head=PROTOCOL_SHA,
         native_execution_allowed=False, complete_historical_reference_binding=False,
         runtime_model_DLL_inventory='RUNTIME_MODEL_DLL_AUDIT.json', proposed_output_cap=128,
         input_manifest_frozen=False, balanced_order_frozen=False, native_budget_reserved=0,
         freeze_commit=None, first_native_start_receipt=None,
         reason='Completing placeholders and calling it frozen would bypass E0. No execution PREREGISTRATION.json is issued.'))

    slots=[]
    for i in range(4):
        for arm in ('R','PQ','QB'):
            slots.append(dict(gate='E1', session='', input_position=i, task_id='UNASSIGNED_E0_STOP', arm=arm,
                              kind='qualification', status='NOT_STARTED_E0_GATE'))
    for s in range(4):
        for i in range(4):
            for arm in ('R','PQ_A','PQ_B','QB'):
                for kind in ('warmup','measured'):
                    slots.append(dict(gate='E2',session=s,input_position=i,task_id='UNASSIGNED_E0_STOP',arm=arm,
                                      kind=kind,status='NOT_STARTED_E0_GATE'))
    for i in range(4):
        for arm in ('PQ','QB'):
            for kind in ('clean_before','profile','clean_after'):
                slots.append(dict(gate='E3',session='',input_position=i,task_id='UNASSIGNED_E0_STOP',arm=arm,
                                  kind=kind,status='CONDITIONAL_UNSTARTED_E0_GATE'))
    with (OUT/'ALL_SLOTS.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(slots[0]));w.writeheader();w.writerows(slots)
    save('PROCESS_RECEIPTS.json', dict(scope='new-study native model, replay, build and profile processes',
         started=[], completed=[], failed=[], native_process_starts=0, native_process_owned_seconds=0,
         cleanup='No study native process was created; no runtime cleanup action required',
         other_processes='Read-only Git, file hashing, Python audit and nvidia-smi are auxiliary operations; not globally process-accounted'))
    save('COST_TABLE.json', dict(new_native_model_loads=0,new_qualification_requests=0,new_warmups=0,
         new_measured_requests=0,new_profile_requests=0,new_native_builds=0,new_native_owned_seconds=0,
         new_GPU_graph_calls=0,new_model_load_seconds=0,new_service_seconds=None,new_GPU_active_seconds=None,
         E0_audit_wall_seconds=time.perf_counter()-start, wall_scope='Audit script only; excludes earlier interactive review and final packaging',
         logical_unstarted_slots=dict(E1=12,E2_warmup=64,E2_measured=64,E3_conditional=24),
         slots_are_positions_not_an_execution_schedule=True))
    shutil.copyfile(__file__,OUT/'audit_e0.py')
    print(json.dumps(dict(out=str(OUT),uuid=study_uuid,identity=dict(collections.Counter(x['status'] for x in rows)),
                          gate='E0_STOP',ledger=ledger_summary,followup_prs=[x['pr'] for x in followups]),ensure_ascii=False),flush=True)

if __name__=='__main__':
    main()
