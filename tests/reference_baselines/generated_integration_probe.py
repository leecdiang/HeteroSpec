"""Compile and run generated loop4 host-side probes.

This executes staged C++ mapping or graph-construction code on CPU. It does not
compile CUDA kernels, run a GPU, count GPU launches, or prove numerical
reference equivalence. The supplied library directory must contain a compatible
ggml-base built from the supplied candidate source.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import os
import shutil
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--library-dir',type=Path,required=True)
p.add_argument('--project-root',type=Path,help='Defaults to the repository root when installed under tests/reference_baselines')
p.add_argument('--compiler',default='g++')
p.add_argument('--sanitizer',choices=['none','undefined','address-undefined'],default='undefined')
p.add_argument('--disable-leak-check',action='store_true',help='For ASan under ptrace environments where LSan is unsupported')
options=p.parse_args()
root=options.project_root.resolve() if options.project_root else Path(__file__).resolve().parents[2];base=options.candidate.resolve();library=options.library_dir.resolve()
compiler=shutil.which(options.compiler)
if not compiler:raise SystemExit('C++ compiler not found: '+options.compiler)
include=base/'ggml/include'
if not include.is_dir() or not library.is_dir():raise SystemExit('Candidate include directory and library directory must exist')
stage_path=root/'scripts/reference_baselines/stage.py'
spec=importlib.util.spec_from_file_location('loop4_stage_under_test',stage_path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
work=tempfile.TemporaryDirectory(prefix='hs-loop4-generated-')
generated=Path(work.name)/'probe.cpp'
_,code=m.backend_variant((base/m.CUDA).read_text(),(base/m.MMVQ).read_text())
start=code.rfind('    if (hs_loop4::marked(dst)) {');i=start+len('    if (hs_loop4::marked(dst)) {');depth=1
while depth:
 if code[i]=='{':depth+=1
 elif code[i]=='}':depth-=1
 i+=1
loop=code[start:i]
generated.write_text('''#include "loop4_tensor.hpp"
#include <vector>
#include <iostream>
#include <cassert>
struct block_q8_1 { char bytes[36]; };
struct Pool { std::vector<char> values; char * get(){return values.data();} };
int Q,K,M,calls;char * origin;float * outputs;
void mul_mat_vec_q_switch_type(const void *,ggml_type t,const void * q,const int32_t * ids,int fusion,float * out,
 int k,int m,int cols,int sx,int sy,int so,int cx,int cy,int co,int scx,int scy,int sco,
 int nx,int no,int ssx,int ssy,int sso,int idstride,int stream){
 assert(t==GGML_TYPE_Q8_0 && !ids && !fusion && !idstride && !stream);
 int begin=calls*4,width=std::min(4,Q-begin);++calls;
 assert(k==K && m==M && cols==width && sx==K/32 && sy==((K+511)/512*512)/32 && so==M);
 assert(cx==1 && cy==1 && co==1 && nx==1 && no==1);
 assert(scx==K/32*M && ssx==scx && scy==width*sy && ssy==scy && sco==width*M && sso==sco);
 assert((const char *)q==origin+begin*sy*int(sizeof(block_q8_1)) && out==outputs+begin*M);
 for(int c=0;c<cols;++c)for(int row=0;row<M;++row)out[c*M+row]=float((unsigned char)((const char *)q)[c*sy*sizeof(block_q8_1)]+row);
}
void run(const ggml_tensor * src0,const ggml_tensor * src1,ggml_tensor * dst,Pool & src1_q8_1){
 const ggml_tensor * ids=nullptr;const void * fusion=nullptr;int fusion_local=0,stream=0;
 float * dst_d=(float *)dst->data;int ne00=src0->ne[0],ne01=src0->ne[1],ncols_dst=src1->ne[1];
 int s01=ne00/32,s02=s01*ne01,s03=s02;
 int stride_col_y=((ne00+511)/512*512)/32,stride_col_dst=ne01;
''' + loop + '''
 throw std::runtime_error("marked branch skipped");
}
int main(){int cases=0;for(Q=5;Q<=32;++Q)for(int k:{32,128,512,1024})for(int m:{1,3,127}){
 K=k;M=m;auto ctx=ggml_init({1024*1024,nullptr,true});auto w=ggml_new_tensor_2d(ctx,GGML_TYPE_Q8_0,K,M);auto x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,K,Q);auto out=ggml_mul_mat(ctx,w,x);hs_loop4::mark(out);
 Pool pool;pool.values.resize(Q*((K+511)/512*512)/32*36);for(size_t i=0;i<pool.values.size();++i)pool.values[i]=char(i*17+3);
 std::vector<float> output(Q*M,-1);out->data=output.data();origin=pool.get();outputs=output.data();calls=0;run(w,x,out,pool);
 assert(calls==(Q+3)/4);for(int c=0;c<Q;++c)for(int row=0;row<M;++row)assert(output[c*M+row]==float((unsigned char)pool.values[c*((K+511)/512*512)/32*36]+row));
 ggml_free(ctx);++cases;
 }std::cout<<"GENERATED_CUDA_CALL_MAPPING_CPU_CASES="<<cases<<" GPU_EXECUTIONS=0\\n";}
''')

flags=['-std=c++17','-Wall','-Wextra','-Werror','-pedantic']
if options.sanitizer!='none':
    flags+=['-fsanitize='+('address,undefined' if options.sanitizer=='address-undefined' else 'undefined'),'-fno-sanitize-recover=all']
exe=Path(work.name)/'probe'
command=[compiler,*flags,'-I'+str(root/'src/reference_baselines'),'-I'+str(include),str(generated),'-L'+str(library),'-Wl,-rpath,'+str(library),'-lggml-base','-o',str(exe)]
env=os.environ.copy()
if options.disable_leak_check:
    env['ASAN_OPTIONS']=env.get('ASAN_OPTIONS','')+':detect_leaks=0'
try:
    subprocess.run(command,check=True)
    subprocess.run([str(exe)],check=True,env=env)
    print('CUDA_COMPILE=NOT_RUN GPU_EXECUTIONS=0 NUMERICAL_REFERENCE_EQUIVALENCE=NOT_ESTABLISHED')
    print('STAGE_SCRIPT_SHA256='+hashlib.sha256(stage_path.read_bytes()).hexdigest())
finally:
    work.cleanup()
