#pragma once
#include <array>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <stdexcept>

// One sequence, one server writer. Hooks never wait for a GPU or modify a tensor.
namespace hsc {
enum Mode { baseline, counts, lite, heavy };
enum Origin { initial, accepted, bonus, correction, fallback };
struct Stamp { const char * event; int role; int rows; int64_t ns; };
struct Work {
    Mode mode=counts; bool active=false, proposal_phase=false, pending=false, unsupported_replay=false;
    void * context=nullptr; int role=0; bool prefill=false; int caller_rows=0;
    int64_t prompt=0, output=0, generated=0, verified=0, accept=0, mismatch=0, unexamined=0, terminal=0;
    int64_t cycles=0, rollback=0;
    int64_t draft_prefill_calls=0,draft_prefill_rows=0,draft_calls=0,draft_rows=0;
    int64_t draft_caller_calls=0,draft_caller_rows=0;
    int64_t draft_proposal_calls=0,draft_proposal_rows=0,draft_catchup_calls=0,draft_catchup_rows=0;
    int64_t target_prefill_calls=0,target_prefill_rows=0,target_calls=0,target_rows=0;
    int64_t target_verify_calls=0,target_replay_calls=0,target_fallback_calls=0;
    int64_t physical_calls=0,physical_rows=0;
    int64_t graphs_reused=0,target_prefill_physical_calls=0,draft_prefill_physical_calls=0;
    std::array<int64_t,5> target_continuation_physical{};
    std::array<int64_t,1025> target_width{},target_physical{},draft_physical{};
    std::array<int64_t,5> prefix{},progress{},verify_width{},attempted_pos{},accepted_pos{};
    std::array<int64_t,5> origin{};
    int cycle_n=0,cycle_a=0,cycle_committed=0,cycle_accepted_committed=0;
    bool cycle_mismatch=false,cycle_terminal=false,cycle_active=false;
    Origin current=fallback;
    std::vector<Stamp> stamps;
};
inline Work w;
inline bool counted(){return w.active && w.mode!=baseline;}
inline bool timed(){return w.active && (w.mode==lite||w.mode==heavy);}
inline bool is_heavy(){return w.active && w.mode==heavy;}
inline void stamp(const char * name,int role=0,int rows=0){
    if(timed())w.stamps.push_back({name,role,rows,std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count()});
}
inline void begin(const std::string & mode,int prompt){
    w=Work{};w.active=true;w.prompt=prompt;
    if(mode=="baseline")w.mode=baseline;else if(mode=="counts")w.mode=counts;
    else if(mode=="lite")w.mode=lite;else if(mode=="heavy")w.mode=heavy;
    else throw std::runtime_error("invalid hs_closeout_mode");
    if(timed())w.stamps.reserve(2048);
    stamp("request_native_begin");
}
inline void decode_begin(void * ctx,const char * role,bool prefill,int rows){
    w.context=ctx;w.role=std::strcmp(role,"target")==0?1:2;w.prefill=prefill;w.caller_rows=rows;
    if(counted()){
        if(w.role==1){
            if(prefill){w.target_prefill_calls++;w.target_prefill_rows+=rows;}
            else {w.target_calls++;w.target_rows+=rows;if(rows>=0&&rows<=1024)w.target_width[rows]++;
                if(w.unsupported_replay)w.target_replay_calls++;else if(w.pending)w.target_verify_calls++;else w.target_fallback_calls++;}
        }else{
            if(prefill){w.draft_prefill_calls++;w.draft_prefill_rows+=rows;}
            else {w.draft_caller_calls++;w.draft_caller_rows+=rows;}
        }
    }
    stamp("decode_api_begin",w.role,rows);
}
inline void decode_end(){stamp("decode_api_return_enqueue_only",w.role,w.caller_rows);w.context=nullptr;}
inline void physical(void * ctx,int rows){
    if(counted()&&w.context==ctx){w.physical_calls++;w.physical_rows+=rows;
        if(rows>=0&&rows<=1024)(w.role==1?w.target_physical:w.draft_physical)[rows]++;
        if(w.prefill){if(w.role==1)w.target_prefill_physical_calls++;else w.draft_prefill_physical_calls++;}
        else if(w.role==1&&rows>=0&&rows<5)w.target_continuation_physical[rows]++;
        if(w.role==2&&!w.prefill){w.draft_calls++;w.draft_rows+=rows;
            if(w.proposal_phase){w.draft_proposal_calls++;w.draft_proposal_rows+=rows;}
            else {w.draft_catchup_calls++;w.draft_catchup_rows+=rows;}}
    }
}
inline void reused(void * ctx){if(counted()&&w.context==ctx)w.graphs_reused++;}
struct proposal_guard {bool before;proposal_guard():before(w.proposal_phase){w.proposal_phase=true;}~proposal_guard(){w.proposal_phase=before;}};
inline void propose(int n){if(counted()){w.generated+=n;w.pending=n>0;}}
inline void verification(int n,int a,bool numerical_mismatch,bool terminal_rejection,bool replay){
    stamp("target_sampling_natural_ready",1,n+1);
    if(!counted())return;
    if(replay){w.unsupported_replay=true;return;}
    w.verified+=n;w.cycles++;w.verify_width[n+1]++;
    w.cycle_n=n;w.cycle_a=a;w.cycle_committed=0;w.cycle_accepted_committed=0;
    w.cycle_mismatch=numerical_mismatch;w.cycle_terminal=terminal_rejection;w.cycle_active=true;
    for(int i=0;i<(numerical_mismatch||terminal_rejection?a+1:n)&&i<5;i++)w.attempted_pos[i]++;
}
inline void set_origin(Origin o){w.current=o;}
inline void commit(){
    if(counted()){
        w.output++;w.origin[w.current]++;
        if(w.cycle_active){w.cycle_committed++;if(w.current==accepted){w.cycle_accepted_committed++;if(w.cycle_accepted_committed<=5)w.accepted_pos[w.cycle_accepted_committed-1]++;}}
    }
}
inline void finish_cycle(){
    if(!counted()||!w.cycle_active)return;
    int a=w.cycle_accepted_committed;
    w.accept+=a;w.terminal+=w.cycle_a-a;
    if(w.cycle_mismatch){w.mismatch++;w.unexamined+=w.cycle_n-w.cycle_a-1;}
    else if(w.cycle_terminal){w.terminal+=w.cycle_n-w.cycle_a;}
    w.prefix[a]++;w.progress[w.cycle_committed]++;w.cycle_active=false;w.pending=false;
}
inline void rollback(){if(counted())w.rollback++;stamp("kv_trim_call");}
}
