"""Create complete CPU-only B2 freeze; publication/readback remains mandatory."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
from execute import need,read,save,sha,utc
from deliver import public,archive_module


def prepare(root,work,source,main_proof,main_download,archive_source,out):
    need(not(work/'STATE.json').exists()and not(work/'ledger.jsonl').exists(),'No prior B2 native progress')
    need(read(main_proof)['statistical_replay']=='PASSED_COMPLETE_72_OPERATIONS','Main result delivery must finish first')
    download=read(main_download)
    need(download['anonymous']is True and download['status']=='COMPLETE_FILE_BYTES_MATCHED','Actual main public archive fetch required')
    need(read(work/'CPU_REUSE_COMPLETE.json')['original_32_cells_recomputed']is True,'Full numeric reuse')
    need(read(work/'EXECUTOR_CPU_CHECKED.json')['all_16_jobs_128_operations_checked']is True,'Prepared full executor')
    inherited=read(work/'INHERITED_ACCOUNTING.json')
    requests=rows=0
    for item in inherited['ledgers']:
        need(sha(item['path'])==item['sha256'],'Predecessor ledger changed; recompute real budget')
        for line in Path(item['path']).read_text().splitlines():
            x=json.loads(line)
            if x.get('event')=='RESERVE':requests+=x['requests'];rows+=x['rows']
    need((requests,rows)==(inherited['requests'],inherited['rows'])==(1909,3053954),'Independent8B cumulative ledger anchor')
    need(requests+128+8<=2048 and rows+33024+8*260<=8000000,'Whole B2 with eight charged-failure slots fits')
    plan=read(work/'PLAN.json');need(len(plan['workers'])==16 and plan['total_requests']==128,'Fixed original panel')
    files={}
    # Include complete host adapter/guard, all jobs, original-reuse records,
    # predecessor chains and actual binary/dependency identities before GPU.
    for base in (source,work/'runtime-exec-01'):
        for path in sorted(base.rglob('*')):
            if path.is_file()and '__pycache__'not in path.parts:files[str(path)]=sha(path)
    frozen={}
    for path in sorted(work.rglob('*')):
        if path.is_file()and '__pycache__'not in path.parts and 'runtime'not in path.parts:
            frozen[str(path)]=sha(path)
    for core in ('loop4','packed'):
        build=Path(plan['reuse']['builds'][core]['path'])
        for path in (build,build.parent/'DEPENDENCIES.json'):frozen[str(path)]=sha(path)
    original=root/'pr210-stage-b-source-05/run.py';frozen[str(original)]=sha(original)
    for path in (main_proof,main_download):frozen[str(path)]=sha(path)
    now=dt.datetime.now(dt.timezone.utc);end=now+dt.timedelta(days=7)
    # Current hardware, driver, ELF, modules and clock contract are unchanged.
    # The historical max is only a planning estimate. The actual per-worker
    # limit remains900s; whole scheduler is separately bounded to six hours.
    bound=16*(900+60);estimate=16*plan['old_full_caller_max_s']*1.5+120
    core=dict(schema='hs.B2.host-admission.v1',GPU_authorized=True,
        work_root=str(work),study_root=str(root),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        source_files=files,frozen_files=frozen,main_delivery_proof=str(main_proof),main_delivery_proof_sha256=sha(main_proof),
        runtime=str(work/'runtime-exec-01'),guard_script=str(work/'resource_guard.py'),
        native_parent_guard=read(work/'CURRENT_ALLOCATION_V2.private.json')['native_parent_guard'],
        allocation_file=str(work/'CURRENT_ALLOCATION_V2.private.json'),
        allocation_start_utc=now.isoformat(),allocation_end_utc=end.isoformat(),
        last_new_worker_utc=(end-dt.timedelta(seconds=2760)).isoformat(),whole_panel_bound_s=bound,
        whole_panel_planning_estimate_s=estimate,archive_bound_s=1800,scheduler_timeout_s=21600,
        budget=dict(initial_requests=requests,initial_rows=rows,panel_requests=128,panel_rows=33024,
                    requalification_requests=0,setup_GPU_requests=0,failure_reserve=8,
                    request_ceiling=2048,row_ceiling=8000000,remaining_after_complete_panel=11),
        execution_policy='Fixed16 processes/128operations; first error stops; no native retry; other-GPU work alone does not pause',
        GPU_scope='Previously authorized single UUID only; protected GPU0; explicit user B2 activation and unrestricted window',
        endpoint='Original native operation_s unchanged; no invented native absolute timestamps',
        estimate_basis='Same original ELF, driver, hardware, modules, target and8-operation fresh process. Historical maximum times1.5 plus120s is estimate only;900s native cap per worker and six-hour outer cap are enforced.',
        created_utc=utc())
    need(not out.exists(),'Fresh public freeze required');out.mkdir(parents=True)
    save(out.parent/'ADMISSION_CORE.private.json',core)
    public_core=out/'ADMISSION_CORE.json';public_core.write_text(public(json.dumps(core,indent=2,allow_nan=False)+'\n',root))
    for name,base in [('source',source),('runtime',work/'runtime-exec-01'),('prepared',work)]:
        for path in sorted(base.rglob('*')):
            if not path.is_file()or '__pycache__'in path.parts:continue
            if name=='prepared'and any(x.startswith('runtime')for x in path.relative_to(base).parts):continue
            target=out/name/path.relative_to(base);target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(public(path.read_text(),root))
    save(out/'DECISION.json',dict(activated_by_explicit_user=True,priority='After main32B delivery, before S3',
         main32B_public_download=download,B2_GPU_started=False,qualifications_reused=32,
         zero_new_GPU_qualification_after_full_saved_numeric_replay=True,
         scope='New epoch kept separate from originalB/C; no live-k7 inference'))
    selection=dict(schema='hs.strong.public-selection.v1',terminal_status='NOT_ADMITTED',files=[],private_literals=[str(root),str(Path.home())])
    for path in sorted(out.rglob('*')):
        if path.is_file():selection['files'].append(dict(path=str(path.relative_to(out)),sha256=sha(path),bytes=path.stat().st_size,
            payload_kind='utf8-text',public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS'))
    save(out.parent/'F0_SELECTION.private.json',selection)
    result=archive_module(archive_source).create(out,selection,out.parent/'B2_F0.tar.gz')
    save(out.parent/'B2_F0_ARCHIVE.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','work','source','main-proof','main-download','archive-source','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.root,a.work,a.source,a.main_proof,a.main_download,a.archive_source,a.out)))
