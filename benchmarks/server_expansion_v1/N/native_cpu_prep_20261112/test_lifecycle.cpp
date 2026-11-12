#include "lifecycle.hpp"
#include <functional>
#include <iostream>
using namespace n1a;
struct M:Meter{size_t charged=0,limit=9999;void reserve_row()override{need(charged<limit,"budget");++charged;}};
struct B:Backend{Tokens ids;Trim result=Trim::Done;bool native=false,fail=false,mutating=false,nan=false,wrong=false;size_t nv=32;bool is_mock()const override{return !native;}size_t head()const override{return ids.size();}Trim trim(size_t n)override{if(result==Trim::Done||mutating)ids.resize(n);return result;}void clear()override{ids.clear();}std::vector<float>decode_one(int32_t t,size_t p)override{need(p==ids.size(),"position");ids.push_back(t);if(fail)throw std::runtime_error("injected after mutation");std::vector<float>v(nv,0);v[3]=1;v[4]=1;if(nan)v[0]=NAN;if(wrong)v.pop_back();return v;}};
void rejects(const std::function<void()>&f){bool threw=false;try{f();}catch(...){threw=true;}need(threw,"expected rejection");}
int main(){int n=0;auto test=[&](const std::function<void()>& f){f();++n;};
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);s.append({10});need(s.generate(1,{31})==Tokens{3},"greedy lowest tie");need(s.s.pending==3&&s.s.materialized==Tokens{10},"pending");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},3);s.append({10});s.generate(3,{3});need(m.charged==1&&s.s.generated.size()==1,"EOG pending");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},3);s.append({10});s.generate(3,{31});need(m.charged==3&&s.s.generated.size()==3,"cap no extra forward");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);s.append({10});s.generate(1,{31});s.s.logical={10,11};s.s.pending=11;auto k=s.begin({10,11,12},1);need(k==1,"pending materialized head");s.append({10,11,12});need(b.ids==Tokens({10,11,12})&&m.charged==3,"append two");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10,11},1);s.append({10,11});s.generate(1,{31});need(s.begin({10,11},1)==1,"cached frontier replay");rejects([&]{s.sample();});s.append({10,11});need(m.charged==3,"last replay once");});
 for(auto r:{Trim::Unsupported,Trim::FailedWithoutMutation})test([r]{B b;M m;Session s(b,m,32);s.begin({10,11},1);s.append({10,11});s.generate(1,{31});b.result=r;need(s.begin({10,12},1)==0&&b.head()==0,"common rebuild");s.append({10,12});need(m.charged==4,"fallback charged");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10,11},1);s.append({10,11});s.generate(1,{31});b.result=Trim::FailedWithoutMutation;b.mutating=true;rejects([&]{s.begin({10,12},1);});need(s.poisoned,"false no-mutation poisons");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);b.fail=true;rejects([&]{s.append({10});});need(m.charged==1&&s.poisoned,"failed decode charged");rejects([&]{s.reset();});});
 test([]{B b;M m;m.limit=0;Session s(b,m,32);s.begin({10},1);rejects([&]{s.append({10});});need(b.head()==0,"pre budget");});
 test([]{B b;M m;Session s(b,m,32);rejects([&]{s.begin(Tokens(4096,1),128);});need(b.head()==0&&m.charged==0,"capacity pre-mutation");});
 test([]{B b;M m;Session s(b,m,32);rejects([&]{s.begin({-1},1);});rejects([&]{s.begin({32},1);});});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);s.append({10});auto owned=s.s.frontier;s.generate(1,{31});s.begin({11},1,true);s.append({11});need(owned[3]==1&&b.ids==Tokens{11},"owned output/cold fresh");});
 test([]{B b;M m;Session s(b,m,32);b.nan=true;s.begin({1},1);rejects([&]{s.append({1});});need(s.poisoned,"NaN poison");});
 test([]{B b;M m;Session s(b,m,32);b.wrong=true;s.begin({1},1);rejects([&]{s.append({1});});});
 test([]{B b;M m;b.native=true;rejects([&]{Session s(b,m,32);});});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);s.append({10});s.generate(1,{31});s.reset();need(b.head()==0&&!s.s.pending&&!s.s.frontier_valid,"reset ownership");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10,11},1);m.limit=1;rejects([&]{s.append({10,11});});need(s.poisoned,"partial append poisons");rejects([&]{s.generate(1,{31});});});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);rejects([&]{s.generate(1,{31});});need(m.charged==0,"no append no sample");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);s.append({10});rejects([&]{s.begin({11},1);});need(b.ids==Tokens{10},"active request cannot be replaced");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);rejects([&]{s.append({11});});need(m.charged==0,"canonical locked");s.append({10});rejects([&]{s.generate(2,{31});});need(!s.s.pending,"cap lock before sample");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);s.append({10});rejects([&]{s.append({10});});s.generate(1,{31});rejects([&]{s.generate(1,{31});});});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},2);s.append({10});m.limit=1;rejects([&]{s.generate(2,{31});});need(s.poisoned,"generation budget fault terminal");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);s.s.logical.push_back(12);rejects([&]{s.append({10});});need(s.poisoned&&m.charged==0,"inconsistent logical state rejected");});
 test([]{B b;M m;Session s(b,m,32);b.ids.push_back(12);rejects([&]{s.begin({10},1);});need(s.poisoned,"external head drift poison");});
 test([]{B b;M m;Session s(b,m,32);s.begin({10},1);s.append({10});s.generate(1,{31});rejects([&]{s.sample();});});
 test([]{B b;M m;Session s(b,m,32);s.begin({10,11},1);m.limit=1;rejects([&]{s.append({10,11});});rejects([&]{s.sample();});});
 std::cout<<"PASS "<<n<<" CPU mock lifecycle cases; native context/forward/placement=0\n";
}
