"""Actual fixed request bytes, child sanitizer and same-object HTTP transport."""
from dataclasses import dataclass
import hashlib,json,os
from pathlib import Path
import urllib.request
from s0_budget import ROOT
FAMILIES=('Qwen','SmolLM2','Llama');ARMS=('R','R_SHADOW','M_QB','M_QH','C_PQ','C_QB','C_QH')
def recipe(arm,selected=None):
    if arm not in ARMS:raise ValueError('unknown arm')
    if arm in ('R','R_SHADOW'):return dict(prefill_ub=1,k=0,spec=False,mask=0,layout='QB',effective_k=0)
    spec=arm.startswith('C_');name=arm.split('_')[1]
    if name=='QH':
        if selected not in ('QH_C','QH_D'):raise ValueError('QH selection requires completed actual census')
        name=selected
    return dict(prefill_ub=4,k=3 if spec else 0,spec=spec,mask=3,layout=name,effective_k=3 if spec else 0)
def environment(parent,condition,trace):
    out={k:v for k,v in parent.items() if not k.startswith(('HS_','LLAMA_ARG_','GGML_','CUDA_'))}
    if condition['layout'] not in ('QB','PQ','QH_C','QH_D') or condition['mask'] not in (0,3):raise ValueError('inadmissible selector')
    out.update(HS_SCOPE_MASK=str(condition['mask']),HS_Q95_LAYOUT=condition['layout'],HS_NATIVE_CAPTURE=str(trace),HS113_NUMERIC_RUNTIME='D:/hs104-e1-v1/native/build/bin')
    return out
@dataclass(frozen=True)
class NativeWire:
    wire:bytes
    def body(self):return json.loads(self.wire)
    @property
    def sha256(self):return hashlib.sha256(self.wire).hexdigest()
    def send(self,opener,url,approval):
        if approval.get('stage') not in ('S2','S3') or not approval.get('authenticated_F0_commit') or not approval.get('author_message_sha256'):raise ValueError('separately approved request stage required')
        return opener.open(urllib.request.Request(url,data=self.wire,headers={'Content-Type':'application/json'}),timeout=240)
def serialize(task,mode):
    ids=task['prompt_ids'];cap=task['cap']
    if not ids or not isinstance(ids,list) or any(type(t)is not int or t<0 for t in ids):raise ValueError('strict natural prompt token IDs required')
    if type(cap)is not int or cap!=128 or len(ids)+cap+4>1024:raise ValueError('inherited cap/context/lookahead')
    if mode not in ('counts','heavy'):raise ValueError('counts or diagnostic mode')
    body=dict(prompt=ids,n_predict=cap,temperature=0,top_k=0,top_p=1,min_p=0,seed=123,cache_prompt=False,return_tokens=True,stream=False,hs_closeout_mode=mode)
    b=json.dumps(body,ensure_ascii=False).encode();assert json.loads(b)==body;return NativeWire(b)
def command(family,arm,task_models,selected=None,original_routes=None):
    if family not in FAMILIES:raise ValueError('family required')
    c=recipe(arm,selected);exe=str(ROOT/'native/build/bin/llama-server.exe')
    if arm=='R':
        if original_routes is None:raise ValueError('original R route required')
        exe=original_routes[family]['path']
    a=[exe,'--model',task_models[family]['target']['path'],'--device','CUDA0','--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','2048','--ubatch-size',str(c['prefill_ub']),'--flash-attn','off','--parallel','1','--threads','24','--threads-batch','24','--cache-ram','0','--cache-type-k','f16','--cache-type-v','f16','--host','127.0.0.1','--port','18789','--no-webui','--no-warmup','--no-cache-prompt']
    if c['spec']:a+=['--spec-type','draft-simple','--model-draft',task_models[family]['draft']['path'],'--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max','3','--spec-draft-n-min','0','--spec-draft-p-min','0','--spec-draft-threads','24','--spec-draft-threads-batch','24','--spec-draft-type-k','f16','--spec-draft-type-v','f16']
    return a
