// Actual three-actor host bridge. CPU lane accepts one compiled-in fixed worker
// image only. Default native lane is permanently denied BEFORE parsing/open/fork.
#include "bridge_job.hpp"
#include "supervisor.hpp"
#include <iostream>
#include <linux/memfd.h>
using namespace hs::n1chain;
static FD sealed_image(const std::string&path,const std::string&fixed,uint64_t maximum){
 auto input=bridge_open_readonly(path);require(bridge_fd_hash(input.n,maximum)==fixed,"actual compiled worker image changed");
 FD image(int(::syscall(SYS_memfd_create,"hs-fixed-bridge-worker",MFD_CLOEXEC|MFD_ALLOW_SEALING)));checked(image.n,"sealed executable image");struct stat s{};checked(::fstat(input.n,&s),"worker image identity");std::vector<char>b(65536);off_t pos=0;while(pos<s.st_size){const auto n=::pread(input.n,b.data(),std::min<off_t>(b.size(),s.st_size-pos),pos);require(n>0,"short worker image read");require(::write(image.n,b.data(),size_t(n))==n,"short worker image staging write");pos+=n;}
 const int seals=F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL;checked(::fcntl(image.n,F_ADD_SEALS,seals),"seal compiled worker image");require((::fcntl(image.n,F_GET_SEALS)&seals)==seals&&bridge_fd_hash(image.n,maximum)==fixed,"worker image seal/hash conflict");return image;
}
static void check_log_fd(int fd,const std::string&path){
 require(fd>STDERR_FILENO,"preopened owned log fd required");struct stat a{},b{};checked(::fstat(fd,&a),"held log fd");require(S_ISREG(a.st_mode)&&a.st_uid==::geteuid()&&a.st_nlink==1&&a.st_size==0,"fresh single-link owned regular log required");const auto flags=::fcntl(fd,F_GETFL);checked(flags,"held log access");require((flags&O_ACCMODE)==O_WRONLY&&!(flags&O_APPEND)&&::lseek(fd,0,SEEK_CUR)==0,"held log must be write-only at offset0");auto linked=bridge_open_readonly(path);checked(::fstat(linked.n,&b),"linked log identity");require(a.st_dev==b.st_dev&&a.st_ino==b.st_ino&&BridgeClient::fd_path(fd)==path,"held/log path identity changed");
}
static BridgeJSON log_descriptor(int fd,const std::string&path,uint64_t bytes){
 struct stat held{},linked{};checked(::fstat(fd,&held),"finished held log");auto f=bridge_open_readonly(path);checked(::fstat(f.n,&linked),"finished log path");require(held.st_dev==linked.st_dev&&held.st_ino==linked.st_ino&&held.st_size>=0&&uint64_t(held.st_size)==bytes,"finished log binding/length changed");return{{"device",uint64_t(held.st_dev)},{"inode",uint64_t(held.st_ino)},{"bytes",bytes},{"sha256",bridge_fd_hash(f.n,12*1024*1024)}};
}
static int run_bridge(const std::string&path,const std::string&sha,bool cpu){
 BridgeJob job(path,sha);const auto&j=job.value;std::string fixed;
 if(cpu){
#ifdef HS_FIXED_CPU_WORKER_SHA
  require(j.at("schema")=="hs.production-bridge.cpu-job.v1"&&j.at("mode")=="CPU_FIXED_WORKER","CPU bridge cannot authorize a native/model worker");fixed=HS_FIXED_CPU_WORKER_SHA;
#else
  throw Blocked("this artifact has no CPU lane");
#endif
 }else{
#if defined(HS_NATIVE_R_SHA) && defined(HS_NATIVE_LOOP4_SHA)
  require(j.at("schema")=="hs.production-bridge.native-job.v1"&&j.at("mode")=="NATIVE_C4096_N1A"&&j.at("role")==j.at("stage"),"bound native N1a job required");fixed=j.at("stage")=="STRONG_WHOLE_RECHUNK_LOOP4"?HS_NATIVE_LOOP4_SHA:HS_NATIVE_R_SHA;
#else
  throw Blocked("native image identities are absent from this artifact");
#endif
 }
 const std::string worker=j.at("worker_id"),run=j.at("run_id"),deployment=j.at("deployment_id");identifier(worker);identifier(run);identifier(deployment);const auto controller=job.controller();const auto binding=job.binding();const auto lease=bridge_digest(j,"lease_sha256"),manifest=bridge_digest(j,"manifest_sha256");const auto socket=bridge_path(j,"accounting_socket"),capture=bridge_path(j,"capture_root");const auto image_path=bridge_path(j,"worker_executable");require(bridge_digest(j,"worker_executable_sha256")==fixed,"worker identity is not compiled into this lane");auto image=sealed_image(image_path,fixed,cpu?4*1024*1024:512ull*1024*1024);
 BoundedLaunchSpec s;s.controller=controller;s.deadline_wall=j.at("deadline_wall").get<double>();s.deadline_mono=j.at("deadline_mono").get<double>();s.per_log_bytes=bridge_uint(j,"per_log_bytes",12*1024*1024);require(s.per_log_bytes>0,"explicit log ceiling required");s.stdout_fd=int(bridge_uint(j,"stdout_fd",std::numeric_limits<int>::max()));s.stderr_fd=int(bridge_uint(j,"stderr_fd",std::numeric_limits<int>::max()));const auto stdout_path=bridge_path(j,"stdout_path"),stderr_path=bridge_path(j,"stderr_path");check_log_fd(s.stdout_fd,stdout_path);check_log_fd(s.stderr_fd,stderr_path);launch_detail::valid_time(s);job.requests();
 std::cout<<(cpu?"CPU_BRIDGE_READY\n":"NATIVE_BRIDGE_READY\n")<<std::flush;char ready=0;require(::read(STDIN_FILENO,&ready,1)==1&&ready=='1',"root must bind this exact launcher before release");job.verify();
 const auto parent=bridge_process(::getpid());
 auto before_permit=[&](pid_t child,int){
  job.verify();BridgeClient launch(socket,run,manifest,"launch/"+worker,1000,controller,lease,capture,binding);
  const auto detail=BridgeJSON{{"child",bridge_process(child)},{"parent",parent},{"worker_executable_sha256",bridge_digest(j,"worker_executable_sha256")},{"worker_executable_fd",image.n},{"job_fd",job.fd.n}};
  launch.bind_child(worker,child,detail.dump());job.verify();launch.close_session("launcher");job.verify();
 };
 auto child_action=[&]{
  job.verify();require(bridge_fd_hash(image.n,cpu?4*1024*1024:512ull*1024*1024)==bridge_digest(j,"worker_executable_sha256"),"sealed child image changed");
  rlimit cores{0,0};require(::setrlimit(RLIMIT_CORE,&cores)==0,"disable own child core dump");
  std::vector<std::string>args={image_path,path,sha};std::vector<char*>argv;for(auto&v:args)argv.push_back(v.data());argv.push_back(nullptr);
  // No arbitrary LD_PRELOAD, library path, command, arguments or environment.
  const std::string visible=cpu?"":j.at("gpu_uuid").get<std::string>();if(!cpu)require(visible.size()==40&&visible.rfind("GPU-",0)==0,"one explicit native UUID required");std::string cuda="CUDA_VISIBLE_DEVICES="+visible;char env_path[]="PATH=/usr/bin:/bin",lang[]="LANG=C.UTF-8",locale[]="LC_ALL=C.UTF-8";char*env[]={env_path,lang,locale,cuda.data(),nullptr};
  ::fexecve(image.n,argv.data(),env);::_exit(131);
 };
 const auto result=launch_detail::supervise_bridge(s,child_action,before_permit);
 BridgeJSON report={{"status",result.status},{"child_pid",result.owned_child},{"exit_confirmed",result.exit_confirmed},{"wait_status",result.wait_status},{"stdout_complete",result.stdout_complete},{"stderr_complete",result.stderr_complete},{"stdout_bytes",result.stdout_bytes},{"stderr_bytes",result.stderr_bytes},{"stop_delivered",result.stop_signal_delivered},{"output_partial",result.output_partial},{"stdout",log_descriptor(s.stdout_fd,stdout_path,result.stdout_bytes)},{"stderr",log_descriptor(s.stderr_fd,stderr_path,result.stderr_bytes)}};
 job.verify();BridgeClient supervisor(socket,run,manifest,"supervise/"+worker,1000,controller,lease,capture,binding);supervisor.report_supervisor(worker,result.owned_child,report.dump());supervisor.close_session("supervisor");
 const bool clean=result.status=="OWNED_CHILD_EXITED"&&result.exit_confirmed&&WIFEXITED(result.wait_status)&&WEXITSTATUS(result.wait_status)==0&&result.stdout_complete&&result.stderr_complete&&!result.output_partial;
 std::cout<<"{\"status\":\""<<(clean?"CPU_BRIDGE_COMPLETE":"CPU_BRIDGE_STOPPED")<<"\",\"actual_native_calls\":0}\n"<<std::flush;return clean?0:72;
}
int main(int argc,char**argv){try{
#ifdef HS_FIXED_CPU_WORKER_SHA
 if(argc==4&&std::string(argv[1])=="--cpu-fixed-worker")return run_bridge(argv[2],argv[3],true);
#endif
 // No JSON receipt, CPU flag, source hash or this prompt can open this gate.
 ProductionGate gate;gate.before_placement("NATIVE_BRIDGE_NOT_ADMITTED");require(argc==3,"native bridge requires exact job and SHA");return run_bridge(argv[1],argv[2],false);
 }catch(const std::exception&e){std::cerr<<"PRODUCTION_BRIDGE_STOP "<<e.what()<<'\n';return 73;}}
