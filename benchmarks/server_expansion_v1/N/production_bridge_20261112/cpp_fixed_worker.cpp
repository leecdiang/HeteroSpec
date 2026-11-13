// Fixed std-only CPU worker. It has no native/model/backend library or API.
#include "bridge_job.hpp"
#include <iostream>
using namespace hs::n1chain;
int main(int argc,char**argv){try{
 require(argc==3,"fixed CPU worker requires exact job and SHA");BridgeJob job(argv[1],argv[2]);const auto&j=job.value;require(j.at("schema")=="hs.production-bridge.cpu-job.v1"&&j.at("mode")=="CPU_FIXED_WORKER","fixed CPU worker job only");
 const auto behavior=j.value("worker_behavior",std::string("normal"));require(behavior=="normal"||behavior=="hang"||behavior=="exit_nonzero"||behavior=="stdout_overflow"||behavior=="stderr_overflow"||behavior=="no_close"||behavior=="no_worker_hello","known fixed CPU fault only");if(behavior=="no_worker_hello")for(;;)::pause();
 BridgeClient client(bridge_path(j,"accounting_socket"),j.at("run_id"),bridge_digest(j,"manifest_sha256"),j.at("worker_id"),1000,job.controller(),bridge_digest(j,"lease_sha256"),bridge_path(j,"capture_root"),job.binding());
 const std::string deployment=j.at("deployment_id");client.before_backend_init(deployment);client.before_model_load(deployment);client.before_context(deployment);client.before_placement(deployment);
 if(behavior=="hang")for(;;)::pause();if(behavior=="exit_nonzero")return 19;
 if(behavior=="stdout_overflow"||behavior=="stderr_overflow"){char bytes[65536];std::memset(bytes,'x',sizeof bytes);for(;;)if(::write(behavior=="stdout_overflow"?STDOUT_FILENO:STDERR_FILENO,bytes,sizeof bytes)<0)return 23;}
 auto root=absolute_dir(bridge_path(j,"capture_root"));auto io=bridge_io(client);const auto requests=job.requests();
 for(const auto&id:requests){job.verify();client.before_request(id);client.before_decode(id,1);client.before_mutation(id,"FIXED_CPU_WORKER_METADATA");const auto file=Sha256::of(id).substr(0,32)+".json";write_once_file(root.n,file,"{\"CPU_mock_only\":true}\n",io);checked(io.sync(root.n),"fixed CPU metadata directory");client.finish_request(id,"COMPLETED");}
 if(behavior=="no_close")return 0;client.close_worker();std::cout<<"{\"status\":\"FIXED_CPU_WORKER_PASS\",\"mock_requests\":"<<requests.size()<<",\"actual_model_context_placement_forward_calls\":0}\n"<<std::flush;return 0;
 }catch(const std::exception&e){std::cerr<<"FIXED_CPU_WORKER_STOP "<<e.what()<<'\n';return 71;}}
