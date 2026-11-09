"""Rebuild a separate mixed-Q4 frontend against each freshly compiled core.

No old archive/source is modified. Numerical eligibility remains unclaimed.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,json,shutil,sys
from build import read,sha,save,command

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--builds',type=Path,required=True);a=p.parse_args();r,b=a.root,a.builds
 assert read(b/'CORES_COMPLETE.json')['passed'];f=b/'frontend';shutil.copytree(r/'m2-build-01/frontend',f)
 path=f/'entry.cpp';s=path.read_text();old='need(phase_target_reserve==8&&(m2_k==3||m2_k==7)&&job.at("draft")==true&&job.at("draft_width")==4,"M2 explicit k3/7 reserve8 D4 contract");'
 assert s.count(old)==1
 s=s.replace(old,'need(phase_target_reserve==8&&m2_k==3&&((job.at("draft")==true&&job.at("draft_width")==4)||(job.at("draft")==false&&job.at("draft_width")==1)),"Q32 explicit k3 reserve8 M/D4 contract");');path.write_text(s)
 path=f/'m1_capability.hpp';s=path.read_text();start=s.index('    need(d && pool.draft');end=s.index('    need(!job.value("profile"',start)
 s=s[:start]+'''    const bool drafting=job.at("draft");
    need(spec.k==3 && phase_target_reserve==8,"Q32 k3/reserve8");
    need(drafting?(d && pool.draft && spec.draft && phase_draft_width==4):(!d && !pool.draft && !spec.draft && phase_draft_width==1),"Q32 real M/D4 residency");
    need(t->hparams.n_layer()==64 && t->hparams.n_head()==64 && t->hparams.n_head_kv()==8 && t->hparams.n_embd_head_k()==128 && t->hparams.n_embd_head_v()==128,"Q32 actual topology");
'''+s[end:]
 s=s.replace('const auto draft_hash=hash_file(job.at("draft_model").get<std::string>());','const std::string draft_hash=drafting?hash_file(job.at("draft_model").get<std::string>()):std::string();')
 s=s.replace('target_hash==job.at("target_sha256") && draft_hash==job.at("draft_sha256")','target_hash==job.at("target_sha256") && (!drafting || draft_hash==job.at("draft_sha256"))')
 s=s.replace('heterospec.m2.native-capability.v1','heterospec.q32.ref1.native-capability.v1').replace('{"draft_sha256",draft_hash}','{"draft_sha256",drafting?json(draft_hash):json(nullptr)}')
 for key,expr in [('draft_structure','m1_structure(d)'),('draft_context','m1_context(*pool.draft)'),('draft_placement','m1_placement(d)')]:s=s.replace('{"'+key+'",'+expr+'}','{"'+key+'",drafting?'+expr+':json(nullptr)}')
 s=s.replace('{"proposal_mode",phase_proposal_mode}', '{"typed_recipes",{{"Q4_K","original scalar vec_dot_q4_K_q8_1"},{"Q6_K","original scalar vec_dot_q6_K_q8_1"}}},{"atomic_columns",1},{"residency",drafting?"matched":"target_only"},{"proposal_mode",phase_proposal_mode}')
 path.write_text(s)
 # Retain geometry/device validation at every invocation; store each unique
 # descriptor once plus count, while executions retain every physical call.
 path=f/'worker.cpp';s=path.read_text();old='auto key=j.dump();o.signatures[key]=std::move(j);';assert s.count(old)==1
 s=s.replace(old,'auto descriptor=j;descriptor.erase("first_position");descriptor.erase("visible_keys_by_causal_row");auto key=descriptor.dump();auto it=o.signatures.find(key);if(it==o.signatures.end()){j["observed_occurrences"]=1;o.signatures[key]=std::move(j);}else{it->second["observed_occurrences"]=it->second["observed_occurrences"].get<int>()+1;}');path.write_text(s)
 def one(core):
  old=r/'m2-build-01'/core;dest=b/core;native=r/'run-01'/f'build-{core}-01/native';tree=dest/'source';obj=dest/'frontend.o';exe=dest/'transfer-worker'
  orig=r/'run-01/stage-04/sources'/core;args=read(old/'compile/command.json')['argv'];args=[x.replace(str(r/'m2-build-01/frontend'),str(f)).replace(str(orig),str(tree)).replace(str(old),str(dest))for x in args];args=[('-DM1_PROJECTION="'+('REF1-group'if core=='packed'else'REF1-loop')+'"')if x.startswith('-DM1_PROJECTION=')else x for x in args]
  command(args,native,dest/'compile-frontend')
  args=read(old/'link/command.json')['argv'];args=[str(dest/'libllama.a')if x=='llama/src/libllama.a'else x.replace(str(old),str(dest))for x in args];command(args,native,dest/'link-frontend')
  deps=read(r/'run-01'/f'build-{core}-01/DEPENDENCIES.json');names=dict(deps['files']);names.update(read(dest/'CORE_BINDING.json')['compiled_graph_dependencies'])
  for s in(dest/'frontend.d').read_text().replace('\\\n',' ').split(':',1)[1].split():
   file=Path(s);file=file if file.is_absolute()else native/file;names[str(file.resolve())]=sha(file)
  for file in [obj,dest/'libllama.a',dest/'CORE_BINDING.json',dest/'llama-graph.cpp.o',dest/'transfer-worker.map',*f.rglob('*')]:
   if file.is_file():names[str(file.resolve())]=sha(file)
  save(dest/'DEPENDENCIES.json',{**deps,'files':names,'new_numerical_TU':'llama-graph.cpp','original_CUDA_archives_unchanged':True})
  base=read(old/'BUILD.json');save(dest/'BUILD.json',{**base,'executable':str(exe),'executable_sha256':sha(exe),'dependency_closure_sha256':sha(dest/'DEPENDENCIES.json'),'status':'Q32_REF1_BUILT_NOT_QUALIFIED','frontend':{str(p.relative_to(f)):sha(p)for p in f.rglob('*')if p.is_file()},'new_core_binding_sha256':sha(dest/'CORE_BINDING.json'),'numerical_archives':'Separate compiled mixed-Q4 REF1 graph TU; unchanged hash-bound original per-type CUDA source build','native_capability_schema':'heterospec.q32.ref1.native-capability.v1'})
  print('Q32_FRONTEND_BUILT',core,sha(exe),flush=True)
 with ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(one,('loop4','packed')))
 save(b/'FRONTENDS_COMPLETE.json',dict(passed=True,qualified=False,originals_modified=False,frontend=str(f)))
if __name__=='__main__':main()
