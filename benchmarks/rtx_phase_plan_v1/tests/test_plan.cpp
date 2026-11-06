#include "../native/execute_groups.hpp"
#include <iostream>
#include <cstring>
using namespace refplan;
static size_t checks=0;
void check(bool v){++checks;if(!v)throw std::runtime_error("test failed");}
std::vector<Row> make(int h,size_t q,int p,int cap){
 auto es=dense_extents(h,q,p,cap);std::vector<Row> r;
 for(size_t i=0;i<q;++i) { r.push_back({h+int64_t(i),es[i],7,i%3==0}); }
 return r;
}
struct Fake {
 bool failed=false;int calls=0;int fail_at=-1;
 void preflight(const std::vector<Row>&,const std::vector<Group>&){}
 void decode(const Group&,const std::vector<Row>&){if(calls++==fail_at)throw std::runtime_error("native error");}
 std::vector<unsigned char> output(size_t row,const Group&){
   uint32_t v=0x80000000u|uint32_t(row);std::vector<unsigned char>b(4);std::memcpy(b.data(),&v,4);return b;
 }
 void poison(){failed=true;}
};
int main(){
 for(int p:{16,32,256})for(int h=0;h<1024;++h)for(int q:{1,2,3,4,5,8,16,31,32}){
  if(h+q>1056)continue;
  auto r=make(h,q,p,1056);auto groups=plan(r,32);size_t total=0;
  for(const auto&g:groups){check(g.begin==total);check(g.count>0&&g.count<=32);
   for(size_t j=g.begin;j<g.begin+g.count;++j)check(r[j].physical_extent==g.extent);
   total+=g.count;
  }check(total==size_t(q));
  for(size_t j=1;j<groups.size();++j){auto&a=groups[j-1];auto&b=groups[j];check(a.count==32||a.extent!=b.extent||a.arithmetic_class!=b.arithmetic_class);}
 }
 auto r=make(767,4,256,1024);auto g=plan(r,4);check(g.size()==2&&g[0].count==1&&g[1].count==3);
 auto other=r;other[2].arithmetic_class=9;check(plan(other,4).size()==4);
 Fake fake;auto out=execute_groups(fake,r,4,4);check(out.complete()&&fake.calls==2);
 check(out.get(0)==std::vector<unsigned char>({0,0,0,128}));
 check(out.get(3)==std::vector<unsigned char>({3,0,0,128}));
 bool bad=false;try{out.get(1);}catch(const std::invalid_argument&){bad=true;}check(bad);
 Fake fail;fail.fail_at=1;try{execute_groups(fail,r,4,4);}catch(const std::runtime_error&){}check(fail.failed&&fail.calls==2);
 bad=false;try{dense_extents(1023,2,256,1024);}catch(const std::invalid_argument&){bad=true;}check(bad);
 Identity a{"frozen","VERIFY","WB",4,r};Identity b=a;check(a==b);b.rows[0].requested_output=!b.rows[0].requested_output;check(!(a==b));
 OnlineWork w;check(w.state_stationary());w.exports=1;check(!w.state_stationary());
 std::cout<<checks<<" CPU helper checks passed; no GPU qualification\n";
}
