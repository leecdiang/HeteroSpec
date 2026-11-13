// CPU-only executable: standard C++/POSIX headers only. No model/native link.
#include "durable_budget.hpp"
#include "stream_writer.hpp"
#include <filesystem>
#include <iostream>
#include <sys/wait.h>
using namespace hs::n1chain;
namespace fs=std::filesystem;
static unsigned checks=0;
static void check(bool b,const char*m){require(b,m);checks++;}
template<class F>static void blocked(F f){bool yes=false;try{f();}catch(const std::exception&){yes=true;}check(yes,"expected fail-closed exception");}
static MockBudgetConfig config(){MockBudgetConfig c;c.run_id="mock-only";c.source_sha256=std::string(64,'a');c.deadline_epoch=200;c.limits={{"requests",2},{"rows",5},{"backend_inits",1},{"models",1},{"contexts",1},{"placements",1}};c.request_rows={{"a",3},{"b",2},{"c",2}};return c;}
static IO clocked(){IO io;io.wall=[](){return 100.;};io.mono=[](){return 10.;};return io;}
static std::string target(int fd){char data[4096];const auto n=::readlink(("/proc/self/fd/"+std::to_string(fd)).c_str(),data,sizeof data);return n<0?"":std::string(data,static_cast<std::size_t>(n));}
static CaptureIdentity identity(){return{"mock-only","a","mock-context",std::string(64,'a'),std::string(64,'b'),std::string(64,'c')};}
static CaptureLimits limits(){return{100000,32,1024};}
int main(int argc,char**argv){try{
 require(argc==3&&std::string(argv[1])=="--cpu-mock-selftest","explicit CPU mock mode and fresh output directory required");
 const fs::path base=argv[2];require(base.is_absolute()&&fs::create_directory(base),"fresh absolute mock output required");
 check(Sha256::of("")=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","SHA empty");
 check(Sha256::of("abc")=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","SHA abc");
 check(Sha256::of(std::string(1000000,'a'))=="cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0","SHA million-a");
 {
  ProductionGate gate;unsigned native_calls=0;
  blocked([&]{gate.before_backend_init("x");native_calls++;});blocked([&]{gate.before_model_load("x");native_calls++;});blocked([&]{gate.before_context("x");native_calls++;});blocked([&]{gate.before_placement("x");native_calls++;});blocked([&]{gate.before_request("a");native_calls++;});blocked([&]{gate.before_decode("a",1);native_calls++;});blocked([&]{gate.before_mutation("a","trim");native_calls++;});
  fs::create_directory(base/"native-denied-writer");blocked([&]{StreamCapture w((base/"native-denied-writer").string(),"capture",identity(),limits(),gate);});check(!fs::exists(base/"native-denied-writer/capture"),"denied writer created files");check(native_calls==0,"native callback reached");
 }
 {
  const auto p=(base/"normal").string();{DurableMockBudget b(p,config(),clocked());b.before_backend_init("be");b.before_model_load("m");b.before_context("ctx");b.before_placement("p");b.before_request("a");b.before_decode("a",1);b.before_decode("a",2);b.before_mutation("a","reset");b.finish_request("a","COMPLETED");blocked([&]{DurableMockBudget::inspect(p,config());});b.seal_success();}
  auto r=DurableMockBudget::inspect(p,config());check(r.state.counts.at("rows")==3&&r.state.counts.at("contexts")==1,"durable totals");check(!r.execution_authorized&&r.status=="SEALED_INSPECTION_ONLY_NO_REENTRY","inspection grants no authority");blocked([&]{DurableMockBudget b(p,config(),clocked());});auto c=config();c.limits["rows"]=100;blocked([&]{DurableMockBudget::inspect(p,c);});
 }
 {
  const auto p=(base/"row-overrun").string();{DurableMockBudget b(p,config(),clocked());b.before_request("a");b.before_decode("a",3);blocked([&]{b.before_decode("a",1);});check(b.poisoned(),"partial-work reservation rejection did not poison");blocked([&]{b.before_request("b");});}
  auto r=DurableMockBudget::inspect(p,config());check(r.state.counts.at("rows")==3&&r.state.counts.at("requests")==1,"failed work refunded");check(!r.execution_authorized&&r.status.find("UNCLEAN")==0,"crash/poison resumed");
 }
 {
  DurableMockBudget b((base/"duplicate").string(),config(),clocked());b.before_request("a");b.finish_request("a","COMPLETED");blocked([&]{b.before_request("a");});blocked([&]{b.before_request("b");});
 }
 {
  DurableMockBudget b((base/"placement-cap").string(),config(),clocked());b.before_placement("p1");blocked([&]{b.before_placement("p2");});check(b.state().counts.at("placements")==1,"placement overrun charged as executed");
 }
 {
  double wall=100,mono=10;auto io=clocked();io.wall=[&]{return wall;};io.mono=[&]{return mono;};DurableMockBudget b((base/"deadline").string(),config(),io);wall=1;mono=111;blocked([&]{b.before_request("a");});
 }
 {
  const auto p=(base/"crash").string();auto pid=::fork();checked(pid,"fork CPU mock");if(pid==0){DurableMockBudget b(p,config(),clocked());b.before_request("a");b.before_decode("a",2);::_exit(0);}int status=0;checked(::waitpid(pid,&status,0),"wait CPU mock");check(WIFEXITED(status)&&WEXITSTATUS(status)==0,"mock crash child");auto r=DurableMockBudget::inspect(p,config());check(r.state.counts.at("rows")==2&&!r.state.active.empty(),"in-flight crash spend lost");check(r.status.find("UNCLEAN")==0&&!r.execution_authorized,"crash reentry permitted");blocked([&]{DurableMockBudget b(p,config(),clocked());});
 }
 {
  const auto p=(base/"journal-short-write").string();bool fault=false;auto io=clocked();io.write=[&](int f,const void*d,std::size_t n){return::write(f,d,fault&&target(f).find("ledger.tsv")!=std::string::npos?std::min<std::size_t>(3,n):n);};
  {DurableMockBudget b(p,config(),io);b.before_request("a");fault=true;blocked([&]{b.before_decode("a",1);});check(b.poisoned(),"short journal not poisoned");}
  check(fs::exists(fs::path(p)/"UNCERTAIN")&&fs::exists(fs::path(p)/"POISONED"),"uncertainty marker missing");blocked([&]{DurableMockBudget::inspect(p,config());});
 }
 {
  const auto p=(base/"journal-sync-failure").string();bool fault=false;auto io=clocked();io.sync=[&](int f){if(fault){errno=EIO;return-1;}return::fsync(f);};
  {DurableMockBudget b(p,config(),io);b.before_request("a");fault=true;blocked([&]{b.before_decode("a",1);});}
  auto r=DurableMockBudget::inspect(p,config());check(r.state.counts.at("requests")==1&&r.status.find("UNCLEAN")==0,"sync fault resumed/refunded");
 }
 {
  const auto p=(base/"writer-success").string();fs::create_directory(base/"payload-success");
  {DurableMockBudget b(p,config(),clocked());b.before_request("a");StreamCapture w((base/"payload-success").string(),"cap",identity(),limits(),b);w.begin_tensor("vectors","F32LE",{1,2},{"requested_row","vocabulary"});unsigned char raw[8]={0,0,128,63,0,0,0,128};w.append_host_chunk(raw,8);raw[2]=0;auto d=w.finish_tensor();check(d.bytes==8&&d.canonical_numeric,"numeric descriptor");w.begin_tensor("active_k","F16LE",{36,8,0,128},{"layer","kv_head","position","dimension"});auto empty=w.finish_tensor();check(empty.bytes==0,"empty reset capture");auto h=w.commit_manifest("{\"schema\":\"CPU_MOCK_SYNTHETIC_ONLY\"}\n");check(h.size()==64&&w.committed(),"transport commit");b.finish_request("a","COMPLETED");b.seal_success();}
  auto dir=absolute_dir((base/"payload-success/cap").string());const auto raw=read_at(dir.n,"vectors.bin");check(raw.size()==8&&static_cast<unsigned char>(raw[2])==128,"caller mutation changed owned bytes");check(read_at(dir.n,"COMPLETE.json").find("\"native_qualified\":false")!=std::string::npos,"transport fabricated qualification");check(!fs::exists(base/"payload-success/cap/CAPTURE_OPEN"),"open marker after successful close");
 }
 {
  fs::create_directory(base/"payload-partial");DurableMockBudget b((base/"writer-partial").string(),config(),clocked());b.before_request("a");b.before_decode("a",1);unsigned calls=0;auto io=clocked();io.write=[&](int f,const void*d,std::size_t n)->ssize_t{if(target(f).find(".bin")!=std::string::npos){if(calls++==0)return::write(f,d,std::min<std::size_t>(1,n));errno=EIO;return-1;}return::write(f,d,n);};
  StreamCapture w((base/"payload-partial").string(),"cap",identity(),limits(),b,io);w.begin_tensor("v","F32LE",{1},{"vocabulary"});unsigned char raw[4]={0,0,128,63};blocked([&]{w.append_host_chunk(raw,4);});check(w.failed()&&b.poisoned(),"writer failure did not close active work");check(fs::file_size(base/"payload-partial/cap/v.bin")==1&&!fs::exists(base/"payload-partial/cap/COMPLETE.json"),"partial data not preserved");check(b.state().counts.at("rows")==1,"writer failure refunded decode reservation");blocked([&]{b.before_request("b");});
 }
 {
  fs::create_directory(base/"payload-nan");DurableMockBudget b((base/"writer-nan").string(),config(),clocked());b.before_request("a");StreamCapture w((base/"payload-nan").string(),"cap",identity(),limits(),b);w.begin_tensor("v","F16LE",{1},{"dimension"});unsigned char raw[2]={0,124};blocked([&]{w.append_host_chunk(raw,2);});check(b.poisoned()&&fs::file_size(base/"payload-nan/cap/v.bin")==0,"nonfinite not rejected before write");
 }
 {
  fs::create_directory(base/"payload-opaque");DurableMockBudget b((base/"writer-opaque").string(),config(),clocked());b.before_request("a");StreamCapture w((base/"payload-opaque").string(),"cap",identity(),limits(),b);w.begin_blob("native_packet",64);unsigned char raw[3]={255,255,255};w.append_host_chunk(raw,3);auto d=w.finish_tensor();check(!d.canonical_numeric&&d.dtype=="OPAQUE_NATIVE_STATE"&&d.bytes==3,"opaque native state mislabeled canonical");w.commit_manifest("{\"schema\":\"CPU_MOCK_OPAQUE_NOT_NUMERICAL_QUALIFICATION\"}\n");b.finish_request("a","COMPLETED");b.seal_success();
 }
 std::cout<<"{\"status\":\"CPU_MOCK_TESTS_PASS\",\"checks\":"<<checks<<",\"model_creation\":0,\"backend_init\":0,\"native_contexts\":0,\"placement_actions\":0,\"forwards\":0,\"native_libraries_linked\":false,\"partial_mock_artifacts_preserved\":true}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"CPU_MOCK_TEST_FAILED: "<<e.what()<<'\n';return 1;}}
