#include "verification_spec.hpp"
#include <iostream>
int main(){
    using server_expansion::VerificationSpec; unsigned n=0;
    for(unsigned k:{3u,7u}){
        VerificationSpec s{k,4,k+1};if(s.max_rows()!=k+1)return 1;++n;
        for(unsigned rows=1;rows<=k+1;++rows){
            std::vector<uint8_t> m(rows,1);s.check_observed(rows,m,rows);++n;
            m.assign(rows,0);m.back()=1;s.check_observed(rows,m,1);++n;
            bool threw=false;try{s.check_observed(rows,m,2);}catch(const std::invalid_argument&){threw=true;}
            if(!threw) return 2;
            ++n;
        }
    }
    bool threw=false;try{VerificationSpec{7,4,4}.check();}catch(const std::invalid_argument&){threw=true;}
    if(!threw) return 3;
    ++n;std::cout<<n<<" specification checks; no llama/CUDA execution\n";
}
