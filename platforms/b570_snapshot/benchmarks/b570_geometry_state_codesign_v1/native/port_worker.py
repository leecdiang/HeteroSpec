"""Derive the PR108 actor from the CAS-restored verified PR97 generic transaction."""
from pathlib import Path
import difflib
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'_host/pr97/native/worker.cpp';before=p.read_text(encoding='utf-8');t=before
def change(a,b):
 global t
 assert t.count(a)==1,(a[:100],t.count(a));t=t.replace(a,b)
change('using json=nlohmann::ordered_json;','''using json=nlohmann::ordered_json;
extern "C" __declspec(dllimport) void llama_b570_geometry_bind(llama_context *,int,int,int,uint32_t,int);
int consumer108=0,capacity108=4;std::string layout108;
json binding108=json::array();std::string request_dir108;
struct ProducerPlan {int ub;std::string role;};
''')
change('int rc=llama_decode(ctx,b);','''// Guard is independent of counters and observers. Draft plan belongs to its context.
  int phase108=phase=="PREFILL"?0:phase=="VERIFY"?1:phase=="ORDINARY"?2:phase=="PROPOSE"?3:4;
  if(phase108!=0&&ids.size()>(role=="TARGET"?2u:1u))throw std::runtime_error("PR108 caller width");
  if(role=="TARGET"&&capacity==1){if(phase=="VERIFY"||all)throw std::runtime_error("Shadow is ordinary only");}
  else llama_b570_geometry_bind(ctx,role=="TARGET"?0:1,phase108,phase108==0||role=="DRAFT"?0:consumer108,phase108==0?ub:(role=="DRAFT"?1:4),capacity);
  int rc=llama_decode(ctx,b);''')
# Capture physical work after guard: reservation has no forward counts, guard must precede snapshots.
change('void prefill(const std::vector<int>&ids){for(size_t i=0;i<ids.size();i+=512)decode(std::vector<int>(ids.begin()+i,ids.begin()+std::min(ids.size(),i+512)),int(i),false,"PREFILL");}', '''void prefill(const std::vector<int>&ids){
  ProducerPlan plan{ub,role};if(plan.ub!=128&&plan.ub!=512)throw std::runtime_error("Independent producer plan");
  // PR101 final-only policy, one complete caller, context-local internal partition.
  decode(ids,0,false,"PREFILL");
 }
 void handoff108(){
  if(role!="TARGET"||capacity==1)return;
  auto lo=llama_memory_seq_pos_min(llama_get_memory(ctx),0),hi=llama_memory_seq_pos_max(llama_get_memory(ctx),0);
  std::vector<uint8_t>a,b;
  if(capture){a.resize(llama_state_seq_get_size(ctx,0));a.resize(llama_state_seq_get_data(ctx,a.data(),a.size(),0));}
  llama_b570_geometry_bind(ctx,0,1,consumer108,4,capacity);
  if(lo!=llama_memory_seq_pos_min(llama_get_memory(ctx),0)||hi!=llama_memory_seq_pos_max(llama_get_memory(ctx),0))throw std::runtime_error("Phase positions changed");
  if(capture){b.resize(llama_state_seq_get_size(ctx,0));b.resize(llama_state_seq_get_data(ctx,b.data(),b.size(),0));if(a!=b)throw std::runtime_error("Phase sequence bytes changed");
   auto hash=sha96(a.data(),a.size());std::ofstream f(request_dir108+"/initial.seqkv.bin",std::ios::binary);f.write((const char*)a.data(),a.size());f.close();if(!f)throw std::runtime_error("KV evidence persistence");
   binding108.push_back({{"role",role},{"phase","HANDOFF"},{"kv_min",lo},{"kv_max",hi},{"serialized_sequence_sha256",hash},{"before_after_sequence_bytes_equal",true},{"cross_runtime_logical_KV_identity","NOT_CHECKED"}});
  }
 }
 void initial_logits108(){if(!capture)return;const float*l=llama_get_logits_ith(ctx,-1);auto bytes=sizeof(float)*llama_vocab_n_tokens(llama_model_get_vocab(model));
  std::ofstream f(request_dir108+"/"+role+".initial.logits.f32",std::ios::binary);f.write((const char*)l,bytes);f.close();if(!f)throw std::runtime_error("Initial logits persistence");
 }''')
