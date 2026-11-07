import os,sys,json,hashlib,shutil,subprocess,zipfile
from pathlib import Path
W=Path(r'C:/Users/DIANG/Documents/ChatGPT/HeteroSpec'); R=W/'work/b570-final-causal-closeout-v1'; N=W/'work/b570-prefill-partition-v1'; P=W/'work/b570-phasebinding-boundary-v1'
os.environ['ComSpec']=r'C:\Windows\System32\cmd.exe';os.environ['PATHEXT']='.COM;.EXE;.BAT;.CMD';os.environ['PYTHONDONTWRITEBYTECODE']='1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
for x in ['code','native','versions','receipts','raw','records','payloads','operator_payloads','analysis','baseline']: (R/x).mkdir(parents=True,exist_ok=True)
shutil.copytree(N/'receipts/remote_restore',R/'baseline/pr99',dirs_exist_ok=True)
for folder in ['dependencies/pinned-source','build/Release']:shutil.copytree(N/folder,R/folder,dirs_exist_ok=True)
shutil.copy2(N/'INPUTS.json',R/'INPUTS.json');shutil.copy2(N/'COUNTER_SEMANTICS.json',R/'COUNTER_SEMANTICS.json')
for f in ['common98.py','restore98.py']:shutil.copy2(N/'code'/f,R/'code'/f)
for f in ['CMakeLists.txt','native_memory_budget.h']:shutil.copy2(N/'native'/f,R/'native'/f)
S=P/'baseline/pr92_restore/native/candidate-src'
for f in ['llama-context.cpp','llama-context.h','llama-kv-cache.cpp','llama-kv-cache.h','llama-kv-cells.h','llama-sampler.cpp','llama-graph.cpp','models/llama.cpp']:
 q=R/'baseline/source'/f;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/f,q)
