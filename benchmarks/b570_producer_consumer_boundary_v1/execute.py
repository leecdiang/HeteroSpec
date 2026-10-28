"""Freeze and execute the 152-slot boundary protocol with fail-closed B0 gates.

The execution ledger never retries or overwrites a request. Native raw data are
content addressed only after actual capture/readback. Diagnostics are not timing
measurements. The unchanged work_package independently audits the evidence.
"""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
import work_package as wp

HERE=Path(__file__).resolve().parent
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def meta(p): return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=wp.sha_file(p))

def freeze(a):
    a.out.mkdir(parents=True,exist_ok=False)
    assert wp.verify_source(HERE.parents[1])['status']=='PASS'
    models=wp.read(HERE.parent/'b570_native_reproduction_v1/MODEL_IDENTITY.json')
    for row,name in zip(models,['Qwen3-8B-Q8_0.gguf','Qwen3-0.6B-Q8_0.gguf']):
        p=a.models/name
        assert p.stat().st_size==row['bytes'] and wp.sha_file(p)==row['sha256'], name
    dlls=sorted(a.bin.glob('*.dll'))
    assert {p.name for p in dlls}=={'llama.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll'}
    modules=[meta(p) for p in dlls]
    for p in dlls: assert wp.sha_file(p)==wp.sha_file(a.qualified_runtime/p.name), p
    wp.write_new(a.out/'NUMERIC_MODULES.json',modules)
    source_files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.cpp','.txt','.md','.json'} and 'execution' not in p.parts]
    source_files += [HERE.parent/'b570_native_reproduction_v1/native'/n for n in ['formal.cpp','raw_capture.h']]
    sources=[meta(p) for p in sorted(source_files)]
    wp.write_new(a.out/'SOURCE_MANIFEST.json',sources)
    tok=wp.read(a.selection/'TOKENIZATION.json')
    runtime=wp.read(HERE/'RUNTIME_TEMPLATE.json')
    runtime.update(status='BUILT_NOT_YET_B0_QUALIFIED',native_extension_implemented=True,
        executable_sha256=wp.sha_file(a.bin/'boundary.exe'),source_manifest_sha256=wp.sha_file(a.out/'SOURCE_MANIFEST.json'),
        numeric_modules_manifest_sha256=wp.sha_file(a.out/'NUMERIC_MODULES.json'),
        vocabulary_size=tok['vocabulary']['vocab_tokens'],eog_ids=tok['vocabulary']['runtime_eog_ids'])
    wp.write_new(a.out/'RUNTIME.json',runtime)
    panel=wp.read(a.selection/'INPUT_PANEL.json')
    assert panel['candidate_inventory_sha256']==wp.sha_file(a.selection/'CANDIDATE_INVENTORY.json')
    assert panel['exposure_audit_sha256']==wp.sha_file(a.selection/'EXPOSURE_AUDIT.json')
    assert wp.read(a.selection/'EXPOSURE_AUDIT.json')['status']=='PASS'
    plan=wp.build_plan(panel,runtime);wp.validate_plan(plan)
    wp.write_new(a.out/'FROZEN_PLAN.json',plan)
    inputs={r['id']:r for r in wp.read(HERE/'CONTROL_INPUTS.json')['inputs']+panel['inputs']}
    wp.write_new(a.out/'NATIVE_PANEL.json',inputs)
    files=source_files+dlls+[a.bin/'boundary.exe',a.out/'FROZEN_PLAN.json',a.out/'NATIVE_PANEL.json']
    files += [a.models/Path(m['path']).name for m in models]
    files += [p for p in a.selection.glob('*') if p.is_file()]
    wp.write_new(a.out/'FREEZE.json',dict(status='FROZEN_BEFORE_NATIVE',utc=utc(),files=[meta(p) for p in sorted(set(files))],
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE,text=True).strip(),
        driver_build='MSVC /O2 /W4 /fp:precise /utf-8; linked PR148 libraries',
        numeric_dlls_byte_identical_to_qualified=True,
        observer_contract='Metadata-only tensor descriptors on both observer arms; heavy additionally persists complete trajectory logits. No stage readbacks.',
        maximum_worker_seconds=900,individual_request_soft_seconds=180,budget=wp.BUDGET))
    print('FROZEN',wp.digest(plan),flush=True)

