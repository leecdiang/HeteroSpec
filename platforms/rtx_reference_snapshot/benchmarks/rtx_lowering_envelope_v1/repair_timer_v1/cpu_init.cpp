#include "core_gate.h"
#include <chrono>
#include <type_traits>
using namespace repair113;
static_assert(std::is_same<decltype(&ggml_time_us),decltype(&ggml_time_ms)>::value,"frozen int64_t(void) clock ABI");
static void write(const fs::path&p,const Json&j){require(!fs::exists(p),"exclusive CPU receipt");std::ofstream f(p);f<<j.dump(2)<<"\n";require(bool(f),"CPU receipt write");}
static Json address(FARPROC p){HMODULE m=nullptr;require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,(LPCWSTR)p,&m),"host symbol owner");return {{"address",uint64_t((uintptr_t)p)},{"owner",module_path(m).u8string()}};}
int main(int argc,char**argv){
    if(argc!=5)return 2;std::string mode=argv[1];Json record={{"mode",mode},{"pid",GetCurrentProcessId()},{"GPU_plugin_loads",0},{"device_queries",0},{"graph_computes",0},{"model_requests",0}};
    try{
        no_gpu_modules();record["modules_before"]=modules();record["call_sequence"]=Json::array();
        // This genuinely calls the separately linked host's ggml_init/time APIs.
        record["call_sequence"].push_back("host_ggml_init_call");auto*context=ggml_init({0,nullptr,true});require(context,"host context");record["call_sequence"].push_back("host_ggml_init_returned");ggml_free(context);record["call_sequence"].push_back("host_ggml_free_returned");
        record["host_symbols"]={{"ggml_init",address((FARPROC)&ggml_init)},{"ggml_time_init",address((FARPROC)&ggml_time_init)},{"ggml_time_us",address((FARPROC)&ggml_time_us)}};
        record["call_sequence"].push_back("verified_core_load_resolve_call");CoreGate gate(argv[2],argv[3]);record["call_sequence"].push_back("verified_core_load_resolve_returned");no_gpu_modules();record["modules_after_cpu_core_load"]=modules();
#ifdef REPAIR_SHARED
        record["host_core_binding"]={{"ggml_init",gate.verify_shared_import("ggml_init")},{"ggml_time_init",gate.verify_shared_import("ggml_time_init")},{"ggml_time_us",gate.verify_shared_import("ggml_time_us")}};
#else
        record["host_core_binding"]="static core, distinct from DLL; negative-control executable only";
#endif
        auto version=(decltype(&ggml_version))gate.resolve("ggml_version");auto commit=(decltype(&ggml_commit))gate.resolve("ggml_commit");
        record["core_version"]=version();record["core_commit"]=commit();record["host_version"]=ggml_version();record["host_commit"]=ggml_commit();
        try{
            if(mode=="wrong_module")gate.verify_owner(GetProcAddress(GetModuleHandleW(L"kernel32.dll"),"GetTickCount64"));
            else if(mode=="missing_export")gate.resolve("ggml_time_init_NOT_A_REAL_EXPORT_PR113");
            else if(mode=="host_only"||mode=="missing_init")gate.microseconds();
            else if(mode=="wrong_order"){try{gate.microseconds();}catch(...){ }gate.initialize();}
            else{
                require(mode=="positive","known CPU mode");record["call_sequence"].push_back("owned_DLL_initializer_call");gate.initialize();record["call_sequence"].push_back("owned_DLL_initializer_returned");
                LARGE_INTEGER frequency{},begin{},end{};require(QueryPerformanceFrequency(&frequency),"QPC frequency");QueryPerformanceCounter(&begin);
                auto first=gate.microseconds();record["call_sequence"].push_back("DLL_us_returned");Json reads=Json::array();for(int i=0;i<32;i++)reads.push_back(gate.microseconds());
                Sleep(35);auto before=gate.microseconds();gate.initialize();auto after_wrapper=gate.microseconds();
                record["call_sequence"].push_back("test_repeat_real_DLL_init_call");gate.test_direct_reinitialize();record["call_sequence"].push_back("test_repeat_real_DLL_init_returned");auto after_export=gate.microseconds();Sleep(25);auto last=gate.microseconds();QueryPerformanceCounter(&end);
                auto low=gate.microseconds(),ms=gate.milliseconds(),high=gate.microseconds();
                record["readings_us"]=reads;record["first_us"]=first;record["before_repeat_us"]=before;record["after_wrapper_repeat_us"]=after_wrapper;record["after_actual_export_repeat_us"]=after_export;record["last_us"]=last;
                record["ms_bracket"]={{"lower_us",low},{"ms",ms},{"upper_us",high}};
                record["QPC_elapsed_us"]=double(end.QuadPart-begin.QuadPart)*1e6/double(frequency.QuadPart);
                require(before>=first&&after_wrapper>=before&&after_export>=after_wrapper&&last>after_export,"monotonic/reinitialize sequence");
                int64_t previous=first;for(const auto&value:reads){auto t=value.get<int64_t>();require(t>=previous,"nondecreasing clock");previous=t;}
                require(ms*1000>=low-1000&&ms*1000<=high+1000,"millisecond/microsecond units");
                double wall=record["QPC_elapsed_us"];require(last-first>=wall*.8&&last-first<=wall*1.2+2000,"clock observed nonzero interval");
                record["call_sequence"].push_back("DLL_ms_us_interval_checks_passed");record["admitted"]=true;
            }
            if(mode!="positive")throw std::runtime_error("negative incorrectly admitted");
        }catch(const std::exception&e){
            if(mode=="positive"||std::string(e.what())=="negative incorrectly admitted")throw;
            record["admitted"]=false;record["expected_rejection"]=e.what();
        }
        record["core_gate"]=gate.receipt();no_gpu_modules();record["modules_end"]=modules();write(argv[4],record);return 0;
    }catch(const std::exception&e){record["unexpected_error"]=e.what();record["admitted"]=false;record["modules_end"]=modules();write(argv[4],record);return 1;}
}
