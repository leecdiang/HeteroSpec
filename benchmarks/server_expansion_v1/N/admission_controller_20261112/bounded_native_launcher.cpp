// Compile/link/static-symbol artifact only. No activated production CLI.
// This file links only libc/libstdc++; neither this executable nor a native
// model worker is invoked by the CPU launcher tests.
#include "bounded_launcher.hpp"
#include <iostream>
hs::n1chain::BoundedLaunchResult native_controller_launch_entry(
 const hs::n1chain::BoundedLaunchSpec&spec,hs::n1chain::BudgetHooks&account){
 hs::n1chain::ProductionGate gate;
 return hs::n1chain::guarded_native_launch(gate,account,spec);
}
int main(){
 try{hs::n1chain::ProductionGate gate;gate.before_placement("CLI_NOT_ADMITTED");return 77;}
 catch(const std::exception&e){std::cerr<<"NATIVE_LAUNCHER_NOT_ADMITTED "<<e.what()<<'\n';return 77;}
}
