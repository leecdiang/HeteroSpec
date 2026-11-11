"""Separate REF1 Q4_K/Q6_K graph recipes; unchanged Q8 guard/CUDA objects.

Compile the modified numerical TU and reconstruct a fresh archive, proving that
every other original archive member is byte-identical. Never write old builds.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,difflib,hashlib,json,shlex,shutil,subprocess,time
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:json.dump(x,f,indent=2);f.write('\n')
def command(args,cwd,out):
 out.mkdir();start=time.monotonic();r=subprocess.run(args,cwd=cwd,capture_output=True,text=True)
 (out/'stdout.log').write_text(r.stdout);(out/'stderr.log').write_text(r.stderr);save(out/'command.json',dict(argv=args,cwd=str(cwd),returncode=r.returncode,wall_s=time.monotonic()-start));assert r.returncode==0,r.stderr
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();base=a.root/'run-01';lock=read(base/'stage-04/SOURCE_LOCK.json')
 verified=set()
 for core in('loop4','packed'):
  old=base/f'build-{core}-01';b=read(old/'BUILD.json');deps=read(old/'DEPENDENCIES.json');assert b['cuda']and b['dependency_closure_complete']and deps['cuda_translation_units']>0
  for file,h in deps['files'].items():
   if file not in verified:assert sha(file)==h,file;verified.add(file)
  for rel,h in lock['sources'][core].items():assert sha(base/'stage-04/sources'/core/rel)==h
 def one(core):
  old=base/f'build-{core}-01';source=base/'stage-04/sources'/core;dest=a.out/core;dest.mkdir();tree=dest/'source';shutil.copytree(source,tree)
  path=tree/'src/llama-graph.cpp';before=path.read_text();anchor='    ggml_tensor * res = nullptr;\n    if (hs_query_batch && w->type == GGML_TYPE_Q8_0 && cur->type == GGML_TYPE_F32 &&';assert before.count(anchor)==1
  body='''    ggml_tensor * res = nullptr;
    // Explicit mixed-Q4 reference recipe: one original scalar-MMVQ column.
    // Q8's four-column marker and its backend guard remain unchanged.
    const bool q32_ref1 = hs_query_batch &&
        (w->type == GGML_TYPE_Q4_K || w->type == GGML_TYPE_Q6_K) &&
        cur->type == GGML_TYPE_F32 && cur->ne[1] > 1;
    if (q32_ref1) {
        if (cur->ne[1] > 32 || cur->ne[2] != 1 || cur->ne[3] != 1 ||
            w->ne[2] != 1 || w->ne[3] != 1 || !ggml_is_contiguous(w) ||
            w->ne[0] != cur->ne[0] || w->ne[0] % ggml_blck_size(w->type) != 0)
            throw std::runtime_error("unsupported mixed-Q4 REF1 descriptor");
'''
  if core=='packed':body+='''        if (!ggml_is_contiguous(cur))
            throw std::runtime_error("REF1-group requires contiguous actual activation");
        // ne11=1 selects the same original per-type scalar kernel as UB1 R;
        // dimension2 enumerates independent columns sharing the same weight.
        auto * groups = ggml_view_3d(ctx0,cur,cur->ne[0],1,cur->ne[1],
                                    cur->nb[1],cur->nb[1],0);
        auto * batch = ggml_mul_mat(ctx0,w,groups);
        ggml_format_name(batch,"hs_ref1_group_%s_%s",ggml_type_name(w->type),w->name);
        res = ggml_reshape_2d(ctx0,batch,w->ne[1],cur->ne[1]);
'''
  else:body+='''        for (int64_t i=0;i<cur->ne[1];++i) {
            auto * x=ggml_view_2d(ctx0,cur,cur->ne[0],1,cur->nb[1],i*cur->nb[1]);
            auto * column=ggml_mul_mat(ctx0,w,x);
            ggml_format_name(column,"hs_ref1_loop_%s_%s_%lld",ggml_type_name(w->type),w->name,(long long)i);
            res=res?ggml_concat(ctx0,res,column,1):column;
        }
'''
  body+='''    } else if (hs_query_batch && w->type == GGML_TYPE_Q8_0 && cur->type == GGML_TYPE_F32 &&'''
  after=before.replace(anchor,body,1);path.write_text(after);(dest/'numerical-source.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='pinned/src/llama-graph.cpp',tofile='q32-ref1/src/llama-graph.cpp')))
  # The old Q8-only tensor marker must remain byte-identical, not broadened.
  guard=Path('ggml/src/hs_loop4_tensor.hpp');assert sha(tree/guard)==sha(source/guard)
  units=read(old/'native/compile_commands.json');unit=next(x for x in units if x['file']==str(source/'src/llama-graph.cpp'))
  args=[s.replace(str(source),str(tree))for s in shlex.split(unit['command'])];obj=dest/'llama-graph.cpp.o';args[args.index('-o')+1]=str(obj);args+=['-MMD','-MF',str(dest/'graph.d')]
  command(args,Path(unit['directory']),dest/'compile-graph')
  original=old/'native/llama/src/libllama.a';archive=dest/'libllama.a';shutil.copy2(original,archive)
  command(['ar','rcs',str(archive),str(obj)],dest,dest/'archive')
  members=subprocess.check_output(['ar','t',str(original)],text=True).splitlines();assert members==subprocess.check_output(['ar','t',str(archive)],text=True).splitlines();assert members.count('llama-graph.cpp.o')==1
  hashes={}
  for name in members:
   aa=hashlib.sha256(subprocess.check_output(['ar','p',str(original),name])).hexdigest();bb=hashlib.sha256(subprocess.check_output(['ar','p',str(archive),name])).hexdigest();hashes[name]=dict(original=aa,new=bb)
   if name!='llama-graph.cpp.o':assert aa==bb,'Unregistered numerical object change'
  deps=read(old/'DEPENDENCIES.json');newfiles={}
  for s in(dest/'graph.d').read_text().replace('\\\n',' ').split(':',1)[1].split():
   f=Path(s);f=f if f.is_absolute()else Path(unit['directory'])/f;newfiles[str(f.resolve())]=sha(f)
  save(dest/'CORE_BINDING.json',dict(status='BUILT_NOT_QUALIFIED',recipe='REF1-group'if core=='packed'else'REF1-loop',atomic_columns=1,supported_weight_types=['Q4_K','Q6_K'],reference_dot_functions={'Q4_K':'vec_dot_q4_K_q8_1','Q6_K':'vec_dot_q6_K_q8_1'},activation_quantizer='Original quantize_row_q8_1_cuda, same weight-type argument/padding,32-element activation blocks',original_source_lock_sha256=sha(base/'stage-04/SOURCE_LOCK.json'),original_build_sha256=sha(old/'BUILD.json'),original_archive_sha256=sha(original),new_archive_sha256=sha(archive),graph_source_sha256=sha(path),Q8_marker_guard_sha256=sha(tree/guard),unchanged_CUDA_dependencies={p:h for p,h in deps['files'].items()if p.endswith(('.cu','.cuh','.a'))and not p.endswith('/libllama.a')},compiled_graph_dependencies=newfiles,archive_members=hashes))
  print('Q32_NUMERICAL_CORE_BUILT',core,sha(archive),flush=True)
 with ThreadPoolExecutor(max_workers=2)as pool:list(pool.map(one,('loop4','packed')))
 save(a.out/'CORES_COMPLETE.json',dict(passed=True,originals_modified=False,CUDA_translation_units_changed=False,new_graph_source_compiled=True,numerical_qualification='NOT_RUN'))
if __name__=='__main__':main()
