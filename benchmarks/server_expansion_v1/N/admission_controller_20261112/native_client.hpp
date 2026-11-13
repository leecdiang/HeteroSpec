#pragma once
// Standard-library/POSIX transport only. No backend/model/loader API.
// An accounting ACK is never GPU authority; the native ProductionGate remains
// permanently closed in the original-source worker/factory.
#include "../native_chain_successor_20261112/budget_writer/accounting_ipc.hpp"
#include <fstream>
namespace hs::n1chain {
struct ControllerPeer {
 pid_t pid=-1;
 std::string start_ticks,boot_id;
};
inline std::string controller_boot_id(){
 std::ifstream f("/proc/sys/kernel/random/boot_id");std::string s;
 require(bool(std::getline(f,s))&&s.size()==36,"controller boot identity unavailable");return s;
}
inline std::string controller_start_ticks(pid_t pid){
 require(pid>0,"positive controller PID required");std::ifstream f("/proc/"+std::to_string(pid)+"/stat");std::string s;
 require(bool(std::getline(f,s)),"controller process unavailable");const auto end=s.rfind(')');require(end!=std::string::npos&&end+2<s.size(),"controller stat framing");
 std::istringstream fields(s.substr(end+2));std::string field;
 for(unsigned i=0;i<=19;i++)require(bool(fields>>field),"controller start identity absent");
 (void)ipc::amount(field);return field;
}
class ControlledNativeClient final:public BudgetHooks {
 FD fd_,capture_root_fd_;std::string manifest_,lease_,active_,capture_root_,socket_path_;ControllerPeer peer_;uint64_t seq_=0;
 dev_t capture_dev_=0,socket_dev_=0;ino_t capture_ino_=0,socket_ino_=0;
 unsigned timeout_;bool poisoned_=false,closed_=false;ipc::SocketIO io_;
 void owner()const{
  require(peer_.pid>0&&peer_.start_ticks==controller_start_ticks(peer_.pid)&&peer_.boot_id==controller_boot_id(),"controller PID/start/boot identity changed");
  struct stat socket{};checked(::lstat(socket_path_.c_str(),&socket),"controller socket still present");require(S_ISSOCK(socket.st_mode)&&socket.st_dev==socket_dev_&&socket.st_ino==socket_ino_&&socket.st_uid==::geteuid()&&(socket.st_mode&077)==0,"controller socket identity/mode changed");
#ifdef __linux__
  struct Cred{pid_t pid;uid_t uid;gid_t gid;}c{};socklen_t n=sizeof c;
  checked(::getsockopt(fd_.n,SOL_SOCKET,SO_PEERCRED,&c,&n),"controller peer credentials");
  require(n==sizeof c&&c.pid==peer_.pid&&c.uid==::geteuid(),"controller peer PID/UID mismatch");
#else
  throw Blocked("Linux kernel peer identity required");
#endif
 }
 void local(bool ok,const char*why){if(!ok){poison(why);throw Blocked(why);}}
 void command(const std::string&kind,const std::string&id,uint64_t n=0,const std::string&detail=""){
  require(!poisoned_&&!closed_,"controlled client poisoned/closed; no reconnect");
  try{owner();identifier(id);const auto until=ipc::deadline(timeout_);
   ipc::send_frame(fd_.n,"CMD\t"+std::to_string(seq_+1)+"\t"+kind+"\t"+hex(id)+"\t"+std::to_string(n)+"\t"+hex(detail),until,io_);
   require(ipc::frame(fd_.n,until)==ipc::ack(seq_+1,manifest_),"unknown/partial/lost stage accounting ACK; STOP");owner();seq_++;
  }catch(...){poison("uncertain controller command/ACK");throw;}
 }
 public:
 ControlledNativeClient(const std::string&socket_path,const std::string&run_id,const std::string&manifest_sha256,const std::string&worker_id,unsigned timeout_ms,ControllerPeer peer,const std::string&lease_sha256,const std::string&capture_root):manifest_(manifest_sha256),lease_(lease_sha256),socket_path_(socket_path),peer_(std::move(peer)),timeout_(timeout_ms){
  try{identifier(run_id);identifier(worker_id);require(manifest_.size()==64&&lease_.size()==64,"frozen manifest and owner lease SHA required");
   for(const auto&s:{manifest_,lease_})for(char c:s)require((c>='0'&&c<='9')||(c>='a'&&c<='f'),"controller digest syntax");
   require(peer_.pid>0&&!peer_.start_ticks.empty()&&peer_.boot_id.size()==36,"explicit controller peer identity required");
   capture_root_fd_=absolute_dir(capture_root);struct stat root{};checked(::fstat(capture_root_fd_.n,&root),"capture root identity");require(root.st_uid==::geteuid()&&(root.st_mode&077)==0,"private owned capture root required");capture_dev_=root.st_dev;capture_ino_=root.st_ino;capture_root_=fd_path(capture_root_fd_.n);
   auto p=ipc::private_path(socket_path);struct stat before{};checked(::fstatat(p.parent.n,p.leaf.c_str(),&before,AT_SYMLINK_NOFOLLOW),"inspect controller socket");
   require(S_ISSOCK(before.st_mode)&&before.st_uid==::geteuid()&&(before.st_mode&077)==0,"private owned controller socket required");
   socket_dev_=before.st_dev;socket_ino_=before.st_ino;
   fd_=FD(::socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0));checked(fd_.n,"controlled accounting socket");
   const auto a=ipc::address(socket_path);const auto until=ipc::deadline(timeout_);auto r=::connect(fd_.n,reinterpret_cast<const sockaddr*>(&a),sizeof a);
   if(r<0){require(errno==EINPROGRESS||errno==EAGAIN,"controller connect failed");ipc::wait(fd_.n,POLLOUT,until);int e=0;socklen_t n=sizeof e;checked(::getsockopt(fd_.n,SOL_SOCKET,SO_ERROR,&e,&n),"controller connect status");require(e==0,"controller connect status failed");}
   owner();struct stat after{};checked(::fstatat(p.parent.n,p.leaf.c_str(),&after,AT_SYMLINK_NOFOLLOW),"reinspect controller socket");
   require(before.st_dev==after.st_dev&&before.st_ino==after.st_ino&&before.st_uid==after.st_uid,"controller socket identity changed");
   ipc::send_frame(fd_.n,"HELLO\t2\t"+hex(run_id)+"\t"+manifest_+"\t"+hex(worker_id)+"\t"+lease_,until,io_);
   require(ipc::frame(fd_.n,until)==ipc::ack(0,manifest_),"controller run/manifest/worker/lease handshake failed");owner();
  }catch(...){poison("controller handshake failed");throw;}
 }
 ~ControlledNativeClient()override{fd_=FD{};}
 ControlledNativeClient(const ControlledNativeClient&)=delete;ControlledNativeClient&operator=(const ControlledNativeClient&)=delete;
 void before_backend_init(const std::string&id)override{command("backend",id,1);}
 void before_model_load(const std::string&id)override{command("model",id,1);}
 void before_context(const std::string&id)override{command("context",id,1);}
 void before_placement(const std::string&id)override{command("placement",id,1);}
 void before_request(const std::string&id)override{local(active_.empty(),"local request already active");command("request",id,1);active_=id;}
 void before_decode(const std::string&id,std::size_t n)override{local(active_==id,"decode does not own active request");command("rows",id,n);}
 void before_mutation(const std::string&id,const std::string&action)override{
  local(active_==id,"mutation does not own active request");command("mutation",id,0,action);
  // The frozen StreamCapture's emergency UNCERTAIN marker uses direct POSIX
  // cleanup after poison. Reserve its bounded1KiB before capture filesystem work;
  // no refund after success. <=348capture directories fits old1MiB marker bound.
  if(action=="capture_open")command("bytes",id,1024,"metadata");
 }
 void finish_request(const std::string&id,const std::string&status)override{local(active_==id,"terminal does not own active request");command("finish",id,0,status);active_.clear();}
 static std::string fd_path(int fd){std::vector<char>b(8192);const auto n=::readlink(("/proc/self/fd/"+std::to_string(fd)).c_str(),b.data(),b.size());require(n>0&&std::size_t(n)<b.size(),"bounded actual fd path required");return std::string(b.data(),std::size_t(n));}
 static bool hex_leaf(const std::string&s,std::size_t n){if(s.size()!=n)return false;for(char c:s)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;return true;}
 std::string write_kind(int fd,bool directory=false)const{
  auto root=absolute_dir(capture_root_);struct stat st{};checked(::fstat(root.n,&st),"capture root still available");require(st.st_dev==capture_dev_&&st.st_ino==capture_ino_,"capture root identity changed");
  const auto full=fd_path(fd);if(directory&&full==capture_root_)return "metadata";
  require(full.rfind(capture_root_+"/",0)==0,"capture fd outside frozen capture root");const auto relative=full.substr(capture_root_.size()+1);const auto slash=relative.find('/');
  if(slash==std::string::npos){if(directory){require(valid_capture(relative),"unknown capture directory");return "metadata";}require(relative.size()==37&&relative.substr(32)==".json"&&hex_leaf(relative.substr(0,32),32),"unknown root receipt file");return "metadata";}
  require(relative.find('/',slash+1)==std::string::npos&&valid_capture(relative.substr(0,slash)),"unknown nested capture path");const auto leaf=relative.substr(slash+1);require(!directory,"unexpected nested capture directory");
  if(leaf=="active_k.bin"||leaf=="active_v.bin"||leaf=="vectors.bin"||leaf=="owned.bin")return "raw";
  require(leaf=="CAPTURE_OPEN"||leaf=="SNAPSHOT.json"||leaf=="TRANSPORT.pending"||leaf=="UNCERTAIN","unknown capture metadata file");return "metadata";
 }
 static bool valid_capture(const std::string&s){if(s.size()<26||!hex_leaf(s.substr(0,24),24)||s[24]!='-')return false;const auto phase=s.substr(25);return phase=="POST_RECONCILE"||phase=="POST_APPEND"||phase=="TERMINAL"||phase=="RESET"||phase=="BEFORE_NEXT_MUTATION"||phase=="AFTER_NEXT_MUTATION";}
 void before_write(std::size_t n,const std::string&kind){local(!active_.empty()&&n>0&&n<=1024*1024&&(kind=="raw"||kind=="metadata"),"bounded active capture write required");command("bytes",active_,n,kind);}
 void before_sync(bool directory){local(!active_.empty(),"sync requires an active charged request");command("sync",active_,0,directory?"directory":"file");}
 void close_worker(){local(active_.empty(),"cannot close active request");command("close","worker");closed_=true;fd_=FD{};}
 void poison(const std::string&)noexcept override{poisoned_=true;fd_=FD{};}
 bool poisoned()const{return poisoned_;}
 const std::string& active_request()const{return active_;}
};
inline IO controller_io(BudgetHooks&hooks,IO host={}){
 auto*client=dynamic_cast<ControlledNativeClient*>(&hooks);require(client,"actual writer requires controller-bound client, not bare mock budget");
 IO io=host;
 io.write=[client,write=host.write](int f,const void*p,std::size_t n)->ssize_t{
  try{struct stat st{};checked(::fstat(f,&st),"capture fd metadata");require(S_ISREG(st.st_mode)&&st.st_uid==::geteuid(),"capture fd must be an owned regular file");
   const auto flags=::fcntl(f,F_GETFL);checked(flags,"capture fd flags");require((flags&O_ACCMODE)==O_WRONLY,"capture fd must be write-only");
   require(n>0,"empty writes need no raw transport operation");client->before_write(n,client->write_kind(f));
   const auto r=write(f,p,n);require(r>=0&&static_cast<std::size_t>(r)==n,"short/failed controlled write; reserved bytes retained; no retry");return r;
  }catch(...){client->poison("controlled capture write failed");throw;}
 };
 io.sync=[client,sync=host.sync](int f)->int{
  try{struct stat st{};checked(::fstat(f,&st),"capture sync fd metadata");require((S_ISREG(st.st_mode)||S_ISDIR(st.st_mode))&&st.st_uid==::geteuid(),"capture sync owned file/directory required");(void)client->write_kind(f,S_ISDIR(st.st_mode));client->before_sync(S_ISDIR(st.st_mode));
   const auto r=sync(f);require(r==0,"controlled fsync failure; STOP");return r;
  }catch(...){client->poison("controlled capture sync failed");throw;}
 };
 return io;
}
}
