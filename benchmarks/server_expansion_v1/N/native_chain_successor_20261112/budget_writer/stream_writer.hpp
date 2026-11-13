#pragma once
// Synchronous host-byte transport only. No llama/GGML/CUDA dependency.
#include "posix.hpp"
#include "sha256.hpp"
#include <limits>
#include <set>
#include <sstream>
#include <vector>
namespace hs::n1chain {
struct CaptureIdentity{std::string run_id,operation_id,context_id,source_sha256,executable_sha256,writer_sha256;};
struct CaptureLimits{uint64_t max_bytes=0;std::size_t max_files=0,max_chunk_bytes=0;};
struct TensorDescriptor{std::string file,dtype,sha256;std::vector<uint64_t>shape;std::vector<std::string>axes;uint64_t bytes=0;bool canonical_numeric=false;};
inline std::string quoted(const std::string&s){std::string o="\"";for(unsigned char c:s){if(c=='"'||c=='\\'){o+='\\';o+=char(c);}else if(c<32){static const char*h="0123456789abcdef";o+="\\u00";o+=h[c>>4];o+=h[c&15];}else o+=char(c);}return o+'"';}
inline std::string descriptor_json(const TensorDescriptor&d){std::ostringstream o;o<<"{\"file\":"<<quoted(d.file)<<",\"dtype\":"<<quoted(d.dtype)<<",\"bytes\":"<<d.bytes<<",\"sha256\":"<<quoted(d.sha256)<<",\"canonical_numeric\":"<<(d.canonical_numeric?"true":"false")<<",\"shape\":[";for(std::size_t i=0;i<d.shape.size();i++){if(i)o<<',';o<<d.shape[i];}o<<"],\"axes\":[";for(std::size_t i=0;i<d.axes.size();i++){if(i)o<<',';o<<quoted(d.axes[i]);}o<<"]}";return o.str();}
class StreamCapture {
 std::string id_;CaptureIdentity identity_;CaptureLimits limits_;BudgetHooks&gate_;IO io_;FD root_,dir_,tensor_;
 std::set<std::string> names_;std::vector<TensorDescriptor> descriptors_;TensorDescriptor current_;Sha256 hash_;
 uint64_t bytes_=0,tensor_bytes_=0,expected_=0;std::size_t files_=0,scalar_=0;bool exact_=false,failed_=false,committed_=false;
 void ready(){require(!failed_&&!committed_,"capture failed/closed");}
 void count_file(){require(files_<limits_.max_files,"capture file-count ceiling");files_++;}
 void allowance(std::size_t n){require(n<=limits_.max_bytes-bytes_,"capture byte ceiling");}
 void fail(const std::string&why)noexcept{
  failed_=true;gate_.poison(why);if(dir_.n<0)return;
  const int f=::openat(dir_.n,"UNCERTAIN",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);
  if(f>=0){auto a=::write(f,why.data(),why.size());(void)a;auto b=::fsync(f);(void)b;::close(f);auto c=::fsync(dir_.n);(void)c;}
 }
 void file(const std::string&name,const std::string&raw){count_file();allowance(raw.size());write_once_file(dir_.n,name,raw,io_);bytes_+=raw.size();}
 void start(const std::string&name,const std::string&dtype,const std::vector<uint64_t>&shape,const std::vector<std::string>&axes,uint64_t expected,bool exact,std::size_t scalar){
  ready();require(tensor_.n<0,"previous tensor not finished");filename(name);require(names_.insert(name).second,"duplicate tensor");
  count_file();allowance(static_cast<std::size_t>(expected));
  tensor_=FD(::openat(dir_.n,(name+".bin").c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600));checked(tensor_.n,"create raw tensor");
  current_={id_+"/"+name+".bin",dtype,"",shape,axes,0,scalar!=0};hash_=Sha256{};tensor_bytes_=0;expected_=expected;exact_=exact;scalar_=scalar;
 }
 public:
 StreamCapture(const std::string&trusted_root,const std::string&capture_id,CaptureIdentity identity,CaptureLimits limits,BudgetHooks&gate,IO io={}):id_(capture_id),identity_(std::move(identity)),limits_(limits),gate_(gate),io_(std::move(io)){
  filename(id_);for(const auto&s:{identity_.run_id,identity_.operation_id,identity_.context_id})identifier(s);
  for(const auto&s:{identity_.source_sha256,identity_.executable_sha256,identity_.writer_sha256}){require(s.size()==64,"capture source/writer/executable digest");for(char c:s)require((c>='0'&&c<='9')||(c>='a'&&c<='f'),"capture digest syntax");}
  require(limits_.max_bytes>0&&limits_.max_files>=5&&limits_.max_chunk_bytes>0&&limits_.max_chunk_bytes<=32*1024*1024,"explicit finite capture profile required");
  gate_.before_mutation(identity_.operation_id,"capture_open"); // denial before any capture filesystem side effect
  try{root_=absolute_dir(trusted_root);checked(::mkdirat(root_.n,id_.c_str(),0700),"capture ID exists; no overwrite/reentry");
   dir_=FD(::openat(root_.n,id_.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW));checked(dir_.n,"open capture directory");
   file("CAPTURE_OPEN","uncommitted raw transport\n");checked(io_.sync(dir_.n),"sync capture open");checked(io_.sync(root_.n),"sync capture directory");}catch(...){fail("capture constructor I/O failure");throw;}
 }
 ~StreamCapture(){if(!committed_&&!failed_)fail("incomplete capture destruction");}
 StreamCapture(const StreamCapture&)=delete;StreamCapture&operator=(const StreamCapture&)=delete;
 void begin_tensor(const std::string&name,const std::string&dtype,const std::vector<uint64_t>&shape,const std::vector<std::string>&axes){
  try{ready();require((dtype=="F16LE"||dtype=="F32LE")&&!shape.empty()&&shape.size()==axes.size(),"numeric tensor dtype/coordinates");std::set<std::string>unique;for(const auto&a:axes){filename(a);require(unique.insert(a).second,"duplicate tensor axis");}
   uint64_t n=dtype=="F16LE"?2:4;for(auto dim:shape){require(dim==0||n<=std::numeric_limits<uint64_t>::max()/dim,"tensor shape overflow");n*=dim;}require(n<=limits_.max_bytes,"tensor exceeds capture profile");start(name,dtype,shape,axes,n,true,dtype=="F16LE"?2:4);
  }catch(...){fail("tensor begin failure");throw;}
 }
 void begin_blob(const std::string&name,uint64_t max_bytes){
  try{require(max_bytes<=limits_.max_bytes,"native blob ceiling");start(name,"OPAQUE_NATIVE_STATE",{}, {},max_bytes,false,0);}catch(...){fail("blob begin failure");throw;}
 }
 void append_host_chunk(const void*data,std::size_t n){
  try{ready();gate_.before_mutation(identity_.operation_id,"capture_chunk");require(tensor_.n>=0&&n<=limits_.max_chunk_bytes&&(data||n==0),"host chunk bound/pointer");require(n<=expected_-tensor_bytes_,"raw tensor exceeds exact shape/bound");allowance(n);
   const auto*p=static_cast<const unsigned char*>(data);
   if(scalar_){require(n%scalar_==0,"chunk splits a scalar");for(std::size_t i=0;i<n;i+=scalar_){uint32_t b=0;for(std::size_t j=0;j<scalar_;j++)b|=uint32_t(p[i+j])<<(j*8);require(scalar_==2?(b&0x7c00)!=0x7c00:(b&0x7f800000)!=0x7f800000,"nonfinite raw tensor value");}}
   std::size_t done=0;while(done<n){auto wrote=io_.write(tensor_.n,p+done,n-done);require(wrote>0&&static_cast<std::size_t>(wrote)<=n-done,"zero/invalid raw write");done+=static_cast<std::size_t>(wrote);}
   hash_.update(data,n);tensor_bytes_+=n;bytes_+=n;
  }catch(...){fail("raw stream write/shape/I/O failure");throw;}
 }
 TensorDescriptor finish_tensor(){
  try{ready();require(tensor_.n>=0&&(!exact_||tensor_bytes_==expected_),"raw tensor incomplete");checked(io_.sync(tensor_.n),"sync raw tensor");tensor_=FD{};current_.bytes=tensor_bytes_;current_.sha256=hash_.finish();if(!exact_){current_.shape={tensor_bytes_};current_.axes={"byte"};}descriptors_.push_back(current_);return current_;
  }catch(...){fail("tensor finish failure");throw;}
 }
 std::string commit_manifest(const std::string&snapshot_json){
  try{ready();require(tensor_.n<0&&!descriptors_.empty()&&!snapshot_json.empty(),"capture incomplete/no metadata");gate_.before_mutation(identity_.operation_id,"capture_commit");
   file("SNAPSHOT.json",snapshot_json);
   std::ostringstream o;o<<"{\"schema\":\"hs.N1chain.raw-transport.v1\",\"native_qualified\":false,\"run_id\":"<<quoted(identity_.run_id)<<",\"operation_id\":"<<quoted(identity_.operation_id)<<",\"context_id\":"<<quoted(identity_.context_id)<<",\"source_sha256\":"<<quoted(identity_.source_sha256)<<",\"executable_sha256\":"<<quoted(identity_.executable_sha256)<<",\"capture_writer_sha256\":"<<quoted(identity_.writer_sha256)<<",\"snapshot_sha256\":"<<quoted(Sha256::of(snapshot_json))<<",\"tensors\":[";
   for(std::size_t i=0;i<descriptors_.size();i++){if(i)o<<',';o<<descriptor_json(descriptors_[i]);}o<<"]}\n";
   file("TRANSPORT.pending",o.str());count_file();checked(::linkat(dir_.n,"TRANSPORT.pending",dir_.n,"COMPLETE.json",0),"publish transport receipt");checked(io_.sync(dir_.n),"sync transport publication");
   checked(::unlinkat(dir_.n,"CAPTURE_OPEN",0),"remove capture-open marker");checked(io_.sync(dir_.n),"sync closed transport");committed_=true;return Sha256::of(snapshot_json);
  }catch(...){fail("capture commit I/O failure");throw;}
 }
 bool committed()const{return committed_;}bool failed()const{return failed_;}
 const std::vector<TensorDescriptor>&descriptors()const{return descriptors_;}
};
}
