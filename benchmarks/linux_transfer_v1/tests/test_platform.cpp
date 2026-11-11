#include "linux_platform.hpp"
#include "linux_profile_disabled.hpp"
#include <iostream>
int main(){
 int checks=0;
 auto exe=linux_transfer::executable();if(!exe.is_absolute()||!std::filesystem::is_regular_file(exe))return 1;++checks;
 auto m=linux_transfer::modules();if(m.empty()||m[0]!=exe.string())return 2;++checks;
 bool rejected=false;try{profile::init();}catch(const std::runtime_error&){rejected=true;}if(!rejected)return 3;++checks;
 std::cout<<checks<<" actual POSIX helper checks passed; no model/CUDA execution\n";
}
