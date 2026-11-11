"""Finite trained-model qualification of the repaired Smol producer."""
from smol import *
def observer_stage():
 dest=SROOT/'producer-observer03';dest.mkdir()
 for n in ('native.cpp','target.cpp','observer.h','CMakeLists.txt'):shutil.copyfile(SROOT/'producer01'/n,dest/n)
 for n in ('smol_capture.hpp','smol_evidence.hpp'):shutil.copyfile(HERE/n,dest/n)
 p=dest/'observer.h';s=p.read_text();s=s.replace('struct prefill_observer {','#include "smol_evidence.hpp"\nstruct prefill_observer {\n    SmolEvidence evidence;')
 s=s.replace('void reset(const pj &req){path=req.at("output");','void reset(const pj &req){evidence.reset(req);path=req.at("output");')
 s=s.replace('        graphs=pj::array(); if (!instrument) return;','        evidence.begin(ctx,b,role);\n        graphs=pj::array(); if (!instrument) return;')
 s=s.replace('    void end(llama_context * ctx,int code) {','    void end(llama_context * ctx,int code) {\n        if(!code&&evidence.heavy)llama_synchronize(ctx);\n        if(!code)evidence.end(ctx,role);')
 anchor='std::vector<float> logits(l,l+nv);bytes(".pending_logits.f32",logits);';assert s.count(anchor)==1
 s=s.replace(anchor,anchor+'\n        if(evidence.heavy||evidence.final_only)evidence.initial_vector=logits;')
 old='        std::ofstream f(path,std::ios::binary);f<<j.dump(2)';assert s.count(old)==1
 s=s.replace(old,'        if(evidence.heavy||evidence.final_only){j["full_target_vectors"]=evidence.vectors;j["committed_states"]=evidence.states;}\n'+old);p.write_text(s)
 p=dest/'native.cpp';s=p.read_text();old='                observer.role="target";observer.mutation("keep",mem_tgt,0,-1,-1,-1);llama_memory_seq_keep(mem_tgt, 0);';assert s.count(old)==1
 s=s.replace(old,old+'\n                if(observer.evidence.heavy)observer.evidence.commit(ctx_tgt);')
 old='    if(ctx_tgt!=source_target)llama_free(ctx_tgt);';assert s.count(old)==1
 s=s.replace(old,'    if(observer.evidence.final_only&&!observer.evidence.heavy)observer.evidence.commit(ctx_tgt);\n'+old);p.write_text(s)
 command(['cmake','-S',dest,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64'],dest/'configure.log')
 command(['cmake','--build',dest/'build','--config','Release','--target','b570-closeout-native','--parallel','4'],dest/'compile.log')
 bins=dest/'build/Release'
 for p in (SROOT/'original-runtime').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(dest/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.exe','.dll')]))
 write(dest/'SOURCE.json',dict(native_sha256=sha(dest/'native.cpp'),observer_sha256=sha(dest/'observer.h'),capture_sha256=sha(dest/'smol_capture.hpp'),evidence_sha256=sha(dest/'smol_evidence.hpp'),numerical_dlls_changed=False,extra_forward_calls=0,requested_output_masks_changed=False))
def run(index,heavy):
 inp=read(SMOL/'SMOL_DISCOVERY_INPUTS.json')[index];name='qual02-'+str(index)+('-heavy' if heavy else '-off');out=SROOT/(name+'-capture.json');req=SROOT/(name+'-request.json')
 req.write_text(json.dumps(dict(request_id=name,prompt_ids=inp['prompt_ids'],output=str(out),heavy_state=heavy,audit_final=not heavy))+'\n')
 env=SROOT/(name+'-env.json');write(env,dict(HS_PREFILL_OUTPUT=str(out),HS_PREFILL_UB='128',**({} if heavy else {'HS_TRACE_OFF':'1'})))
 argv=read(SROOT/'units'/('producer01-'+str(index))/'SUPERVISOR.json')['argv'];argv[0]=str(SROOT/'producer-observer03/build/Release/b570-closeout-native.exe')
 unit,rc=supervised(name,SROOT/'producer-observer03/FILES.json',argv,dict(requests=1,token_rows=2*len(inp['prompt_ids'])+512,operators=0),stdin_file=req,environment_file=env);assert rc==0
 a=read(out);b=read(SROOT/('producer01-'+str(index)+'-capture.json'));assert a['ids']==b['ids'] and a['eog']==b['eog']
 if heavy:assert a['commits']==b['commits']
 print(name,'NATIVE_CAPTURE_COMPLETE',len(a['full_target_vectors']),len(a['committed_states']))
if __name__=='__main__':
 if sys.argv[1]=='stage':observer_stage()
 else:run(int(sys.argv[2]),sys.argv[1]=='heavy')
