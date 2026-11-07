import pathlib,shutil,subprocess,tempfile,unittest,sys
HERE=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
import operator_patch,plan

class OffloadTests(unittest.TestCase):
    def test_compiled_preference_and_no_operand_mutation(self):
        compiler=shutil.which('g++') or shutil.which('clang++') or shutil.which('zig')
        if not compiler:self.skipTest('native compiler unavailable')
        source=r'''
#include <cstdint>
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstring>
enum { GGML_OP_MUL, GGML_OP_ADD };
namespace hs_scope { inline bool active=false; }
struct Tensor { int op=GGML_OP_MUL;int64_t ne[4]={128,8,4,1};char name[64]="Kcur_normed-10"; };
bool ggml_backend_offload_op(int,const Tensor*t){return t->ne[1]*t->ne[2]*t->ne[3]>=32;}
#include "repair_offload.hpp"
int main(){
 Tensor t;const auto original=t;
 assert(hs_repair_offload::offload_op(0,&t));
 hs_scope::active=true;assert(!hs_repair_offload::offload_op(0,&t));
 assert(std::memcmp(&t,&original,sizeof(t))==0);
 t.ne[1]=40;std::strcpy(t.name,"Qcur_normed-7");assert(hs_repair_offload::offload_op(0,&t));
 t.ne[1]=8;t.ne[2]=1;assert(!hs_repair_offload::offload_op(0,&t));
 t.ne[2]=4;std::strcpy(t.name,"ffn_norm-10");assert(hs_repair_offload::offload_op(0,&t));
 std::strcpy(t.name,"Kcur_normed-10");t.op=GGML_OP_ADD;assert(hs_repair_offload::offload_op(0,&t));
 t.op=GGML_OP_MUL;t.ne[2]=5;assert(hs_repair_offload::offload_op(0,&t));
}
'''
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);p=root/'test.cpp';p.write_text(source);exe=root/'test.exe'
            cmd=[compiler,'c++'] if pathlib.Path(compiler).stem=='zig' else [compiler]
            compiled=subprocess.run(cmd+['-std=c++17','-O2','-Wall','-Wextra','-Werror','-I'+str(HERE),str(p),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            subprocess.run([str(exe)],check=True,capture_output=True)
    def test_exact_scheduler_anchor_and_default_no_change(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);p=root/'ggml/src/ggml-backend.cpp';p.parent.mkdir(parents=True)
            text='#include "ggml-backend-impl.h"\nreturn ggml_backend_offload_op(sched->backends[b], tensor);\n';p.write_text(text)
            operator_patch.apply_rows(root,HERE,0,False);self.assertEqual(p.read_text(),text)
            r=operator_patch.apply_rows(root,HERE,0,True);self.assertEqual(r['mode'],'STABLE_HEAD_NORM_OFFLOAD')
            self.assertIn('hs_repair_offload::offload_op',p.read_text())
            with self.assertRaises(ValueError):operator_patch.apply_rows(root,HERE,0,True)
    def test_flag_must_be_bool(self):
        with self.assertRaises(ValueError):plan.policy_check({'prefill':'reference','rowwise_roles':0,'stable_norm_offload':1,'mechanism':'x'})

if __name__=='__main__':unittest.main()
