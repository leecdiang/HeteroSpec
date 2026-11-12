"""Explicit source-epoch continuation; never retries an existing native slot.

Only the complete pristine R is reusable. Every failed candidate slot remains
charged and gets a new registered identity; no performance result is reused.
"""
import os
from pathlib import Path
import shutil
from host import verify_files
from ledger import Ledger
from support import need,read,sha
from terminal_guard import terminal_phase


def register_reference_reuse(plan,configuration,journal):
    c=read(configuration)
    with terminal_phase(c,{'S1_STOPPED'}):
        return _register_reference_reuse(plan,configuration,journal,c)


def _register_reference_reuse(plan,configuration,journal,c):
    root=Path(c['output_root'])
    if read(root/'STATE.json').get('reason')=='Unexpected draft/graph policy':
        return _register_reader_correction(plan,configuration,journal,c)
    need(read(root/'STATE.json')['status']=='S1_STOPPED','Only an explicitly stopped S1 may continue')
    need(c['execution_phase']=='S1'and c['ledger']==str(journal),'Same global journal required')
    prior=read(c['manifest']);ledger=Ledger(journal,c['inheritance'],c['budget_approval']).snapshot()
    old_workers={w['worker_id']:w for w in prior['workers']}
    reused={};failed=[]
    for worker in plan['workers']:
        name=worker['worker_id'];need(old_workers[name]==worker,'Qualification inputs/order changed')
        statuses=[ledger['operations'].get(op['operation_id'])for op in worker['operations']]
        if worker['kind'].startswith('pristine-model-'):
            need(all(s=='COMPLETE'for s in statuses),'Pristine R incomplete; no partial oracle reuse')
            directory=root/'workers'/name
            need(read(directory/'HOST.json')['status']=='COMPLETE','Reference worker failed')
            launch=read(directory/'LAUNCH.private.json')
            need(launch['executable_sha256']==c['executables']['R']['sha256'],'Original R executable binding')
            files={str(p):sha(p)for p in directory.rglob('*')if p.is_file()}
            need(not any(p.is_symlink()for p in directory.rglob('*')),'Reference payload links are not allowed')
            reused[name]=dict(directory=str(directory),files=files,original_worker=worker,
                              original_JOB=read(directory/'JOB.json'),reference_executable=c['executables']['R'])
        elif any(s is not None for s in statuses):
            need(worker['kind']=='candidate-model-geometry'and worker['arm']=='G'and
                 all(s=='FAILED'for s in statuses),'Unexpected prior candidate progress; audit instead of automatic retry')
            directory=root/'workers'/name
            need('Actual embedding device\n'in(directory/'stderr.log').read_text()and
                 not(directory/'native/CAPABILITY.json').exists(),
                 'This continuation only covers the recorded pre-forward CPU_Mapped ABI failure')
            failed.extend(op['operation_id']for op in worker['operations'])
            worker['worker_id']+='-e02'
            for op in worker['operations']:op['operation_id']+='-e02'
        else:need(all(s is None for s in statuses),'Mixed/uncertain reservation state')
    need(len(reused)==4 and len(failed)==4 and ledger['new_requests']==22,'Unexpected cumulative continuation state')
    budget=plan['budget'];need(c['budget_approval']['incremental_request_ceiling']==budget['new_request_ceiling']==871,
                              'Do not reset or silently expand the existing871-operation envelope')
    budget.update(prior_epoch_consumed_requests=22,reused_reference_requests=18,prior_failed_requests=4,
                  planned_fresh_requests=837,failure_closeout_reserve=12,
                  failure_reserve_original=16,failure_reserve_consumed=4)
    failed_rows=sum(e['reserved_rows']for e in ledger['events']if e['kind']=='RESERVE'and e['operation_id']in failed)
    budget['prior_failed_reserved_rows']=failed_rows
    budget['new_reserved_rows']=sum(op['reserved_rows']for w in plan['workers']for op in w['operations'])+failed_rows+12*1024
    budget['cumulative_reserved_rows']=budget['inherited_rows']+budget['new_reserved_rows']
    plan['reference_reuse']=reused
    plan['continuation']=dict(prior_configuration=str(configuration),prior_configuration_sha256=sha(configuration),
          global_journal_sha256=sha(journal),global_requests_at_freeze=ledger['requests'],
          global_reserved_rows_at_freeze=ledger['reserved_rows'],failed_operations_retained=failed,
          reason='CPU_Mapped host buffer has no owning ggml device; correct capability adapter and rerun all candidate qualification',
          original_R_and_reference_inputs_unchanged=True,no_native_performance_output_exists=True)


def reuse_reference(host,worker,job):
    entry=host.manifest['reference_reuse'][worker['worker_id']]
    need(entry['original_worker']==worker and entry['original_JOB']==job,'Exact original R input/worker binding')
    need(entry['reference_executable']==host.c['executables']['R'],'Pristine R changed')
    ledger=host.ledger.snapshot()
    need(all(ledger['operations'].get(op['operation_id'])=='COMPLETE'for op in worker['operations']),
         'No credit for incomplete original R')
    verify_files(entry['files'])
    output=host.root/'workers'/worker['worker_id']
    need(not output.exists(),'Never overwrite a reused reference view')
    # Immutable raw bytes are hard-linked into the new archive namespace, while
    # original paths and accounting remain intact. No model request is made.
    shutil.copytree(entry['directory'],output,copy_function=os.link)
    return output


