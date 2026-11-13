#pragma once
// Dedicated bounded successor accounting; old ProductionGate remains unchanged.
#include "../pilot4_20261112/pilot_gate.hpp"
#include <sys/stat.h>
namespace hs::n1chain {
class SuccessorGate final:public BudgetHooks {
 PJ job_,manifest_,state_;std::string root_,last_,active_;int fd_=-1;bool dead_=false;
 void commit(){durable(root_+"/STATE.next",state_.dump()+"\n");if(::rename((root_+"/STATE.next").c_str(),(root_+"/STATE.json").c_str()))throw Blocked("ledger rename");int d=::open(root_.c_str(),O_RDONLY|O_DIRECTORY);pilot_need(d>=0&&::fsync(d)==0,"ledger directory sync");::close(d);last_=state_.dump()+"\n";}
 const PJ&op(const std::string&id)const{for(auto&v:manifest_.at("operations"))if(v.at("id")==id)return v;throw Blocked("unregistered request");}
 public:
 SuccessorGate(const PJ&j):job_(j),root_(j.at("ledger_root")){
#if !defined(HS_SUCC_ROOT) || !defined(HS_SUCC_MANIFEST_SHA)
 throw Blocked("no compiled successor admission binding");
#else
 pilot_need(root_==HS_SUCC_ROOT&&hashfile(root_+"/MANIFEST.json")==HS_SUCC_MANIFEST_SHA,"frozen successor identity differs");
#endif
 manifest_=PJ::parse(textfile(root_+"/MANIFEST.json"));auto payload=j;payload.erase("job_payload_sha256");Sha256 hh;auto encoded=payload.dump();hh.update(encoded.data(),encoded.size());pilot_need(hh.finish()==j.at("job_payload_sha256"),"job payload binding differs");auto pre=PJ::parse(textfile(j.at("output").get<std::string>()+"/PREEXEC_KERNEL.json"));pilot_need(pre.at("pid")==::getpid()&&pre.at("cgroup")==j.at("cgroup")&&pre.at("sealed")==true,"preexec owner differs");pilot_need(hashfile("/proc/self/exe")==j.at("native_sha256"),"native worker image differs");
 fd_=::open((root_+"/COUNTER.LOCK").c_str(),O_RDWR|O_NOFOLLOW);pilot_need(fd_>=0&&::flock(fd_,LOCK_EX|LOCK_NB)==0,"unknown/concurrent ledger owner");struct stat st{};pilot_need(::fstat(fd_,&st)==0&&uint64_t(st.st_ino)==j.at("lock_inode").get<uint64_t>()&&st.st_uid==::geteuid(),"counter lock identity differs");
 last_=textfile(root_+"/STATE.json");state_=PJ::parse(last_);pilot_need(state_.at("active_worker").at("id")==j.at("worker_id")&&state_.at("active_worker").at("job_sha256")==j.at("job_payload_sha256"),"unreserved worker/job");pilot_need(state_.at("active_worker").at("role")==j.at("role"),"reserved role differs");PJ previous=PJ::array();for(auto r:{"R","REPEAT","COLD","STRONG","LOCAL"}){if(j.at("role")==r)break;previous.push_back(r);}pilot_need(state_.at("passed_roles")==previous,"prior stage not strictly qualified");guard();
 }
 ~SuccessorGate(){if(fd_>=0)::close(fd_);}
 void guard(){pilot_need(!dead_,"worker poisoned");pilot_need(textfile(root_+"/STATE.json")==last_,"ledger externally changed");
  auto w=manifest_.at("window");const auto wall=std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();pilot_need(mono()<w.at("deadline_mono").get<double>()&&wall<w.at("deadline_wall").get<double>()&&mono()<job_.at("worker_deadline_mono").get<double>(),"GPU window/deadline exhausted");
  pilot_need(textfile("/proc/self/cgroup")=="0::"+job_.at("cgroup").get<std::string>()+"\n","wrong kernel resource domain");std::string base="/sys/fs/cgroup"+job_.at("cgroup").get<std::string>();pilot_need(textfile(base+"/memory.max")=="25769803776\n"&&textfile(base+"/memory.swap.max")=="0\n"&&textfile(base+"/pids.max")=="128\n","actual kernel limits differ");
  const char*v=::getenv("CUDA_VISIBLE_DEVICES");pilot_need(v&&v==job_.at("gpu_uuid").get<std::string>(),"allocated UUID differs");auto lease=PJ::parse(textfile(root_+"/LEASE.json"));pilot_need(lease.at("worker_id")==job_.at("worker_id")&&lease.at("run_id")==state_.at("run_id")&&mono()-lease.at("mono").get<double>()>=0&&mono()-lease.at("mono").get<double>()<5&&lease.at("GPU_safe")==true,"lost parent/resource lease");
 }
 void begin(const std::string&id){guard();pilot_need(active_.empty(),"concurrent request");const auto&o=op(id);pilot_need(o.at("role")==job_.at("role")&&!state_.at("requests").contains(id),"wrong/duplicate role request");std::string next;for(auto&candidate:manifest_.at("operations"))if(candidate.at("role")==job_.at("role")&&!state_["requests"].contains(candidate.at("id").get<std::string>())){next=candidate.at("id");break;}pilot_need(id==next,"out of order request");int count=state_["consumed"]["requests"].get<int>();pilot_need(count<76,"request ceiling");state_["consumed"]["requests"]=count+1;state_["requests"][id]={{"status","ACTIVE"},{"rows",0},{"raw_bytes",0}};active_=id;commit();}
 void finish(){guard();pilot_need(!active_.empty()&&state_["requests"][active_]["rows"]==op(active_).at("rows"),"incomplete actual row work");state_["requests"][active_]["status"]="COMPLETED";active_.clear();commit();}
 void rows(size_t n){guard();pilot_need(!active_.empty()&&n>0&&n<=4096,"decode outside request");auto&r=state_["requests"][active_];pilot_need(r["rows"].get<size_t>()+n<=op(active_).at("rows").get<size_t>()&&state_["consumed"]["rows"].get<size_t>()+n<=85738,"physical row ceiling");r["rows"]=r["rows"].get<size_t>()+n;state_["consumed"]["rows"]=state_["consumed"]["rows"].get<size_t>()+n;commit();}
 void bytes(size_t n){guard();pilot_need(!active_.empty(),"capture outside request");auto total=state_["raw_bytes"].get<uint64_t>();pilot_need(total+n<=32ULL*1024*1024*1024,"raw capture cap");state_["raw_bytes"]=total+n;state_["requests"][active_]["raw_bytes"]=state_["requests"][active_]["raw_bytes"].get<uint64_t>()+n;commit();}
 void before_backend_init(const std::string&)override{guard();pilot_need(!state_["active_worker"].value("backend",false),"duplicate backend");state_["active_worker"]["backend"]=true;commit();}
 void before_model_load(const std::string&)override{guard();pilot_need(!state_["active_worker"].value("model",false),"second model in worker");state_["active_worker"]["model"]=true;commit();}
 void before_context(const std::string&)override{guard();pilot_need(!state_["active_worker"].value("context",false),"second context in worker");state_["active_worker"]["context"]=true;commit();}
 void before_placement(const std::string&)override{guard();}
 void before_request(const std::string&id)override{begin(id);}
 void before_decode(const std::string&,size_t n)override{rows(n);}
 void before_mutation(const std::string&,const std::string&)override{guard();}
 void finish_request(const std::string&,const std::string&)override{finish();}
 void poison(const std::string&)noexcept override{dead_=true;}
 PJ state()const{return state_;}
 std::string active()const{return active_;}
};
}
