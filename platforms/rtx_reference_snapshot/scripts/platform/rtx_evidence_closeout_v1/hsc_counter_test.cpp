#include "hsc_counter.h"
#include <cassert>
int main(){
    using namespace hsc;
    begin("counts",10);set_origin(initial);commit();propose(3);verification(3,1,true,false,false);
    set_origin(accepted);commit();set_origin(correction);commit();finish_cycle();
    assert(w.generated==3&&w.verified==3&&w.accept==1&&w.mismatch==1&&w.unexamined==1);
    assert(w.output==3&&w.prefix[1]==1&&w.progress[2]==1&&w.stamps.empty());
    assert(w.attempted_pos[0]==1&&w.attempted_pos[1]==1&&w.attempted_pos[2]==0);
    begin("counts",10);set_origin(initial);commit();propose(3);verification(3,3,false,false,false);
    set_origin(accepted);commit();finish_cycle(); // cap prevents two matching proposals and bonus
    assert(w.accept==1&&w.terminal==2&&w.output==2&&w.origin[bonus]==0);
    begin("counts",10);set_origin(initial);commit();propose(2);verification(2,2,false,false,false);
    set_origin(accepted);commit();commit();set_origin(bonus);commit();finish_cycle();
    assert(w.accept==2&&w.origin[bonus]==1&&w.progress[3]==1&&w.output==4);
    begin("baseline",10);propose(3);verification(3,3,false,false,false);commit();finish_cycle();
    assert(w.generated==0&&w.output==0&&w.stamps.empty());
    begin("lite",10);assert(!w.stamps.empty()&&!is_heavy());
    begin("heavy",10);assert(is_heavy());
    begin("counts",10);int context;
    decode_begin(&context,"draft",false,3);physical(&context,1);physical(&context,1);physical(&context,1);decode_end();
    assert(w.draft_caller_calls==1&&w.draft_caller_rows==3&&w.draft_calls==3&&w.draft_rows==3&&w.draft_catchup_calls==3);
    begin("counts",10);{proposal_guard g;decode_begin(&context,"draft",false,1);physical(&context,1);decode_end();}
    assert(w.draft_proposal_calls==1&&!w.proposal_phase&&w.stamps.empty());
}
