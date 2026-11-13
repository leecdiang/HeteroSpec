#pragma once
// CPU-only immutable job and POSIX identity helpers; no model/backend API.
#include "bridge_client.hpp"
#include <nlohmann/json.hpp>
#include <set>
#include <linux/memfd.h>
#include <sys/syscall.h>
namespace hs::n1chain {
using BridgeJSON=nlohmann::json;
inline std::string bridge_path(const BridgeJSON&j,const char*name){
 require(j.at(name).is_string(),"job path must be a string");const auto s=j.at(name).get<std::string>();require(!s.empty()&&s[0]=='/'&&s.size()<8192&&s.find('\0')==std::string::npos&&s.find('\n')==std::string::npos,"bounded absolute job path required");return s;
}
inline std::string bridge_digest(const BridgeJSON&j,const char*name){require(j.at(name).is_string(),"job digest string required");const auto s=j.at(name).get<std::string>();require(s.size()==64,"full job binding SHA256 required");for(char c:s)require((c>='0'&&c<='9')||(c>='a'&&c<='f'),"job binding digest syntax");return s;}
inline uint64_t bridge_uint(const BridgeJSON&j,const char*name,uint64_t maximum=uint64_t(1)<<62){require(j.at(name).is_number_integer(),"integer job field required");const auto n=j.at(name).get<int64_t>();require(n>=0&&uint64_t(n)<=maximum,"bounded job integer required");return uint64_t(n);}
inline std::string bridge_fd_hash(int fd,uint64_t maximum=4*1024*1024){
 struct stat a{};checked(::fstat(fd,&a),"held file identity");require(S_ISREG(a.st_mode)&&a.st_size>=0&&uint64_t(a.st_size)<=maximum,"bounded held regular file required");Sha256 h;std::vector<char>b(65536);off_t offset=0;
 while(offset<a.st_size){const auto want=std::min<off_t>(off_t(b.size()),a.st_size-offset);const auto n=::pread(fd,b.data(),size_t(want),offset);require(n==want,"short held file read");h.update(b.data(),size_t(n));offset+=n;}
 struct stat z{};checked(::fstat(fd,&z),"held file stable identity");require(a.st_dev==z.st_dev&&a.st_ino==z.st_ino&&a.st_size==z.st_size&&a.st_mtim.tv_sec==z.st_mtim.tv_sec&&a.st_mtim.tv_nsec==z.st_mtim.tv_nsec&&a.st_ctim.tv_sec==z.st_ctim.tv_sec&&a.st_ctim.tv_nsec==z.st_ctim.tv_nsec,"held file changed during hash");return h.finish();
}
inline FD bridge_open_readonly(const std::string&path){const auto split=path.find_last_of('/');require(split!=std::string::npos&&split+1<path.size(),"job/file basename required");auto dir=absolute_dir(split?path.substr(0,split):"/");const auto leaf=path.substr(split+1);require(leaf!="."&&leaf!=".."&&leaf.find('\0')==std::string::npos,"safe job/file leaf");FD f(::openat(dir.n,leaf.c_str(),O_RDONLY|O_NOFOLLOW|O_CLOEXEC));checked(f.n,"open frozen job/file");return f;}
inline BridgeJSON bridge_process(pid_t pid){return{{"pid",pid},{"start_ticks",ipc::amount(controller_start_ticks(pid))},{"uid",::geteuid()},{"boot_id",controller_boot_id()}};}
struct BridgeJob {
 std::string path,sha256;FD source_fd,fd;struct stat initial{};BridgeJSON value;
 BridgeJob(const std::string&p,const std::string&hash):path(p),sha256(hash),source_fd(bridge_open_readonly(p)){
  require(sha256.size()==64,"exact job SHA required");for(char c:sha256)require((c>='0'&&c<='9')||(c>='a'&&c<='f'),"job SHA syntax");checked(::fstat(source_fd.n,&initial),"job initial identity");require(initial.st_uid==::geteuid()&&(initial.st_mode&022)==0&&initial.st_size>0&&initial.st_size<=2*1024*1024,"owned immutable bounded job required");
  // Parse exactly the bytes whose hash is checked. Hash-before-read alone can
  // accept a changed/restored mutable source between those two operations.
  std::string raw(size_t(initial.st_size),'\0');require(::pread(source_fd.n,raw.data(),raw.size(),0)==ssize_t(raw.size()),"full job read");require(Sha256::of(raw)==sha256,"parsed job bytes differ from root binding");
  fd=FD(int(::syscall(SYS_memfd_create,"hs-immutable-bridge-job",MFD_CLOEXEC|MFD_ALLOW_SEALING)));checked(fd.n,"sealed job snapshot");require(::write(fd.n,raw.data(),raw.size())==ssize_t(raw.size()),"short immutable job staging write");const int seals=F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL;checked(::fcntl(fd.n,F_ADD_SEALS,seals),"seal immutable job");require((::fcntl(fd.n,F_GET_SEALS)&seals)==seals&&bridge_fd_hash(fd.n,2*1024*1024)==sha256,"immutable job snapshot seal/hash conflict");
  value=BridgeJSON::parse(raw);require(value.is_object(),"job object required");verify();
 }
 void verify()const{
  auto pathfd=bridge_open_readonly(path);struct stat current{},linked{};checked(::fstat(source_fd.n,&current),"held job source identity");checked(::fstat(pathfd.n,&linked),"job pathname identity");require(current.st_dev==initial.st_dev&&current.st_ino==initial.st_ino&&current.st_size==initial.st_size&&current.st_mtim.tv_sec==initial.st_mtim.tv_sec&&current.st_mtim.tv_nsec==initial.st_mtim.tv_nsec&&current.st_ctim.tv_sec==initial.st_ctim.tv_sec&&current.st_ctim.tv_nsec==initial.st_ctim.tv_nsec&&linked.st_dev==initial.st_dev&&linked.st_ino==initial.st_ino,"held or linked job source identity changed");require(bridge_fd_hash(source_fd.n,2*1024*1024)==sha256&&bridge_fd_hash(pathfd.n,2*1024*1024)==sha256&&bridge_fd_hash(fd.n,2*1024*1024)==sha256,"job bytes changed");const int seals=F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL;require((::fcntl(fd.n,F_GET_SEALS)&seals)==seals,"job snapshot lost immutable seals");
 }
 ControllerPeer controller()const{
  const auto&j=value.at("controller_owner");const auto pid=bridge_uint(j,"pid",uint64_t(std::numeric_limits<pid_t>::max()));require(pid>0&&bridge_uint(j,"uid")==::geteuid(),"same-owner controller required");std::string ticks;if(j.at("start_ticks").is_string())ticks=j.at("start_ticks").get<std::string>();else ticks=std::to_string(bridge_uint(j,"start_ticks"));(void)ipc::amount(ticks);return{pid_t(pid),ticks,j.at("boot_id").get<std::string>()};
 }
 BridgeBinding binding()const{return{sha256,bridge_digest(value,"domain_sha256"),bridge_digest(value,"device_sha256"),value.at("stage").get<std::string>()};}
 std::vector<std::string> requests()const{const auto&v=value.at("request_ids");require(v.is_array()&&!v.empty()&&v.size()<=18,"finite fixed CPU request IDs");std::vector<std::string>out;std::set<std::string>seen;for(const auto&x:v){require(x.is_string(),"CPU request ID string");auto id=x.get<std::string>();identifier(id);require(seen.insert(id).second,"duplicate CPU request ID");out.push_back(std::move(id));}return out;}
};
}
