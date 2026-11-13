// Standard-library-only successor admission probe: no model/backend/CUDA link.
#include "successor_gate.hpp"
#include <iostream>
using namespace hs::n1chain;
int main(int n,char**v){try{pilot_need(n==3&&hashfile(v[1])==v[2],"job SHA");auto j=PJ::parse(textfile(v[1]));SuccessorGate g(j);g.begin("R/C0/INITIAL");bool denied=false;try{g.rows(187);}catch(const Blocked&){denied=true;}pilot_need(denied&&g.state().at("consumed").at("rows")==0,"row overrun was not rejected before work");g.poison("injected failure");denied=false;try{g.guard();}catch(const Blocked&){denied=true;}pilot_need(denied,"poison bypass");durable(j.at("output").get<std::string>()+"/CPU_RESULT.json",PJ({{"status","PASS_REAL_PREEXEC_AND_SUCCESSOR_ROW_FAIL_CLOSED"},{"pid",::getpid()},{"models",0},{"backend_contexts",0},{"GPU_contexts",0},{"placements",0},{"forwards",0},{"synthetic_request_reservations",1},{"physical_rows",0}}).dump(2)+"\n");return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 74;}}
