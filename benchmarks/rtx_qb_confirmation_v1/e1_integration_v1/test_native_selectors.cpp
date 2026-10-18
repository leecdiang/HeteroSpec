// CPU-only test of the actual generated header. No model/backend/operator calls.
#include "capture95.h"
#include <iostream>
int main() {
    auto put=[](const char * k,const char * v){if(_putenv_s(k,v))throw std::runtime_error("environment setup");};
    put("HS_E1_LAYER","18");if(q95capture::layer()!=18)return 1;
    hsc::w.prefill=true;put("HS_E1_PHASE","0");if(!q95capture::selected_phase())return 2;
    put("HS_E1_PHASE","1");if(q95capture::selected_phase())return 3;
    hsc::w.prefill=false;if(!q95capture::selected_phase())return 4;
    put("HS_E1_Q","4");if(q95capture::setting("HS_E1_Q",1,4)!=4)return 5;
    put("HS_E1_MIN_KEY","128");if(q95capture::setting("HS_E1_MIN_KEY",0,1024)!=128)return 6;
    int rejected=0;
    for(const char * bad:{"-1","256","bad","1x"}) {
        put("HS_E1_LAYER",bad);
        try{(void)q95capture::layer();}catch(const std::runtime_error &){rejected++;}
    }
    if(rejected!=4)return 7;
    std::cout<<"PASS: actual native header layer/phase/q/key selectors and four invalid values; zero model/backend/operator calls\n";
    return 0;
}
