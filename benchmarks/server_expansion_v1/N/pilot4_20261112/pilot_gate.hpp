#pragma once
// Dedicated pilot admission, not an override of the old ProductionGate.
#include "../native_chain_successor_20261112/budget_writer/hooks.hpp"
#include "../native_chain_successor_20261112/budget_writer/sha256.hpp"
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <fcntl.h>
#include <sys/file.h>
#include <sys/statvfs.h>
#include <unistd.h>
#include <chrono>
namespace hs::n1chain {
using PJ=nlohmann::json;
inline void pilot_need(bool ok,const std::string&why){if(!ok)throw Blocked(why);}
inline std::string textfile(const std::string&p){std::ifstream f(p);if(!f)throw Blocked("missing bound file");return{std::istreambuf_iterator<char>(f),{}};}
inline std::string hashfile(const std::string&p){std::ifstream f(p,std::ios::binary);if(!f)throw Blocked("identity file missing");Sha256 h;char b[65536];while(f){f.read(b,sizeof b);h.update(b,size_t(f.gcount()));}if(!f.eof())throw Blocked("identity read");return h.finish();}
inline double mono(){return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();}
inline void durable(const std::string&p,const std::string&raw,bool fresh=true){int f=::open(p.c_str(),O_WRONLY|O_CREAT|O_NOFOLLOW|(fresh?O_EXCL:O_TRUNC),0600);if(f<0)throw Blocked("durable open");auto n=::write(f,raw.data(),raw.size());auto s=::fsync(f);::close(f);if(n!=ssize_t(raw.size())||s)throw Blocked("short/unsynced durable write");int d=::open(std::filesystem::path(p).parent_path().c_str(),O_RDONLY|O_DIRECTORY);if(d<0||::fsync(d))throw Blocked("capture directory sync");::close(d);}
class PilotGate final:public BudgetHooks {
 PJ job_,state_;std::string dir_,last_,active_;int lock_=-1;bool dead_=false;
 void commit(){auto raw=state_.dump()+"\n";std::string p=dir_+"/STATE.next";durable(p,raw);if(::rename(p.c_str(),(dir_+"/STATE.json").c_str()))throw Blocked("state rename");int d=::open(dir_.c_str(),O_RDONLY|O_DIRECTORY);if(d<0||::fsync(d))throw Blocked("state directory sync");::close(d);last_=raw;}
 public:
 PilotGate(const PJ&j):job_(j),dir_(j.at("output")){
#if !defined(HS_PILOT_RUN_ID) || !defined(HS_PILOT_OUTPUT)
  throw Blocked("no compiled single-attempt pilot binding");
#else
  pilot_need(j.at("run_id")==HS_PILOT_RUN_ID&&dir_==HS_PILOT_OUTPUT,"different pilot attempt/output; cannot reset ledger");
#endif
  pilot_need(j.at("approval_scope")=="USER_PILOT_4_8192_1"&&j.at("case_sha256")==hashfile(j.at("case_file")),"pilot scope/case identity");
  pilot_need(j.at("native_sha256")==hashfile("/proc/self/exe"),"native image changed");
  lock_=::open((dir_+"/NATIVE.LOCK").c_str(),O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW,0600);pilot_need(lock_>=0&&::flock(lock_,LOCK_EX|LOCK_NB)==0,"fresh owned native lock");
  pilot_need(!std::filesystem::exists(dir_+"/STATE.json")&&!std::filesystem::exists(dir_+"/STATE.next"),"prior pilot state cannot restart");
  pilot_need(textfile(dir_+"/DEPLOYMENT_RESERVED.json")==j.at("deployment_receipt").get<std::string>(),"preexec deployment not durably bound");
  state_={{"run_id",j.at("run_id")},{"deployment_reserved",1},{"model_loads",0},{"contexts",0},{"requests",0},{"rows",0},{"bytes",0},{"status","ADMITTED_SETUP"},{"completed",PJ::array()}};guard();commit();
 }
 ~PilotGate(){if(lock_>=0)::close(lock_);}
 void guard(){pilot_need(!dead_,"pilot poisoned");pilot_need(mono()<job_.at("deadline_mono").get<double>(),"pilot deadline");
  pilot_need(last_.empty()||textfile(dir_+"/STATE.json")==last_,"durable state replaced");
  auto cg=textfile("/proc/self/cgroup");const auto expected=job_.at("cgroup").get<std::string>();pilot_need(cg=="0::"+expected+"\n","native outside approved real resource domain");
  auto base="/sys/fs/cgroup"+expected;pilot_need(textfile(base+"/memory.max")=="25769803776\n"&&textfile(base+"/memory.swap.max")=="0\n"&&textfile(base+"/pids.max")=="128\n","actual kernel limits differ");
  PJ lease=PJ::parse(textfile(dir_+"/LEASE.json"));pilot_need(lease.at("run_id")==job_.at("run_id")&&mono()-lease.at("mono").get<double>()>=0&&mono()-lease.at("mono").get<double>()<5&&lease.at("GPU_safe")==true,"lost controller/resource lease");
  const char*v=::getenv("CUDA_VISIBLE_DEVICES");pilot_need(v&&v==job_.at("gpu_uuid").get<std::string>(),"wrong allocated UUID");
 }
 void request(int i){guard();pilot_need(active_.empty()&&state_["requests"]==i&&i<4,"request sequence/ceiling");active_="R"+std::to_string(i+1);state_["requests"]=i+1;state_["active"]=active_;state_["active_rows"]=0;commit();}
 void row(size_t n){guard();pilot_need(!active_.empty()&&n>0,"decode outside request");const int i=state_["requests"].get<int>()-1;const int limits[]={186,186,224,136};pilot_need(state_["active_rows"].get<size_t>()+n<=size_t(limits[i])&&state_["rows"].get<size_t>()+n<=8192,"physical row limit");state_["rows"]=state_["rows"].get<size_t>()+n;state_["active_rows"]=state_["active_rows"].get<size_t>()+n;commit();}
 void finish(){guard();state_["completed"].push_back({{"id",active_},{"rows",state_["active_rows"]}});state_["active"]="";active_.clear();commit();}
 void bytes(size_t n){guard();pilot_need(state_["bytes"].get<size_t>()+n<=size_t(2ULL<<30),"raw byte cap");state_["bytes"]=state_["bytes"].get<size_t>()+n;commit();}
 void before_backend_init(const std::string&)override{guard();pilot_need(state_["model_loads"]==0,"duplicate backend");}
 void before_model_load(const std::string&)override{guard();pilot_need(state_["model_loads"]==0,"second model deployment");state_["model_loads"]=1;commit();}
 void before_context(const std::string&)override{guard();pilot_need(state_["model_loads"]==1&&state_["contexts"].get<int>()<2,"context cap");state_["contexts"]=state_["contexts"].get<int>()+1;commit();}
 void before_placement(const std::string&)override{guard();}
 void before_request(const std::string&)override{throw Blocked("use exact pilot sequence");}
 void before_decode(const std::string&,size_t n)override{row(n);}
 void before_mutation(const std::string&,const std::string&)override{guard();}
 void finish_request(const std::string&,const std::string&)override{finish();}
 void poison(const std::string&)noexcept override{dead_=true;}
 PJ state()const{return state_;}
};
}
