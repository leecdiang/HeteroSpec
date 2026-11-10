"""CPU-only admission materialization after real immutable public byte readback."""
import argparse
import datetime as dt
import subprocess
from pathlib import Path
from host import resource,utc,verify_public_readback,relevant_environment
from support import fresh,need,read,sha


def admit(root,source,cpu,public,proof_path,authority_path,out):
    authority=read(authority_path)
    need(authority['GPU_allocation_confirmed']is True and authority['S1_S2_budget_extension_authorized']is True,
         'Missing user allocation/budget authority')
    need(authority['time_window_unlimited']is True,'Register the actual finite user window instead')
    proof=read(proof_path);verify_public_readback(proof)
    need(read(cpu/'STATE.json')['status']=='CPU_IMPLEMENTATIONS_BUILT_F0_S1_NOT_ADMITTED','CPU gate incomplete')
    source_files={str(p):sha(p)for p in source.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
    for p,digest in source_files.items():
        relative=Path(p).relative_to(source);need(sha(public/relative)==digest,'Executed source differs from publicly frozen bytes')
    manifest=cpu/'prospective/MANIFEST.json';m=read(manifest);budget=m['budget']
    from freeze_cpu import public_text
    need((public/'F0_DATA/MANIFEST.json').read_text()==public_text(manifest.read_text(),root),
         'Frozen complete manifest differs from the declared exact path-prefix transform')
    old=root/'q32-q4-full-20261109-01';ledger=old/'ledger.jsonl'
    need(sha(ledger)==budget['inherited_ledger_sha256'],'Live inherited consumption changed')
    executables={}
    for role,folder,filename in [('operand','backend','operand-worker'),('gold','gold','gold-worker'),('model','model','model-worker')]:
        build=read(cpu/folder/'BUILD.json');path=cpu/folder/filename
        need(sha(path)==build['executable_sha256'],'Compiled artifact identity')
        executables[role]=dict(path=str(path),sha256=sha(path))
    reference=read(root/'run-01/build-R-01/BUILD.json')
    need(reference['reference_source_is_pristine']is True and sha(reference['executable'])==reference['executable_sha256'],'Unchanged pristine R')
    executables['R']=dict(path=reference['executable'],sha256=reference['executable_sha256'])
    need(read(cpu/'PARENT_GUARD_ZERO_GPU_PROOF.json')['status']=='PASSED','Supervisor-loss zero-GPU heartbeat gate')
    executables['guard']=dict(path=str(cpu/'parent-guard'),sha256=sha(cpu/'parent-guard'))
    out.mkdir(parents=True,exist_ok=True)
    start=dt.datetime.now(dt.timezone.utc);end=start+dt.timedelta(days=7)
    namespace=root/'strong-baseline-followup-20261110'
    device_lines=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid','--format=csv,noheader'],text=True).splitlines()
    indices=[int(line.split(',')[0])for line in device_lines if line.split(',')[1].strip()==authority['gpu_uuid']]
    need(len(indices)==1 and indices[0]!=0,'Assigned UUID missing or now on protected GPU0')
    global_ledger=namespace/'PR217_GLOBAL_LEDGER.jsonl'
    if m.get('reference_reuse'):
        need(sha(global_ledger)==m['continuation']['global_journal_sha256'],'Global consumption changed after continuation registration')
    else:need(not global_ledger.exists()or global_ledger.stat().st_size==0,'Existing PR217 journal: audit before admitting another S1')
    configuration=dict(schema='hs.strong.host-admission.v1',execution_phase='S1',GPU_authorized=True,
          authority_file_sha256=sha(authority_path),gpu_uuid=authority['gpu_uuid'],
          gpu_index=indices[0],parent_environment=relevant_environment(),
          boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
          output_root=str(out/'S1'),manifest=str(manifest),manifest_sha256=sha(manifest),source_files=source_files,
          compiled_closure=str(cpu/'COMPILED_CLOSURE.private.json'),compiled_closure_sha256=sha(cpu/'COMPILED_CLOSURE.private.json'),
          descriptor_inventory=str(cpu/'prospective/DESCRIPTOR_INVENTORY.json'),
          model=dict(path=str(root/'q32-models-01/Qwen3-32B-Q4_K_M.gguf'),**m['model']),
          executables=executables,state_profile=str(old/'STATE_PROFILE.json'),state_profile_sha256=sha(old/'STATE_PROFILE.json'),
          F0_public_readback=proof,ledger=str(global_ledger),
          inheritance=dict(ledger_path=str(ledger),ledger_sha256=sha(ledger),requests=budget['inherited_requests'],reserved_rows=budget['inherited_rows']),
          budget_approval=dict(scope='S1+S2',status='EXPLICITLY_APPROVED',request_ceiling=budget['cumulative_request_ceiling'],
              row_ceiling=budget['row_ceiling'],incremental_request_ceiling=budget['new_request_ceiling'],
              authority='User explicitly approved autonomous expansion beyond 256; exact current F0 manifest plus 16 failure/closeout slots'),
          allocation_start_utc=start.isoformat(),allocation_end_utc=end.isoformat(),
          last_new_worker_utc=(end-dt.timedelta(seconds=960)).isoformat(),delivery_deadline_utc=(end+dt.timedelta(hours=6)).isoformat(),
          window_note='User gave no time limit; this runner still has a finite seven-day safety window and 900-second worker bounds',
          worker_timeout_s=900,native_cpu_affinity='32,33',fixed_worker_gap_s=3,
          gpu_reserve_bytes=1024**3,ram_reserve_bytes=4*1024**3,disk_required_free_bytes=185*1024**3,
          disk_formula='100 GiB reserve + 40 GiB conservative registered raw bound + 40 GiB staging duplication + 5 GiB text archive',
          max_idle_gpu_memory_bytes=128*1024**2,max_host_load_fraction=.8,
          S1_cost_calibration='First registered worker of each class is also its bounded development caller-cost observation; no added free requests',
          automatic_native_retry=False,S2='Requires complete S1 certificate and separate F1 full public readback',
          B2='Second priority; independent 8B ledger/window/freeze, never consumes this budget',
          S3='Conditionally user authorized; separate new-root/source/budget admission before execution')
    Path(configuration['output_root']).mkdir(parents=True,exist_ok=True)
    preflight=resource(configuration);fresh(out/'RESOURCE_ADMISSION.private.json',preflight)
    fresh(out/'ADMISSION_S1.private.json',configuration)
    fresh(out/'ADMISSION_STATUS.json',dict(status='S1_ADMITTED',registered_utc=utc(),
          native_model_requests_started=0,phase='S1',manifest_sha256=sha(manifest),F0_commit=proof['commit'],
          planned_main_operations=budget['planned_logical_operations'],main_incremental_ceiling=budget['new_request_ceiling'],
          cumulative_main_ceiling=budget['cumulative_request_ceiling'],formal_S2='NOT_STARTED'))


def main():
    p=argparse.ArgumentParser()
    for name in ('root','source','cpu','public','proof','authority','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();admit(a.root,a.source,a.cpu,a.public,a.proof,a.authority,a.out)


if __name__=='__main__':main()
