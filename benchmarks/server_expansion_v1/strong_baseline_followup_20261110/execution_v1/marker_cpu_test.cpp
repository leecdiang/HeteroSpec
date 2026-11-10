#include "hs_strong_ref1.hpp"
#include "request_contract.hpp"
#include <iostream>
int main(){
    try{
        ggml_tensor t{};t.op=GGML_OP_MUL_MAT;hs_strong_mark(&t);
        std::strcpy(t.name,"Qcur-0");if(!hs_strong_marked(&t))return 1;
        ggml_tensor clone=t;if(!hs_strong_marked(&clone))return 2;
        bool rejected=false;try{hs_strong_mark(&t);}catch(const std::runtime_error&){rejected=true;}
        if(!rejected)return 3;
        ggml_tensor other{};other.op=GGML_OP_ADD;rejected=false;
        try{hs_strong_mark(&other);}catch(const std::runtime_error&){rejected=true;}
        if(!rejected)return 4;
        other.op=GGML_OP_MUL_MAT;std::strcpy(other.name,"hs_backend_ref1_fake");
        if(hs_strong_marked(&other))return 5;
        if(!hs_m_input_valid(1023,1,1024))return 6;
        if(hs_m_input_valid(1024,1,1024))return 7;
        if(hs_m_input_valid(20,0,1024))return 8;
        if(hs_m_input_valid(0,1,1024))return 9;
        if(!hs_m_input_valid(192,128,1024))return 10;
        if(hs_m_input_valid(20,129,1024))return 11;
        std::cout<<"{\"scope\":\"CPU_metadata_only\",\"passed_cases\":11,\"native_model_requests\":0}\n";
        return 0;
    }catch(...){return 6;}
}
