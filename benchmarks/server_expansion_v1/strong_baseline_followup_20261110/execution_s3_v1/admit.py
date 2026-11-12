"""CPU-only complete S3 F2 materialization. Never launches a GPU worker."""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent/'execution_v1'))
from support import need,read,sha,fresh
from public_text import transform
from ledger import Ledger
from host import relevant_environment,resource
from qualify import reference_services_pair
import archive


def storage_bound(roots,profile,old_manifest):
    # Exact dense_seq_f16_v1 writer:24 header bytes,12 per position,
    # 12 header bytes per layer per K/V stream, all active F16 K/V.
    layers=profile['layers'];per_token=12+sum(2*(x['k_elements']+x['v_elements'])for x in layers)
    header=24+24*len(layers);vocab_bytes=151936*4
    sequence=lambda n:header+n*per_token
    raw=0;details=[]
    for x in roots['inputs']:
        n=len(x['prompt_ids']);cap=128
        # Two R copies and three complete heavy candidate trajectories. Heavy
        # candidate frontiers are written both as sample and state frontier.
        states=sum(sequence(p)for p in range(n,n+cap));vectors=cap*vocab_bytes
        value=5*states+8*vectors+3*(sequence(n+cap-1)+vocab_bytes)
        #39 new-root clean qualification/calibration requests,288 formal;
        # one bounded terminal export per clean, with no per-step heavy state.
        clean_count=27  # per root24 formal +3bridge; slot0 has3 extra below
        value+=clean_count*(sequence(n+cap-1)+vocab_bytes)
        if x['slot']==0:value+=3*(sequence(n+cap-1)+vocab_bytes)
        raw+=value;details.append(dict(slot=x['slot'],prompt_tokens=n,cap=cap,worst_raw_bytes=value))
    for service in old_manifest['services']:
        n=len(service['input']['prompt_ids']);cap=service['input']['cap']
        raw+=3*(sum(sequence(p)+2*vocab_bytes for p in range(n,n+cap))+2*(sequence(n+cap-1)+vocab_bytes))
    # Trace/JSON/source allowance and public staging/archive copies are separate
    # from the single retained numeric payload copy; no historical deletion.
    trace=16*1024**3;public_staging=8*1024**3;safety=100*1024**3
    return dict(writer_profile='dense_seq_f16_v1',header_bytes=header,bytes_per_active_position=per_token,
        no_state_truncation=True,raw_numeric_single_copy_upper_bytes=raw,trace_allowance_bytes=trace,
        public_staging_archive_allowance_bytes=public_staging,safety_reserve_bytes=safety,
        required_free_bytes=raw+trace+public_staging+safety,per_root=details,
        formula='n active positions:24+24*layers+n*(12+sum2*(K+V)); all roots may reach cap128; natural EOG never padded')


