"""Additive, source-pinned derivatives. No changes to the frozen oracle tree.
Stagers intentionally preserve target arithmetic, output reserve and transaction.
Native host still must compile, bridge and qualify the generated workers.
"""
from __future__ import annotations
import argparse, difflib, hashlib, importlib.util, shutil, subprocess
from pathlib import Path
from common import need,write_new,git_blob,file_sha

LOOP_REF='7ac1b6bd91a69fe3a27819c81978c4a78fac5cbd'
DRAFT_REF='895c20513bd086d389ea52a60d0cd52a89bec73d'
RTX_WORKER_REF='29511ed91eb9f3d9773cfdda53e3554b0f4ad08b'
RTX_WORKER='scripts/experiments/rtx_scope_transfer_v1/worker.cpp'
RTX_PIN='4423bf687de4d652809c3ffad9cd9bf31770c2019c383fb54bd7abd24858b124'
LOOP_FILES=['scripts/reference_baselines/stage.py','scripts/reference_baselines/compare.py',
 'src/reference_baselines/loop4_plan.hpp','src/reference_baselines/loop4_tensor.hpp','src/reference_baselines/loop4_marker.h']
HERE=Path(__file__).resolve().parent

def gitbytes(repo:Path,ref:str,path:str)->bytes:
    need(len(ref)==40 and all(c in '0123456789abcdef' for c in ref),'fixed commit required')
    return subprocess.run(['git','-C',str(repo),'show',ref+':'+path],check=True,capture_output=True).stdout

def once(s,old,new):
    need(s.count(old)==1,'source anchor changed: '+old[:100]);return s.replace(old,new,1)

