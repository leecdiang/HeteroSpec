"""Reuse the qualified resident frontend with explicit width/build configuration."""
import hashlib,json,time,urllib.request
from close_base import HERE,PHASE2,ASSET,EOG,sha,save
from server import Server as QualifiedServer

class Server(QualifiedServer):
    def __init__(self,directory,condition,capture=False,exe=None):
        super().__init__(directory,condition['mask'],condition['spec'],capture)
        if exe is not None:self.exe=exe;self.command[0]=str(exe)
        self.condition=condition
        self.identity_sha256=sha(self.exe)
        self.command[self.command.index('--ubatch-size')+1]=str(condition['ub'])
        self.command[self.command.index('--port')+1]='18765'
        if condition['spec']:self.command[self.command.index('--spec-draft-n-max')+1]=str(condition['k'])
    def request(self,route,body=None,timeout=120):
        q=urllib.request.Request('http://127.0.0.1:18765'+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with self.opener.open(q,timeout=timeout) as r:return json.load(r)

def measure(server,task,condition,repetition,source,cap=None):
    cap=task['cap'] if cap is None else cap
    started=time.perf_counter();r=server.complete(task['formatted_prompt'],cap);wall=1000*(time.perf_counter()-started)
    ids=r['tokens'];assert ids and len(ids)==r['tokens_predicted'] and len(ids)<=cap
    assert r['prompt']==task['formatted_prompt'] and r['timings']['cache_n']==0 and not r['truncated']
    assert r['stop_type'] in ['eos','limit'];endpoint='EOS' if r['stop_type']=='eos' else 'limit'
    assert len(ids)==cap or endpoint=='EOS'
    assert not any(t in EOG for t in ids[:-1]) and ((ids[-1] in EOG)==(endpoint=='EOS'))
    return {'task':task['id'],'condition':condition,'repetition':repetition,'source_commit':source,
            'requested_cap':cap,'mask':server.mask,'spec':server.spec,'ub':server.condition['ub'],'k':server.condition['k'],
            'server_sha256':server.identity_sha256,'wall_ms':wall,'response':r,'endpoint':endpoint,
            'formatted_prompt_sha256':hashlib.sha256(task['formatted_prompt'].encode()).hexdigest()}