def prepare(previous,main_work,cpu_work,study_root,out,source,b2_proof,guard_script):
    need(not out.exists(),'New complete F2 epoch only');out.mkdir(parents=True)
    c=read(previous);manifest=read(cpu_work/'prospective-01/MANIFEST.json');roots=read(cpu_work/'roots-01/ROOTS.json')
    need(read(b2_proof)['statistical_replay']=='PASSED_COMPLETE_128_OPERATIONS','Finish B2 delivery first')
    need(read(main_work/'RESULT_PUBLIC_REPLAY_PASS_02.json')['statistical_replay']=='PASSED_COMPLETE_72_OPERATIONS','Finish main32B delivery first')
    build=read(cpu_work/'model/BUILD.json');need(build['status']=='CPU_BUILT_NOT_GPU_QUALIFIED','New shared frontend CPU build missing')
    need(sha(build['executable'])==build['executable_sha256'],'New shared frontend binary changed')
    for obj in build['unchanged_numerical_objects']:need(sha(obj['path'])==obj['sha256'],'Qualified numerical object changed')
    source_build=source/'execution_s3_v1/build_service.py'
    need(sha(source_build)==sha(cpu_work/'source/execution_s3_v1/build_service.py'),'Changed native build source requires new compile')
    echoes=[];echo_env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
    echo_env.pop('HS_STRONG_GPU_ADMISSION_FILE',None)
    for arm in 'GBC':
        for kind in ('frontend-boundary-bridge','S3-formal-full-service'):
            worker=next(w for w in manifest['workers']if w.get('arm')==arm and w['kind']==kind)
            job=cpu_work/'prospective-01'/worker['job']
            result=subprocess.run([build['executable'],'--echo',str(job)],capture_output=True,text=True,env=echo_env,timeout=30)
            need(result.returncode==0,'New actual native configuration echo failed')
            actual=json.loads(result.stdout);need(actual['cuda_initialized']is False and actual['arm']==arm and
                actual['n_ctx']==1024 and actual['n_ubatch']==32 and actual['output_reserve']==32 and
                actual['planned_native_planner']=='SIMPLE'and actual['cuda_graphs']is False,'New actual native configuration differs')
            echoes.append(dict(worker=worker['worker_id'],job_sha256=sha(job),actual=actual,stdout=result.stdout,stderr=result.stderr))
    fresh(out/'ACTUAL_CPU_CONFIG_ECHO.json',dict(records=echoes,GPU_requests=0,native_backend_initialized=False))
    profile=read(c['state_profile']);need(sha(c['state_profile'])==c['state_profile_sha256'],'Original64-layer writer profile')
    old_manifest=read(c['manifest']);old_native=Path(c['output_root'])/'workers/R-services-0/native'
    old_repeat=Path(c['output_root'])/'workers/R-services-1/native'
    old_proof=reference_services_pair(old_repeat,old_native,old_manifest,profile)
    old_freeze=read(Path(c['output_root'])/'R_ORACLE_CONTENT_FREEZE.json')
    need(old_proof==old_freeze['services'],'Old scalar oracle bytes no longer match original freeze')
    fresh(out/'OLD_SCALAR_SERVICE_REUSE_CHECK.json',old_proof)
    # Verify the exact serializer size rule on independent original states.
    bound=storage_bound(roots,profile,old_manifest);checked=[]
    for service in old_manifest['services']:
        for p in (old_native/service['id']/'captures').glob('*/sequence.bin'):
            n=int(p.parent.name);need(p.stat().st_size==bound['header_bytes']+n*bound['bytes_per_active_position'],'Actual writer/storage bound changed')
            checked.append(dict(positions=n,bytes=p.stat().st_size,sha256=sha(p)))
    fresh(out/'STORAGE_BOUND.json',dict(bound,original_scalar_state_checks=checked))
    prefix=Path(c['ledger']).read_bytes();prefix_path=out/'ORIGINAL32B_S1_S2_PREFIX.jsonl'
    need(transform(prefix.decode(),study_root)==prefix.decode(),'Historical ledger cannot be silently privacy-rewritten')
    with prefix_path.open('xb')as f:f.write(prefix)
    from importlib.util import spec_from_file_location,module_from_spec
    # Explicit source path from the actual old configuration, not an assumed
    # parent layout of the compiled reuse cache.
    old_ledger_source=next(Path(p)for p in c['source_files']if p.endswith('/execution_v1/ledger.py'))
    spec=spec_from_file_location('_S3_predecessor_ledger',old_ledger_source);legacy=module_from_spec(spec);spec.loader.exec_module(legacy)
    prior=legacy.Ledger(c['ledger'],c['inheritance'],c['budget_approval']).snapshot()
    need((prior['requests'],prior['reserved_rows'])==(1373,677712),'Latest32B accounting changed; do not replace real totals')
    need(not any(v in ('RESERVE','START')for v in prior['operations'].values()),'Uncertain predecessor native outcome')
    approval=dict(authority='Explicit user autonomous expansion beyond256 and latest conditional S3 approval; exact F2 planned423 plus16failure slots',
        scope='S3',status='EXPLICITLY_APPROVED',request_ceiling=prior['requests']+439,row_ceiling=2000000,
        incremental_request_ceiling=prior['requests']+439-c['inheritance']['requests'],phase_request_ceiling=439,
        operation_prefix='s3-v1-',predecessor_prefix_bytes=len(prefix),predecessor_prefix_sha256=sha(prefix_path),
        predecessor_approval=c['budget_approval'],predecessor_requests=prior['requests'])
    inheritance=dict(c['inheritance'],approval_prefix_path=str(prefix_path))
    need(prior['reserved_rows']+manifest['planned_reserved_rows']+16*1024<=2000000,'Exact rows plus failure reserve exceed original row envelope')
    need(Ledger(c['ledger'],inheritance,approval).snapshot()['requests']==prior['requests'],'Same canonical journal extension proof')
    execution=out/'execution';execution.mkdir();phase_roots={x:str(execution/x)for x in ('S3_QUAL','S3')}
    for path in phase_roots.values():Path(path).mkdir()
    now=dt.datetime.now(dt.timezone.utc);end=now+dt.timedelta(days=7)
    config=dict(c,schema='hs.strong.S3-host-admission.v1',execution_root=str(execution),study_root=str(study_root),
        execution_phase='S3_QUAL',output_root=phase_roots['S3_QUAL'],phase_output_roots=phase_roots,
        manifest=str(cpu_work/'prospective-01/MANIFEST.json'),manifest_sha256=sha(cpu_work/'prospective-01/MANIFEST.json'),
        roots=str(cpu_work/'roots-01/ROOTS.json'),roots_sha256=sha(cpu_work/'roots-01/ROOTS.json'),
        predecessor_manifest=c['manifest'],old_R_native0=str(old_native),old_R_native1=str(old_repeat),
        S1_certificate=str(Path(c['output_root'])/'S1_CERTIFICATE.json'),S1_certificate_sha256=sha(Path(c['output_root'])/'S1_CERTIFICATE.json'),
        compiled_closure=str(cpu_work/'model/COMPILED_CLOSURE.private.json'),compiled_closure_sha256=sha(cpu_work/'model/COMPILED_CLOSURE.private.json'),
        executables=dict(c['executables'],model=dict(path=build['executable'],sha256=build['executable_sha256'])),
        inheritance=inheritance,budget_approval=approval,archive_bound_s=3600,worker_timeout_s=900,
        scheduler_timeout_s=216000,fixed_worker_gap_s=3,native_cpu_affinity='32,33',controller_cpu_affinity='36',
        allocation_start_utc=now.isoformat(),allocation_end_utc=end.isoformat(),
        last_new_worker_utc=(end-dt.timedelta(seconds=4560)).isoformat(),delivery_deadline_utc=end.isoformat(),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),parent_environment=relevant_environment(),
        disk_required_free_bytes=bound['required_free_bytes'],guard_script=str(guard_script),
        B2_public_delivery_proof=str(b2_proof),B2_public_delivery_proof_sha256=sha(b2_proof),
        source_files={str(p):sha(p)for p in source.rglob('*')if p.is_file()and'__pycache__'not in p.parts},
        F2_public_readback=None,F0_public_readback=None,GPU_authorized=True)
    for key in ('resume_configuration','completed_worker_reuse','S1_certificate_previous'):
        config.pop(key,None)
    frozen=[c['state_profile'],c['manifest'],cpu_work/'roots-01/ROOTS.json',cpu_work/'prospective-01/MANIFEST.json',
         cpu_work/'HISTORY_RECONCILIATION_01.json',out/'STORAGE_BOUND.json',out/'OLD_SCALAR_SERVICE_REUSE_CHECK.json',prefix_path,b2_proof,guard_script]
    frozen+=list((cpu_work/'prospective-01/jobs').glob('*.json'))
    config['frozen_files']={str(p):sha(p)for p in frozen}
    resource(config)
    fresh(out/'ADMISSION_CORE.private.json',config)
    allocation=dict(gpu_uuid=c['gpu_uuid'],ram_reserve_bytes=c['ram_reserve_bytes'],disk_reserve_bytes=bound['required_free_bytes'])
    fresh(execution/'CURRENT_ALLOCATION_V2.private.json',allocation)
    public=out/'public';public.mkdir()
    (public/'RESOURCE_GUARD_SOURCE.py').write_text(transform(guard_script.read_text(),study_root))
    (public/'ADMISSION_CORE.json').write_text(transform((out/'ADMISSION_CORE.private.json').read_text(),study_root))
    # The input records and complete jobs are explicit; raw prior private
    # captures are represented by verified commitments, never silently omitted.
    selections=[('source',source),('generated_frontend',cpu_work/'model/frontend'),('roots',cpu_work/'roots-01'),
                ('prospective',cpu_work/'prospective-01'),('licenses',cpu_work/'licenses-01')]
    for name,base in selections:
        for path in sorted(base.rglob('*')):
            if not path.is_file()or '__pycache__'in path.parts:continue
            target=public/name/path.relative_to(base);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(transform(path.read_text(),study_root))
    input_materials=public/'input_materials';input_materials.mkdir()
    pool_path=study_root/'strong-baseline-followup-20261110/sb217-s3-prep-20261110-01/input-prep-01/TOKENIZED_UNIVERSE.json'
    # Use the immutable pool registered by the completed history review; never
    # introduce a new universe or reselect roots after any model output.
    reconciliation=read(cpu_work/'HISTORY_RECONCILIATION_01.json')
    need(sha(pool_path)==reconciliation['pool_sha256'],'Complete registered input universe changed')
    material_paths=[pool_path,pool_path.parent/'SCAFFOLD.json',pool_path.parent/'STATEMENT_UNIVERSE.json',
        pool_path.parent.parent/'LOCAL_INCREMENTAL_EXPOSURE_01.json',
        study_root/'f-confirmation-bundle-01/confirmation_v1/EXPOSURE_REVIEW.json',
        study_root/'f-byte-audit-source-03/native/vocabulary.cpp',
        study_root/'f-vocabulary-build-03/BUILD.json',study_root/'f-vocabulary-build-03/DEPENDENCIES.json']
    input_index=[]
    for ordinal,path in enumerate(material_paths):
        name=str(ordinal)+'-'+path.name;text=path.read_text();(input_materials/name).write_text(transform(text,study_root))
        input_index.append(dict(file=name,original_sha256=sha(path),original_bytes=path.stat().st_size))
    exclusion=study_root/'f-confirmation-bundle-01/confirmation_v1/EXCLUSION_UNIVERSE.sha256.txt.gz'
    review=read(study_root/'f-confirmation-bundle-01/confirmation_v1/EXPOSURE_REVIEW.json')
    need(sha(exclusion)==review['compressed_sha256'],'Full inherited exposure exclusion bytes changed')
    (input_materials/'EXCLUSION_UNIVERSE.sha256.txt.gz.b64').write_text(base64.b64encode(exclusion.read_bytes()).decode()+'\n')
    fresh(input_materials/'INDEX.json',dict(text_files=input_index,exclusion_file='EXCLUSION_UNIVERSE.sha256.txt.gz.b64',
        exclusion_gzip_sha256=sha(exclusion),exclusion_gzip_bytes=exclusion.stat().st_size,
        scope='Complete674 input-only prompts/tokens/eligibility table and closed recoverable project exposure material; no generated selection output'))
    for path in [out/'STORAGE_BOUND.json',out/'OLD_SCALAR_SERVICE_REUSE_CHECK.json',out/'ACTUAL_CPU_CONFIG_ECHO.json',prefix_path,cpu_work/'model/BUILD.json',cpu_work/'HISTORY_RECONCILIATION_01.json']:
        (public/path.name).write_text(transform(path.read_text(),study_root))
    fresh(public/'DECISION.json',dict(activate_S3=True,reason='Explicit user requests full-service follow-up; S2 is only local exposed-cell mechanism evidence',
        independent_of_C_B_performance_sign=True,all_prior_S1_S2_B2_deliveries_complete=True,graphs_policy='off_only_unchanged',
        planned_requests=423,failure_reserve=16,phase_ceiling=439,global_request_ceiling=approval['request_ceiling'],
        original640_and_S1S2_1385_ceiling_history_preserved=True,new_S3_GPU_requests_started=0,
        formal_inputs_order_statistics_fixed_before_any_new_R_output=True,
        continuation='After this full F2 anonymous byte readback:24R/oracle freeze, all qualification, automatic final resource/cost/budget gates, then fixed288 formal requests. Any error stops without retry.'))
    selection=dict(schema='hs.strong.public-selection.v1',terminal_status='NOT_ADMITTED',files=[],private_literals=[str(study_root),str(Path.home())])
    for path in public.rglob('*'):
        if path.is_file():selection['files'].append(dict(path=str(path.relative_to(public)),bytes=path.stat().st_size,sha256=sha(path),payload_kind='utf8-text',public_review='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS'))
    fresh(out/'F2_SELECTION.private.json',selection);meta=archive.create(public,selection,out/'S3_F2.tar.gz');fresh(out/'S3_F2_ARCHIVE.json',meta)
    print(json.dumps(dict(status='S3_F2_CPU_PREPARED_NOT_PUBLIC_NOT_GPU_ADMITTED',**meta,global_request_ceiling=approval['request_ceiling'],planned_rows=manifest['planned_reserved_rows'],disk_required_free_bytes=bound['required_free_bytes'])))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('previous','main-work','cpu-work','study-root','out','source','b2-proof','guard-script'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prepare(a.previous,a.main_work,a.cpu_work,a.study_root,a.out,a.source,a.b2_proof,a.guard_script)