def module_check(receipt,manifest):
    expected={Path(r['path']).name.lower():r['sha256'] for r in manifest if Path(r['path']).suffix.lower() in {'.dll','.exe'}}
    observed={Path(r['path']).name.lower():r['sha256'] for r in receipt.get('loaded_module_hashes',[])}
    return all(observed.get(k)==v for k,v in expected.items())

def classify(row):
    if row.get('status')!='TECHNICAL_FAILURE':return
    reason=row.get('reason','')
    if 'budget exhausted' in reason:row['status']='BUDGET_EXHAUSTED'
    elif any(s in reason for s in ['restored boundary','state import','state export','receiver not empty','own-path']):row['status']='RESTORE_SHAM_FAILED'
    elif 'observer' in reason:row['status']='OBSERVER_INTERFERENCE'
    elif 'geometry' in reason or 'layout bridge' in reason:row['status']='GEOMETRY_NOT_ADMITTED'

def run(a):
    plan=wp.read(a.freeze/'FROZEN_PLAN.json');wp.validate_plan(plan)
    freeze_doc=wp.read(a.freeze/'FREEZE.json')
    a.out.mkdir(parents=True,exist_ok=False);raw=a.out/'raw';raw.mkdir()
    records=[];owned=0.;block=None;gate=False
    slots=plan['slots'];modules=wp.read(a.freeze/'NUMERIC_MODULES.json')
    binaries=modules+[r for r in freeze_doc['files'] if Path(r['path']).name=='boundary.exe']
    exe=Path(next(r['path'] for r in binaries if Path(r['path']).name=='boundary.exe'))
    model_paths=[Path(r['path']) for r in freeze_doc['files'] if Path(r['path']).suffix=='.gguf']
    target=next(p for p in model_paths if '8B-' in p.name);draft=next(p for p in model_paths if '0.6B-' in p.name)
    ledger=a.out/'REQUESTS.jsonl'
    def append(row):
        assert row['slot_id'] not in {r['slot_id'] for r in records}
        with ledger.open('a',encoding='utf8',newline='\n') as f:
            f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n');f.flush()
        records.append(row)
    for stage,index in [('B0',0),('B0',1)]+[('B1',i) for i in range(8)]:
        group=[s for s in slots if s['stage']==stage and s['input_index']==index]
        if block:break
        assert stage=='B0' or gate, 'B1 gate not established'
        raw_bytes=sum(p.stat().st_size for p in raw.rglob('*') if p.is_file())
        if owned>=wp.BUDGET['owned_seconds_cap'] or raw_bytes>=wp.BUDGET['payload_bytes_cap']:
            block=dict(status='NOT_RUN_BUDGET',reason='frozen owned/raw cap exhausted before worker',blocking_slot=None);break
        job=dict(slots=group,payload_root=str(raw.resolve()),runtime_sha256=wp.digest(plan['runtime']),
                 vocabulary_size=plan['runtime']['vocabulary_size'],eog_ids=plan['runtime']['eog_ids'])
        label=f'{stage}-{index}';jobfile=a.out/(label+'.job.json');receipt_path=a.out/(label+'.receipt.json')
        wp.write_new(jobfile,job)
        # Include the exact worker coordinate file in its own immutable launch manifest.
        launch=dict(freeze_doc,files=freeze_doc['files']+[meta(jobfile)])
        launchfile=a.out/(label+'.launch.json');wp.write_new(launchfile,launch)
        command=[sys.executable,str(HERE/'run_native.py'),'--manifest',str(launchfile),'--receipt',str(receipt_path),
            '--limit',str(min(900,int(wp.BUDGET['owned_seconds_cap']-owned))),str(exe),str(a.out/label),str(target),str(draft),
            str(a.freeze/'NATIVE_PANEL.json'),str(jobfile)]
        print('START',label,'requests',len(group),flush=True)
        proc=subprocess.run(command,check=False)
        receipt=wp.read(receipt_path);owned+=receipt.get('charged_seconds',0)
        module_ok=module_check(receipt,binaries)
        worker_path=a.out/label/'result.json';worker=wp.read(worker_path) if worker_path.exists() else {}
        rows=worker.get('requests',[])
        if worker.get('active_request'):
            row=worker['active_request'];row.update(status='TECHNICAL_FAILURE',reason='worker interrupted; partial raw retained',finished_utc=receipt['finished_utc']);rows.append(row)
        for row in rows:
            assert row['slot_id'] in {s['slot_id'] for s in group}
            row.setdefault('checks',{})['module_identity']=module_ok
            row['supervisor_receipt']=receipt_path.name
            if row['status'] in wp.COMPLETE and not module_ok:
                row.update(status='TECHNICAL_FAILURE',reason='actual loaded modules do not match freeze')
            classify(row)
            if row['status'] in wp.COMPLETE:
                check=wp.audit_controls(plan,[row],a.references,raw)
                failed=[c for c in check['checks'] if c['slot_id']==row['slot_id'] and c['status']=='FAIL']
                if failed:row.update(status='REFERENCE_MISMATCH',reason=failed[0]['error'])
                slot=next(s for s in group if s['slot_id']==row['slot_id'])
                prior={r['slot_id']:r for r in records}
                bad=[s for s in slot['depends_on'] if s not in prior or prior[s]['status'] not in wp.COMPLETE]
                if bad and not failed:
                    row.update(status='TECHNICAL_FAILURE',reason='Executed before host audit exposed failed dependency: '+bad[0])
            append(row)
        # Historical and structural audits are independently re-run after each input.
        control=wp.audit_controls(plan,records,a.references,raw)
        wp.write_new(a.out/(label+'.CONTROL_AUDIT.json'),control)
        audit=wp.audit_records(plan,records,raw,control)
        wp.write_new(a.out/(label+'.CPU_AUDIT.json'),audit)
        gate=audit['b0_qualified']
        problems=audit['errors']+[r for r in records if r['status'] in wp.FAILURE]
        if proc.returncode or receipt['status']!='complete' or worker.get('status')!='WORKER_COMPLETE' or problems or len(rows)!=len(group):
            block=dict(status='NOT_RUN_DEPENDENCY',reason='native/control/restore/observer gate failed; no automatic retry',
                       blocking_slot=next((r['slot_id'] for r in rows if r['status'] in wp.FAILURE),rows[-1]['slot_id'] if rows else group[0]['slot_id']))
        print('FINISH',label,'worker',worker.get('status'),'B0',gate,'errors',len(audit['errors']),'owned',round(owned,1),flush=True)
    if block:
        for slot in slots:
            if slot['slot_id'] not in {r['slot_id'] for r in records}:
                append(dict(slot_id=slot['slot_id'],attempt=0,native_started=False,**block))
    control=wp.audit_controls(plan,records,a.references,raw);wp.write_new(a.out/'CONTROL_AUDIT.json',control)
    audit=wp.audit_records(plan,records,raw,control);wp.write_new(a.out/'CPU_AUDIT.json',audit)
    wp.write_new(a.out/'EXECUTION_SUMMARY.json',dict(status=audit['status'],counts=audit['counts'],b0_qualified=gate,
        owned_seconds=owned,raw_unique_bytes=sum(p.stat().st_size for p in raw.rglob('*') if p.is_file()),
        started_requests=sum(r['native_started'] for r in records),primary_coordinates=len(records),block=block,
        new_performance_claims=False,finished_utc=utc()))
    print(json.dumps(wp.read(a.out/'EXECUTION_SUMMARY.json')),flush=True)

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('freeze')
    for n in ['bin','models','qualified-runtime','selection','out']:p.add_argument('--'+n,type=Path,required=True)
    p=sub.add_parser('run')
    for n in ['freeze','out','references']:p.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();freeze(a) if a.cmd=='freeze' else run(a)

if __name__=='__main__':main()
