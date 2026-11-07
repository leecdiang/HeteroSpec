#include "../native/target_capture.hpp"
#include <iostream>
int main(int argc,char**argv){
    if(argc!=2)return 1;
    llama_context c;llama_model m;
    tpds_decisive::capture_existing(&c,&m,argv[1],-1);
    if(std::filesystem::file_size(std::filesystem::path(argv[1])/"frontier.f32")!=16)return 2;
    bool rejected=false;try{tpds_decisive::capture_existing(&c,&m,argv[1],-1);}catch(const std::runtime_error&){rejected=true;}
    if(!rejected)return 3;
    std::cout<<"API-stub header compile and two file behavior checks; NOT native llama/model evidence\n";
}
