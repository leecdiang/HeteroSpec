// Standalone CPU-only accounting executable. Link std/POSIX only, never llama,
// GGML or GPU libraries: its own pre-main initialization must be CPU-only too.
#include "accounting_ipc.hpp"
#include <fstream>
#include <iostream>
using namespace hs::n1chain;
namespace {
struct Config{MockBudgetConfig budget;BrokerConfig broker;};
unsigned bounded_ms(const std::string&s){const auto n=ipc::amount(s);require(n>0&&n<=24*60*60*1000u,"finite IPC timeout bound");return unsigned(n);}
Config read_config(const std::string&file){
 std::ifstream in(file);require(bool(in),"explicit CPU mock config required");std::string line;require(bool(std::getline(in,line))&&line=="CPU_MOCK_ONLY_V1","native authority is absent; CPU_MOCK_ONLY_V1 required");
 Config c;std::set<std::string>single;std::size_t lines=0;
 while(std::getline(in,line)){require(++lines<=10000&&line.size()<=65536,"config line/count bound");if(line.empty())continue;const auto f=ipc::fields(line);const auto kind=f[0];
  if(kind=="RUN"){require(f.size()==2&&single.insert(kind).second,"RUN config");c.budget.run_id=unhex(f[1]);}
  else if(kind=="SOURCE_SHA"){require(f.size()==2&&single.insert(kind).second,"SOURCE_SHA config");c.budget.source_sha256=f[1];}
  else if(kind=="DEADLINE"){require(f.size()==2&&single.insert(kind).second,"DEADLINE config");std::size_t used=0;c.budget.deadline_epoch=std::stod(f[1],&used);require(used==f[1].size(),"finite exact deadline syntax");}
  else if(kind=="LIMIT"){require(f.size()==3&&c.budget.limits.emplace(f[1],ipc::amount(f[2])).second,"duplicate/invalid limit");}
  else if(kind=="REQUEST"){require(f.size()==3&&c.budget.request_rows.emplace(unhex(f[1]),ipc::amount(f[2])).second,"duplicate/invalid request");}
  else if(kind=="CLIENT"){require(f.size()==4,"client policy fields");BrokerClientPolicy p;p.role=f[2];p.required_launch_client=unhex(f[3]);require(c.broker.clients.emplace(unhex(f[1]),std::move(p)).second,"duplicate client");}
  else if(kind=="REQUEST_SCOPE"||kind=="DEPLOY_SCOPE"){require(f.size()==3,"scope config");auto p=c.broker.clients.find(unhex(f[1]));require(p!=c.broker.clients.end(),"scope needs declared client");auto&scope=kind=="REQUEST_SCOPE"?p->second.request_ids:p->second.deployment_ids;require(scope.insert(unhex(f[2])).second,"duplicate scope");}
  else if(kind=="IPC"){require(f.size()==4&&single.insert(kind).second,"IPC config");c.broker.max_commands=ipc::amount(f[1]);c.broker.idle_timeout_ms=bounded_ms(f[2]);c.broker.total_timeout_ms=bounded_ms(f[3]);}
  else throw Blocked("unknown CPU mock coordinator config field");
 }
 require(in.eof(),"config read I/O failure");
 require(single==std::set<std::string>({"RUN","SOURCE_SHA","DEADLINE","IPC"}),"missing fixed config identity/window");
 c.broker.mode="CPU_MOCK_ONLY";c.broker.run_id=c.budget.run_id;c.broker.manifest_sha256=Sha256::of(c.budget.canonical());
 require(!c.broker.clients.empty()&&c.broker.clients.size()<=100&&c.broker.max_commands>0&&c.broker.max_commands<=1000000,"finite coordinator config");
 for(const auto&p:c.broker.clients){for(const auto&id:p.second.request_ids){require(c.budget.request_rows.count(id),"scoped request not in global allowance");}}
 return c;
}
}
int main(int argc,char**argv){try{
 require(argc==3||argc==5,"--validate-cpu-mock CONFIG.tsv | --serve-cpu-mock CONFIG.tsv FRESH_LEDGER PRIVATE_SOCKET");
 const auto c=read_config(argv[2]);
 if(std::string(argv[1])=="--validate-cpu-mock"&&argc==3){std::cout<<"{\"status\":\"CPU_MOCK_CONFIG_ONLY\",\"manifest_sha256\":\""<<c.broker.manifest_sha256<<"\",\"native_authority\":false}\n";return 0;}
 require(std::string(argv[1])=="--serve-cpu-mock"&&argc==5,"explicit bounded CPU mock coordinator mode required");
 DurableMockBudget budget(argv[3],c.budget);AccountingBroker broker(argv[4],budget,c.broker);
 std::cout<<"{\"status\":\"CPU_MOCK_ACCOUNTING_READY\",\"manifest_sha256\":\""<<c.broker.manifest_sha256<<"\",\"native_authority\":false}"<<std::endl;
 auto r=broker.run();std::cout<<"{\"status\":\""<<(r.complete?"CPU_MOCK_ACCOUNTING_COMPLETE":"CPU_MOCK_ACCOUNTING_STOPPED_PARTIAL")<<"\",\"commands\":"<<r.commands<<",\"clients\":"<<r.clients<<",\"native_authority\":false}\n";return r.complete?0:2;
 }catch(const std::exception&e){std::cerr<<"CPU_MOCK_COORDINATOR_BLOCKED: "<<e.what()<<'\n';return 2;}}
