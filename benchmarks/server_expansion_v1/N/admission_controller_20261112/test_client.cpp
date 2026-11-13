// CPU-only fake controller and owned host files. No native/model libraries.
#include "native_client.hpp"
#include <filesystem>
#include <iostream>
#include <sys/wait.h>
namespace fs=std::filesystem;
using namespace hs::n1chain;
static unsigned groups=0;
static void check(bool b,const char*w){if(!b)throw Blocked(w);}
template<class F>static void rejects(F f){bool no=false;try{f();}catch(const std::exception&){no=true;}check(no,"expected CPU fixture rejection");}
static std::string read(const std::string&p){std::ifstream f(p);return{std::istreambuf_iterator<char>(f),std::istreambuf_iterator<char>()};}
struct Child{
 pid_t pid=-1;std::string dir,socket,capture;ControllerPeer peer;
 int finish(){int s=0;checked(::waitpid(pid,&s,0),"wait owned mock controller");pid=-1;check(WIFEXITED(s),"mock controller exited by signal");return WEXITSTATUS(s);}
};
static Child start(const std::string&root,const std::string&name,const std::string&fault=""){
 const auto d=root+"/"+name;checked(::mkdir(d.c_str(),0700),"fresh mock case");const auto cap=d+"/captures";checked(::mkdir(cap.c_str(),0700),"fresh capture root");
 int ready[2];checked(::pipe(ready),"owned mock readiness pipe");const std::string socket=d+"/s";auto pid=::fork();checked(pid,"fork owned std-only mock controller");
 if(pid==0){::close(ready[0]);int rc=0;try{
  FD listener(::socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0));checked(listener.n,"fake controller socket");const auto a=ipc::address(socket);checked(::bind(listener.n,reinterpret_cast<const sockaddr*>(&a),sizeof a),"bind fake controller");checked(::chmod(socket.c_str(),0600),"fake controller private mode");checked(::listen(listener.n,1),"listen fake controller");const char yes='1';check(::write(ready[1],&yes,1)==1,"fake ready");::close(ready[1]);
  pollfd p{listener.n,POLLIN,0};if(::poll(&p,1,2000)<=0)::_exit(0);FD conn(::accept4(listener.n,nullptr,nullptr,SOCK_CLOEXEC|SOCK_NONBLOCK));checked(conn.n,"fake accept");
  ipc::SocketIO io;const auto h=ipc::fields(ipc::frame(conn.n,ipc::deadline(2000)));
  check(h.size()==6&&h[0]=="HELLO"&&h[1]=="2"&&unhex(h[2])=="run"&&h[3]==std::string(64,'a')&&unhex(h[4])=="worker"&&h[5]==std::string(64,'b'),"fake v2 handshake");
  if(fault=="hello-deny"){ipc::send_frame(conn.n,"DENY",ipc::deadline(2000),io);::_exit(0);}
  ipc::send_frame(conn.n,ipc::ack(0,std::string(64,'a')),ipc::deadline(2000),io);
  std::ofstream log(d+"/COMMANDS.tsv");uint64_t seq=0;
  for(;;){const auto f=ipc::fields(ipc::frame(conn.n,ipc::deadline(2000)));check(f.size()==6&&f[0]=="CMD"&&ipc::amount(f[1])==++seq,"fake command sequence");log<<f[1]<<'\t'<<f[2]<<'\t'<<unhex(f[3])<<'\t'<<f[4]<<'\t'<<unhex(f[5])<<'\n';log.flush();
   if(fault=="bad-ack"){ipc::send_frame(conn.n,ipc::ack(seq+1,std::string(64,'a')),ipc::deadline(2000),io);break;}
   if(fault=="partial-ack"){uint32_t n=htonl(100);check(::send(conn.n,&n,4,MSG_NOSIGNAL)==4,"partial frame header");check(::send(conn.n,"ACK",3,MSG_NOSIGNAL)==3,"partial frame body");break;}
   if(fault=="timeout"){::poll(nullptr,0,200);break;}
   if(fault=="deny-bytes"&&f[2]=="bytes"){ipc::send_frame(conn.n,"DENY",ipc::deadline(2000),io);break;}
   if(f[2]=="bytes")check((unhex(f[5])=="raw"||unhex(f[5])=="metadata")&&ipc::amount(f[4])>0&&ipc::amount(f[4])<=1024*1024,"fake byte contract");
   ipc::send_frame(conn.n,ipc::ack(seq,std::string(64,'a')),ipc::deadline(2000),io);if(f[2]=="close")break;
  }
 }catch(const std::exception&e){std::ofstream(d+"/EXPECTED_DISCONNECT.txt")<<e.what()<<'\n';}::_exit(rc);}
 ::close(ready[1]);char yes=0;check(::read(ready[0],&yes,1)==1&&yes=='1',"fake server ready");::close(ready[0]);return{pid,d,socket,cap,{pid,controller_start_ticks(pid),controller_boot_id()}};
}
static ControlledNativeClient connect(const Child&c,unsigned timeout=500){return ControlledNativeClient(c.socket,"run",std::string(64,'a'),"worker",timeout,c.peer,std::string(64,'b'),c.capture);}
static FD output(const Child&c,const std::string&leaf="active_k.bin"){
 const auto dir=c.capture+"/"+std::string(24,'c')+"-TERMINAL";if(!fs::exists(dir))checked(::mkdir(dir.c_str(),0700),"fresh mock tensor directory");FD f(::open((dir+"/"+leaf).c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600));checked(f.n,"fresh mock tensor");return f;
}
int main(int argc,char**argv){try{
 check(argc==3&&std::string(argv[1])=="--cpu-only-client-test","explicit std-only CPU test mode required");const std::string root=argv[2];check(root.size()<50&&root[0]=='/',"short fresh absolute fixture directory");checked(::mkdir(root.c_str(),0700),"fresh root");
 auto test=[&](const char*name,const auto&fn){fn();groups++;std::cout<<"PASS "<<name<<'\n';};
 test("v2 owner-bound hook and raw/metadata IO path",[&]{auto c=start(root,"ok");{auto a=connect(c);a.before_backend_init("deployment");a.before_model_load("deployment");a.before_context("deployment");a.before_placement("deployment");a.before_request("req");a.before_decode("req",1);a.before_mutation("req","capture_open");auto io=controller_io(a);auto f=output(c);check(io.write(f.n,"abcd",4)==4,"raw host write");check(io.sync(f.n)==0,"raw host sync");FD receipt(::open((c.capture+"/"+std::string(32,'d')+".json").c_str(),O_WRONLY|O_CREAT|O_EXCL,0600));checked(receipt.n,"mock receipt");check(io.write(receipt.n,"{}\n",3)==3,"metadata write");auto dir=absolute_dir(c.capture);check(io.sync(dir.n)==0,"owned root sync");a.finish_request("req","COMPLETED");a.close_worker();}check(c.finish()==0,"controller close");const auto log=read(c.dir+"/COMMANDS.tsv");check(log.find("bytes\treq\t1024\tmetadata")!=std::string::npos&&log.find("bytes\treq\t4\traw")!=std::string::npos&&log.find("bytes\treq\t3\tmetadata")!=std::string::npos,"separate conservative byte reservations");});
 for(const auto&fault:{"bad-ack","partial-ack","timeout"})test(("fail closed on "+std::string(fault)).c_str(),[&,fault]{auto c=start(root,fault,fault);{auto a=connect(c,50);rejects([&]{a.before_request("req");});check(a.poisoned(),"uncertain ACK poisons");rejects([&]{a.before_request("retry");});}check(c.finish()==0,"fake fail closed");});
 test("controller rejects owner lease handshake",[&]{auto c=start(root,"lease","hello-deny");rejects([&]{auto a=connect(c);(void)a;});check(c.finish()==0,"lease rejection");});
 test("wrong peer PID rejects before controller commands",[&]{auto c=start(root,"pid");auto peer=c.peer;peer.pid=::getpid();peer.start_ticks=controller_start_ticks(peer.pid);rejects([&]{ControlledNativeClient a(c.socket,"run",std::string(64,'a'),"worker",200,peer,std::string(64,'b'),c.capture);});check(c.finish()==0,"wrong PID");});
 test("wrong peer start ticks rejects",[&]{auto c=start(root,"start");auto peer=c.peer;peer.start_ticks="0";rejects([&]{ControlledNativeClient a(c.socket,"run",std::string(64,'a'),"worker",200,peer,std::string(64,'b'),c.capture);});check(c.finish()==0,"wrong start");});
 test("wrong boot identity rejects",[&]{auto c=start(root,"boot");auto peer=c.peer;peer.boot_id=std::string(36,'0');rejects([&]{ControlledNativeClient a(c.socket,"run",std::string(64,'a'),"worker",200,peer,std::string(64,'b'),c.capture);});check(c.finish()==0,"wrong boot");});
 test("lost controller socket identity poisons before request",[&]{auto c=start(root,"socket");{auto a=connect(c);checked(::rename(c.socket.c_str(),(c.socket+".retained").c_str()),"retain owned mock socket");rejects([&]{a.before_request("req");});check(a.poisoned(),"lost socket poisons");}check(c.finish()==0,"socket loss");});
 test("duplicate local request poisons without second command",[&]{auto c=start(root,"duplicate");{auto a=connect(c);a.before_request("req");rejects([&]{a.before_request("again");});check(a.poisoned(),"duplicate local request poison");}check(c.finish()==0,"duplicate request");});
 test("cross-request decode poisons before row reservation",[&]{auto c=start(root,"cross");{auto a=connect(c);a.before_request("req");rejects([&]{a.before_decode("other",1);});check(a.poisoned(),"cross request poison");}check(c.finish()==0,"cross request");});
 test("byte denial precedes any host write",[&]{auto c=start(root,"bytes","deny-bytes");{auto a=connect(c);a.before_request("req");unsigned writes=0;IO host;host.write=[&](int,const void*,size_t n){writes++;return ssize_t(n);};auto io=controller_io(a,host);auto f=output(c);rejects([&]{io.write(f.n,"abcd",4);});check(writes==0&&a.poisoned(),"quota denies before write");}check(c.finish()==0,"byte denial");});
 test("partial host write preserves reservation and forbids retry",[&]{auto c=start(root,"short");{auto a=connect(c);a.before_request("req");unsigned writes=0;IO host;host.write=[&](int,const void*,size_t){writes++;return ssize_t(2);};auto io=controller_io(a,host);auto f=output(c);rejects([&]{io.write(f.n,"abcd",4);});rejects([&]{io.write(f.n,"cd",2);});check(writes==1&&a.poisoned(),"partial write no retry");}check(c.finish()==0,"partial write");check(read(c.dir+"/COMMANDS.tsv").find("bytes\treq\t4\traw")!=std::string::npos,"full attempted bytes retained");});
 test("ENOSPC poisons after durable byte reservation",[&]{auto c=start(root,"enospc");{auto a=connect(c);a.before_request("req");IO host;host.write=[](int,const void*,size_t)->ssize_t{errno=ENOSPC;return-1;};auto io=controller_io(a,host);auto f=output(c);rejects([&]{io.write(f.n,"abcd",4);});check(a.poisoned(),"disk exhaustion poison");}check(c.finish()==0,"disk exhaustion");});
 test("failed fsync poisons after sync guard",[&]{auto c=start(root,"fsync");{auto a=connect(c);a.before_request("req");IO host;host.sync=[](int){errno=EIO;return-1;};auto io=controller_io(a,host);auto f=output(c);rejects([&]{io.sync(f.n);});check(a.poisoned(),"fsync poison");}check(c.finish()==0,"fsync failure");});
 test("outside-root FD never reaches write or byte reservation",[&]{auto c=start(root,"outside");{auto a=connect(c);a.before_request("req");auto io=controller_io(a);FD f(::open((c.dir+"/outside.bin").c_str(),O_WRONLY|O_CREAT|O_EXCL,0600));checked(f.n,"outside mock file");rejects([&]{io.write(f.n,"x",1);});check(a.poisoned(),"outside path poison");}check(c.finish()==0,"outside path");check(read(c.dir+"/COMMANDS.tsv").find("\tbytes\t")==std::string::npos,"outside fd uncharged/unwritten");});
 test("unknown in-root filename fails before host write",[&]{auto c=start(root,"unknown");{auto a=connect(c);a.before_request("req");auto io=controller_io(a);auto f=output(c,"unknown.bin");rejects([&]{io.write(f.n,"x",1);});check(a.poisoned(),"unknown leaf poison");}check(c.finish()==0,"unknown file");});
 test("changed capture root inode fails before write",[&]{auto c=start(root,"root");{auto a=connect(c);a.before_request("req");auto io=controller_io(a);auto f=output(c);checked(::rename(c.capture.c_str(),(c.capture+".retained").c_str()),"retain mock capture root");checked(::mkdir(c.capture.c_str(),0700),"new mock inode");rejects([&]{io.write(f.n,"x",1);});check(a.poisoned(),"root identity poison");}check(c.finish()==0,"root replacement");});
 test("oversize and unowned request write guards poison",[&]{for(unsigned variant=0;variant<2;variant++){auto c=start(root,variant?"size":"inactive");{auto a=connect(c);if(variant)a.before_request("req");rejects([&]{a.before_write(variant?1024*1024+1:1,"raw");});check(a.poisoned(),"write guard poison");}check(c.finish()==0,"write guard");}});
 std::cout<<"{\"status\":\"CPU_ONLY_CONTROLLED_CLIENT_PASS\",\"groups\":"<<groups<<",\"native_authority\":false,\"backend_init\":0,\"models\":0,\"contexts\":0,\"placements\":0,\"forwards\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"CPU_ONLY_CONTROLLED_CLIENT_FAIL "<<e.what()<<'\n';return 1;}}