def publish_derivative(raw:bytes,new:bytes,out:Path,meta:dict):
    out.mkdir(parents=True,exist_ok=False)
    (out/'worker.cpp').write_bytes(new)
    (out/'CHANGE.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),new.decode().splitlines(True),fromfile='frozen-worker.cpp',tofile='worker.cpp')),encoding='utf8')
    write_new(out/'STAGE.json',{'status':'SOURCE_DERIVATIVE_ONLY','original_sha256':hashlib.sha256(raw).hexdigest(),
        'worker_sha256':hashlib.sha256(new).hexdigest(),'native_build':'NOT_RUN','gpu_execution':'NOT_RUN',**meta})

def rtx_draft(raw:bytes,ub:int)->bytes:
    need(ub in (1,2,4),'draft width');need(hashlib.sha256(raw).hexdigest()==RTX_PIN,'not exact PR151 worker')
    s=raw.decode('utf8')
    s=once(s,'using Clock=std::chrono::steady_clock;',f'using Clock=std::chrono::steady_clock;\nstatic constexpr int draft_ubatch={ub};')
    s=once(s,'const fs::path&dir,int layout):model(m)','const fs::path&dir,int layout,int draft_physical=1):model(m)')
    s=once(s,'p.n_ubatch=ub;','p.n_ubatch=istarget?ub:draft_physical;')
    anchor='dir/"draft",spec.selector);';need(s.count(anchor)==2,'resident/fresh draft constructor drift')
    s=s.replace(anchor,'dir/"draft",spec.selector,draft_ubatch);')
    need('"rtx_scope_transfer_v1"' in s,'historical study ID missing')
    s=s.replace('"rtx_scope_transfer_v1"','"tpds_decisive_rtx_draft_v1"')
    s=once(s,'{"draft_producer","NATIVE"}','{"draft_producer","NATIVE"},{"draft_ubatch",draft_ubatch}')
    s=once(s,'need(slot.at("schema")==1','need(slot.at("draft_ubatch")==draft_ubatch,"draft slot mismatch");\n            need(plan.at("context").at("draft_ubatch")==draft_ubatch,"draft plan mismatch");\n            need(identity.at("draft_ubatch")==draft_ubatch,"draft binding mismatch");\n            need(slot.at("schema")==1')
    s=once(s,'    double setup=since(start);','    if(draft)need(int(llama_n_ubatch(draft->c))==draft_ubatch,"actual draft width differs");\n    double setup=since(start);')
    # These two output reserves and the target invocation must not change.
    need('p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;' in s,'output reserve changed')
    need('if(draft)draft->decode(prompt,0,false,"PREFILL");' in s,'draft caller changed')
    return s.encode()

def b570_draft(raw:bytes,caller:int,ub:int)->bytes:
    """Apply to recovered PR165 post-adaptation boundary.cpp, NOT original R.
    The host pins the exact recovered bytes in its pre-output revision manifest.
    """
    need((caller,ub) in ((1,1),(4,1),(4,2),(4,4)),'B570 arm')
    s=raw.decode('utf8');crlf='\r\n' in s;s=s.replace('\r\n','\n')
    need('policy.precision' in s and 'DecodeScope scope(role,phase)' in s,'expected qualified PR165 adapter structure')
    s=once(s,'#include <bcrypt.h>','#include "draft_prefill.hpp"\n#include <bcrypt.h>\n'+f'static constexpr int hs_draft_caller={caller}, hs_draft_ubatch={ub};')
    s=once(s,'NativeContext(llama_model*m,int ub,bool capture,std::string label):','NativeContext(llama_model*m,int ub,bool capture,std::string label,int draft_physical=1):')
    s=once(s,'p.n_ubatch=ub;','p.n_ubatch=(role=="draft"?draft_physical:ub);')
    s=once(s,'c=llama_init_from_model(m,p);need(c,"context");','c=llama_init_from_model(m,p);need(c,"context");\n  if(role=="draft")need(int(llama_n_ubatch(c))==draft_physical,"actual draft microbatch differs");')
    s=once(s,'std::make_unique<NativeContext>(d,1,heavy,"draft")','std::make_unique<NativeContext>(d,1,heavy,"draft",hs_draft_ubatch)')
    # Admission must allocate the same physical draft width as the measured arm.
    s=once(s,'NativeContext draft(d,1,false,"draft");','NativeContext draft(d,1,false,"draft",hs_draft_ubatch);')
    s=once(s,'draft->prefill(prompt,std::vector<int>(prompt.size(),1))','draft->prefill(prompt,tpds_decisive::draft_schedule(prompt.size(),hs_draft_caller))')
    start='json run_request(llama_model*t,llama_model*d,const json&input,const json&slot,const json&donor){'
    checks='''
 need(slot.at("study_id")=="tpds_decisive_b570_draft_v1","wrong study");
 need(slot.at("draft_ubatch")==hs_draft_ubatch && slot.at("draft_caller")==hs_draft_caller,"draft intervention binding");'''
    s=once(s,start,start+checks)
    s=once(s,' out["endpoint"]=', ' out["draft_caller"]=hs_draft_caller;out["draft_ubatch"]=hs_draft_ubatch;\n out["endpoint"]=')
    need('p.n_outputs_max=ub;p.n_outputs_max_per_seq=ub;' in s,'draft output reserve changed')
    need('target.prefill(prompt,lengths);' in s,'target producer changed')
    need('draft->decode({proposal},base+1,false,"PROPOSE")' in s,'proposal calls changed')
    return s.replace('\n','\r\n').encode() if crlf else s.encode()

def observe_rtx(raw:bytes)->bytes:
    """Heavy-only readbacks of existing rows; never request new logits.
    Observer-on/off must be bridged on the original host before qualification.
    """
    s=raw.decode();crlf='\r\n' in s;s=s.replace('\r\n','\n')
    s=once(s,'#include "llama.h"','#include "llama.h"\n#include "target_capture.hpp"')
    method='''
    void snapshot(const std::string & key,int row) {
        if (!capture || !target) return;
        tpds_decisive::capture_existing(c,model,path/"state"/key,row);
    }
'''
    s=once(s,'    json bounds(){',method+'    json bounds(){')
    # Free ordinary R snapshots, plus candidate initial and committed boundaries.
    s=once(s,'    bool done=commit(pending);','    if(capture)target->snapshot("initial",-1);\n    bool done=commit(pending);')
    old='pending=target->sample(-1,"ordinary-"+std::to_string(ids.size()));done=commit(pending);'
    new='pending=target->sample(-1,"ordinary-"+std::to_string(ids.size()));if(capture)target->snapshot("ordinary-"+std::to_string(ids.size()),-1);done=commit(pending);'
    s=once(s,old,new)
    s=once(s,'target->trim(keep);draft->trim(keep);','target->trim(keep);draft->trim(keep);\n        if(capture)target->snapshot("commit-"+std::to_string(cycle),accepted);')
    return s.replace('\n','\r\n').encode() if crlf else s.encode()

def observe_b570(raw:bytes)->bytes:
    s=raw.decode();crlf='\r\n' in s;s=s.replace('\r\n','\n')
    # Old boundary() already preserves logits separately from native KV serialization.
    s=once(s,' bool done=commit(next);',' if(heavy)out["state_boundaries"].push_back({{"key","initial"},{"snapshot",target.boundary(initial)}});\n bool done=commit(next);')
    s=once(s,'next=target.sample(-1,"target_ordinary/"+std::to_string(ids.size()));done=commit(next);',
        'next=target.sample(-1,"target_ordinary/"+std::to_string(ids.size()));if(heavy)out["state_boundaries"].push_back({{"key","ordinary/"+std::to_string(ids.size())},{"snapshot",target.boundary(target.logits(-1))}});done=commit(next);')
    s=once(s,'target.trim(keep);draft->trim(keep);','target.trim(keep);draft->trim(keep);\n  if(heavy)out["state_boundaries"].push_back({{"key","commit/"+std::to_string(cycle)},{"snapshot",target.boundary(target.logits(accepted))}});')
    return s.replace('\n','\r\n').encode() if crlf else s.encode()

def materialize_loop(repo:Path,candidate:Path,out:Path):
    need(not out.exists(),'fresh staging root required');out.mkdir(parents=True)
    tools=out/'pinned-tools';pins=[]
    for path in LOOP_FILES:
        raw=gitbytes(repo,LOOP_REF,path);p=tools/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        pins.append({'commit':LOOP_REF,'path':path,'git_blob':git_blob(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    need(next(x['git_blob'] for x in pins if x['path'].endswith('/stage.py'))=='630b4112dfaa51ba8cede64004de306c3c8e68be','loop4 stager differs')
    module_path=tools/'scripts/reference_baselines/stage.py'
    spec=importlib.util.spec_from_file_location('frozen_loop_stager',module_path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    result=mod.stage(candidate,out/'native-arms')
    write_new(out/'PINNED_DEPENDENCIES.json',{'files':pins,'result':result,'scope':'Source staging; no new GPU evidence'})

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    l=sub.add_parser('rtx-loop4');l.add_argument('--repo',type=Path,required=True);l.add_argument('--candidate',type=Path,required=True);l.add_argument('--out',type=Path,required=True)
    r=sub.add_parser('rtx-draft');r.add_argument('--repo',type=Path,required=True);r.add_argument('--out',type=Path,required=True)
    b=sub.add_parser('b570-draft');b.add_argument('--worker',type=Path,required=True);b.add_argument('--expected-sha256',required=True);b.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='rtx-loop4':materialize_loop(a.repo,a.candidate,a.out);return
    if a.cmd=='rtx-draft':
        raw=gitbytes(a.repo,RTX_WORKER_REF,RTX_WORKER)
        publish_derivative(raw,observe_rtx(raw),a.out/'reference-observer',{'arm':'old-R-observer','arithmetic_changes':False})
        shutil.copyfile(HERE/'native/target_capture.hpp',a.out/'reference-observer/target_capture.hpp')
        for ub in (1,2,4):
            altered=rtx_draft(raw,ub)
            publish_derivative(raw,altered,a.out/f'D{ub}',{'draft_ubatch':ub,'draft_output_reserve':1,'caller':'original whole-prompt','contract':'T'})
            publish_derivative(altered,observe_rtx(altered),a.out/f'D{ub}-observer',{'draft_ubatch':ub,'observer':'heavy only; read existing outputs'})
            shutil.copyfile(HERE/'native/target_capture.hpp',a.out/f'D{ub}-observer/target_capture.hpp')
    else:
        raw=a.worker.read_bytes();need(hashlib.sha256(raw).hexdigest()==a.expected_sha256,'recovered source identity differs')
        need(not a.out.exists(),'fresh staging root required')
        for caller,ub in ((1,1),(4,1),(4,2),(4,4)):
            d=a.out/f'C{caller}U{ub}';changed=b570_draft(raw,caller,ub)
            publish_derivative(raw,changed,d,{'draft_caller':caller,'draft_ubatch':ub,'draft_output_reserve':1,'contract':'T'})
            shutil.copyfile(HERE/'native/draft_prefill.hpp',d/'draft_prefill.hpp')
            ob=a.out/f'C{caller}U{ub}-observer';publish_derivative(changed,observe_b570(changed),ob,{'observer':'heavy-only committed sequence + retained-prefix logits'})
            shutil.copyfile(HERE/'native/draft_prefill.hpp',ob/'draft_prefill.hpp')
if __name__=='__main__':main()
