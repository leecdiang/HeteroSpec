#pragma once
// Optional host-only timing aid. It never synchronizes a GPU or owns a model.
#include <chrono>
#include <cstddef>
#include <stdexcept>
namespace phase1 {
class BurstClock {
    using C=std::chrono::steady_clock;
    C::time_point started=C::now(),test_start,finished;
    bool in_test=false,ended=false;
    std::size_t ready=0;
    double first=-1,first_test=-1;
    double since(C::time_point t)const{return std::chrono::duration<double>(C::now()-t).count();}
public:
    void begin_test(){if(in_test||ended)throw std::logic_error("burst already started");in_test=true;test_start=C::now();}
    void result_ready(){if(ended)throw std::logic_error("finished burst");const double t=since(started);if(ready++==0)first=t;if(in_test&&first_test<0)first_test=t;}
    void finish(){if(!in_test||first_test<0||ended)throw std::logic_error("incomplete burst");finished=C::now();ended=true;}
    double native_main_to_first_result_s()const{return first;}
    double native_main_to_first_test_result_s()const{return first_test;}
    double test_burst_wall_s()const{if(!ended)throw std::logic_error("unfinished burst");return std::chrono::duration<double>(finished-test_start).count();}
};
} // namespace phase1
