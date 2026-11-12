// Native-linked CPU-preparation artifact. DO NOT execute (including --help).
// All exported worker/factory entries require a concrete final deny gate.
#include "runtime.hpp"
#include "producer_facade.hpp"
#include "active_kv.hpp"
#include "raw_checks.hpp"
#include "../budget_writer/stream_writer.hpp"
#include "../budget_writer/accounting_ipc.hpp"
#include "native_client.hpp"
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <memory>
#include <map>
namespace hs::n1chain {
using J=nlohmann::ordered_json;
static J load_json(const std::string&p){std::ifstream f(p);require(bool(f),"job/receipt input");J v;f>>v;require(bool(f),"job JSON");return v;}
static std::string own_executable_hash(){std::ifstream f("/proc/self/exe",std::ios::binary);require(bool(f),"own executable identity");Sha256 h;std::vector<char>b(1024*1024);while(f){f.read(b.data(),b.size());h.update(b.data(),size_t(f.gcount()));}require(f.eof(),"own executable hash read");return h.finish();}
static J desc(const TensorDescriptor&d){return J::parse(descriptor_json(d));}
static J kv_meta(const KVMeta&m){
 J cells=J::array(),tensors=J::array();for(auto&x:m.cells_physical_order)cells.push_back({{"physical",x.physical},{"position",x.position},{"sequence",x.sequence}});
 for(auto&x:m.tensors)tensors.push_back({{"kind",x.kind},{"layer",x.layer},{"name",x.tensor_name},{"storage",x.storage_name},{"ne",x.dimensions},{"nb",x.byte_strides},{"physical_read_bytes",x.physical_read_bytes},{"active_bytes",x.canonical_active_bytes}});
 return{{"format",m.format},{"head",m.head},{"capacity",m.capacity},{"v_trans",m.v_trans},{"serialized_v_trans_present",m.serialized_v_trans_present},{"cell_map",cells},{"physical_by_position",m.physical_by_position},{"tensors",tensors},{"scalar_metadata_bytes",m.scalar_metadata_bytes},{"serialized_memory_logical_bytes",m.serialized_memory_bytes},{"opaque_sequence_prefix_included",false},{"physical_read_bytes",m.physical_read_bytes},{"canonical_active_bytes",m.canonical_active_bytes}};
}
static Tokens token_json(const J&j){require(j.is_array(),"dense token JSON array");Tokens out;for(auto&x:j){require(x.is_number_integer(),"integer model token");const auto n=x.get<int64_t>();require(n>=0&&n<151936,"bound model token");out.push_back(int32_t(n));}return out;}
static std::string safe_capture_id(const std::string&op,const std::string&phase){return Sha256::of(op+"/"+phase).substr(0,24)+"-"+phase;}
struct WorkerCapture {
 NativeCore&core;ProductionGate&gate;BudgetHooks&account;const J&job;
 std::string previous_terminal,previous_operation;
 std::map<std::string,J>snapshots;
 std::map<std::string,J>descriptors;
 std::vector<J>capture_receipts;
 uint64_t ordinal=0,mutation_begin=0;
 J before_event=J::object(),ownership_origin=J::object();
 J record(const std::string&key,const J&value,const std::string&charged,size_t max_bytes=65536){
  gate.before_mutation(charged,"WRITE_NATIVE_RECEIPT");account.before_mutation(charged,"WRITE_NATIVE_RECEIPT");
  const auto file=Sha256::of(key).substr(0,32)+".json",raw=value.dump()+"\n";require(max_bytes<=1024*1024&&raw.size()<=max_bytes,"bounded native receipt metadata exceeded; reject without truncation");auto root=absolute_dir(job.at("capture_root"));auto io=controller_io(account);
  try{write_once_file(root.n,file,raw,io);checked(io.sync(root.n),"native receipt directory sync");}
  catch(...){account.poison("native receipt short/uncertain write");throw;}
  return{{"file",file},{"sha256",Sha256::of(raw)}};
 }
 J owned_event(const std::string&phase,const std::string&next,const std::vector<float>&v,const std::string&charged){
  require(!previous_operation.empty()&&v.size()==151936,"owned source terminal row absent");
  const auto source=snapshots.at(previous_operation+"/TERMINAL"),source_desc=descriptors.at(previous_operation+"/TERMINAL");
  const auto row=source.at("requested_vector_positions").size()-1;
  const auto own=source.at("owned_vector_ids").at(row);
  const auto capture=safe_capture_id(previous_operation+"/"+next,phase);
  CaptureIdentity ci{job.at("run_id"),charged,core.context_id(),job.at("source_sha256"),job.at("executable_sha256"),job.at("writer_sha256")};
  StreamCapture writer(job.at("capture_root"),capture,ci,{2*1024*1024,8,1024*1024},account,controller_io(account));
  writer.begin_tensor("owned","F32LE",{1,151936},{"requested_row","vocabulary"});writer.append_host_chunk(v.data(),v.size()*sizeof(float));const auto tensor=writer.finish_tensor();
  J e={{"schema","hs.N1a.owned-vector-event.v1"},{"phase",phase},{"run_id",job.at("run_id")},{"context_id",core.context_id()},
   {"source_operation_id",previous_operation},{"next_operation_id",next},{"source_snapshot_sha256",source_desc.at("sha256")},
   {"source_requested_row_index",row},{"source_vector_position",source.at("requested_vector_positions").at(row)},
   {"ownership_id",own},{"caller_owned",true},{"capture_writer_sha256",job.at("writer_sha256")},{"event_ordinal",++ordinal},{"tensor",desc(tensor)}};
  const auto digest=writer.commit_manifest(e.dump()+"\n");
  if(phase=="BEFORE_NEXT_MUTATION")ownership_origin={{"snapshot",source_desc},{"requested_row_index",row},{"vector_position",source.at("requested_vector_positions").at(row)},{"ownership_id",own},{"next_operation_id",next}};
  return{{"file",capture+"/SNAPSHOT.json"},{"sha256",digest}};
 }
 void before_next(const std::string&next,const std::vector<float>&v){
  if(previous_operation.empty())return;
  // Old request is still active until Session.begin_lazy closes it.
  before_event=owned_event("BEFORE_NEXT_MUTATION",next,v,previous_operation);mutation_begin=++ordinal;
 }
 void after_next(const std::string&next,const std::vector<float>&v){
  if(previous_operation.empty())return;const auto end=++ordinal;const auto work=J::parse(core.actual_work_json());uint64_t rows=0;for(auto&w:work)rows+=w.contains("rows")?w.at("rows").get<uint64_t>():w.at("width").get<uint64_t>();
  require(!work.empty()&&rows>0&&rows<=4096,"bounded actual native mutation work receipt");
  J m={{"schema","hs.N1a.mutation-receipt.v1"},{"run_id",job.at("run_id")},{"context_id",core.context_id()},{"operation_id",next},{"source_operation_id",previous_operation},
   {"begin_event_ordinal",mutation_begin},{"end_event_ordinal",end},{"actual_decode_calls",work.size()},{"actual_model_rows",rows},{"status","COMPLETE"}};
  auto mutation=record(next+"/MUTATION",m,next),after=owned_event("AFTER_NEXT_MUTATION",next,v,next);
  record(next+"/OWNERSHIP_CHECK",{{"schema","hs.N1chain.owned-required-binding.v1"},{"scope","OWNED_VECTOR_STABILITY"},{"origin",ownership_origin},{"before_event",before_event},{"after_event",after},{"mutation_receipt",mutation}},next);
 }
 // This entry writes canonical active bytes, not opaque original sequence.bin.
 void checkpoint(const char*phase,const State&s){
  const std::string name(phase),id=safe_capture_id(s.request_id,name);
  gate.before_mutation(s.request_id,"CAPTURE_"+name);
  const auto identity=job.at("identity");
  CaptureIdentity transport{job.at("run_id"),s.request_id,core.context_id(),job.at("source_sha256"),job.at("executable_sha256"),job.at("writer_sha256")};
  // One raw K, raw V and requested-vector tensor. Control/reset captures use
  // the same finite envelope; the complete disk proposal is recomputed outside.
  StreamCapture writer(job.at("capture_root"),id,transport,{700000000,12,1024*1024},account,controller_io(account));
  const uint64_t head=s.materialized.size();std::map<std::string,TensorDescriptor>td;
  std::string open="K";int next_layer=0;
  writer.begin_tensor("active_k","F16LE",{36,8,head,128},{"layer","kv_head","position","dimension"});
  auto feed=[&](const std::string&kind,int layer,const uint8_t*p,size_t n){
   require(kind=="K"||kind=="V","native KV kind");
   if(kind!=open){require(open=="K"&&kind=="V"&&next_layer==36,"native KV layer order");td["active_k"]=writer.finish_tensor();open="V";next_layer=0;writer.begin_tensor("active_v","F16LE",{36,8,head,128},{"layer","kv_head","position","dimension"});}
   require(layer==next_layer++,"missing/reordered native KV layer");
   for(size_t off=0;off<n;off+=1024*1024)writer.append_host_chunk(p+off,std::min<size_t>(1024*1024,n-off));
  };
  auto actual=capture_active_kv(core.existing_context(),gate,account,s.request_id,uint32_t(head),feed);
  if(!head){td["active_k"]=writer.finish_tensor();writer.begin_tensor("active_v","F16LE",{36,8,0,128},{"layer","kv_head","position","dimension"});}
  else require(open=="V"&&next_layer==36,"incomplete actual active KV");
  td["active_v"]=writer.finish_tensor();
  std::vector<size_t>positions;std::vector<std::vector<float>>vectors;
  if(name=="TERMINAL"){vectors=s.requested_vectors;for(size_t i=0;i<vectors.size();++i)positions.push_back(s.canonical.size()-1+i);}
  else if(s.frontier_valid){vectors.push_back(s.frontier);positions.push_back(head-1);}
  writer.begin_tensor("vectors","F32LE",{vectors.size(),151936},{"requested_row","vocabulary"});
  for(auto&v:vectors){require(v.size()==151936,"full vocabulary output capture");writer.append_host_chunk(v.data(),v.size()*sizeof(float));}
  td["vectors"]=writer.finish_tensor();
  J tensors=J::object();for(auto&x:td)tensors[x.first]=desc(x.second);
  const bool cold=job.at("role")=="COLD_CANONICAL_ORACLE",scripted=job.at("operation_caps").at(s.request_id)==1;
  J owned=J::array();for(auto p:positions)owned.push_back(Sha256::of(s.request_id+"/owned/"+std::to_string(p)));
  J snapshot={{"schema","hs.N1a.raw-state.v1"},{"phase",name},{"path_kind",cold?"COLD_ORACLE":"RESIDENT"},
   {"cohort",scripted?"SCRIPTED_CONTROL":"NATURAL"},{"execution_mode",scripted?(cold?"SCRIPTED_CONTROL_ORACLE":"SCRIPTED_STATE_CONTROL"):(cold?"CANONICAL_INPUT_ORACLE_REPLAY":"FREE_SEQUENTIAL")},
   {"generation_cap",job.at("operation_caps").at(s.request_id)},{"owned_vector_ids",owned},{"event_ordinal",++ordinal},
   {"run_id",job.at("run_id")},{"operation_id",s.request_id},{"context_id",core.context_id()},
   {"identity",identity},{"provenance",{{"executable_sha256",job.at("executable_sha256")},{"capture_writer_sha256",job.at("writer_sha256")}}},
   {"canonical_ids",s.canonical},{"materialized_ids",s.materialized},{"logical_ids",s.logical},{"generated_ids",s.generated},
   {"head",head},{"pending",s.pending?J{{"id",*s.pending},{"position",head}}:J(nullptr)},
   {"frontier",{{"valid",s.frontier_valid},{"owned",s.frontier_owned},{"position",s.frontier_valid?J(head-1):J(nullptr)}}},
   {"requested_vector_positions",positions},{"tensors",tensors},{"actual_KV",kv_meta(actual)},
   {"actual_native_work",J::parse(core.actual_work_json())}};
  if(name=="TERMINAL"){snapshot["generation_cap"]=job.at("operation_caps").at(s.request_id);snapshot["stop_reason"]=s.stop_reason;}
  bool retained_ok=true;
  if(name=="POST_RECONCILE"&&!cold&&!previous_operation.empty()){
   const auto&old=snapshots.at(previous_operation+"/TERMINAL");J raw_checks=J::object();
   for(const auto&kind:{"active_k","active_v"}){
    auto result=compare_retained_prefix(job.at("capture_root"),old.at("tensors").at(kind).at("file"),td.at(kind).file,old.at("head"),head);
    retained_ok=retained_ok&&result.pass;raw_checks[kind]={{"pass",result.pass},{"actual_bytes_compared",result.bytes_compared},{"layer",result.layer},{"kv_head",result.kv_head},{"position",result.position},{"dimension",result.dimension},{"reason",result.reason}};
   }snapshot["retained_prefix_full_raw_comparison"]=raw_checks;
  }
  const auto raw=snapshot.dump()+"\n";require(raw.size()<=1024*1024,"snapshot metadata exceeds frozen1MiB envelope; no truncation");const auto digest=writer.commit_manifest(raw);
  snapshots[s.request_id+"/"+name]=snapshot;
  J sd={{"operation_id",s.request_id},{"phase",name},{"run_id",job.at("run_id")},{"file",id+"/SNAPSHOT.json"},{"sha256",digest},{"executable_sha256",job.at("executable_sha256")}};
  descriptors[s.request_id+"/"+name]=sd;capture_receipts.push_back(sd);
  if(name=="POST_RECONCILE"&&!cold&&!previous_operation.empty()){
   const auto&old=snapshots.at(previous_operation+"/TERMINAL");size_t lcp=0;const Tokens logical=token_json(old.at("logical_ids"));while(lcp<logical.size()&&lcp<s.canonical.size()&&logical[lcp]==s.canonical[lcp])++lcp;
   const auto oldhead=old.at("head").get<size_t>();size_t expect=std::min(lcp,oldhead);const bool replay=expect==s.canonical.size();if(replay)--expect;
   J fallback=nullptr;std::string mode=lcp==logical.size()&&expect==oldhead?"DIRECT_APPEND":"LCP_TRIM_REPLAY";if(replay)mode="LAST_TOKEN_REPLAY";
   if(head==0&&expect>0){const auto reason=job.at("operation_faults").at(s.request_id).get<std::string>();fallback=reason=="UNSUPPORTED_BEFORE_CALL"?"TRIM_CAPABILITY_UNSUPPORTED":"CALLER_INJECTED_TRIM_FAILURE_BEFORE_NATIVE_MUTATION";mode="COMMON_FULL_REBUILD";}
   const auto pending=old.at("pending");const auto disposition=pending.is_null()?"NONE":mode=="COMMON_FULL_REBUILD"?"DISCARD_OLD_PENDING_WITH_RESET":lcp>oldhead?"REPLAY_OLD_PENDING_ONCE_AT_CANONICAL_POSITION":"DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX";
   J rr={{"schema","hs.N1a.reconcile-receipt.v1"},{"run_id",job.at("run_id")},{"context_id",core.context_id()},{"source_operation_id",previous_operation},{"operation_id",s.request_id},
    {"previous_snapshot_sha256",descriptors.at(previous_operation+"/TERMINAL").at("sha256")},{"current_snapshot_sha256",digest},{"fallback_reason",fallback},{"mode",mode},{"actual_head_before",oldhead},{"actual_keep",head},{"actual_model_rows_before_append",0},{"old_frontier_invalidated",true},{"old_pending_id",pending.is_null()?J(nullptr):pending.at("id")},{"pending_disposition",disposition}};
   record(s.request_id+"/RECONCILE",rr,s.request_id);
  }
  require(retained_ok,"strict retained active-prefix byte difference; snapshot preserved; stop");
  if(name=="TERMINAL"){previous_terminal=id+"/SNAPSHOT.json";previous_operation=s.request_id;}
  if(name=="RESET"){previous_terminal.clear();previous_operation.clear();}
 }
};
// Typed callable for a future separately audited controller. No JSON/env flag
// can replace this build's concrete deny gate with a mock budget.
int prepare_native_worker(const J&job,ProductionGate&gate,BudgetHooks&account){
 gate.before_backend_init("worker-entry"); // before any model/producer/capture object
 require(job.at("executable_sha256").get<std::string>()==own_executable_hash(),"actual executable differs from frozen native job");
 const std::string role=job.at("role");const bool cold=role=="COLD_CANONICAL_ORACLE";
 require(role=="RESIDENT_R"||role=="REPEAT_RESIDENT_R"||cold||role=="STRONG_WHOLE_RECHUNK_LOOP4","known N1a role");
#if defined(HS_STRONG_LOOP4)
 require(role=="STRONG_WHOLE_RECHUNK_LOOP4","loop4 binary role mismatch");
#else
 require(role!="STRONG_WHOLE_RECHUNK_LOOP4","independent reference cannot load candidate core");
#endif
 RuntimeConfig cfg{job.at("run_id"),job.at("model_path"),job.at("identity").at("model_sha256"),job.at("placement_id"),job.at("gpu_uuid"),2};
 auto core=make_native_core(gate,account,cfg);
 std::cout<<"N1A_DEPLOYMENT_READY "<<J{{"context_id",core->context_id()},{"placement_id",cfg.placement_id},{"gpu_uuid",cfg.gpu_uuid},{"n_ctx",4096},{"model_requests",0},{"native_qualified",false}}.dump()<<'\n'<<std::flush;
 Session session(*core,account);WorkerCapture capture{*core,gate,account,job};
 auto checkpoint=[&](const char*p,const State&s){capture.checkpoint(p,s);};
 for(const auto&episode:job.at("episodes")){
  const bool scripted=episode.at("kind")=="SCRIPTED_RAW_TOKEN_CONTROL";
  std::unique_ptr<NativeProducer>producer;if(!scripted&&!cold)producer=std::make_unique<NativeProducer>(core->existing_model(),gate,account);
  Tokens emitted;std::string stop;size_t last_cap=128;
  for(size_t turn=0;turn<episode.at("operations").size();++turn){const auto&op=episode.at("operations").at(turn);const std::string request=op.at("id");const size_t cap=op.at("cap");
   gate.before_request(request); // typed permission before CPU producer entry
   if(turn)capture.before_next(request,session.state().frontier);
   const size_t cold_keep=cold?op.at("reference_retained_head").get<size_t>():0;
   if(op.contains("caller_fault")){require(scripted,"fault injection restricted to frozen scripted controls");core->set_control_fault(op.at("caller_fault"));}
   session.begin_lazy(request,[&]{
    Tokens q;if(scripted||cold)q=token_json(op.at("canonical_ids"));
    else{ProducerPrompt p;if(!turn){J messages=J::array({op.at("user")});p=producer->initial(messages.dump(),request);}else p=producer->advance(emitted,stop,last_cap,op.at("user").dump(),request);q=p.canonical_ids;
     // Preserve the actual producer chain before any decode. An oversized
     // complete receipt is a capture-admission failure, never a truncated
     // history, rewritten canonical input, or silently supplied R tape.
     capture.record(request+"/PRODUCER",{{"schema","hs.N1chain.actual-producer.v1"},{"operation_id",request},{"run_id",job.at("run_id")},{"context_id",core->context_id()},
      {"role",role},{"mode","ACTUAL_FREE_SEQUENTIAL_PRODUCER"},{"identity",job.at("identity")},{"source_sha256",job.at("source_sha256")},
      {"canonical_ids",q},{"prompt_utf8",p.prompt_utf8},{"history_json",p.history_json},{"runtime_parser_state_json",p.runtime_parser_state_json},
      {"wire_response_json",p.wire_response_json},{"parser_input_hex",p.parser_input_hex},{"previous_actual_generated_ids",emitted},
      {"previous_stop_reason",stop},{"previous_cap",turn?J(last_cap):J(nullptr)},{"next_user",op.at("user")},{"native_qualified",false}},request,1024*1024);
    }
    if(op.contains("expected_canonical_ids"))require(q==token_json(op.at("expected_canonical_ids")),"canonical producer differs from frozen reference; do not force R tape");return q;
   },cap,cold,cold_keep,checkpoint);
   session.append(checkpoint);if(turn)capture.after_next(request,session.previous_owned());const Tokens forced=scripted?token_json(op.at("forced_terminal_ids")):Tokens{};session.generate(forced,checkpoint);
   emitted=session.state().generated;stop=session.state().stop_reason;last_cap=cap;
  }
  const auto last=episode.at("operations").back().at("id").get<std::string>();session.reset(last,checkpoint);
 }
 return 0;
}
}
int main(int argc,char**argv){
 // Intentionally no --help/--self-test execution is used by preparation tools.
 // Real-linked ELF initialization itself is outside CPU-only test authority.
 try{hs::n1chain::ProductionGate gate;gate.before_backend_init("main-entry");
  hs::n1chain::require(argc==2,"native worker JOB.json; execution NOT ADMITTED");
  const auto job=hs::n1chain::load_json(argv[1]);
  hs::n1chain::ControlledNativeClient account(job.at("accounting_socket"),job.at("run_id"),job.at("accounting_manifest_sha256"),job.at("worker_id"),5000,hs::n1chain::ControllerPeer{job.at("controller_owner").at("pid").get<pid_t>(),job.at("controller_owner").at("start_ticks").get<std::string>(),job.at("controller_owner").at("boot_id").get<std::string>()},job.at("owner_lease_sha256"),job.at("capture_root"));
  const auto rc=hs::n1chain::prepare_native_worker(job,gate,account);account.close_worker();return rc;
 }catch(const std::exception&e){std::cerr<<"N1A_NATIVE_STOP "<<e.what()<<'\n';return 77;}
}
