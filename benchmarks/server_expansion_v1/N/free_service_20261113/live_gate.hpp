#pragma once
#include "../pilot4_20261112/pilot_gate.hpp"
#include <sys/stat.h>
namespace hs::n1chain {
class LiveGate final:public BudgetHooks {
 PJ j_,m_,s_;std::string root_,last_,active_;int lock_=-1;bool poisoned_=false;
 void commit(){durable(root_+"/STATE.next",s_.dump()+"\n");pilot_need(::rename((root_+"/STATE.next").c_str(),(root_+"/STATE.json").c_str())==0,"ledger rename");int d=::open(root_.c_str(),O_RDONLY|O_DIRECTORY);pilot_need(d>=0&&::fsync(d)==0,"ledger directory sync");::close(d);last_=s_.dump()+"\n";}
 public:
 LiveGate(const PJ&j):j_(j),root_(j.at("ledger_root")){
#if !defined(HS_LIVE_ROOT) || !defined(HS_LIVE_MANIFEST_SHA) || !defined(HS_LIVE_KIND)
 throw Blocked("no compiled live authorization binding");
#else
 pilot_need(root_==HS_LIVE_ROOT&&j.at("kind")==HS_LIVE_KIND&&hashfile(root_+"/MANIFEST.json")==HS_LIVE_MANIFEST_SHA,"live source/root/kind mismatch");
#endif
 m_=PJ::parse(textfile(root_+"/MANIFEST.json"));pilot_need(m_.at("approved").at("requests")==42&&m_.at("approved").at("rows")==40000&&m_.at("approved").at("deployments")==4,"different approved budget");auto p=j;p.erase("job_payload_sha256");auto encoded=p.dump();Sha256 hash;hash.update(encoded.data(),encoded.size());pilot_need(hash.finish()==j.at("job_payload_sha256"),"job payload differs");pilot_need(hashfile("/proc/self/exe")==j.at("native_sha256"),"native image differs");auto pre=PJ::parse(textfile(j.at("output").get<std::string>()+"/PREEXEC_KERNEL.json"));pilot_need(pre.at("pid")==::getpid()&&pre.at("cgroup")==j.at("cgroup")&&pre.at("sealed")==true,"preexec owner differs");
 lock_=::open((root_+"/COUNTER.LOCK").c_str(),O_RDWR|O_NOFOLLOW);pilot_need(lock_>=0&&::flock(lock_,LOCK_EX|LOCK_NB)==0,"unknown or concurrent budget owner");struct stat st{};pilot_need(::fstat(lock_,&st)==0&&st.st_uid==::geteuid()&&uint64_t(st.st_ino)==j.at("lock_inode"),"counter identity differs");last_=textfile(root_+"/STATE.json");s_=PJ::parse(last_);pilot_need(s_.at("active_worker").at("id")==j.at("worker_id")&&s_.at("active_worker").at("job_sha256")==j.at("job_payload_sha256"),"unreserved worker");pilot_need(s_.at("next_operation")==j.at("first_operation"),"worker operation order");guard();
 }
 ~LiveGate(){if(lock_>=0)::close(lock_);}
 void guard(){pilot_need(!poisoned_,"live worker poisoned");pilot_need(textfile(root_+"/STATE.json")==last_,"external ledger mutation");auto w=PJ::parse(textfile(root_+"/WINDOW.json"));double wall=std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();pilot_need(mono()<j_.at("worker_deadline_mono").get<double>()&&mono()<w.at("deadline_mono").get<double>()&&wall<w.at("deadline_wall").get<double>(),"live deadline");auto cg=j_.at("cgroup").get<std::string>();pilot_need(textfile("/proc/self/cgroup")=="0::"+cg+"\n","wrong live kernel domain");auto base="/sys/fs/cgroup"+cg;pilot_need(textfile(base+"/memory.max")=="25769803776\n"&&textfile(base+"/memory.swap.max")=="0\n"&&textfile(base+"/pids.max")=="128\n","kernel limits differ");const char*v=::getenv("CUDA_VISIBLE_DEVICES");pilot_need(v&&v==j_.at("gpu_uuid").get<std::string>(),"wrong UUID");auto lease=PJ::parse(textfile(root_+"/LEASE.json"));pilot_need(lease.at("worker_id")==j_.at("worker_id")&&lease.at("GPU_safe")==true&&mono()-lease.at("mono").get<double>()>=0&&mono()-lease.at("mono").get<double>()<8,"controller/quiet resource lease lost");struct statvfs fs{};pilot_need(::statvfs(root_.c_str(),&fs)==0&&uint64_t(fs.f_bavail)*fs.f_frsize>=64ULL*1024*1024*1024,"disk reserve");}
 PJ begin(const std::string&id){guard();int idx=s_.at("next_operation");pilot_need(active_.empty()&&idx<j_.at("end_operation").get<int>()&&idx<int(m_.at("operations").size()),"request scope/sequence");auto op=m_.at("operations").at(idx);pilot_need(op.at("id")==id&&s_["consumed"]["requests"].get<int>()<42&&!s_["requests"].contains(id),"wrong or duplicate request");active_=id;s_["consumed"]["requests"]=s_["consumed"]["requests"].get<int>()+1;s_["requests"][id]={{"rows",0},{"status","ACTIVE"},{"operation",op}};commit();return op;}
 void rows(size_t n){guard();pilot_need(!active_.empty()&&n>0&&n<=4096,"decode without request");auto&r=s_["requests"][active_];pilot_need(r["rows"].get<size_t>()+n<=r["operation"]["rows_max"].get<size_t>()&&s_["consumed"]["rows"].get<size_t>()+n<=40000,"row cap before actual work");r["rows"]=r["rows"].get<size_t>()+n;s_["consumed"]["rows"]=s_["consumed"]["rows"].get<size_t>()+n;commit();}
 void finish(size_t actual){guard();pilot_need(!active_.empty()&&s_["requests"][active_]["rows"]==actual,"complete physical row accounting differs");s_["requests"][active_]["status"]="COMPLETED";s_["next_operation"]=s_["next_operation"].get<int>()+1;active_.clear();commit();}
 void bytes(size_t n,bool raw){guard();auto field=raw?"raw_bytes":"metadata_bytes";uint64_t limit=uint64_t(raw?20:2)*1024*1024*1024;pilot_need(s_[field].get<uint64_t>()+n<=limit,"writer byte cap");s_[field]=s_[field].get<uint64_t>()+n;commit();}
 void passed(const std::string&id,const std::string&certificate){guard();s_["passed_episodes"].push_back({{"id",id},{"certificate_sha256",certificate}});commit();}
 void before_backend_init(const std::string&)override{guard();pilot_need(!s_["active_worker"].value("backend",false),"second backend");s_["active_worker"]["backend"]=true;commit();}
 void before_model_load(const std::string&)override{guard();pilot_need(!s_["active_worker"].value("model",false),"second model");s_["active_worker"]["model"]=true;commit();}
 void before_context(const std::string&)override{guard();pilot_need(!s_["active_worker"].value("context",false),"second context");s_["active_worker"]["context"]=true;commit();}
 void before_placement(const std::string&)override{guard();}
 void before_request(const std::string&id)override{begin(id);}
 void before_decode(const std::string&,size_t n)override{rows(n);}
 void before_mutation(const std::string&,const std::string&)override{guard();}
 void finish_request(const std::string&,const std::string&)override{throw Blocked("finish requires actual row receipt");}
 void poison(const std::string&)noexcept override{poisoned_=true;}
 const PJ&state()const{return s_;}const PJ&manifest()const{return m_;}const PJ&job()const{return j_;}std::string active()const{return active_;}std::string root()const{return root_;}
};
}
