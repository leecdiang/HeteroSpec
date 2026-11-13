#pragma once
#include "live_gate.hpp"
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/random.h>
#include <poll.h>
#include <cstring>
namespace hs::n1chain {
class Peer final{
 int fd_=-1;LiveGate&g_;
 public:
 explicit Peer(LiveGate&g):g_(g){fd_=::socket(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0);pilot_need(fd_>=0,"peer socket");sockaddr_un a{};a.sun_family=AF_UNIX;auto p=g.root()+"/SUPERVISOR.sock";pilot_need(p.size()<sizeof a.sun_path,"socket path too long");std::memcpy(a.sun_path,p.c_str(),p.size()+1);pilot_need(::connect(fd_,reinterpret_cast<sockaddr*>(&a),sizeof a)==0,"supervisor unavailable");ucred cred{};socklen_t n=sizeof cred;pilot_need(::getsockopt(fd_,SOL_SOCKET,SO_PEERCRED,&cred,&n)==0&&cred.uid==::geteuid()&&cred.pid==g.job().at("controller_pid"),"supervisor peer identity differs");}
 ~Peer(){if(fd_>=0)::close(fd_);}
 void send(PJ j){g_.guard();j["worker_id"]=g_.job().at("worker_id");auto b=j.dump();pilot_need(b.size()<60000&&::send(fd_,b.data(),b.size(),MSG_NOSIGNAL)==ssize_t(b.size()),"peer short send");}
 PJ recv(){for(;;){g_.guard();pollfd p{fd_,POLLIN,0};int n=::poll(&p,1,100);pilot_need(n>=0,"peer poll");if(!n)continue;char b[65536];auto r=::recv(fd_,b,sizeof b,0);pilot_need(r>0&&r<ssize_t(sizeof b),"peer closed/truncated");return PJ::parse(std::string(b,r));}}
 std::string ready(const std::string&id){uint64_t random=0;pilot_need(::getrandom(&random,sizeof random,0)==sizeof random,"nonce");std::string nonce=std::to_string(random);send({{"event","READY"},{"episode",id},{"nonce",nonce}});auto a=recv();pilot_need(a.at("event")=="GO"&&a.at("episode")==id&&a.at("nonce")==nonce,"out of order GO");return nonce;}
 bool audit(const std::string&id,const std::string&nonce,const std::string&path){send({{"event","AUDIT_READY"},{"episode",id},{"nonce",nonce},{"relative_path",path}});auto a=recv();pilot_need(a.at("event")=="COMMIT"&&a.at("episode")==id&&a.at("nonce")==nonce,"episode gate rejected");auto cert=g_.root()+"/certificates/"+id+".json";pilot_need(hashfile(cert)==a.at("certificate_sha256"),"certificate image differs");auto j=PJ::parse(textfile(cert));pilot_need(j.at("status")=="PASS"&&j.at("episode")==id&&j.at("nonce")==nonce&&j.at("job_sha256")==g_.job().at("job_payload_sha256"),"certificate binding differs");g_.passed(id,a.at("certificate_sha256"));return !a.value("stop",false);}
};
}
