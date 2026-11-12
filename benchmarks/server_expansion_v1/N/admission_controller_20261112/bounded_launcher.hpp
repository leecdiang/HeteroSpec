#pragma once
// Linux host supervision only; no backend/model/CUDA or dynamic-loader API.
// Native fork/exec is behind the unchanged concrete permanent deny gate.
#include "native_client.hpp"
#include <cmath>
#include <signal.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <sys/timerfd.h>
#include <sys/wait.h>
namespace hs::n1chain {
inline double launch_clock(clockid_t id){timespec t{};checked(::clock_gettime(id,&t),"launcher clock");return double(t.tv_sec)+double(t.tv_nsec)/1e9;}
struct BoundedLaunchSpec {
 ControllerPeer controller;
 double deadline_wall=0,deadline_mono=0;
 uint64_t per_log_bytes=0;
 std::string placement_id,executable,executable_sha256;
 std::vector<std::string>arguments,environment;
 int stdout_fd=-1,stderr_fd=-1;
};
struct BoundedLaunchResult {
 std::string status;pid_t owned_child=-1;bool stop_signal_delivered=false,exit_confirmed=false;
 int wait_status=0;bool native_authority=false;
 bool stdout_complete=false,stderr_complete=false,output_partial=false;
 uint64_t stdout_bytes=0,stderr_bytes=0;
};
struct BoundedLogIO {
 std::function<ssize_t(int,const void*,std::size_t)>write=[](int f,const void*p,std::size_t n){return::write(f,p,n);};
 std::function<int(int)>sync=[](int f){return::fsync(f);};
};
namespace launch_detail {
inline bool owner_present(const ControllerPeer&peer)noexcept{try{if(peer.pid<=0||peer.start_ticks!=controller_start_ticks(peer.pid)||peer.boot_id!=controller_boot_id())return false;std::ifstream f("/proc/"+std::to_string(peer.pid)+"/stat");std::string s;if(!std::getline(f,s))return false;const auto end=s.rfind(')');return end!=std::string::npos&&end+2<s.size()&&s[end+2]!='Z'&&s[end+2]!='X';}catch(...){return false;}}
inline void valid_time(const BoundedLaunchSpec&s){const auto wall=launch_clock(CLOCK_REALTIME),mono=launch_clock(CLOCK_MONOTONIC);require(std::isfinite(s.deadline_wall)&&std::isfinite(s.deadline_mono)&&s.deadline_wall>wall&&s.deadline_mono>mono&&s.deadline_wall-wall<=18000&&s.deadline_mono-mono<=18000,"explicit remaining wall/monotonic lease at most5h required");require(owner_present(s.controller),"controller owner identity unavailable");}
inline bool expired(const BoundedLaunchSpec&s){return launch_clock(CLOCK_REALTIME)>=s.deadline_wall||launch_clock(CLOCK_MONOTONIC)>=s.deadline_mono;}
inline FD timer(const BoundedLaunchSpec&s){FD f(::timerfd_create(CLOCK_MONOTONIC,TFD_CLOEXEC|TFD_NONBLOCK));checked(f.n,"create lease timer");itimerspec t{};t.it_value.tv_sec=time_t(s.deadline_mono);t.it_value.tv_nsec=long((s.deadline_mono-double(t.it_value.tv_sec))*1e9);checked(::timerfd_settime(f.n,TFD_TIMER_ABSTIME,&t,nullptr),"arm absolute lease timer");return f;}
inline FD child_pidfd(pid_t child){
#ifdef SYS_pidfd_open
 FD f(int(::syscall(SYS_pidfd_open,child,0)));checked(f.n,"owned child pidfd required");return f;
#else
 (void)child;throw Blocked("Linux pidfd support required; no PID-number kill fallback");
#endif
}
inline bool kill_owned(int pidfd){
#ifdef SYS_pidfd_send_signal
 const auto r=int(::syscall(SYS_pidfd_send_signal,pidfd,SIGKILL,nullptr,0));if(r<0&&errno==ESRCH)return false;checked(r,"signal owned pidfd");return true;
#else
 (void)pidfd;throw Blocked("pidfd signal unavailable; no unknown PID/group signal");
#endif
}
inline bool reap_owned(pid_t child,int pidfd,int&status,unsigned timeout){pollfd p{pidfd,POLLIN,0};const auto n=::poll(&p,1,int(timeout));if(n<0&&errno==EINTR)return false;checked(n,"poll owned child exit");if(!n)return false;const auto got=::waitpid(child,&status,WNOHANG);checked(got,"reap owned child");return got==child;}
// This internal host primitive executes only a supplied compiled child action.
// CPU fixtures supply a fixed pause loop. The sole native caller below checks
// ProductionGate before reaching this function or constructing its exec action.
template<class ChildAction>
BoundedLaunchResult supervise_owned(const BoundedLaunchSpec&s,ChildAction child_action,BoundedLogIO log_io={}){
 valid_time(s);auto lease_timer=timer(s);int barrier[2];checked(::socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,barrier),"pre-exec owner barrier");FD barrier_read(barrier[0]),barrier_write(barrier[1]);
 const bool logs=s.stdout_fd>=0||s.stderr_fd>=0;FD log_read[2],log_write[2];const int targets[2]={s.stdout_fd,s.stderr_fd};uint64_t recorded[2]={0,0};
 if(logs){require(s.stdout_fd>STDERR_FILENO&&s.stderr_fd>STDERR_FILENO&&s.per_log_bytes>0&&s.per_log_bytes<=12*1024*1024,"two finite parent-drained logs required");struct stat identities[2]{};for(unsigned i=0;i<2;i++){checked(::fstat(targets[i],&identities[i]),"log file identity");require(S_ISREG(identities[i].st_mode)&&identities[i].st_uid==::geteuid()&&identities[i].st_size==0,"fresh owned regular log required");const auto flags=::fcntl(targets[i],F_GETFL);checked(flags,"log fd flags");require((flags&O_ACCMODE)==O_WRONLY&&!(flags&O_APPEND)&&::lseek(targets[i],0,SEEK_CUR)==0,"fresh write-only log at offset0 required");int pipe[2];checked(::pipe2(pipe,O_CLOEXEC|O_NONBLOCK),"bounded log pipe");log_read[i]=FD(pipe[0]);log_write[i]=FD(pipe[1]);}require(identities[0].st_dev!=identities[1].st_dev||identities[0].st_ino!=identities[1].st_ino,"stdout/stderr must be distinct frozen files");}
 const pid_t supervisor=::getpid();const auto supervisor_start=controller_start_ticks(supervisor),boot=controller_boot_id();const auto child=::fork();checked(child,"fork own bounded child");
 if(child==0){barrier_write=FD{};
  // Parent can die between fork and prctl. The identity recheck closes that
  // gap before the barrier/exec; later death is handled by the kernel signal.
  if(::prctl(PR_SET_PDEATHSIG,SIGKILL)<0)::_exit(121);
  if(::getppid()!=supervisor)::_exit(122);
  try{if(controller_start_ticks(supervisor)!=supervisor_start||controller_boot_id()!=boot)::_exit(123);}catch(...){::_exit(123);}
  if(::setsid()<0)::_exit(124);char permit=0;
  if(::read(barrier_read.n,&permit,1)!=1||permit!='1')::_exit(125);barrier_read=FD{};
  if(logs){for(unsigned i=0;i<2;i++){log_read[i]=FD{};const auto flags=::fcntl(log_write[i].n,F_GETFL);if(flags<0||::fcntl(log_write[i].n,F_SETFL,flags&~O_NONBLOCK)<0||::dup2(log_write[i].n,i?STDERR_FILENO:STDOUT_FILENO)<0)::_exit(132);log_write[i]=FD{};::close(targets[i]);}}
  try{if(expired(s)||!owner_present(s.controller))::_exit(126);child_action();}catch(...){::_exit(127);}::_exit(0);
 }
 barrier_read=FD{};log_write[0]=FD{};log_write[1]=FD{};FD pidfd;
 try{pidfd=child_pidfd(child);require(!expired(s)&&owner_present(s.controller),"lease/owner lost before child permit");const char permit='1';require(::send(barrier_write.n,&permit,1,MSG_NOSIGNAL)==1,"child pre-exec permit failed");barrier_write=FD{};}
 catch(...){barrier_write=FD{};int ignored=0;auto n=::waitpid(child,&ignored,WNOHANG);(void)n;throw;}
 BoundedLaunchResult result;result.owned_child=child;
 const auto stop=[&](const std::string&why){result.stdout_bytes=recorded[0];result.stderr_bytes=recorded[1];result.output_partial=logs;result.stop_signal_delivered=kill_owned(pidfd.n);if(!result.exit_confirmed)result.exit_confirmed=reap_owned(child,pidfd.n,result.wait_status,1000);result.status=why;if(!result.exit_confirmed)result.status+="_EXIT_UNCONFIRMED_BLOCKED";return result;};
 try{for(;;){pollfd p[4]={{result.exit_confirmed?-1:pidfd.n,POLLIN,0},{lease_timer.n,POLLIN,0},{log_read[0].n,POLLIN,0},{log_read[1].n,POLLIN,0}};auto n=::poll(p,4,100);if(n<0&&errno==EINTR)continue;checked(n,"bounded child supervision poll");
  if(p[0].revents&POLLIN)result.exit_confirmed=reap_owned(child,pidfd.n,result.wait_status,0);
  for(unsigned i=0;i<2;i++)if(log_read[i].n>=0&&(p[i+2].revents&(POLLIN|POLLHUP))){char bytes[65536];const auto got=::read(log_read[i].n,bytes,sizeof bytes);if(got<0&&(errno==EAGAIN||errno==EINTR))continue;checked(int(got),"read bounded child log");if(!got){log_read[i]=FD{};continue;}const auto remaining=s.per_log_bytes-recorded[i],keep=std::min<uint64_t>(uint64_t(got),remaining);if(keep){const auto wrote=log_io.write(targets[i],bytes,std::size_t(keep));if(wrote>=0&&uint64_t(wrote)<=keep)recorded[i]+=uint64_t(wrote);if(wrote<0||uint64_t(wrote)!=keep)return stop("OUTPUT_WRITE_FAILURE_STOP_SENT");}if(uint64_t(got)>remaining)return stop("OUTPUT_LIMIT_STOP_SENT");}
  if(result.exit_confirmed&&log_read[0].n<0&&log_read[1].n<0){result.stdout_bytes=recorded[0];result.stderr_bytes=recorded[1];if(logs)for(int target:targets)if(log_io.sync(target)<0){result.status="OUTPUT_FSYNC_FAILURE";result.output_partial=true;return result;}result.stdout_complete=result.stderr_complete=logs;result.status="OWNED_CHILD_EXITED";return result;}
  const bool timed=(p[1].revents&POLLIN)||expired(s),lost=!owner_present(s.controller);
  if(timed||lost)return stop(lost?"CONTROLLER_LOST_STOP_SENT":"DEADLINE_STOP_SENT");
 }}catch(...){return stop("SUPERVISION_EXCEPTION_STOP_SENT");}
}
inline std::string file_sha(const std::string&p){std::ifstream f(p,std::ios::binary);require(bool(f),"bound executable file");Sha256 h;std::vector<char>b(1024*1024);while(f){f.read(b.data(),b.size());h.update(b.data(),std::size_t(f.gcount()));}require(f.eof(),"bound executable hash read");return h.finish();}
inline void logfile(int fd,uint64_t limit){struct stat st{};checked(::fstat(fd,&st),"preopened launcher log identity");require(S_ISREG(st.st_mode)&&st.st_uid==::geteuid()&&uint64_t(st.st_size)<=limit,"owned bounded regular log required");const auto flags=::fcntl(fd,F_GETFL);checked(flags,"launcher log flags");require((flags&O_ACCMODE)==O_WRONLY,"write-only launcher log required");}
}
inline BoundedLaunchResult guarded_native_launch(ProductionGate&gate,BudgetHooks&account,const BoundedLaunchSpec&s){
 gate.before_placement(s.placement_id); // permanent denial BEFORE fork/exec/hash/FD effects
 launch_detail::valid_time(s);identifier(s.placement_id);require(!s.executable.empty()&&s.executable[0]=='/'&&s.executable_sha256.size()==64,"explicit frozen native executable required");
 require(launch_detail::file_sha(s.executable)==s.executable_sha256,"native executable identity mismatch");
 require(s.per_log_bytes>0&&s.per_log_bytes<=12*1024*1024,"finite per-log ceiling <=12MiB required");launch_detail::logfile(s.stdout_fd,s.per_log_bytes);launch_detail::logfile(s.stderr_fd,s.per_log_bytes);
 account.before_placement(s.placement_id); // controller verifies the pre-exec reservation, never refunds/double-charges
 return launch_detail::supervise_owned(s,[&]{
  rlimit cores{0,0};if(::setrlimit(RLIMIT_CORE,&cores)<0)::_exit(128);
  std::vector<char*>argv,env;for(const auto&x:s.arguments)argv.push_back(const_cast<char*>(x.c_str()));argv.push_back(nullptr);for(const auto&x:s.environment)env.push_back(const_cast<char*>(x.c_str()));env.push_back(nullptr);
  if(s.arguments.empty()||s.arguments.front()!=s.executable)::_exit(130);::execve(s.executable.c_str(),argv.data(),env.data());::_exit(131);
 });
}
}
