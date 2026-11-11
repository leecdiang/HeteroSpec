"""Run a fixed original-entry preparation plan on an explicitly allocated GPU."""
import argparse
import csv
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
sys.dont_write_bytecode = True
from protocol import DRAFT_SHA, HOST_RUNNER_SHA, TARGET_SHA, digest, identity, make_plan, write_new
from verify_production import verify_directory, verify_job


def load_host(public_root):
    path = public_root/'matched_cost/run_probe.py'
    if digest(path) != HOST_RUNNER_SHA:
        raise ValueError('PR221 host admission dependency changed')
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('pinned_pr221_host', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def numerical_modules(paths, expected):
    observed = {}
    for value in paths:
        path = Path(value)
        if path.name.startswith(('libllama', 'libggml')) and '.so' in path.name:
            path = path.resolve()
            if not path.is_file():
                raise ValueError('Actual numerical module cannot be read')
            observed[str(path)] = identity(path)
    if observed != expected:
        raise ValueError('Actual loaded numerical modules differ from the frozen build')
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, default=Path(__file__).with_name('INPUTS.json'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--build', type=Path)
    parser.add_argument('--public-root', type=Path)
    parser.add_argument('--target-model', type=Path)
    parser.add_argument('--draft-model', type=Path)
    parser.add_argument('--gpu-index', type=int)
    parser.add_argument('--experiment-commit')
    args = parser.parse_args()
    inputs = json.loads(args.inputs.read_text()); plan = make_plan(inputs)
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    write_new(out/'INPUTS.json', inputs); write_new(out/'PLAN.json', plan)
    run = {'schema': 'heterospec.original-entry-preparation-run.v1', 'status': 'PLAN_ONLY',
           'run_id': uuid.uuid4().hex, 'started_utc': datetime.now(timezone.utc).isoformat(),
           'plan_identity': identity(out/'PLAN.json'), 'inputs_identity': identity(out/'INPUTS.json'),
           'performance_admitted': False, 'completed': [], 'attempted_processes': 0,
           'historical_R_bridge': 'OPEN', 'clean_full_vector_state_bridge': 'OPEN'}
    def save():
        temporary = out/'RUN.json.tmp'; temporary.write_text(json.dumps(run, indent=2)+'\n'); temporary.replace(out/'RUN.json')
    save()
    if not args.execute:
        print(json.dumps({'status': 'PLAN_ONLY', 'model_loads': 0, 'plan': plan}, indent=2)); return
    try:
        if any(value is None for value in [args.build,args.public_root,args.target_model,args.draft_model,args.gpu_index,args.experiment_commit]):
            raise ValueError('Execution requires explicit build, public source, both real models, allocated GPU and committed source')
        if not re.fullmatch(r'[0-9a-f]{40}', args.experiment_commit):
            raise ValueError('A full committed experiment identity is required')
        public = args.public_root.resolve(); host = load_host(public)
        git = host.git_identity(public)
        if git.get('HEAD') != args.experiment_commit or git.get('status') != 'CLEAN_COMMITTED_SUBTREE':
            raise ValueError('Experiment commit must match a clean tracked checkout')
        if Path(__file__).resolve().parent != public/'production_compare':
            raise ValueError('Execute the committed production_compare module in the declared public checkout')
        module=Path(__file__).resolve().parent
        required=[path for path in module.iterdir() if path.suffix in {'.py','.cpp'} or path.name=='INPUTS.json']
        source_before={path.name:identity(path) for path in required}
        repository=Path(git['repo'])
        relative=[str(path.relative_to(repository)) for path in required]
        tracked=subprocess.run(['git','-C',str(repository),'ls-files','--',*relative],capture_output=True,text=True,check=True).stdout.splitlines()
        if sorted(tracked)!=sorted(relative):
            raise ValueError('All production_compare execution sources and frozen inputs must be committed')
        build_dir = args.build.resolve(); build = json.loads((build_dir/'BUILD.json').read_text())
        if build['status'] != 'BUILT_NOT_EXECUTED_NOT_QUALIFIED':
            raise ValueError('Incomplete or unknown build')
        if build['audit_source'] != identity(Path(__file__).with_name('request_audit.cpp')) or build['build_source'] != identity(Path(__file__).with_name('build_production.py')):
            raise ValueError('Built sources differ from the committed module')
        for name, expected in build['outputs'].items():
            if identity(build_dir/name) != expected:
                raise ValueError('Compiled binary changed: '+name)
        for path, expected in build['numerical_libraries'].items():
            if identity(path) != expected:
                raise ValueError('Numerical library changed')
        lib_dir = Path(build['lib_dir'])
        if not (lib_dir/'libggml-cuda.so').is_file():
            raise ValueError('CPU link checks are not executable CUDA qualification builds')
        for role, path, expected in [('target',args.target_model,TARGET_SHA),('draft',args.draft_model,DRAFT_SHA)]:
            if digest(path) != expected:
                raise ValueError('Authenticated real model required: '+role)
        models = {role: {'path': str(path.resolve()), **identity(path)} for role,path in [('target',args.target_model),('draft',args.draft_model)]}
        if shutil.disk_usage(out).free < plan['capture_storage_ceiling']['minimum_free_disk_bytes']:
            raise ValueError('Insufficient disk for structure-bounded full captures')
        smi = shutil.which('nvidia-smi')
        if not smi:
            raise RuntimeError('UNAVAILABLE: no GPU execution interface')
        inventory = subprocess.run([smi,'--query-gpu=index,pci.bus_id,mig.mode.current','--format=csv,noheader'], capture_output=True,text=True,check=True,timeout=15)
        physical = host.physical_gpu_binding(inventory.stdout,args.gpu_index)
        env = host.clean_environment(lib_dir,'cuda',physical['CUDA_PCI_order_ordinal'])
        env['GGML_BACKEND_PATH'] = str((lib_dir/'libggml-cuda.so').resolve())
        env.pop('HETEROSPEC_PAIR_AUDIT',None)
        visible = host.verify_cuda_visible_device(physical['pci_bus_id'],env)
        run.update(status='PREPARED_BEFORE_FIRST_NATIVE_PROCESS', git=git, experiment_commit=args.experiment_commit,
                   build_identity=identity(build_dir/'BUILD.json'), build=build, models=models,
                   GPU_binding={'physical':physical,'visible':visible}, host_dependency_sha256=HOST_RUNNER_SHA,
                   sources=source_before, committed_production_files=relative)
        (out/'GPU_INVENTORY.stdout').write_text(inventory.stdout)
        for planned in plan['jobs']:
            name = planned['name']; job_dir=out/'jobs'/name; job_dir.mkdir(parents=True)
            job = {'target_model':models['target']['path'],'draft_model':models['draft']['path'],
                   'target_sha256':TARGET_SHA,'draft_sha256':DRAFT_SHA,'n_ctx':1024,'threads':2,
                   'k':7,'draft':True,'draft_width':4,'lowering':'LOCAL','residency':'matched','profile':False,
                   'target_output_reserve':8,'proposal_mode':'live','experiment_run_id':run['run_id'],
                   'process_name':name,'inputs':[
                       {'name':f'{case["name"]}-{run["run_id"]}-{name}',
                        'capture':planned['capture'],'input':{'prompt_ids':case['prompt_ids'],'cap':16}}
                       for case in inputs['inputs']]}
            write_new(job_dir/'JOB.json',job)
            if planned['capture']:
                write_new(job_dir/'AUDIT_CONFIG.json',{'job_path':str(job_dir/'JOB.json'),'job_sha256':digest(job_dir/'JOB.json'),
                    'output_path':str(job_dir/'native'),'storage':plan['capture_storage_ceiling']})
        save()
        for index, planned in enumerate(plan['jobs']):
            name=planned['name']; job_dir=out/'jobs'/name; native=job_dir/'native'
            apps=subprocess.run([smi,'-i',str(args.gpu_index),'--query-compute-apps=pid','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15)
            (job_dir/'GPU_APPS.stdout').write_text(apps.stdout)
            if apps.stdout.strip():
                raise ValueError('Allocated GPU has an existing compute process; no job launched')
            device=subprocess.run([smi,'-i',str(args.gpu_index),'--query-gpu=index,name,driver_version,memory.free,memory.total,pci.bus_id','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15)
            (job_dir/'GPU_DEVICE.stdout').write_text(device.stdout)
            rows=list(csv.reader(device.stdout.splitlines()))
            if len(rows)!=1 or len(rows[0])!=6 or int(rows[0][0])!=args.gpu_index or host.pci_address(rows[0][5].strip())!=host.pci_address(physical['pci_bus_id']):
                raise ValueError('Allocated GPU inventory changed')
            if int(rows[0][3])*1024**2 < models['target']['bytes']+models['draft']['bytes']+1024**3:
                raise ValueError('Free VRAM below both weight files plus the declared 1GiB admission margin')
            host.verify_cuda_visible_device(physical['pci_bus_id'],env)
            for path, expected in build['numerical_libraries'].items():
                if identity(path) != expected:
                    raise ValueError('Numerical library changed before launch')
            executable=build_dir/planned['binary']
            if identity(executable)!=build['outputs'][planned['binary']]:
                raise ValueError('Executable changed before launch')
            child_env=dict(env)
            if planned['capture']:
                child_env['HETEROSPEC_PAIR_AUDIT']=str(job_dir/'AUDIT_CONFIG.json')
            run['attempted_processes']+=1;run['status']='RUNNING_OR_PARTIAL';save()
            process=host.run_owned_native([str(executable),str(job_dir/'JOB.json'),str(native)],job_dir/'process',child_env,
                                          timeout=plan['process_seconds'])
            write_new(job_dir/'PROCESS.json',process)
            if process['returncode']!=0 or process.get('timed_out') or not process.get('child_reaped'):
                raise RuntimeError('Native process failed or timed out; partial raw output retained; no later job')
            result=json.loads((native/'result.json').read_text())
            files={str(path.relative_to(native)):identity(path) for path in native.rglob('*') if path.is_file()}
            maximum=plan['capture_storage_ceiling']['all_capture_bytes_per_process'] if planned['capture'] else 64*1024**2
            if sum(value['bytes'] for value in files.values())>maximum:
                raise ValueError('Raw output exceeded declared structure-based storage ceiling')
            record={'name':name,'run_id':run['run_id'],'binary':planned['binary'],'binary_identity':identity(executable),
                    'job_file':str((job_dir/'JOB.json').relative_to(out)),'job_identity':identity(job_dir/'JOB.json'),
                    'output_dir':str(native.relative_to(out)),'native_files':files,'process':process,
                    'loaded_numerical_modules_before':numerical_modules(result['modules_before'],build['numerical_libraries']),
                    'loaded_numerical_modules_after':numerical_modules(result['modules_after'],build['numerical_libraries'])}
            verify_job(out,record,planned,inputs['inputs'])
            run['completed'].append(record)
            if index==1:
                run['status']='CAPTURE_COMPLETE_PENDING_COMPARISON';save()
                write_new(out/'CAPTURE_CHECK.json',verify_directory(out))
            save()
        for role, path in [('target',args.target_model),('draft',args.draft_model)]:
            if identity(path)!={key:models[role][key] for key in ('bytes','sha256')}:
                raise ValueError('Model changed during the plan')
        if source_before != {path.name:identity(path) for path in required} or host.git_identity(public)!=git:
            raise ValueError('Committed source/subtree identity changed during execution')
        run['status']='COMPLETE_PREPARATION_NOT_PERFORMANCE_ADMITTED';save()
        write_new(out/'OFFLINE_CHECK.json',verify_directory(out))
        print(json.dumps({'status':run['status'],'performance_admitted':False,'requests':12},indent=2))
    except Exception as error:
        run.update(status='FAILED_OR_OPEN_PARTIAL_NOT_ADMITTED',error=str(error));save();raise


if __name__=='__main__':
    main()
