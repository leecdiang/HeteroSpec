"""Additive failure-accounting fix; build stays execution-disabled."""
from pathlib import Path
import difflib,hashlib,json,shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--out',default='operator-v3')
args=parser.parse_args()
OUT=HERE/args.out
if OUT.parent!=HERE:raise RuntimeError('isolated output directory required')
OUT.mkdir(exist_ok=False)
(OUT/'native').mkdir()
(OUT/'build_tools').mkdir()
original=(ROOT/'native/operator_probe.cu').read_text(encoding='utf8')
s=original
def once(old,new):
    global s
    if s.count(old)!=1: raise RuntimeError('source anchor not unique: '+old[:90])
    s=s.replace(old,new)
once('#include "two_group_q8.cuh"','#include "two_group_q8.cuh"\n#include "launch_accounting.hpp"')
once('static void save(const std::string & path, const void * data, size_t bytes) {',
     'static std::vector<std::string> attempted_capture_paths;\nstatic void save(const std::string & path, const void * data, size_t bytes) {\n    if(path.size()>=4 && path.substr(path.size()-4)==".bin")attempted_capture_paths.push_back(path);')
once('float * y, int k, int m, int pk, cudaStream_t stream) {','float * y, int k, int m, int pk, cudaStream_t stream, hs_operator_accounting::LaunchCounts & counts) {')
once('        hs_two_group_q8<<<','        counts.before();\n        hs_two_group_q8<<<')
once('>(w,a,y,k,m,pk);','>(w,a,y,k,m,pk);\n        check(cudaGetLastError());counts.submission_succeeded();')
once('            mul_mat_vec_q<GGML_TYPE_Q8_0,4,false><<<','            counts.before();\n            mul_mat_vec_q<GGML_TYPE_Q8_0,4,false><<<')
once('4*stride,4*m,make_uint3(1,0,1),m*k/32,8*stride,8*m,0);','4*stride,4*m,make_uint3(1,0,1),m*k/32,8*stride,8*m,0);\n            check(cudaGetLastError());counts.submission_succeeded();')
once('    std::string out;','    std::string out;\n    hs_operator_accounting::LaunchCounts counts;\n    int quantizers=0,projections=0;')
once('        int quantizers=0,projections=0;','')
once('            ++quantizers;result["quantizer_launch_attempts"]=quantizers;','            counts.before();\n            ++quantizers;result["quantizer_launch_attempts"]=quantizers;')
once('            check(cudaGetLastError());\n        };\n        auto project=', '            check(cudaGetLastError());counts.submission_succeeded();\n        };\n        auto project=')
once('            projections+=arm==0?2:1;result["projection_launch_attempts_reserved"]=projections;\n            launch_arm(arm,dw,da,dy,k,m,pk,stream);',
     '            const auto before=counts.attempted;\n            try {launch_arm(arm,dw,da,dy,k,m,pk,stream,counts);}\n            catch(...) {projections+=int(counts.attempted-before);throw;}\n            projections+=int(counts.attempted-before);')
once('    if(!out.empty()) {','''    result["kernel_launch_attempts"]=counts.attempted;
    result["kernel_launch_submissions"]=counts.submitted;
    result["kernel_launches"]=counts.attempted; // failures remain charged
    result["quantizer_launch_attempts"]=quantizers;
    result["projection_launch_attempts"]=projections;
    result["completed_kernel_activity_count"]="unknown";
    result["counter_scope"]="explicit standalone quantizer/MMVQ sites only; not model backend";
    std::uint64_t capture_bytes=0;bool capture_bytes_known=true;
    for(const auto & path:attempted_capture_paths){
        WIN32_FILE_ATTRIBUTE_DATA info{};
        if(GetFileAttributesExA(path.c_str(),GetFileExInfoStandard,&info))
            capture_bytes+=(std::uint64_t(info.nFileSizeHigh)<<32)|info.nFileSizeLow;
        else if(GetLastError()!=ERROR_FILE_NOT_FOUND)capture_bytes_known=false;
    }
    result["capture_bytes"]=capture_bytes_known?json(capture_bytes):json(nullptr);
    result["capture_binary_bytes_lower_bound"]=capture_bytes;
    result["capture_bytes_scope"]="all attempted raw binary output paths, including partial failed writes; result metadata accounted separately by supervisor";
    if(!out.empty()) {''')
(OUT/'native/operator_probe.cu').write_text(s,encoding='utf8',newline='\n')
for src in [ROOT/'native/two_group_q8.cuh',HERE/'launch_accounting.hpp']:
    shutil.copy2(src,OUT/'native'/src.name)
shutil.copy2(ROOT/'build_tools/build_operator.py',OUT/'build_tools/build_operator.py')
diff=''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='frozen-e01/operator_probe.cu',tofile='e02/operator-v2/operator_probe.cu'))
(OUT/'OPERATOR_ACCOUNTING.patch').write_text(diff,encoding='utf8')
receipt={'parent_source_sha256':hashlib.sha256(original.encode()).hexdigest(),'new_source_sha256':hashlib.sha256(s.encode()).hexdigest(),
         'scope':'host launch-accounting only; GPU arithmetic unchanged; execution disabled',
         'old_source_modified':False,'model_requests':0,'CUDA_contexts':0,'kernel_launches':0}
(OUT/'SOURCE.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(receipt))
