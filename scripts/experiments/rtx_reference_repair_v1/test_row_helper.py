"""Compile/execute the real row helper against a small synthetic GGML graph API.
This checks graph/index/precision logic, NOT native CUDA/CPU numeric correspondence.
"""
import os, shutil, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).parent
STUB=r'''
#pragma once
#include <cstdint>
#include <cstddef>
#include <string>
#include <cstdarg>
#include <cstdio>
#include <vector>
#include <stdexcept>
enum ggml_type {GGML_TYPE_F32,GGML_TYPE_F16};
enum ggml_op {GGML_OP_NONE,GGML_OP_MUL_MAT,GGML_OP_CONCAT,GGML_OP_VIEW};
enum ggml_prec {GGML_PREC_DEFAULT,GGML_PREC_F32};
struct ggml_context {};
struct ggml_tensor {int64_t ne[4]={1,1,1,1};size_t nb[4]={4,4,4,4};ggml_type type=GGML_TYPE_F32;ggml_op op=GGML_OP_NONE;ggml_tensor* src[2]={};std::string name;std::vector<float> data;ggml_prec prec=GGML_PREC_DEFAULT;};
inline const char* ggml_get_name(ggml_tensor*t){return t->name.c_str();}
inline void ggml_format_name(ggml_tensor*t,const char* fmt,...){char b[200];va_list a;va_start(a,fmt);vsnprintf(b,sizeof(b),fmt,a);va_end(a);t->name=b;}
inline ggml_tensor* ggml_view_2d(ggml_context*,ggml_tensor*b,int64_t d,int64_t n,size_t stride,size_t offset){auto*r=new ggml_tensor;r->ne[0]=d;r->ne[1]=n;r->nb[1]=stride;r->op=GGML_OP_VIEW;r->src[0]=b;for(int i=0;i<d;i++)r->data.push_back(b->data.at(offset/4+i));return r;}
inline ggml_tensor* ggml_mul_mat(ggml_context*,ggml_tensor*a,ggml_tensor*b){auto*r=new ggml_tensor;r->ne[0]=a->ne[1];r->ne[1]=b->ne[1];r->op=GGML_OP_MUL_MAT;r->src[0]=a;r->src[1]=b;for(int j=0;j<b->ne[1];j++)for(int i=0;i<a->ne[1];i++){float v=0;for(int k=0;k<a->ne[0];k++)v+=a->data.at(i*a->ne[0]+k)*b->data.at(j*b->nb[1]/4+k);r->data.push_back(v);}return r;}
inline ggml_tensor* ggml_concat(ggml_context*,ggml_tensor*a,ggml_tensor*b,int axis){if(axis!=1)throw std::runtime_error("axis");auto*r=new ggml_tensor;r->ne[0]=a->ne[0];r->ne[1]=a->ne[1]+b->ne[1];r->op=GGML_OP_CONCAT;r->src[0]=a;r->src[1]=b;r->data=a->data;r->data.insert(r->data.end(),b->data.begin(),b->data.end());return r;}
inline void ggml_mul_mat_set_prec(ggml_tensor*t,ggml_prec p){if(t->op!=GGML_OP_MUL_MAT)throw std::runtime_error("precision on non-matmul");t->prec=p;}
'''
MAIN=r'''
#include "reference_rows.h"
#include <iostream>
static bool leaves(ggml_tensor*t){if(t->op==GGML_OP_MUL_MAT)return t->prec==GGML_PREC_F32;return leaves(t->src[0])&&leaves(t->src[1]);}
int main(int argc,char**argv){std::string mode=argv[1];ggml_context ctx;ggml_tensor a,b;a.name="blk.0.attn_q.weight";a.ne[0]=3;a.ne[1]=2;a.data={1,2,3,4,5,6};b.ne[0]=3;b.ne[1]=4;b.nb[1]=16;b.data={1,2,3,99,4,5,6,99,7,8,9,99,10,11,12,99};hs_scope::active=true;
if(mode=="off")hs_scope::active=false;
if(mode=="q1")b.ne[1]=1;
if(mode=="unselected")a.name="blk.0.ffn_up.weight";
if(mode=="q5")b.ne[1]=5;
if(mode=="bad-stride")b.nb[0]=8;
if(mode=="bad-type")b.type=GGML_TYPE_F16;
if(mode=="bad-geometry")b.ne[2]=2;
try{auto*r=hs_repair_rows::mul_mat(&ctx,&a,&b);if(mode=="q5"||mode=="bad-stride"||mode=="bad-type"||mode=="bad-geometry"||mode=="bad-policy")return 10;
if(mode=="off"||mode=="q1"||mode=="unselected"){if(r->op!=GGML_OP_MUL_MAT)return 11;}
else {auto*baseline=ggml_mul_mat(&ctx,&a,&b);if(r->data!=baseline->data||r->op!=GGML_OP_CONCAT)return 12;hs_repair_rows::set_prec(r,GGML_PREC_F32);if(!leaves(r))return 13;}
}catch(const std::exception&e){if(mode!="q5"&&mode!="bad-stride"&&mode!="bad-type"&&mode!="bad-geometry"&&mode!="bad-policy"){std::cerr<<e.what();return 14;}}
std::cout<<"SYNTHETIC_GRAPH_CHECK_PASS";return 0;}
'''

class CompiledHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('g++'):raise unittest.SkipTest('g++ unavailable; native Windows qualification is separate')
        cls.temp=tempfile.TemporaryDirectory();r=Path(cls.temp.name)
        (r/'ggml.h').write_text(STUB);(r/'hs_scope.h').write_text('#pragma once\nnamespace hs_scope {inline bool active=false;}\n');(r/'main.cpp').write_text(MAIN)
        cls.binary=r/'test';subprocess.run(['g++','-std=c++17','-O2','-I'+str(r),'-I'+str(ROOT),str(r/'main.cpp'),'-o',str(cls.binary)],check=True,capture_output=True,timeout=30)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def check(self,mode,policy='qkv'):
        x=subprocess.run([str(self.binary),mode],env=dict(os.environ,HS_REPAIR_ROWS=policy),capture_output=True,text=True,timeout=10)
        self.assertEqual(x.returncode,0,x.stdout+x.stderr);self.assertIn('SYNTHETIC_GRAPH_CHECK_PASS',x.stdout)
    def test_row_values_and_precision(self):self.check('split')
    def test_reference_bypass(self):self.check('off')
    def test_single_row_bypass(self):self.check('q1')
    def test_other_family_bypass(self):self.check('unselected')
    def test_reject_wide_query(self):self.check('q5')
    def test_reject_channel_stride(self):self.check('bad-stride')
    def test_reject_precision_change(self):self.check('bad-type')
    def test_reject_extra_batch(self):self.check('bad-geometry')
    def test_reject_unknown_policy(self):self.check('bad-policy','special-input-111')

if __name__=='__main__':unittest.main(verbosity=2)
