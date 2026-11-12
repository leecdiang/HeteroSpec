"""Stage fixes without changing sources being compiled by build-v1."""
from pathlib import Path
import argparse,hashlib,json

HERE=Path(__file__).resolve().parent
CUDA=HERE/'source/ggml/src/ggml-cuda'
parser=argparse.ArgumentParser();parser.add_argument('--out',default='stage-v3');args=parser.parse_args()
OUT=HERE/args.out
if OUT.parent!=HERE:raise RuntimeError('isolated staging output required')
OUT.mkdir(exist_ok=False)
sources={name:(CUDA/name).read_text(encoding='utf8') for name in ['mmvq.cu','ggml-cuda.cu','hs_e03_runtime.hpp','hs_e03_runtime.cpp']}
before={name:hashlib.sha256((CUDA/name).read_bytes()).hexdigest() for name in sources}
needle='tensor->buffer->buft!=ggml_backend_cuda_buffer_type(ctx.device)'
if sources['mmvq.cu'].count(needle)!=1:raise RuntimeError('buffer fix anchor')
sources['mmvq.cu']=sources['mmvq.cu'].replace(needle,'ggml_backend_buffer_get_type(tensor->buffer)!=ggml_backend_cuda_buffer_type(ctx.device)')
shape_anchor='ne00<=0||ne01<=0||ne00%512!=0||ne01%2!=0||GGML_PAD(ne10,MATRIX_ROW_PADDING)!=ne00 ||'
if sources['mmvq.cu'].count(shape_anchor)!=1:raise RuntimeError('shape equality guard anchor')
sources['mmvq.cu']=sources['mmvq.cu'].replace(shape_anchor,
    'ne00<=0||ne01<=0||ne10!=ne00||ne0!=ne01||ne00%512!=0||ne01%2!=0||GGML_PAD(ne10,MATRIX_ROW_PADDING)!=ne00 ||')
span_anchor='''                throw std::runtime_error("e03 pair4 requires actual same-device CUDA buffers");
        }'''
if sources['mmvq.cu'].count(span_anchor)!=1:raise RuntimeError('allocation span guard anchor')
sources['mmvq.cu']=sources['mmvq.cu'].replace(span_anchor,'''                throw std::runtime_error("e03 pair4 requires actual same-device CUDA buffers");
            const auto allocation_base=reinterpret_cast<std::uintptr_t>(ggml_backend_buffer_get_base(tensor->buffer));
            const auto allocation_data=reinterpret_cast<std::uintptr_t>(tensor->data);
            const auto allocation_size=ggml_backend_buffer_get_size(tensor->buffer);
            if(allocation_data<allocation_base || allocation_data-allocation_base>allocation_size ||
               ggml_nbytes(tensor)>allocation_size-(allocation_data-allocation_base))
                throw std::runtime_error("e03 pair4 actual allocation span invalid before quantizer");
        }''')
h=sources['hs_e03_runtime.hpp']
h=h.replace('__declspec(dllexport) std::uint64_t hs_e03_loop4_dispatches();','''__declspec(dllexport) std::uint64_t hs_e03_loop4_dispatches();
__declspec(dllexport) std::uint64_t hs_e03_pair4_dispatch_attempts();
__declspec(dllexport) std::uint64_t hs_e03_packed_dispatch_attempts();
__declspec(dllexport) std::uint64_t hs_e03_loop4_dispatch_attempts();
__declspec(dllexport) int hs_e03_failure_code();
__declspec(dllexport) const char * hs_e03_failure_message();''')
h+='\nvoid hs_e03_record_failure(int code,const char * message) noexcept;\n'
sources['hs_e03_runtime.hpp']=h
sources['hs_e03_runtime.cpp']=sources['hs_e03_runtime.cpp'].replace(
    '"\\"metadata_function_calls_CUDA\\":false,',
    '"\\"dispatch_observation\\":\\"branch_attempt_before_launch_guard_not_submitted_or_completed\\",\\"metadata_function_calls_CUDA\\":false,')
sources['hs_e03_runtime.cpp']+='''
extern "C" __declspec(dllexport) std::uint64_t hs_e03_pair4_dispatch_attempts(){return routes[2].load();}
extern "C" __declspec(dllexport) std::uint64_t hs_e03_packed_dispatch_attempts(){return routes[1].load();}
extern "C" __declspec(dllexport) std::uint64_t hs_e03_loop4_dispatch_attempts(){return routes[0].load();}
static std::atomic<int> failure_state{0};
static std::atomic<int> failure_code{0};
static char failure_message[512]{};
void hs_e03_record_failure(int code,const char * message) noexcept {
    int expected=0;
    if(!failure_state.compare_exchange_strong(expected,1))return;
    unsigned i=0;
    if(message)for(;i<511 && message[i];++i)failure_message[i]=message[i];
    failure_message[i]=0;failure_code.store(code);failure_state.store(2,std::memory_order_release);
}
extern "C" __declspec(dllexport) int hs_e03_failure_code(){return failure_code.load();}
extern "C" __declspec(dllexport) const char * hs_e03_failure_message(){
    return failure_state.load(std::memory_order_acquire)==2?failure_message:"NO_COMPLETED_FAILURE_RECORD";
}
'''
s=sources['ggml-cuda.cu'];begin=s.index('static enum ggml_status ggml_backend_cuda_graph_compute(');end=s.index('\nstatic ',begin+20)
segment=s[begin:end]
opening=segment.index('{')
tail='    return GGML_STATUS_SUCCESS;\n}'
if segment.count(tail)!=1:raise RuntimeError('graph boundary tail not unique')
segment=segment[:opening+1]+'\n    try {'+segment[opening+1:]
segment=segment.replace(tail,'''    return GGML_STATUS_SUCCESS;
    } catch(const std::exception & error) {
        hs_e03_record_failure(1,error.what());
        return GGML_STATUS_FAILED;
    } catch(...) {
        hs_e03_record_failure(2,"non-standard exception inside CUDA DLL graph boundary");
        return GGML_STATUS_FAILED;
    }
}''')
sources['ggml-cuda.cu']=s[:begin]+segment+s[end:]
for name,text in sources.items():(OUT/name).write_text(text,encoding='utf8',newline='\n')
receipt={'schema':'heterospec.e03.runtime-stage-fixes.v1','before_sha256':before,
    'after_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in sources},
    'fixes':['public buffer type accessor for complete-type independence','catch C++ exceptions inside numerical DLL graph callback and return C enum error','CPU-only first-failure exports'],
    'not_claimed':['recoverable allocator/model-transfer API','budget denial recoverability','GPU qualification'],'model_requests':0,'kernel_launches':0}
(OUT/'SOURCE.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');print(json.dumps(receipt))
