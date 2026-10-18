#include "timing_loop.h"
#include <iostream>
#include <string>
int main(){try{
    for(std::string kind:{"compute","sync","output"}){
        struct C{int64_t frequency=1000,t=10;int64_t now(){return t;}}c;
        struct O{C&c;std::string k;void before(int){}int compute(){c.t+=2;return k=="compute"?1:0;}int sync(){c.t+=3;return k=="sync"?1:0;}void readback(int){c.t+=4;}void verify(int){if(k=="output")throw std::runtime_error("CPU_ONLY_OUTPUT_FAILURE");}}o{c,kind};
        std::vector<s1b::Interval>partial;bool failed=false;try{s1b::loop(c,o,8,&partial);}catch(...){failed=true;}
        s1b::need(failed&&partial.size()==1&&partial[0].sync_return==15,"partial attempt lost");
        s1b::need(kind!="output"||partial[0].readback_return==19,"failed output timestamp lost");
    }
    std::cout<<"{\"status\":\"PASS\",\"partial_failure_cases\":3,\"GPU_queries\":0,\"CUDA_loads\":0,\"graph_computes\":0}\n";return 0;
}catch(...){return 2;}}
