"""Run finite operator replays with the same GPU lock, Job and cumulative ledger."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser()
    for name in ('repo', 'bundle', 'manifest', 'build'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--name', required=True)
    a = p.parse_args()
    sys.path.insert(0, str(a.repo/'scripts/experiments/rtx_llama_repair_v1'))
    import host
    import parent
    from lr_common import read, save, file_hash, need, utc, confined
    cfg = host.check_epoch(a.bundle)
    _, run, _ = parent.load(cfg['parent_snapshot'])
    manifest, build = read(a.manifest), read(a.build)
    count = 2*len(manifest['cases'])
    need(0 < count <= 512, 'finite operator reservation')
    research = Path(cfg['research_root'])
    ledger = research/'LEDGER.jsonl'
    used, spent = run.resource_totals(ledger)
    limits = host.budget_current(research)
    dev = sum(x.get('reserved_requests', 0) for x in map(json.loads, ledger.read_text().splitlines())
              if x['event']=='START' and x['stage']=='development')
    need(used+count <= limits['request_credits'] and dev+count <= limits['development_credits'], 'shared work-credit reservation')
    need(spent < limits['total_native_seconds'], 'shared time reservation')
    exe = Path(build['executable'])
    need(file_hash(exe)==build['executable_sha256'] and file_hash(build['source'])==build['source_sha256'], 'operator source/executable identity')
    for name, h in build['numerical_modules'].items():
        need(file_hash(exe.parent/name)==h, 'operator DLL cohort')
    for case in manifest['cases']:
        for item in case['inputs']:
            need(file_hash(item['file'])==item['sha256'], 'operator input changed')
        if case.get('expected_file'):
            need(file_hash(case['expected_file'])==case['expected_sha256'], 'own-path expectation changed')
    Job, ram = run.windows_helpers(cfg['repo'])
    need(ram() >= cfg['resources']['min_ram_free_bytes'], 'RAM reservation')
    need(shutil.disk_usage(a.bundle).free >= cfg['resources']['min_disk_free_bytes'], 'disk reservation')
    gpu = subprocess.check_output(['nvidia-smi','--query-gpu=uuid,driver_version,memory.free','--format=csv,noheader,nounits'],text=True,timeout=30)
    rows = [r.split(',') for r in gpu.splitlines() if cfg['gpu_uuid'] in r]
    need(len(rows)==1 and rows[0][1].strip()==cfg['gpu_driver'], 'GPU identity')
    need(int(rows[0][2])*1024**2 >= cfg['resources']['min_vram_free_bytes'], 'VRAM reservation')
    unit = confined(a.bundle/'units', a.name)
    need(not unit.exists(), 'fresh replay unit')
    unit.mkdir(parents=True)
    save(unit/'MANIFEST.json', manifest)
    save(unit/'BUILD.json', build)
    lock = Path(cfg['gpu_lock_file'])
    save(lock, {'pid':os.getpid(), 'epoch':str(a.bundle), 'unit':a.name, 'utc':utc()}, exclusive=True)
    argv = [str(exe),str(unit/'MANIFEST.json'),str(unit/'native'),str(exe.parent)]
    run.append(ledger, {'event':'START','utc':utc(),'epoch':str(a.bundle),'unit':a.name,'stage':'development',
                        'reserved_requests':count,'model_requests':0,'operator_replays':count,'argv':argv,
                        'manifest_sha256':file_hash(a.manifest),'helper_exe_sha256':file_hash(exe)})
    proc = job = None
    active = None
    success, error, completed = False, None, 0
    started = time.monotonic()
    try:
        env = {k:v for k,v in os.environ.items() if not k.startswith(('HS_','HSC_','JSA_','GGML_'))}
        env['CUDA_VISIBLE_DEVICES'] = cfg['gpu_uuid']
        with (unit/'stderr.log').open('x') as err:
            proc = subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,
                                    encoding='utf-8',env=env,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
            job = Job(proc)
            output, _ = proc.communicate('RUN\n',timeout=min(300,limits['worker_timeout_seconds'],limits['total_native_seconds']-spent))
            (unit/'stdout.log').write_text(output)
            need(proc.returncode==0, 'operator helper failed')
            result = read(unit/'native/RESULT.json')
            need(result['status']=='COMPLETE' and result['normal_cleanup_returned'] and result['operator_replays']==count, 'incomplete replay')
            for module in result['modules']:
                path = Path(module)
                if path.name in build['numerical_modules']:
                    need(path.resolve()==(exe.parent/path.name).resolve() and file_hash(path)==build['numerical_modules'][path.name], 'loaded operator DLL drift')
            completed = count
            active = job.wait_empty(timeout=10)
            need(active==0, 'operator Job cleanup')
            success = True
    except BaseException as exc:
        error = repr(exc)
        if job: job.terminate()
        elif proc and proc.poll() is None: proc.kill()
        if proc: proc.wait(timeout=30)
        if job: active=job.wait_empty(timeout=10)
        raise
    finally:
        if job: job.close()
        if proc is None or active==0: lock.unlink(missing_ok=True)
        receipt = {'event':'END','utc':utc(),'epoch':str(a.bundle),'unit':a.name,'seconds':time.monotonic()-started,
                   'success':success,'error':error,'completed_requests':0,'completed_operator_replays':completed,
                   'active_processes_after_wait':active,'lock_retained':lock.exists()}
        save(unit/'RECEIPT.json',receipt)
        run.append(ledger,receipt)
    print('OPERATOR_EXECUTION_COMPLETE_NOT_YET_AUDITED', completed)


if __name__ == '__main__':
    main()
