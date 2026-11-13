#pragma once
#include "hooks.hpp"
#include <cerrno>
#include <chrono>
#include <cstring>
#include <fcntl.h>
#include <functional>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
namespace hs::n1chain {
inline void require(bool b,const std::string&m){if(!b)throw Blocked(m);}
inline void checked(int n,const std::string&m){if(n<0)throw Blocked(m+": "+std::strerror(errno));}
struct FD{int n=-1;FD()=default;explicit FD(int x):n(x){}FD(const FD&)=delete;FD&operator=(const FD&)=delete;FD(FD&&x)noexcept:n(x.n){x.n=-1;}FD&operator=(FD&&x)noexcept{if(this!=&x){if(n>=0)::close(n);n=x.n;x.n=-1;}return*this;}~FD(){if(n>=0)::close(n);}int release(){const int x=n;n=-1;return x;}};
struct IO {
 std::function<ssize_t(int,const void*,std::size_t)> write=[](int f,const void*p,std::size_t n){return::write(f,p,n);};
 std::function<int(int)> sync=[](int f){return::fsync(f);};
 std::function<double()> wall=[](){return std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();};
 std::function<double()> mono=[](){return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();};
};
inline bool exists_at(int fd,const char*name){struct stat s{};if(::fstatat(fd,name,&s,AT_SYMLINK_NOFOLLOW)==0)return true;require(errno==ENOENT,"cannot inspect marker");return false;}
inline FD absolute_dir(const std::string&p){require(!p.empty()&&p[0]=='/',"absolute trusted directory required");FD d(::open("/",O_RDONLY|O_DIRECTORY));checked(d.n,"open root");std::size_t a=1;while(a<p.size()){auto b=p.find('/',a);if(b==std::string::npos)b=p.size();const auto part=p.substr(a,b-a);require(!part.empty()&&part!="."&&part!="..","unsafe directory component");FD next(::openat(d.n,part.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW));checked(next.n,"open trusted directory");d=std::move(next);a=b+1;}return d;}
inline void identifier(const std::string&s){require(!s.empty()&&s.size()<=4096,"identifier length");for(unsigned char c:s)require(c>=32&&c<127&&c!='\t'&&c!='\n'&&c!='\r',"unsafe identifier");}
inline void filename(const std::string&s){require(!s.empty()&&s.size()<=200,"filename length");for(unsigned char c:s)require((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='-'||c=='.',"unsafe filename");require(s!="."&&s!="..","unsafe filename");}
inline std::string read_at(int d,const std::string&name){FD f(::openat(d,name.c_str(),O_RDONLY|O_NOFOLLOW));checked(f.n,"read file");struct stat s{};checked(::fstat(f.n,&s),"stat file");require(S_ISREG(s.st_mode)&&s.st_size>=0&&s.st_size<64*1024*1024,"journal/metadata file bound");std::string out(static_cast<std::size_t>(s.st_size),'\0');std::size_t off=0;while(off<out.size()){auto n=::read(f.n,out.data()+off,out.size()-off);require(n>0,"short metadata read");off+=static_cast<std::size_t>(n);}return out;}
inline void write_once_file(int dir,const std::string&name,const std::string&data,IO&io){FD f(::openat(dir,name.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600));checked(f.n,"create immutable file");require(io.write(f.n,data.data(),data.size())==static_cast<ssize_t>(data.size()),"short durable metadata write");checked(io.sync(f.n),"sync immutable file");}
inline std::string hex(const std::string&s){static const char*x="0123456789abcdef";std::string o;for(unsigned char c:s){o+=x[c>>4];o+=x[c&15];}return o;}
inline std::string unhex(const std::string&s){require(s.size()%2==0,"odd hex field");std::string o;for(std::size_t i=0;i<s.size();i+=2){auto n=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw Blocked("invalid hex field");};o+=static_cast<char>(n(s[i])*16+n(s[i+1]));}return o;}
}
