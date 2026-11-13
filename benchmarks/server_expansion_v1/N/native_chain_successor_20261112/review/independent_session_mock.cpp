// Independent state-machine adversarial tests. Standard library + abstract Core
// only; deliberately no native backend, model library, CUDA or dynamic loader.
#include "../native/session.hpp"
#include <iostream>
#include <set>
using namespace hs::n1chain;
namespace {
void rejects(const std::function<void()>&f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}require(failed,"expected failure");}
struct Meter:BudgetHooks {
 bool dead=false,deny_request=false;size_t rows=0,row_limit=9999;std::string active;std::set<std::string>seen;
 void check(){require(!dead,"mock budget poisoned");}
 void before_backend_init(const std::string&)override{throw Blocked("mock never backend init");}
 void before_model_load(const std::string&)override{throw Blocked("mock never model load");}
 void before_context(const std::string&)override{throw Blocked("mock never native context");}
 void before_placement(const std::string&)override{throw Blocked("mock never placement");}
 void before_request(const std::string&id)override{check();require(!deny_request&&active.empty()&&!seen.count(id),"mock request rejection");seen.insert(id);active=id;}
 void before_decode(const std::string&id,size_t n)override{check();require(active==id&&n>0&&rows+n<=row_limit,"mock row cap");rows+=n;}
 void before_mutation(const std::string&id,const std::string&)override{check();require(active==id,"mock mutation needs active request");}
 void finish_request(const std::string&id,const std::string&status)override{check();require(active==id&&status=="COMPLETED","mock terminal status mismatch");active.clear();}
 void poison(const std::string&)noexcept override{dead=true;}
};
struct Mock:Core {
 Meter&m;Tokens ids;bool bad_head=false,bad_greedy=false,trim_error=false,partial_error=false,start_error=false;TrimResult trim_result=TrimResult::Done;size_t clears=0,appends=0;
 explicit Mock(Meter&meter):m(meter){}
 void start_request(const std::string&id)override{require(m.active==id,"request must be charged before Core start hook");if(start_error)throw Blocked("mock request-start metadata failure");}
 size_t head()const override{return ids.size();}size_t vocabulary()const override{return 32;}
 bool is_eog(int32_t t)const override{return t==31;}
 int32_t greedy(const std::vector<float>&v)const override{return bad_greedy?32:int32_t(std::max_element(v.begin(),v.end())-v.begin());}
 std::vector<float> append(const std::string&id,const Tokens&t,size_t p,bool initial)override{m.before_decode(id,t.size());require(p==ids.size(),"mock actual offset");appends++;if(partial_error){ids.push_back(t.front());throw Blocked("mock partial physical decode");}if(!(bad_head&&!initial))ids.insert(ids.end(),t.begin(),t.end());std::vector<float>v(32,0);v[3]=v[4]=1;return v;}
 TrimResult trim(const std::string&id,size_t p)override{m.before_mutation(id,"trim");if(trim_error)throw Blocked("unexpected trim failure with unchanged head");if(trim_result==TrimResult::Done)ids.resize(p);return trim_result;}
 void clear(const std::string&id)override{m.before_mutation(id,"clear");ids.clear();clears++;}
};
Session::Checkpoint no_capture=[](const char*,const State&){};
void complete(Session&s,Meter&m,const std::string&id){(void)m;(void)id;s.generate({},no_capture);}
}
int main(){int passed=0;auto test=[&](const std::string&name,const std::function<void()>&body){body();passed++;std::cout<<"PASS "<<name<<'\n';};
 test("pending full-prefix continuation materializes pending exactly once",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10},1,false,0,no_capture);s.append(no_capture);complete(s,m,"a");require(s.state().pending==3,"actual sampled pending");s.begin("b",{10,3,11},1,false,0,no_capture);require(s.state().retained==1,"materialized bound");s.append(no_capture);require(c.ids==Tokens({10,3,11})&&m.rows==3,"exact two-row suffix");});
 test("fully cached prompt invalidates frontier and replays final token",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10,11},1,false,0,no_capture);s.append(no_capture);complete(s,m,"a");s.begin("b",{10,11},1,false,0,no_capture);require(s.state().retained==1&&!s.state().frontier_valid,"cache backoff invalid frontier");s.append(no_capture);require(m.rows==3&&s.state().frontier_owned,"fresh final row owned");});
 test("generation row-budget rejection poisons and retains consumption",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10},2,false,0,no_capture);s.append(no_capture);m.row_limit=1;rejects([&]{s.generate({},no_capture);});require(s.poisoned()&&m.dead&&m.rows==1,"budget error is terminal");rejects([&]{s.reset("a",no_capture);});});
 test("partial physical append failure spends reservation and forbids reset retry",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10,11},1,false,0,no_capture);c.partial_error=true;rejects([&]{s.append(no_capture);});require(s.poisoned()&&m.dead&&m.rows==2&&c.head()==1,"partial physical work retained and closed");rejects([&]{s.reset("a",no_capture);});});
 test("generation returned full row with wrong actual head cannot reach terminal",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10},2,false,0,no_capture);s.append(no_capture);c.bad_head=true;bool terminal=false;rejects([&]{s.generate({},[&](const char*phase,const State&){terminal|=std::string(phase)=="TERMINAL";});});require(s.poisoned()&&m.dead&&!terminal&&m.rows==2,"bad native head stops before terminal receipt");});
 test("unexpected trim failure with unchanged head is not fallback proof",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10,11},1,false,0,no_capture);s.append(no_capture);complete(s,m,"a");c.trim_error=true;const auto clears=c.clears;rejects([&]{s.begin("b",{10,12},1,false,0,no_capture);});require(s.poisoned()&&c.clears==clears,"no implicit second pass after native error");});
 test("request and forced-tape guard failures poison the attempt",[]{for(bool request_failure:{false,true}){Meter m;Mock c(m);Session s(c,m);if(request_failure){m.deny_request=true;rejects([&]{s.begin("a",{10},1,false,0,no_capture);});}else{s.begin("a",{10},1,false,0,no_capture);s.append(no_capture);rejects([&]{s.generate({32},no_capture);});}require(s.poisoned()&&m.dead,"entry/forced guard must poison");}});
 test("request-start hook failure is charged before producer and poisons",[]{Meter m;Mock c(m);Session s(c,m);c.start_error=true;bool built=false;rejects([&]{s.begin_lazy("a",[&]{built=true;return Tokens{10};},1,false,0,no_capture);});require(m.seen.count("a")&&m.rows==0&&!built&&s.poisoned()&&m.dead,"hook failure retains charged request without producer or decode");});
 test("out-of-vocabulary greedy output cannot become pending",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10},1,false,0,no_capture);s.append(no_capture);c.bad_greedy=true;rejects([&]{s.generate({},no_capture);});require(s.poisoned()&&m.dead,"invalid sampled token is terminal error");});
 test("cold prefix alignment is independently built and owns its fresh prefix output",[]{Meter m;Mock c(m);Session s(c,m);size_t aligned=999;s.begin("a",{10,11,12},1,true,2,[&](const char*phase,const State&st){if(std::string(phase)=="POST_RECONCILE")aligned=st.materialized.size();});require(aligned==2&&c.clears==1&&c.ids==Tokens({10,11}),"cold actual prefix from empty");s.append(no_capture);require(c.ids==Tokens({10,11,12})&&m.rows==3,"cold complete canonical IDs");});
 test("checkpoint write failure after append poisons without refund",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10},1,false,0,no_capture);rejects([&]{s.append([](const char*,const State&){throw Blocked("synthetic partial writer failure");});});require(s.poisoned()&&m.dead&&m.rows==1,"failed capture closes request after charged decode");});
 test("old owned output remains a distinct stable copy across continuation",[]{Meter m;Mock c(m);Session s(c,m);s.begin("a",{10},1,false,0,no_capture);s.append(no_capture);complete(s,m,"a");s.begin("b",{10,3,11},1,false,0,no_capture);const auto before=s.previous_owned();s.append(no_capture);require(before==s.previous_owned()&&before==s.previous_before()&&before.size()==32,"old full output owner survives new decode");});
 std::cout<<"{\"tests\":"<<passed<<",\"failures\":0,\"evidence\":\"INDEPENDENT_STD_ONLY_SYNTHETIC_SESSION\",\"backend_init\":0,\"model_loads\":0,\"native_contexts\":0,\"placements\":0,\"forwards\":0}\n";
}
