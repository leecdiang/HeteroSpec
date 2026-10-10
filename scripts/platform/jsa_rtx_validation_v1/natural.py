"""Observe the last natural shared R/N prefix without forcing a future call."""
from common import *

class DiagnosticServer(Server):
    def __init__(self,*args,cut,**kwargs):super().__init__(*args,**kwargs);self.cut=cut
    def __enter__(self):
        self.d.mkdir(parents=True,exist_ok=False);env=clean_env(self.c['mask'],self.d/'trace.jsonl');env.update(HS_LIVE_CAPTURE=str(self.d/'live'),HS_LIVE_CUT=str(self.cut))
        save(self.d/'COMMAND.json',{'command':self.command,'condition':self.c,'exe_sha256':sha(self.exe),'natural_cut':self.cut,'capture':True,'warm_cap':1,'utc':now()})
        self.log=(self.d/'server.log').open('wb');self.start=time.perf_counter();self.p=subprocess.Popen(self.command,stdout=self.log,stderr=subprocess.STDOUT,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));save(self.d/'PROCESS.json',{'pid':self.p.pid,'utc':now()})
        try:
            deadline=time.monotonic()+180
            while True:
                if self.p.poll() is not None:raise RuntimeError('diagnostic server exited '+str(self.p.returncode))
                try:
                    if self.request('/health',timeout=2).get('status')=='ok':break
                except (OSError,urllib.error.URLError):pass
                if time.monotonic()>deadline:raise TimeoutError('diagnostic readiness')
                time.sleep(.5)
            save(self.d/'WARMUP.json',{'response':self.complete(self.warm,1),'utc':now()});return self
        except BaseException:self.__exit__(None,None,None);raise

def main():
    discovery=read(PUB/'F_DISCOVERY.json')
    if discovery['native_N0_qualified']:
        save(PUB/'F_NATURAL_DIAGNOSTICS.json',{'status':'NOT_TRIGGERED','requests':0,'auxiliary_decodes':0,'reason':'N0 passed all discovery outputs; no divergent natural boundary selected'});return
    cfg=read(LOCAL/'F_MODEL_CONFIG.json');tasks=read(PUB/'F_DISCOVERY_INPUTS.json');fail={r['task'] for r in discovery['condition_qualification']['N0']['mismatches']};chosen=[t for t in tasks if t['id'] in fail][:2];root=LOCAL/'runs/F_natural';root.mkdir(parents=True,exist_ok=False);rows=[]
    for t in chosen:
        ref=read(LOCAL/'runs/F_discovery/r1-R'/(t['id'].replace('/','-')+'.json'));native=read(LOCAL/'runs/F_discovery/r1-N0'/(t['id'].replace('/','-')+'.json'));left=ref['response']['tokens'];right=native['response']['tokens'];cut=next((i for i,(a,b) in enumerate(zip(left,right)) if a!=b),min(len(left),len(right)))
        pair={'task':t['id'],'last_shared_prefix_length':cut,'prefix':left[:cut],'donors':{}}
        if not cut:pair.update(status='ALIGNMENT_UNSUPPORTED',reason='Own consistent prefills already choose different first pending token; no shared natural committed prefix');rows.append(pair);continue
        for c in [{'name':'R','mask':0,'spec':False,'ub':1,'k':0},{'name':'N0','mask':0,'spec':True,'ub':4,'k':3}]:
            d=root/(t['id'].replace('/','-')+'-'+c['name'])
            with DiagnosticServer(d,c,False,cfg['models'],cfg['exe'],cfg['warm'],cut=cut) as s:a=measure(s,t,d.name+'|'+t['id']);save(d/'REQUEST.json',a)
            expected=ref if c['name']=='R' else native;unchanged=a['response']['tokens']==expected['response']['tokens'] and a['response']['stop_type']==expected['response']['stop_type'];cp=read(d/'live/checkpoint.json') if (d/'live/checkpoint.json').exists() else None
            pair['donors'][c['name']]={'record':str((d/'REQUEST.json').relative_to(LOCAL)),'output_capture_unchanged':unchanged,'checkpoint':cp,'state_sha256':sha(d/'live/donor.state') if cp else None,'trace_sha256':sha(d/'trace.jsonl')}
        a=pair['donors']['R']['checkpoint'];b=pair['donors']['N0']['checkpoint'];keys=['committed_ids','tokens','positions','sequence_ids','logits_mask','sampler','bounds'];same=a is not None and b is not None and all(a[k]==b[k] for k in keys)
        pair['call_alignment_fields']={k:(a[k]==b[k] if a is not None and b is not None else None) for k in keys}
        if not all(x['output_capture_unchanged'] for x in pair['donors'].values()):pair.update(status='CAPTURE_CHANGED_OUTPUT',reason='Diagnostic capture is not a qualified natural parent')
        elif not same:pair.update(status='ALIGNMENT_UNSUPPORTED',reason='Last shared committed prefix is not a common own-path checkpoint with identical natural caller tokens/positions/logits mask/sampler; no cross or forced future proposal performed')
        else:pair.update(status='ALIGNED_REQUIRES_CROSS',reason='Supported natural pair must be crossed before mechanism interpretation')
        rows.append(pair)
    requests=sum(len(r['donors']) for r in rows);save(PUB/'F_NATURAL_DIAGNOSTICS.json',{'status':'ALIGNMENT_UNSUPPORTED' if all(r['status']=='ALIGNMENT_UNSUPPORTED' for r in rows) else 'REQUIRES_REVIEW','requests':requests,'warmups':requests,'auxiliary_decodes':0,'rows':rows,'claim':'No inferred unique kernel cause or full counterfactual; unsupported natural alignments preserve actual donor evidence'});print('NATURAL DIAGNOSTICS',[(r['task'],r['status']) for r in rows],flush=True)
if __name__=='__main__':main()
