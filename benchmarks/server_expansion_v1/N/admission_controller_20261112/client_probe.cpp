// SYNTHETIC std-only interoperability probe. No native/backend/model libraries.
#include "native_client.hpp"
#include <iostream>
using namespace hs::n1chain;
int main(int argc,char**argv){try{
 require(argc==13&&std::string(argv[1])=="--cpu-only-probe","explicit bounded CPU-only probe arguments required");
 const std::string file=argv[12];struct stat st{};checked(::stat(file.c_str(),&st),"CPU request list");require(S_ISREG(st.st_mode)&&st.st_size>0&&st.st_size<=65536,"bounded CPU request list");
 std::ifstream input(file);std::vector<std::string>requests;std::set<std::string>unique;std::string id;while(std::getline(input,id)){identifier(id);require(unique.insert(id).second,"duplicate CPU request ID");requests.push_back(id);}require(input.eof()&&!requests.empty()&&requests.size()<=18,"finite exact CPU request set");
 const auto pid=ipc::amount(argv[8]);require(pid>0&&pid<=uint64_t(std::numeric_limits<pid_t>::max()),"controller PID range");
 std::cout<<"CPU_ONLY_PROBE_READY\n"<<std::flush;char permit=0;require(::read(STDIN_FILENO,&permit,1)==1&&permit=='1',"parent must register this exact PID before probe release");
 ControlledNativeClient client(argv[2],argv[3],argv[4],argv[5],1000,ControllerPeer{pid_t(pid),argv[9],argv[10]},argv[6],argv[7]);
 // These are mock accounting events only. This ELF has no backend/model API.
 client.before_backend_init(argv[11]);client.before_model_load(argv[11]);client.before_context(argv[11]);client.before_placement(argv[11]);
 auto root=absolute_dir(argv[7]);auto io=controller_io(client);
 for(const auto&request:requests){client.before_request(request);client.before_decode(request,1);client.before_mutation(request,"CPU_ONLY_PROBE_RECEIPT");const auto name=Sha256::of(request).substr(0,32)+".json";write_once_file(root.n,name,"{\"CPU_mock_only\":true}\n",io);checked(io.sync(root.n),"CPU probe receipt directory");client.finish_request(request,"COMPLETED");}
 client.close_worker();std::cout<<"{\"status\":\"CPU_ONLY_INTEROP_PROBE_PASS\",\"mock_requests\":"<<requests.size()<<",\"actual_backend_model_context_placement_forward_calls\":0,\"native_authority\":false}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"CPU_ONLY_INTEROP_PROBE_STOP "<<e.what()<<'\n';return 71;}}