change('{"all_outputs",all}', '{"all_outputs",all},{"requested_logit_positions",[&](){std::vector<int>p;for(size_t j=0;j<ids.size();++j)if(all||j+1==ids.size())p.push_back(pos+int(j));return p;}()},{"attention_layout",phase=="PREFILL"||role=="DRAFT"?"MQ":layout108},{"output_capacity",capacity},{"caller_rows",ids.size()}')
change('if(argc!=10)','if(argc!=12)')
change('int ub=std::stoi(argv[4]),k=std::stoi(argv[6]);','int ub=std::stoi(argv[4]),k=std::stoi(argv[6]);layout108=argv[10];capacity108=std::stoi(argv[11]);consumer108=layout108=="MQ"||layout108=="ordinary"?0:layout108=="PQ"?1:layout108=="QB"?2:-1;if(consumer108<0||(capacity108!=1&&capacity108!=4))throw std::runtime_error("Layout/capacity contract");')
change('if(draft!="NONE"&&ub!=512)throw std::runtime_error("PR96 speculative UB512 fixed");','if(draft!="NONE"&&mode!="native_greedy")throw std::runtime_error("PR108 fixed generic k1");')
change('Context tgt(target,"TARGET",ub,mode=="ordinary"?1:4,&memory);','Context tgt(target,"TARGET",ub,capacity108,&memory);')
change('Context>(draft,"DRAFT",1,1,&memory)','Context>(draft,"DRAFT",128,1,&memory)')
change('bool heavy(){return observation_mode=="heavy";}','bool heavy(){return observation_mode=="diagnostic";}')
change('bool timed(){return observation_mode=="lite"||heavy();}','bool timed(){return false;}')
t=t.replace('observation_mode!="heavy"','observation_mode!="diagnostic"')
change('if(heavy())timer=std::thread','if(false)timer=std::thread')
# No per-decode heavy synchronization. The finite admitted diagnostic captures are explicit.
t=t.replace('if(heavy())memory->sample("BEFORE_"+role+"_"+phase);','')
t=t.replace('if(heavy()){llama_synchronize(ctx);memory->sample("AFTER_"+role+"_"+phase);}','')
change('if(k!=1||action!="probe"&&action!="resident")','if(k!=1||action!="resident")')
change('auto start=clock_type::now();auto inp=', '''binding108=json::array();request_dir108=dir;auto normalized=req.at("normalized108");
   if(normalized.at("recipe").at("continuation")!=layout108||normalized.at("target_output_capacity")!=capacity108||normalized.at("producer_plan").at("ubatch")!=ub||normalized.at("prompt_ids")!=req.at("prompt_ids")||normalized.at("cap")!=req.at("cap")||normalized.at("mode")!=observation_mode||normalized.at("recipe").at("draft")!=(draft!="NONE"))throw std::runtime_error("Wire/CLI role mismatch");
   auto start=clock_type::now();auto inp=''')
change('bool capture=req.at("capture");','bool capture=req.at("capture");if(capture!=(observation_mode=="diagnostic"))throw std::runtime_error("Observation mismatch");')
change('tgt.prefill(inp);memory.require("TARGET_PREFILL");if(dft){dft->prefill(inp);memory.require("DRAFT_PREFILL");}', 'tgt.prefill(inp);memory.require("TARGET_PREFILL");tgt.initial_logits108();tgt.handoff108();if(dft){dft->prefill(inp);memory.require("DRAFT_PREFILL");dft->initial_logits108();}')
change('{"output_capacity",mode=="ordinary"?1:4}', '{"output_capacity",capacity108}')
change('result["observation_mode"]=observation_mode;', 'result["binding108"]=binding108;result["normalized108"]=normalized;result["effective_k108"]=dft?1:0;result["native_arg_k108"]=k;result["layout108"]=layout108;result["observation_mode"]=observation_mode;')
(ROOT/'native/worker.cpp').write_text(t,encoding='utf-8',newline='\n')
(ROOT/'p0/source-worker.cpp.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),t.splitlines(True),fromfile='PR97/native/worker.cpp',tofile='PR108/native/worker.cpp')),encoding='utf-8')
print('Generic transaction retained; independent draft producer; no native start')
