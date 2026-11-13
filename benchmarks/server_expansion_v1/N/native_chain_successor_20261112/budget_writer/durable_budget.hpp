#pragma once
// Durable CPU-MOCK coordinator. It is NOT a native admission implementation.
#include "posix.hpp"
#include "sha256.hpp"
#include <cmath>
#include <iomanip>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <sys/file.h>
#include <vector>
namespace hs::n1chain {
struct MockBudgetConfig {
 std::string run_id,source_sha256;
 double deadline_epoch=0;
 std::map<std::string,uint64_t> limits,request_rows;
 std::string canonical()const{
  identifier(run_id);require(source_sha256.size()==64,"source digest required");for(char c:source_sha256)require((c>='0'&&c<='9')||(c>='a'&&c<='f'),"source digest syntax");
  require(std::isfinite(deadline_epoch)&&deadline_epoch>0,"finite deadline required");
  const std::set<std::string> required{"requests","rows","backend_inits","models","contexts","placements"};
  std::set<std::string> keys;for(const auto&x:limits)keys.insert(x.first);require(keys==required,"all explicit mock limits required");
  require(!request_rows.empty(),"finite request-ID map required");
  std::ostringstream o;o<<"CPU_MOCK_ONLY\n"<<hex(run_id)<<'\n'<<source_sha256<<'\n'<<std::setprecision(17)<<deadline_epoch<<'\n';
  for(const auto&x:limits){o<<x.first<<'\t'<<x.second<<'\n';}
  for(const auto&x:request_rows){identifier(x.first);o<<hex(x.first)<<'\t'<<x.second<<'\n';}return o.str();
 }
};
struct MockBudgetState {
 std::map<std::string,uint64_t> counts{{"requests",0},{"rows",0},{"backend_inits",0},{"models",0},{"contexts",0},{"placements",0}},request_rows;
 std::set<std::string> deployments,finished;
 std::string active;bool header=false,sealed=false;
};
class DurableMockBudget final:public BudgetHooks {
 MockBudgetConfig cfg_;IO io_;FD dir_,lock_;MockBudgetState s_;std::string fingerprint_,chain_;uint64_t seq_=0,journal_bytes_=0;double mono_deadline_=0;bool poisoned_=false,closed_=false;
 static constexpr uint64_t journal_limit_=512ull*1024*1024;
 static uint64_t add(uint64_t a,uint64_t b){require(b<=std::numeric_limits<uint64_t>::max()-a,"counter overflow");return a+b;}
 static uint64_t number(const std::string&t){require(!t.empty()&&t.size()<=20,"invalid event amount");uint64_t n=0;for(char c:t){require(c>='0'&&c<='9',"invalid event amount");require(n<=(std::numeric_limits<uint64_t>::max()-uint64_t(c-'0'))/10,"event amount overflow");n=n*10+uint64_t(c-'0');}return n;}
 void apply(MockBudgetState&st,const std::string&kind,const std::string&id,uint64_t n,const std::string&detail)const{
  if(!st.header){require(kind=="header"&&id==cfg_.run_id&&n==0&&detail==fingerprint_,"journal header/manifest mismatch");st.header=true;return;}
  require(!st.sealed,"event after sealed ledger");
  if(kind=="request"){
   require(n==1&&st.active.empty()&&cfg_.request_rows.count(id)&&!st.request_rows.count(id),"duplicate/unplanned/in-flight request");st.active=id;st.request_rows[id]=0;st.counts["requests"]=add(st.counts["requests"],1);
  }else if(kind=="rows"){
   require(n>0&&n<=4096&&st.active==id,"rows need active bounded request");st.request_rows[id]=add(st.request_rows.at(id),n);require(st.request_rows[id]<=cfg_.request_rows.at(id),"per-request row ceiling");st.counts["rows"]=add(st.counts["rows"],n);
  }else if(kind=="mutation"){
   require(n==0&&st.active==id&&!detail.empty(),"mutation needs active request identity");
  }else if(kind=="finish"){
   require(n==0&&st.active==id&&(detail=="COMPLETED"||detail=="FAILED"||detail=="REJECTED"),"request terminal status required");st.finished.insert(id);st.active.clear();
  }else if(kind=="verify-placement"){
   require(n==0&&st.deployments.count("placement:"+id),"pre-exec placement reservation absent");
  }else if(kind=="seal"){
   require(n==0&&id==cfg_.run_id&&st.active.empty(),"cannot seal in-flight request");st.sealed=true;
  }else{
   const std::map<std::string,std::string> k{{"backend","backend_inits"},{"model","models"},{"context","contexts"},{"placement","placements"}};
   auto it=k.find(kind);require(it!=k.end()&&n==1&&!id.empty()&&st.deployments.insert(kind+":"+id).second,"invalid/duplicate deployment reservation");st.counts[it->second]=add(st.counts[it->second],1);
  }
  for(const auto&x:st.counts)require(x.second<=cfg_.limits.at(x.first),"aggregate budget ceiling");
 }
 void ready()const{require(!closed_&&!poisoned_&&!s_.sealed,"closed/poisoned/sealed mock coordinator");require(io_.wall()<cfg_.deadline_epoch&&io_.mono()<mono_deadline_,"fixed deadline exceeded");}
 void record(const std::string&kind,const std::string&id,uint64_t amount,const std::string&detail=""){
  try{
  ready();identifier(id);auto next=s_;apply(next,kind,id,amount,detail);
  const auto prefix=std::to_string(seq_)+"\t"+kind+"\t"+hex(id)+"\t"+std::to_string(amount)+"\t"+hex(detail)+"\t"+chain_;
  const auto digest=Sha256::of(prefix),line=prefix+"\t"+digest+"\n";
  require(line.size()<=65536&&line.size()<=journal_limit_-journal_bytes_,"bounded journal bytes exhausted before reservation");
  try{
   write_once_file(dir_.n,"UNCERTAIN","uncommitted reservation\n",io_);checked(io_.sync(dir_.n),"sync uncertainty marker");
   FD f(::openat(dir_.n,"ledger.tsv",O_WRONLY|O_APPEND|O_CREAT|O_NOFOLLOW,0600));checked(f.n,"open journal");
   require(io_.write(f.n,line.data(),line.size())==static_cast<ssize_t>(line.size()),"short journal write; no retry");checked(io_.sync(f.n),"sync journal");checked(io_.sync(dir_.n),"sync journal directory");
   checked(::unlinkat(dir_.n,"UNCERTAIN",0),"remove committed transaction marker");checked(io_.sync(dir_.n),"sync marker removal");
   s_=std::move(next);chain_=digest;seq_++;journal_bytes_+=line.size();
  }catch(...){poison("durable reservation failure");throw;}
  }catch(...){poison("reservation rejection or uncertain transaction; no continuation");throw;}
 }
 void deployment(const std::string&kind,const std::string&id){record(kind,id,1);}
 public:
 DurableMockBudget(const std::string&fresh_directory,MockBudgetConfig config,IO io={}):cfg_(std::move(config)),io_(std::move(io)){
  const auto canonical=cfg_.canonical();fingerprint_=Sha256::of(canonical);chain_=fingerprint_;
  const auto now=io_.wall();require(std::isfinite(now)&&now<cfg_.deadline_epoch,"expired mock proposal");mono_deadline_=io_.mono()+cfg_.deadline_epoch-now;
  require(!fresh_directory.empty()&&fresh_directory[0]=='/',"absolute fresh mock ledger required");
  const auto split=fresh_directory.find_last_of('/');const auto leaf=fresh_directory.substr(split+1);filename(leaf);auto parent=absolute_dir(split?fresh_directory.substr(0,split):"/");
  checked(::mkdirat(parent.n,leaf.c_str(),0700),"existing STATE/directory forbids reentry; inspect only");dir_=absolute_dir(fresh_directory);
  try{
   lock_=FD(::openat(dir_.n,"LOCK",O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW,0600));checked(lock_.n,"create exclusive lock");checked(::flock(lock_.n,LOCK_EX|LOCK_NB),"coordinator lock");
   write_once_file(dir_.n,"STATE","CPU_MOCK_ACTIVE_NO_NATIVE_AUTHORITY\n",io_);write_once_file(dir_.n,"MANIFEST",canonical,io_);checked(io_.sync(dir_.n),"sync initial STATE");checked(io_.sync(parent.n),"sync ledger directory creation");
   record("header",cfg_.run_id,0,fingerprint_);
  }catch(...){poison("constructor incomplete");throw;}
 }
 ~DurableMockBudget()override{if(!s_.sealed&&!closed_)poison("unsealed coordinator destruction");}
 DurableMockBudget(const DurableMockBudget&)=delete;DurableMockBudget&operator=(const DurableMockBudget&)=delete;
 void before_backend_init(const std::string&id)override{deployment("backend",id);}
 void before_model_load(const std::string&id)override{deployment("model",id);}
 void before_context(const std::string&id)override{deployment("context",id);}
 void before_placement(const std::string&id)override{deployment("placement",id);}
 void verify_pre_reserved_placement(const std::string&id){record("verify-placement",id,0);}
 void before_request(const std::string&id)override{record("request",id,1);}
 void before_decode(const std::string&id,std::size_t rows)override{record("rows",id,rows);}
 void before_mutation(const std::string&id,const std::string&action)override{identifier(action);record("mutation",id,0,action);}
 void finish_request(const std::string&id,const std::string&status)override{record("finish",id,0,status);if(status!="COMPLETED")poison("failed/rejected request is terminal");}
 void seal_success(){record("seal",cfg_.run_id,0);try{write_once_file(dir_.n,"SEALED","CPU_MOCK_FINISHED_INSPECTION_ONLY\n",io_);checked(io_.sync(dir_.n),"sync sealed marker");closed_=true;}catch(...){poison("seal I/O failure");throw;}}
 void poison(const std::string&reason)noexcept override{
  poisoned_=true;if(dir_.n<0)return;
  const auto fd=::openat(dir_.n,"POISONED",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);
  if(fd>=0){const auto n=::write(fd,reason.data(),reason.size());(void)n;const auto a=::fsync(fd);(void)a;::close(fd);const auto b=::fsync(dir_.n);(void)b;}
 }
 const MockBudgetState& state()const{return s_;}
 const std::string& fingerprint()const{return fingerprint_;}
 const std::string& run_id()const{return cfg_.run_id;}
 static constexpr uint64_t journal_limit_bytes(){return journal_limit_;}
 bool poisoned()const{return poisoned_;}
 struct Inspection{MockBudgetState state;std::string status;bool execution_authorized=false;};
 static Inspection inspect(const std::string&directory,const MockBudgetConfig&cfg){
  auto d=absolute_dir(directory);FD lock(::openat(d.n,"LOCK",O_RDWR|O_NOFOLLOW));checked(lock.n,"inspect existing lock");checked(::flock(lock.n,LOCK_EX|LOCK_NB),"ledger still held by another process");
  const auto canonical=cfg.canonical();require(read_at(d.n,"MANIFEST")==canonical,"immutable manifest identity mismatch");
  // A parser-only object cannot be constructed without creating STATE, so use
  // the same state transition validator through a private read-only instance.
  DurableMockBudget parser(cfg,ReadOnlyTag{});std::string line;uint64_t seq=0;std::string chain=Sha256::of(canonical);
  auto replay_line=[&](){std::vector<std::string>f;std::size_t p=0;for(;;){auto n=line.find('\t',p);if(n==std::string::npos){f.push_back(line.substr(p));break;}f.push_back(line.substr(p,n-p));p=n+1;}
   require(f.size()==7&&number(f[0])==seq&&f[5]==chain,"journal sequence/hash chain conflict");const auto at=line.find_last_of('\t');require(Sha256::of(line.substr(0,at))==f[6],"journal checksum conflict");parser.apply(parser.s_,f[1],unhex(f[2]),number(f[3]),unhex(f[4]));chain=f[6];seq++;
  };
  FD journal(::openat(d.n,"ledger.tsv",O_RDONLY|O_NOFOLLOW));checked(journal.n,"open journal for bounded streaming inspection");struct stat st{};checked(::fstat(journal.n,&st),"journal metadata");require(S_ISREG(st.st_mode)&&st.st_size>0&&uint64_t(st.st_size)<=journal_limit_,"journal total-byte bound");
  char chunk[8192];for(;;){auto n=::read(journal.n,chunk,sizeof chunk);if(n<0&&errno==EINTR)continue;require(n>=0,"journal read failure");if(n==0)break;
   for(ssize_t i=0;i<n;i++){if(chunk[i]=='\n'){require(!line.empty(),"empty journal record");replay_line();line.clear();}else{require(line.size()<65536,"journal line bound");line+=chunk[i];}}
  }
  require(line.empty()&&seq>0,"partial journal blocks reconciliation");
  const bool uncertain=exists_at(d.n,"UNCERTAIN")||exists_at(d.n,"POISONED")||!exists_at(d.n,"SEALED")||!parser.s_.sealed||!parser.s_.active.empty();
  return{parser.s_,uncertain?"UNCLEAN_OR_POISONED_INSPECTION_ONLY_NO_REENTRY":"SEALED_INSPECTION_ONLY_NO_REENTRY",false};
 }
 private:
 struct ReadOnlyTag{};
 DurableMockBudget(const MockBudgetConfig&cfg,ReadOnlyTag):cfg_(cfg),fingerprint_(Sha256::of(cfg.canonical())),closed_(true){}
};
}
