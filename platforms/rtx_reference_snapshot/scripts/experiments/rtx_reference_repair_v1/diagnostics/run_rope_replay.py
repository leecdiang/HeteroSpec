import pathlib,sys,os,subprocess,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from common import *
import run
bundle=Path(sys.argv[1]);manifest=Path(sys.argv[2]);build=read(sys.argv[3]);name='rope_replay01';unit=bundle/'units'/name;cfg=run.check_epoch(bundle);research=Path(cfg['research_root']);ledger=research/'LEDGER.jsonl';used,spent=run.resource_totals(ledger)
need(used+8<=1200 and spent<cfg['resources']['total_native_seconds'],'shared budget')
dev=sum(x.get('reserved_requests',0) for x in map(__import__('json').loads,ledger.read_text().splitlines()) if x['event']=='START' and x['stage']=='development');need(dev+8<=480,'development budget')
exe=Path(build['executable']);need(file_hash(exe)==build['executable_sha256'],'helper identity');need(file_hash(build['source'])==build['source_sha256'],'helper source changed')
for n,h in build['numerical_modules'].items():need(file_hash(exe.parent/n)==h,'numerical DLL changed')
m=read(manifest)
for x in m['operands']:
    need(file_hash(x['input_file'])==x['input_sha256'] and file_hash(x['expected_file'])==x['expected_sha256'],'operand bytes changed')
Job,ram=run.windows_helpers(cfg['repo']);need(ram()>=cfg['resources']['min_ram_free_bytes'],'RAM reserve');need(not unit.exists(),'fresh replay unit')
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,driver_version,memory.free','--format=csv,noheader,nounits'],text=True,timeout=30);need(cfg['gpu_uuid'] in gpu and cfg['gpu_driver'] in gpu,'GPU identity');need(int(gpu.strip().split(',')[-1])*1024**2>=cfg['resources']['min_vram_free_bytes'],'VRAM reserve')
lock=Path(cfg['gpu_lock_file']);save(lock,{'epoch':str(bundle),'unit':name,'pid':os.getpid(),'utc':utc()},exclusive=True);unit.mkdir(parents=True);argv=[str(exe),str(manifest),str(unit/'native'),str(exe.parent)];p=job=None;active=None;success=False;error=None;start=time.monotonic();count=0
append(ledger,{'event':'START','utc':utc(),'epoch':str(bundle),'unit':name,'stage':'development','reserved_requests':8,'model_requests':0,'operator_replays':8,'argv':argv,'manifest_sha256':file_hash(manifest),'helper_exe_sha256':file_hash(exe)})
try:
    env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','HSC_','JSA_','GGML_'))};env['CUDA_VISIBLE_DEVICES']=cfg['gpu_uuid']
    with (unit/'stderr.log').open('x') as err:
        p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',env=env,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW);job=Job(p)
        stdout,_=p.communicate('RUN\n',timeout=min(180,cfg['resources']['total_native_seconds']-spent));(unit/'stdout.log').write_text(stdout)
        need(p.returncode==0,'operator helper failed');result=read(unit/'native/RESULT.json');need(result['status']=='COMPLETE' and result['normal_cleanup_returned'] and result['operator_replays']==8,'operator helper incomplete')
        for module in result['modules']:
            q=Path(module)
            if q.name in build['numerical_modules']:need(q.resolve()==(exe.parent/q.name).resolve() and file_hash(q)==build['numerical_modules'][q.name],'loaded DLL identity')
        count=8;active=job.wait_empty(timeout=10);need(active==0,'helper cleanup');success=True
except BaseException as e:
    error=repr(e)
    if job:job.terminate()
    elif p and p.poll() is None:p.kill()
    if p:p.wait(timeout=30)
    if job:active=job.wait_empty(timeout=10)
    raise
finally:
    if job:job.close()
    if p is None or active==0:lock.unlink(missing_ok=True)
    r={'event':'END','utc':utc(),'epoch':str(bundle),'unit':name,'seconds':time.monotonic()-start,'success':success,'error':error,'completed_requests':0,'completed_operator_replays':count,'active_processes_after_wait':active,'lock_retained':lock.exists()};save(unit/'RECEIPT.json',r);append(ledger,r)
print('Native operator replays complete; correspondence not yet audited')
