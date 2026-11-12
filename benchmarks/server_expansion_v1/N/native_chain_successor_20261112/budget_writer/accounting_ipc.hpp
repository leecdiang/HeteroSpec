#pragma once
// Private AF_UNIX accounting only. An ACK is NEVER native/model authority.
// This CPU-preparation broker uses one DurableMockBudget, not per-worker ledgers.
#include "durable_budget.hpp"
#include <arpa/inet.h>
#include <poll.h>
#include <sys/socket.h>
#include <sys/un.h>
namespace hs::n1chain {
namespace ipc {
using Clock=std::chrono::steady_clock;
using Deadline=Clock::time_point;
struct SocketIO{std::function<ssize_t(int,const void*,std::size_t)>send=[](int f,const void*p,std::size_t n){return::send(f,p,n,MSG_NOSIGNAL);};};
inline Deadline deadline(unsigned ms){require(ms>0&&ms<=24*60*60*1000u,"finite IPC deadline required");return Clock::now()+std::chrono::milliseconds(ms);}
inline void wait(int fd,short events,Deadline until){for(;;){auto left=std::chrono::duration_cast<std::chrono::milliseconds>(until-Clock::now()).count();require(left>0,"IPC timeout; state unknown, STOP");pollfd p{fd,events,0};auto r=::poll(&p,1,int(std::min<int64_t>(left,1000000)));if(r<0&&errno==EINTR)continue;require(r>0&&!(p.revents&POLLNVAL),"IPC timeout/error, STOP");if(p.revents&(events|POLLHUP|POLLERR))return;}}
inline void write(int fd,const void*raw,std::size_t n,Deadline until,SocketIO&io){const auto*p=static_cast<const char*>(raw);std::size_t done=0;while(done<n){wait(fd,POLLOUT,until);auto r=io.send(fd,p+done,n-done);if(r<0&&(errno==EINTR||errno==EAGAIN||errno==EWOULDBLOCK))continue;require(r>0&&static_cast<std::size_t>(r)<=n-done,"partial/failed IPC send, STOP without retry/reconnect");done+=static_cast<std::size_t>(r);}}
inline void read(int fd,void*raw,std::size_t n,Deadline until){auto*p=static_cast<char*>(raw);std::size_t done=0;while(done<n){wait(fd,POLLIN,until);auto r=::recv(fd,p+done,n-done,0);if(r<0&&(errno==EINTR||errno==EAGAIN||errno==EWOULDBLOCK))continue;require(r>0,"IPC EOF/partial frame, STOP without retry/reconnect");done+=static_cast<std::size_t>(r);}}
inline void send_frame(int fd,const std::string&s,Deadline until,SocketIO&io){require(!s.empty()&&s.size()<=65536,"IPC frame bound");const uint32_t n=htonl(uint32_t(s.size()));write(fd,&n,4,until,io);write(fd,s.data(),s.size(),until,io);}
inline std::string frame(int fd,Deadline until){uint32_t n=0;read(fd,&n,4,until);n=ntohl(n);require(n>0&&n<=65536,"unknown/oversized IPC frame");std::string s(n,'\0');read(fd,s.data(),s.size(),until);return s;}
inline std::vector<std::string>fields(const std::string&s){std::vector<std::string>out;std::size_t p=0;for(;;){auto q=s.find('\t',p);if(q==std::string::npos){out.push_back(s.substr(p));return out;}out.push_back(s.substr(p,q-p));p=q+1;}}
inline uint64_t amount(const std::string&s){require(!s.empty()&&s.size()<=20,"invalid IPC amount");uint64_t n=0;for(char c:s){require(c>='0'&&c<='9'&&n<=(std::numeric_limits<uint64_t>::max()-uint64_t(c-'0'))/10,"invalid IPC amount");n=n*10+uint64_t(c-'0');}return n;}
inline void peer_uid(int fd,uid_t expected){
#ifdef __linux__
 struct Cred{pid_t pid;uid_t uid;gid_t gid;}cred{};socklen_t n=sizeof cred;checked(::getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&cred,&n),"private IPC peer credentials");require(n==sizeof cred&&cred.uid==expected,"foreign IPC peer UID rejected");
#else
 (void)fd;(void)expected;throw Blocked("verified Linux peer credentials required");
#endif
}
struct SocketPath{FD parent;std::string leaf;struct stat parent_stat{};};
inline SocketPath private_path(const std::string&p){require(!p.empty()&&p[0]=='/'&&p.size()<sizeof(sockaddr_un{}.sun_path),"absolute private socket path bound");const auto i=p.find_last_of('/');auto d=absolute_dir(i?p.substr(0,i):"/");const auto leaf=p.substr(i+1);filename(leaf);struct stat s{};checked(::fstat(d.n,&s),"socket parent metadata");require(s.st_uid==::geteuid()&&(s.st_mode&077)==0,"socket parent must be owned private0700");return{std::move(d),leaf,s};}
inline sockaddr_un address(const std::string&p){sockaddr_un a{};a.sun_family=AF_UNIX;std::memcpy(a.sun_path,p.c_str(),p.size()+1);return a;}
inline std::string ack(uint64_t seq,const std::string&sha){return"ACK\t"+std::to_string(seq)+"\tACCOUNTING_ONLY_NOT_NATIVE_AUTHORITY\t"+sha;}
}
class NativeAccountingClient final:public BudgetHooks {
 FD fd_;std::string manifest_;uint64_t seq_=0;unsigned timeout_;bool poisoned_=false,closed_=false;ipc::SocketIO io_;
 void command(const std::string&kind,const std::string&id,uint64_t n=0,const std::string&detail=""){
  require(!poisoned_&&!closed_,"IPC client poisoned/closed; no reconnect");
  try{identifier(id);const auto until=ipc::deadline(timeout_);const auto body="CMD\t"+std::to_string(seq_+1)+"\t"+kind+"\t"+hex(id)+"\t"+std::to_string(n)+"\t"+hex(detail);
   ipc::send_frame(fd_.n,body,until,io_);require(ipc::frame(fd_.n,until)==ipc::ack(seq_+1,manifest_),"unknown/partial/lost accounting ACK; STOP");seq_++;
  }catch(...){poison("uncertain IPC command/ACK");throw;}
 }
 public:
 NativeAccountingClient(const std::string&socket_path,const std::string&run_id,const std::string&manifest_sha256,const std::string&client_id,unsigned command_timeout_ms):manifest_(manifest_sha256),timeout_(command_timeout_ms){
  try{identifier(run_id);identifier(client_id);require(manifest_.size()==64,"manifest SHA required");auto p=ipc::private_path(socket_path);struct stat st{};checked(::fstatat(p.parent.n,p.leaf.c_str(),&st,AT_SYMLINK_NOFOLLOW),"inspect broker socket");require(S_ISSOCK(st.st_mode)&&st.st_uid==::geteuid()&&(st.st_mode&077)==0,"private owned socket required");
   fd_=FD(::socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0));checked(fd_.n,"create accounting socket");const auto a=ipc::address(socket_path);const auto until=ipc::deadline(timeout_);auto r=::connect(fd_.n,reinterpret_cast<const sockaddr*>(&a),sizeof a);if(r<0){require(errno==EINPROGRESS||errno==EAGAIN,"accounting connect failed");ipc::wait(fd_.n,POLLOUT,until);int e=0;socklen_t n=sizeof e;checked(::getsockopt(fd_.n,SOL_SOCKET,SO_ERROR,&e,&n),"accounting connect status");require(e==0,"accounting connect failed");}ipc::peer_uid(fd_.n,::geteuid());
   ipc::send_frame(fd_.n,"HELLO\t1\t"+hex(run_id)+"\t"+manifest_+"\t"+hex(client_id),until,io_);
   require(ipc::frame(fd_.n,until)==ipc::ack(0,manifest_),"broker identity/manifest/run mismatch; no reconnect");
  }catch(...){poison("handshake failed");throw;}
 }
 ~NativeAccountingClient()override{fd_=FD{};}
 NativeAccountingClient(const NativeAccountingClient&)=delete;NativeAccountingClient&operator=(const NativeAccountingClient&)=delete;
 void before_backend_init(const std::string&id)override{command("backend",id,1);}
 void before_model_load(const std::string&id)override{command("model",id,1);}
 void before_context(const std::string&id)override{command("context",id,1);}
 void before_placement(const std::string&id)override{command("placement",id,1);}
 void before_request(const std::string&id)override{command("request",id,1);}
 void before_decode(const std::string&id,std::size_t rows)override{command("rows",id,rows);}
 void before_mutation(const std::string&id,const std::string&action)override{command("mutation",id,0,action);}
 void finish_request(const std::string&id,const std::string&status)override{command("finish",id,0,status);}
 void close_worker(){command("close","worker",0);closed_=true;fd_=FD{};}
 void poison(const std::string&)noexcept override{poisoned_=true;fd_=FD{};}
 bool poisoned()const{return poisoned_;}
};
struct BrokerClientPolicy{std::set<std::string>request_ids,deployment_ids;std::string role="WORKER",required_launch_client;};
struct BrokerConfig {
 std::string mode,run_id,manifest_sha256;
 std::map<std::string,BrokerClientPolicy>clients;
 uint64_t max_commands=0;
 unsigned idle_timeout_ms=0,total_timeout_ms=0;
};
class AccountingBroker final {
 std::string path_;DurableMockBudget&budget_;BrokerConfig cfg_;ipc::SocketIO io_;FD listener_;std::set<std::string>claimed_,completed_;uint64_t commands_=0;dev_t dev_=0;ino_t ino_=0;
 ipc::Deadline total_;
 ipc::Deadline until()const{return std::min(total_,ipc::deadline(cfg_.idle_timeout_ms));}
 void dispatch(const BrokerClientPolicy&p,const std::vector<std::string>&f){
  const auto kind=f[2],id=unhex(f[3]),detail=unhex(f[5]);const auto n=ipc::amount(f[4]);
  require(p.role!="LAUNCH_ONLY"||kind=="placement","launch-only client cannot issue model/context/request work");
  if(kind=="backend"||kind=="model"||kind=="context"||kind=="placement"){
   require(n==1&&detail.empty()&&p.deployment_ids.count(id),"unplanned/cross-worker deployment ID");
   if(kind=="backend")budget_.before_backend_init(id);else if(kind=="model")budget_.before_model_load(id);else if(kind=="context")budget_.before_context(id);else if(p.role=="WORKER")budget_.verify_pre_reserved_placement(id);else budget_.before_placement(id);
  }else{
   require(p.request_ids.count(id),"unplanned/cross-worker request ID");
   if(kind=="request"){require(n==1&&detail.empty(),"request amount/detail");budget_.before_request(id);}else if(kind=="rows"){require(detail.empty(),"row detail");budget_.before_decode(id,n);}
   else if(kind=="mutation"){require(n==0,"mutation amount");budget_.before_mutation(id,detail);}else if(kind=="finish"){require(n==0,"finish amount");budget_.finish_request(id,detail);}
   else throw Blocked("unknown broker command");
  }
 }
 public:
 struct Result{bool complete=false;uint64_t commands=0;std::size_t clients=0;std::string stop_reason;bool native_execution_authorized=false;};
 AccountingBroker(const std::string&socket_path,DurableMockBudget&budget,BrokerConfig config,ipc::SocketIO io={}):path_(socket_path),budget_(budget),cfg_(std::move(config)),io_(std::move(io)){
  require(cfg_.mode=="CPU_MOCK_ONLY"&&cfg_.run_id==budget_.run_id()&&cfg_.manifest_sha256==budget_.fingerprint(),"explicit CPU mock coordinator identity required");require(!cfg_.clients.empty()&&cfg_.clients.size()<=100&&cfg_.max_commands>0&&cfg_.max_commands<=1000000,"finite broker client/command bounds");
  total_=ipc::deadline(cfg_.total_timeout_ms);(void)ipc::deadline(cfg_.idle_timeout_ms);std::set<std::string>requests,launch_clients,worker_deployments;
  for(const auto&c:cfg_.clients){identifier(c.first);require(c.second.role=="LAUNCH_ONLY"||c.second.role=="WORKER"||c.second.role=="CPU_MOCK_ONLY","unknown client role");
   if(c.second.role=="LAUNCH_ONLY")require(c.second.request_ids.empty()&&c.second.required_launch_client.empty(),"launch client has worker authority");
   if(c.second.role=="WORKER"){
    const auto launcher=cfg_.clients.find(c.second.required_launch_client);require(launcher!=cfg_.clients.end()&&launcher->second.role=="LAUNCH_ONLY","worker requires a registered pre-exec launch client");
    require(launch_clients.insert(c.second.required_launch_client).second,"one launch client cannot authorize two native process execs");
    for(const auto&id:c.second.deployment_ids){require(launcher->second.deployment_ids.count(id),"worker placement not in launch policy");require(worker_deployments.insert(id).second,"two workers share one pre-exec deployment identity");}
   }
   for(const auto&id:c.second.request_ids){identifier(id);require(requests.insert(id).second,"request assigned to two workers");}for(const auto&id:c.second.deployment_ids)identifier(id);}
  auto p=ipc::private_path(path_);require(!exists_at(p.parent.n,p.leaf.c_str()),"existing socket/STATE path cannot be replaced");
  listener_=FD(::socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0));checked(listener_.n,"create private accounting broker");const auto a=ipc::address(path_);checked(::bind(listener_.n,reinterpret_cast<const sockaddr*>(&a),sizeof a),"bind fresh accounting socket");checked(::chmod(path_.c_str(),0600),"private socket mode");struct stat s{};checked(::lstat(path_.c_str(),&s),"socket identity");dev_=s.st_dev;ino_=s.st_ino;checked(::listen(listener_.n,1),"bounded broker listen");
 }
 ~AccountingBroker(){listener_=FD{};struct stat s{};if(::lstat(path_.c_str(),&s)==0&&S_ISSOCK(s.st_mode)&&s.st_dev==dev_&&s.st_ino==ino_){auto r=::unlink(path_.c_str());(void)r;}}
 AccountingBroker(const AccountingBroker&)=delete;AccountingBroker&operator=(const AccountingBroker&)=delete;
 Result run()noexcept{
  Result result;
  try{while(completed_.size()<cfg_.clients.size()){
   ipc::wait(listener_.n,POLLIN,until());FD client(::accept4(listener_.n,nullptr,nullptr,SOCK_CLOEXEC|SOCK_NONBLOCK));checked(client.n,"accept accounting worker");ipc::peer_uid(client.n,::geteuid());
   const auto h=ipc::fields(ipc::frame(client.n,until()));require(h.size()==5&&h[0]=="HELLO"&&h[1]=="1"&&unhex(h[2])==cfg_.run_id&&h[3]==cfg_.manifest_sha256,"worker handshake identity conflict");const auto worker=unhex(h[4]);auto policy=cfg_.clients.find(worker);require(policy!=cfg_.clients.end()&&claimed_.insert(worker).second,"unknown/reentered accounting worker");
   if(policy->second.role=="WORKER"){require(completed_.count(policy->second.required_launch_client),"worker started before pre-exec launch client completed");for(const auto&id:policy->second.deployment_ids)require(budget_.state().deployments.count("placement:"+id),"worker ELF has no pre-exec placement reservation");}
   ipc::send_frame(client.n,ipc::ack(0,cfg_.manifest_sha256),until(),io_);uint64_t seq=0;
   for(;;){const auto f=ipc::fields(ipc::frame(client.n,until()));require(++commands_<=cfg_.max_commands,"broker command budget exhausted");require(f.size()==6&&f[0]=="CMD"&&ipc::amount(f[1])==seq+1,"unknown/duplicate/out-of-order accounting frame");
    if(f[2]=="close"){
     require(unhex(f[3])=="worker"&&ipc::amount(f[4])==0&&f[5].empty()&&budget_.state().active.empty(),"unclean worker close with in-flight request");
     if(policy->second.role=="LAUNCH_ONLY")for(const auto&id:policy->second.deployment_ids)require(budget_.state().deployments.count("placement:"+id),"launch closed without durable before-exec reservation");
     for(const auto&id:policy->second.request_ids)require(budget_.state().finished.count(id),"worker skipped planned request");
     ipc::send_frame(client.n,ipc::ack(++seq,cfg_.manifest_sha256),until(),io_);completed_.insert(worker);break;
    }
    dispatch(policy->second,f);require(!budget_.poisoned(),"failed request poisons complete global attempt");ipc::send_frame(client.n,ipc::ack(++seq,cfg_.manifest_sha256),until(),io_);
   }
  }
  budget_.seal_success();result.complete=true;result.stop_reason="ALL_PLANNED_MOCK_CLIENTS_CLOSED_ACCOUNTING_ONLY";
  }catch(const std::exception&e){budget_.poison("broker disconnect/protocol/reservation/ACK uncertainty");result.stop_reason=e.what();}catch(...){budget_.poison("broker unknown failure");result.stop_reason="unknown broker failure";}
  result.commands=commands_;result.clients=completed_.size();return result;
 }
};
}
