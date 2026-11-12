#include "launch_accounting.hpp"
#include <cstdio>
#include <stdexcept>

static void need(bool condition,const char * text) {if(!condition)throw std::runtime_error(text);}
int main() {
    using hs_operator_accounting::LaunchCounts;
    unsigned passed=0;
    try {
        { LaunchCounts c;c.before();c.submission_succeeded();c.before();c.submission_succeeded();
          need(c.attempted==2&&c.submitted==2,"successful pair accounting");++passed; }
        { LaunchCounts c;try{c.before();c.submission_succeeded();throw std::runtime_error("numerical mismatch");}catch(...){}
          need(c.attempted==1&&c.submitted==1,"mismatch must retain previous launch");++passed; }
        { LaunchCounts c;try{c.before();c.submission_succeeded();c.before();throw std::runtime_error("submission failure");}catch(...){}
          need(c.attempted==2&&c.submitted==1,"second submission failure must remain charged");++passed; }
        { LaunchCounts c;c.cap=0;bool refused=false;try{c.before();}catch(...){refused=true;}
          need(refused&&c.attempted==0,"zero allowance must refuse before dispatch");++passed; }
        { LaunchCounts c;bool refused=false;try{c.submission_succeeded();}catch(...){refused=true;}
          need(refused&&c.submitted==0,"submission without attempt");++passed; }
        { LaunchCounts c;c.cap=2;c.before();c.submission_succeeded();c.before();c.submission_succeeded();
          bool refused=false;try{c.before();}catch(...){refused=true;}
          need(refused&&c.attempted==2&&c.submitted==2,"cap must not be exceeded");++passed; }
        std::printf("{\"status\":\"PASS_CPU_NATIVE_ACCOUNTING_ONLY\",\"cases\":%u,\"CUDA_contexts\":0,\"kernel_launches\":0}\n",passed);
        return 0;
    } catch(const std::exception & e) {std::fprintf(stderr,"%s\n",e.what());return 2;}
}
