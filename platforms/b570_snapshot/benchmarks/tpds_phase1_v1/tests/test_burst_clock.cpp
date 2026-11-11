#include "../native/burst_clock.hpp"
#include <stdexcept>
int main(){
    int n=0;
    auto check=[&](bool x){if(!x)throw std::runtime_error("failed helper check");++n;};
    phase1::BurstClock c;
    check(c.native_main_to_first_result_s()<0);
    bool caught=false;try{c.test_burst_wall_s();}catch(const std::logic_error&){caught=true;}check(caught);
    c.result_ready();c.result_ready();c.begin_test();c.result_ready();c.finish();
    check(c.native_main_to_first_result_s()>=0);
    check(c.native_main_to_first_test_result_s()>=c.native_main_to_first_result_s());
    check(c.test_burst_wall_s()>=0);
    caught=false;try{c.result_ready();}catch(const std::logic_error&){caught=true;}check(caught);
    caught=false;try{c.begin_test();}catch(const std::logic_error&){caught=true;}check(caught);
    caught=false;try{c.finish();}catch(const std::logic_error&){caught=true;}check(caught);
    return n==8?0:1;
}