def _register_reader_correction(plan,configuration,journal,c):
    """All native bytes/inputs unchanged: recompute every saved comparison."""
    need(c['execution_phase']=='S1'and c['ledger']==str(journal),'Same single cumulative journal')
    verify_files(c['source_files']);verify_files(read(c['compiled_closure'])['files'])
    prior=read(c['manifest']);ledger=Ledger(journal,c['inheritance'],c['budget_approval']).snapshot()
    def normalized(worker):
        import copy
        value=copy.deepcopy(worker)
        value['worker_id']=value['worker_id'].removesuffix('-e02')
        for op in value['operations']:op['operation_id']=op['operation_id'].removesuffix('-e02')
        return value
    need([normalized(w)for w in plan['workers']]==[normalized(w)for w in prior['workers']],
         'Reader correction cannot change numerical inputs, operation kinds or order')
    plan['workers']=prior['workers'];reused={};completed=0
    for worker in plan['workers']:
        statuses=[ledger['operations'].get(op['operation_id'])for op in worker['operations']]
        if all(s is None for s in statuses):continue
        need(all(s=='COMPLETE'for s in statuses),'Incomplete/uncertain native slot: no implicit retry')
        directory=Path(c['output_root'])/'workers'/worker['worker_id']
        need(read(directory/'HOST.json')['status']=='COMPLETE'and read(directory/'WORKER.json')==worker,
             'Saved completed worker binding differs')
        need(not any(p.is_symlink()for p in directory.rglob('*')),'No linked-path alias in reusable evidence')
        executable=read(directory/'LAUNCH.private.json')['executable_sha256']
        need(executable in {x['sha256']for x in c['executables'].values()},'Saved native executable differs')
        files={str(p):sha(p)for p in directory.rglob('*')if p.is_file()}
        reused[worker['worker_id']]=dict(directory=str(directory),files=files,original_worker=worker,
             original_JOB=read(directory/'JOB.json'),executables=c['executables'],
             scope='Saved complete native output; every numerical/physical/service comparison rerun by corrected reader')
        completed+=len(worker['operations'])
    need(len(reused)==208 and completed==714 and ledger['new_requests']==718,
         'Unexpected progress for this explicitly audited reader correction')
    need(c['budget_approval']['incremental_request_ceiling']==871,'Do not change the global envelope')
    plan['budget'].update(prior_epoch_consumed_requests=718,reused_completed_requests=714,
         reused_reference_requests=18,prior_failed_requests=4,planned_fresh_requests=141,
         failure_closeout_reserve=12,failure_reserve_original=16,failure_reserve_consumed=4,
         prior_failed_reserved_rows=1288,new_reserved_rows=37974,cumulative_reserved_rows=690000)
    plan['completed_worker_reuse']=reused
    plan['continuation']=dict(kind='OFFLINE_READER_CORRECTION_UNCHANGED_NATIVE_AND_INPUTS',
         prior_configuration=str(configuration),prior_configuration_sha256=sha(configuration),
         global_journal_sha256=sha(journal),global_requests_at_freeze=ledger['requests'],
         global_reserved_rows_at_freeze=ledger['reserved_rows'],prior_stop='Unexpected draft/graph policy',
         reason='hsc host graph cache reuse is not CUDA graph replay; actual env-controlled off-only policy is unchanged',
         original_R_and_reference_inputs_unchanged=True,native_code_and_ELFs_unchanged=True,
         recheck='All complete saved outputs are compared again; no numerical/physical/clean gate omitted')


def _job_identity(job):
    """Only verified operand file locations may differ in a new archive view."""
    import copy
    value=copy.deepcopy(job)
    def visit(node):
        if isinstance(node,dict):
            for key,hashkey in (('activation_file','activation_sha256'),('weight_file','weight_sha256')):
                if key in node:
                    need(hashkey in node and sha(node[key])==node[hashkey],'Reused operand file identity changed')
                    node[key]={'verified_bytes_sha256':node[hashkey]}
            for item in node.values():visit(item)
        elif isinstance(node,list):
            for item in node:visit(item)
    visit(value);return value


def reuse_completed_worker(host,worker,job):
    entry=host.manifest['completed_worker_reuse'][worker['worker_id']]
    need(entry['original_worker']==worker and _job_identity(entry['original_JOB'])==_job_identity(job),
         'Reused native semantic request differs')
    need(entry['executables']==host.c['executables'],'Reader-only continuation must retain exact native ELFs/paths')
    need(all(host.ledger.snapshot()['operations'].get(op['operation_id'])=='COMPLETE'for op in worker['operations']),
         'No reuse of incomplete native slots')
    verify_files(entry['files']);output=host.root/'workers'/worker['worker_id']
    need(not output.exists(),'Never overwrite a prior worker view')
    shutil.copytree(entry['directory'],output,copy_function=os.link)
    return output
