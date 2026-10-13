"""CPU-only falsification receipts and exact line-addressed source binding."""
from common95 import *
import ast
CODE=Path(__file__).parent
for p in CODE.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
p=subprocess.run([str(PYTHON),'-m','unittest','discover','-s',str(CODE),'-p','test_audit95.py','-v'],capture_output=True)
(LOCAL/'synthetic.stdout.log').write_bytes(p.stdout);(LOCAL/'synthetic.stderr.log').write_bytes(p.stderr);assert p.returncode==0
save(PUB/'SYNTHETIC_CHECKS.json',dict(utc=now(),status='PASS',tests=14,script_sha256=sha(CODE/'test_audit95.py'),stdout_sha256=sha(LOCAL/'synthetic.stdout.log'),stderr_sha256=sha(LOCAL/'synthetic.stderr.log'),GPU_forwards=0))
terms={'src/llama-graph.cpp':['if (hs_query_batch && hs_scope::layout95()==1','q = ggml_permute','hs_scope::layout95()==0','q->nb[1], q->nb[2], q->nb[1]','ggml_soft_max_ext','kqv = ggml_mul_mat'],
       'src/llama-context.cpp':['hs_scope::active && hs_scope::layout95()==2','ggml_backend_sched_set_eval_callback','hsc::physical'],
       'src/llama-graph.h':['hs_query_batch != other.hs_query_batch','HS_Q95_REUSE_TRACE'],
       'src/hs_scope.h':['layout95','bit = prefill ? 1 : 2','bit = prefill ? 4 : 8','active = prior'],
       'common/hs_observer.h':['hs_scope::guard','if(!enabled())','q95capture::callback'],
       'common/capture95.h':['dump_tensor','readback','callback'],
       'ggml/src/ggml-backend.cpp':['callback_eval(t, true','callback_eval(t, false','graph_compute_async']}
bindings={}
for name,needles in terms.items():
    path=LOCAL/'native/source'/name;lines=path.read_text(encoding='utf-8').splitlines();bindings[name]=dict(sha256=sha(path),matches=[dict(line=i+1,source=line) for i,line in enumerate(lines) if any(n in line for n in needles)])
save(PUB/'SOURCE_LINE_BINDINGS.json',dict(source_inventory_sha256=sha(PUB/'NATIVE_SOURCE_HASHES.json'),bindings=bindings,line_origin='Actual compiled native source files, one-based',proof='METHOD_CONDITIONS.md separates mathematical index mapping from floating-point/native admission'))
status('PRE_FORWARD_CPU_AND_SOURCE_CHECKS_PASS',synthetic_tests=14,new_forwards=0)
