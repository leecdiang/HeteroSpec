"""Post-run, zero-forward model-load probes; never replace historical logs."""
from common import *
import re
def main():
    profiles=[('S_Qwen','S_formal/s1-r1-p3-target_scopes'),('new_Qwen','confirmation_Qwen/r1-p4-C3'),('new_SmolLM2','confirmation_SmolLM2/r1-p4-C3')];rows=[]
    for name,original in profiles:
        d=LOCAL/'post_offload'/name;d.mkdir(parents=True,exist_ok=False)
        prior=read(LOCAL/'runs'/original/'COMMAND.json');command=prior['command']+['--verbose']
        save(d/'COMMAND.json',{'command':command,'original_run_command':original,'changed_only':'post-run verbosity; no completion/warmup request','exe_sha256':sha(command[0]),'model_forwards':0,'utc':now()})
        with (d/'server.log').open('wb') as log:
            p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=clean_env(prior['condition']['mask']),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));port=read(LOCAL/'CONFIG.json')['port'];deadline=time.monotonic()+180
                while True:
                    if p.poll() is not None:raise RuntimeError('zero-forward loader exited')
                    try:
                        with opener.open('http://127.0.0.1:'+str(port)+'/health',timeout=2) as r:healthy=json.load(r).get('status')=='ok'
                        if healthy:break
                    except (OSError,urllib.error.URLError):pass
                    if time.monotonic()>deadline:raise TimeoutError('zero-forward readiness')
                    time.sleep(.5)
            finally:
                if p.poll() is None:
                    p.terminate()
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
        text=(d/'server.log').read_text(encoding='utf-8',errors='replace');counts=[(int(a),int(b)) for a,b in re.findall(r'offloaded (\d+)/(\d+) layers to GPU',text)]
        row={'profile':name,'original_run_command':original,'layer_counts':counts,'log_sha256':sha(d/'server.log'),'exe_sha256':sha(command[0]),'model_forwards':0,'expected_model_count':2,'full_GPU_layers':len(counts)==2 and all(a==b for a,b in counts)};rows.append(row);print('POST-RUN ZERO-FORWARD OFFLOAD',name,counts,flush=True)
    result={'status':'PASS' if all(a['full_GPU_layers'] for a in rows) else 'LOG_UNAVAILABLE','profiles':rows,'scope':'post-run same assets/binary/load parameters with verbose logging; no per-formal-block layer-count log is retrospectively invented','model_forwards':0};save(PUB/'POST_LOAD_OFFLOAD.json',result)
if __name__=='__main__':main()