# Fully verify inherited remote-restored evidence with independent old CPU auditor, no forward.
a=subprocess.run([sys.executable,'-B','-X','utf8',str(R/'baseline/pr99/code/verify98.py'),'--root',str(R/'baseline/pr99'),'--output',str(R/'analysis/inherited99')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=180)
(R/'versions/INHERITED_AUDIT.stdout').write_bytes(a.stdout);(R/'versions/INHERITED_AUDIT.stderr').write_bytes(a.stderr)
assert a.returncode==0,a.stderr.decode(errors='replace')
for n in ['RESULTS','QUALIFICATION','WORK_WITNESSES','NUMERICAL_STATE_LAYOUTS','INDEPENDENT_VERIFICATION']:assert (R/'analysis/inherited99'/f'{n}.json').read_bytes()==(R/'baseline/pr99'/f'{n}.json').read_bytes()
save(R/'INHERITED_AUDIT.json',dict(status='PASS_FULL_CPU_REDERIVATION',parent_head='c0e16aff9f3eeb0e677a52fcdc092068c096bf5d',remote_manifest_sha256=sha(R/'PR99_MANIFEST_REMOTE.json'),full_target_rehash=True,files=643))
cases=load(R/'INPUTS.json')['cases']; arms=load(N/'PLAN.json')['arms'];arms['D']=dict(arms['C'],partition=128,source_role='NEW UB128 explicit external128/remainder')
blocks=[]
for rep in range(3):
 order=cases[rep:]+cases[:rep]
 blocks.append(dict(name=f'p1a_r{rep}_D',phase='P1A',repeat=rep,arm='D',observation_mode='counts' if rep==0 else 'heavy',own_bind_sham=False,slots=[dict(slot=f'P1A/r{rep}/D|'+c['id'],task=c['id'],schedule=[min(128,len(c['prompt_ids'])-i) for i in range(0,len(c['prompt_ids']),128)]) for c in order]))
schedules=[[64,64,33],[96,65],[128,33],[160,1]]
grid={'GSM8K/test/1248':schedules,'GSM8K/test/831':[[64,64,5],[96,37],[128,5],[132,1]],'GSM8K/test/1011':[[64,64,62],[96,94],[128,62],[160,30]],'GSM8K/test/1249':[[64,64,35],[96,67],[128,35],[160,3]],'FIXED_PREFIX_1248/129':[[64,65],[96,33],[128,1]]}
for rep in range(2):
 slots=[]
 for task,gs in grid.items():
  for j,g in enumerate(gs):slots.append(dict(slot=f'P1B/r{rep}/s{j}|{task}',task=task,schedule=g,exposure='EXPOSED_REPLICATION' if j==2 else 'EXPOSED_INPUT_NEW_PARTITION'))
 slots=slots[rep:]+slots[:rep]
 blocks.append(dict(name=f'p1b_r{rep}',phase='P1B',repeat=rep,arm='A',observation_mode='counts' if rep==0 else 'heavy',own_bind_sham=False,slots=slots))
for rep in range(3):
 for arm in ['A','B','C'][rep:]+['A','B','C'][:rep]:
  slots=[]
  for c in cases[:2]:slots.append(dict(slot=f'P1C/r{rep}/{arm}|'+c['id'],task=c['id'],schedule=[len(c['prompt_ids'])] if arm!='B' else [128,len(c['prompt_ids'])-128],operator_capture=rep>0,operator_layer=0))
  blocks.append(dict(name=f'p1c_r{rep}_{arm}',phase='P1C',repeat=rep,arm=arm,observation_mode='counts' if rep==0 else 'heavy',own_bind_sham=False,slots=slots))
# P0 receiver model/contextUB512; each request receiver recreated, donor is actual immutable PR99 raw boundary0.
refs=load(N/'STUDY_RECORDS.json')
donors={}
for c in cases[:4]:
 for arm in ['A','B']:
  rec=next(x for x in refs if x['task']==c['id'] and x['arm']==arm and x['repeat']==1); raw=load(N/rec['raw_path']); pp=raw['partition98']['full_payloads']['0']
  donors[c['id']+'|'+arm]=dict(record=rec,initial=raw['phase96']['boundaries'][0],logits=pp['logits'],KV=pp['sequence_KV'])
save(R/'DONORS.json',donors)
for rep in range(2):
 slots=[]
 for c in cases[:4]:
  for arm in ['A','B']:slots.append(dict(slot=f'P0/r{rep}/{arm}|'+c['id'],task=c['id'],schedule=[],restore_donors=[arm,arm]))
 slots=slots[rep:]+slots[:rep]
 blocks.append(dict(name=f'p0_r{rep}',phase='P0',repeat=rep,arm='A',observation_mode='counts' if rep==0 else 'heavy',own_bind_sham=False,slots=slots))
conditional=[]
for rep in range(3):
 slots=[]
 for idx,c in enumerate(cases[:4]):
  if idx>=2 and rep==2:continue
  for kv,l in [('A','A'),('A','B'),('B','A'),('B','B')]:slots.append(dict(slot=f'P2/r{rep}/{kv}{l}|'+c['id'],task=c['id'],schedule=[],restore_donors=[kv,l]))
 slots=slots[rep:]+slots[:rep]
 conditional.append(dict(name=f'p2_r{rep}',phase='P2',repeat=rep,arm='A',observation_mode='heavy',own_bind_sham=False,slots=slots))
plan=dict(design_head='a1925c4a3b040f9ad3db7ec4301042791a82fe75',parent_head='c0e16aff9f3eeb0e677a52fcdc092068c096bf5d',arms=arms,blocks=blocks,conditional_blocks=conditional,load_probes=[dict(name='base_probe_A',arm='A')],limits=dict(P1A=21,P1B=38,P1C=18,P0=16,P2=40,P3=18,total_whole=200,registered_max=151,engineering=49,probe=8,operator_starts=72,owned_gpu_seconds=21600,operator_payload_bytes=536870912,timeline_bytes=67108864,total_disk_bytes=4294967296),warmups=0,retries=0,paid_cost=False,operator_rule='Traverse all source-bound named layer0 ops and all dynamic source operands; no later layer if layer0 first comparable divergence exists; if no first-divergence in layer0 after 2 captures, report bounded localization unresolved, no extra requests.',operator_replay_rule='RMS_NORM, norm-weight MUL, Q/K/V MUL_MAT at layer0 of A source operands; 2 cases x5 ops x2 geometries(full vs128/remainder) x2 repeats =40 max replay starts. Same full input values and shader/backend DLLs; no result selection.',restore_gate='P2 executes only after standalone CPU P0 own-path admission across all16 slots; any failure blocks allcrosses.')
save(R/'PLAN.json',plan)
# New worker: only caller schedule, bounded observation, explicitly equivalent native greedy initial sampling on clean restored receiver.
s=(N/'native/worker.cpp').read_text(encoding='utf8')
s=s.replace('int partition98=512;', 'std::vector<int> schedule100; bool op100=false; int layer100=0; json tensors100=json::array(); uint64_t opbytes100=0; std::string opdir100;\nint partition98=512;')
s=s.replace('cp.cb_eval=nullptr;cp.cb_eval_user_data=nullptr;', 'cp.cb_eval=observe100;cp.cb_eval_user_data=this;')
# Define source tensors immutable metadata and synchronous capped writes. Capture CPU readbacks only, never set tensor values.
hook=r'''
 static json capture100(ggml_tensor*t,const std::string&kind){
  auto*base=t;while(base->view_src)base=base->view_src;
  auto bt=base->buffer?ggml_backend_buffer_get_type(base->buffer):nullptr;auto dev=bt?ggml_backend_buft_get_device(bt):nullptr;
  json ne=json::array(),nb=json::array();for(int i=0;i<4;++i){ne.push_back(t->ne[i]);nb.push_back(t->nb[i]);}
  json j={{"kind",kind},{"name",t->name},{"op",ggml_op_name(t->op)},{"dtype",ggml_type_name(t->type)},{"type",int(t->type)},{"ne",ne},{"nb",nb},{"buffer_identity",uint64_t(reinterpret_cast<uintptr_t>(base->buffer))},{"tensor_identity",uint64_t(reinterpret_cast<uintptr_t>(t))},{"buffer_type",bt?ggml_backend_buft_name(bt):"UNKNOWN"},{"device",dev?ggml_backend_dev_name(dev):"UNKNOWN"},{"view_offset",t->view_offs},{"op_params_sha256",sha96(t->op_params,sizeof(t->op_params))}};
  j["op_params"]=json::array();for(auto p:t->op_params)j["op_params"].push_back(p);
  bool weight=std::string(t->name).find(".weight")!=std::string::npos;
  bool permitted=!weight||std::string(t->name)=="blk.0.attn_q.weight"||std::string(t->name)=="blk.0.attn_k.weight"||std::string(t->name)=="blk.0.attn_v.weight"||ggml_nbytes(t)<=65536;
  if(!permitted||ggml_nbytes(t)>33554432){j["payload"]=nullptr;j["scope"]="SOURCE_GGUF_PIN_NOT_RAW_CAPTURE";return j;}
  size_t n=ggml_nbytes(t);std::vector<uint8_t>b(n);ggml_backend_tensor_get(t,b.data(),0,n);auto h=sha96(b.data(),n);auto p=std::filesystem::path(opdir100)/(h+".tensor");
  if(!std::filesystem::exists(p)){if(opbytes100+n>536870912)throw std::runtime_error("SYNCHRONOUS_P1C_PAYLOAD_CAP");opbytes100+=n;std::ofstream f(p,std::ios::binary);f.write((char*)b.data(),n);f.close();if(!f)throw std::runtime_error("P1C_PAYLOAD_WRITE");}
  j["payload"]={{"path","operator_payloads/"+h+".tensor"},{"bytes",n},{"sha256",h}};return j;
 }
 static bool observe100(ggml_tensor*t,bool ask,void*data){
  auto*self=static_cast<Context*>(data);std::string name=t->name,suffix="-"+std::to_string(layer100);
  bool selected=op100&&self->last_phase96=="PREFILL"&&(name=="inp_embd"||(name.size()>=suffix.size()&&name.compare(name.size()-suffix.size(),suffix.size(),suffix)==0));
  if(ask)return selected;
  if(!selected)return true;
  json operands=json::array();for(int i=0;i<GGML_MAX_SRC;++i)if(t->src[i])operands.push_back(capture100(t->src[i],"src"+std::to_string(i)));
  auto r=capture100(t,"output");r["operands"]=operands;r["caller_pos"]=self->last_pos96;r["caller_ids"]=self->last_input96;r["native_context_ub"]=llama_n_ubatch(self->ctx);r["logical_mapping_rule"]="ne1=n_tokens for2D,ne2=n_tokens for Q/K/3D; verify against source and per-micrograph input IDs; raw offset not position";r["actual_shader_pipeline"]=nullptr;r["dispatch_dimensions"]=nullptr;
  tensors100.push_back(r);if(tensors100.dump().size()>4194304)throw std::runtime_error("SYNCHRONOUS_METADATA_CAP");return true;
 }
 void clean_receiver100(){
  llama_synchronize(ctx);llama_free(ctx);llama_sampler_free(sampler);
  auto p=llama_context_default_params();p.n_ctx=1024;p.n_batch=512;p.n_ubatch=ub;p.n_seq_max=1;p.n_outputs_max=capacity;p.n_outputs_max_per_seq=capacity;p.n_threads=10;p.n_threads_batch=10;p.type_k=GGML_TYPE_F16;p.type_v=GGML_TYPE_F16;p.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;p.offload_kqv=true;p.cb_eval=observe100;p.cb_eval_user_data=this;
  ctx=llama_init_from_model(model,p);sampler=llama_sampler_init_greedy();if(!ctx||!sampler)throw std::runtime_error("Fresh receiver allocation");reset();
 }
'''
s=s.replace(' static bool observe_compute',hook+'\n static bool observe_compute')
a=s.index(' void prefill(const');b=s.index(' void boundary_snapshot96',a)
s=s[:a]+r''' void prefill(const std::vector<int>&ids){
 size_t pos=0;for(int n:schedule100){if(n<=0||n>512||pos+n>ids.size())throw std::runtime_error("Frozen schedule invalid");size_t end=pos+n;decode(std::vector<int>(ids.begin()+pos,ids.begin()+end),int(pos),false,"PREFILL",end==ids.size());pos=end;}
 if(pos!=ids.size())throw std::runtime_error("Incomplete prompt schedule");
}
'''+s[b:]
s=s.replace('payloads98=json::object();','payloads98=json::object();') # occurs global, no addition there
needle=' diagnostic96=req.value("phase96_diagnostic",false);'
s=s.replace(needle,'''
 schedule100=req.at("prefill_schedule").get<std::vector<int>>();op100=req.value("operator_capture",false);layer100=req.value("operator_layer",0);opdir100=req.value("operator_dir","");tensors100=json::array();opbytes100=req.value("operator_bytes_existing",uint64_t(0));
 if(op100&&(!capture||opdir100.empty()||layer100!=0))throw std::runtime_error("Operator capture contract");
'''+needle)
needle='memory.start();tgt.prefill(inp);memory.require("TARGET_PREFILL");'
s=s.replace(needle,'''memory.start();json restored100=nullptr;std::vector<float>initial100;
 if(req.contains("restore100")){
  if(ub!=512||!schedule100.empty()||op100)throw std::runtime_error("Receiver geometry contract");tgt.clean_receiver100();
  auto rd=[&](std::string key){auto path=req["restore100"][key]["path"].get<std::string>();std::ifstream f(path,std::ios::binary);std::vector<uint8_t>b((std::istreambuf_iterator<char>(f)),{});if(b.size()!=req["restore100"][key]["bytes"].get<size_t>()||sha96(b.data(),b.size())!=req["restore100"][key]["sha256"].get<std::string>())throw std::runtime_error("Invalid donor payload pin");return b;};
  auto kv=rd("KV"),l=rd("logits");if(l.size()!=size_t(llama_vocab_n_tokens(v))*4)throw std::runtime_error("Invalid logits shape");initial100.resize(l.size()/4);memcpy(initial100.data(),l.data(),l.size());for(float x:initial100)if(!std::isfinite(x))throw std::runtime_error("Invalid FP32 logits");
  auto size=llama_state_seq_set_data(tgt.ctx,kv.data(),kv.size(),0);llama_synchronize(tgt.ctx);if(size!=kv.size())throw std::runtime_error("Incomplete sequence import");
  std::vector<uint8_t>check(llama_state_seq_get_size(tgt.ctx,0));check.resize(llama_state_seq_get_data(tgt.ctx,check.data(),check.size(),0));
  if(check!=kv||llama_memory_seq_pos_min(llama_get_memory(tgt.ctx),0)!=0||llama_memory_seq_pos_max(llama_get_memory(tgt.ctx),0)!=int(inp.size())-1)throw std::runtime_error("KV import differs");
  restored100={{"contract","BOUNDARY0_CLEAN_RECEIVER_NATIVE_GREEDY_EQUIVALENT_NOT_GENERAL_OPAQUE_CLONE"},{"KV_source",req["restore100"]["KV"]},{"logits_source",req["restore100"]["logits"]},{"post_restore_KV_sha256",sha96(check.data(),check.size())},{"post_restore_logits_sha256",sha96(initial100.data(),l.size())},{"KV_min",0},{"KV_max",int(inp.size())-1},{"extra_forward_calls",0},{"clean_context_and_scheduler",true},{"output_slot_reconstruction","initial FP32 consumed through same native apply/accept; next native decode recreates row0; no private dynamic-logit pointer injection"},{"committed_prefix",json::array()},{"pending_before_sample",nullptr},{"receiver_ub",512},{"capacity",1}};
 }else{tgt.prefill(inp);}memory.require("TARGET_PREFILL");''')
s=s.replace('int next=tgt.sample(-1);int base=int(inp.size());',r'''int next=-1;
 if(!initial100.empty()){
  std::vector<llama_token_data>cur;for(int i=0;i<int(initial100.size());++i)cur.push_back({i,initial100[i],0.0f});
  llama_token_data_array a={cur.data(),cur.size(),-1,false};llama_sampler_apply(tgt.sampler,&a);if(a.selected<0||a.selected>=int64_t(cur.size()))throw std::runtime_error("Native equivalent sample failed");next=cur[a.selected].id;llama_sampler_accept(tgt.sampler,next);work->inc("sampling_calls");restored100["natural_first_id"]=next;restored100["sampler_provenance"]="same llama_sampler_init_greedy/apply/accept, source-equivalent full ordered token_data vector";restored100["first_token_consumed_count"]=1;
 }else next=tgt.sample(-1);int base=int(inp.size());''')
s=s.replace('result["partition98"]=', 'result["restore100"]=restored100;result["operator100"]={{"enabled",op100},{"layer",layer100},{"tensors",tensors100},{"new_unique_payload_total_bytes",opbytes100},{"shader_pipeline","UNKNOWN_NO_PUBLIC_BACKEND_DISPATCH_HOOK"}};\n result["partition100"]={{"caller_lengths",schedule100},{"final_only_logits",true}};\n result["partition98"]=')
(R/'native/worker.cpp').write_text(s,encoding='utf8',newline='\n')
# module-level new bound controller, no scientific retries, conditional gate before P2.
s=(N/'code/controller98.py').read_text()
s=s.replace("limit={'P1':63,'P2':0,'probe':1}","limit={'P1A':21,'P1B':38,'P1C':18,'P0':16,'P2':40,'probe':8}")
s=s.replace("sum(counts.values())<64 and owned()<3600","sum(v for k,v in counts.items() if k!='probe')<200 and owned()<21600")
s=s.replace("f=load(ROOT/'F0A.json');remote=load(ROOT/'F0A_AUTHENTICATED.json')","f=load(ROOT/'F0_BASE.json');remote=load(ROOT/'F0_AUTHENTICATED.json')")
s=s.replace("load(ROOT/'ASSET_PREFLIGHT.json')['status']=='PASS'","load(ROOT/'ASSET_PREFLIGHT.json')['status']=='PASS'")
s=s.replace("owned()>=3598","owned()>=21598")
s=s.replace("prefill_partition=self.cfg['partition'],payload_dir=str(ROOT/'payloads')","prefill_partition=self.cfg['partition'],payload_dir=str(ROOT/'payloads'),prefill_schedule=c['schedule'],operator_capture=c.get('operator_capture',False),operator_layer=c.get('operator_layer',0),operator_dir=str(ROOT/'operator_payloads'),operator_bytes_existing=sum(p.stat().st_size for p in (ROOT/'operator_payloads').glob('*.tensor'))")
needle="  started=now();self.send(dict(op='CHECK'));"
s=s.replace(needle,'''  if c.get('restore_donors'):
   ds=load(ROOT/'DONORS.json');kv,l=c['restore_donors'];K=ds[c['id']+'|'+kv]['KV'];L=ds[c['id']+'|'+l]['logits']
   req['restore100']=dict(KV=dict(K,path=str(ROOT/'baseline/pr99'/K['path'])),logits=dict(L,path=str(ROOT/'baseline/pr99'/L['path'])),donor_labels=[kv,l])
'''+needle)
s=s.replace("actual_recipe=self.cfg,observation_mode=", "actual_recipe=self.cfg,slot_config={k:v for k,v in c.items() if k not in ['prompt_ids']},observation_mode=")
s=s.replace("w.request(x['slot'],CASES[x['task']])","w.request(x['slot'],dict(CASES[x['task']],**{k:v for k,v in x.items() if k!='task'}))")
s=s.replace("planned=63", "planned=133")
s=s.replace("  save(ROOT/'STUDY_COMPLETION.json',dict(status='COMPLETED',requests_started=63",'''  # Standalone independent P0 gate is recomputed before any conditional cross.
  p=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'code/gate100.py'),'--root',str(ROOT)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=120)
  (ROOT/'versions/P0_GATE.stdout').write_bytes(p.stdout);(ROOT/'versions/P0_GATE.stderr').write_bytes(p.stderr)
  assert p.returncode==0,p.stderr.decode(errors='replace')
  if load(ROOT/'STATE_RESTORE_ADMISSION.json')['status']=='PASS':
   for b in PLAN['conditional_blocks']:
    with Worker(b) as w:
     for x in b['slots']:
      records.append(w.request(x['slot'],dict(CASES[x['task']],**{k:v for k,v in x.items() if k!='task'})))
      save(ROOT/'STUDY_RECORDS.json',records);save(ROOT/'PROGRESS.json',dict(status='RUNNING',completed=len(records),planned=133,last_slot=x['slot'],utc=now()))
  save(ROOT/'STUDY_COMPLETION.json',dict(status='COMPLETED',requests_started=len(records)''')
s=s.replace("STUDY_COMPLETED',len(records)","STUDY_COMPLETED',len(records)")
(R/'code/controller100.py').write_text(s,encoding='utf8',newline='\n')
# old independent numeric parsers are pure stdlib and no executor imports.
shutil.copy2(N/'code/verify98.py',R/'code/numeric99.py')
save(R/'PREPARATION_ISSUES.json',dict(native_starts=0,issues=['Authenticated manifest transport exceeded Node64KiB input once; chunked transport verified full exact bytes. No model start.'],source_model_name_correction='Normative shorthand Llama-3.2 target conflicts actual Meta-Llama-3.1-8B Q6_K asset; inherit exact historical full GGUF hash, never substitute.'))
print('PREPARED',len(blocks),sum(len(b['slots']) for b in blocks),sum(len(b['slots']) for b in conditional),flush=True)
