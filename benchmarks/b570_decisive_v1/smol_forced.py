"""Independent scalar continuation on actual candidate token prefixes only."""
from smol_state import *
FORCED=r'''
    if(req.contains("forced_suffix")) {
        auto suffix=req.at("forced_suffix").get<std::vector<int>>();
        auto wanted=req.at("state_prefixes").get<std::vector<std::vector<int>>>();
        if(input.size()+suffix.size()>1024)throw std::runtime_error("forced capacity");
        std::vector<int> prefix=input;pj entries=pj::array();
        for(size_t j=0;j<=suffix.size();j++){
            llama_synchronize(ctx);auto*ptr=llama_get_logits_ith(ctx,-1);
            if(!ptr)throw std::runtime_error("forced frontier absent");
            int nv=llama_vocab_n_tokens(vocab);std::vector<float> owned(ptr,ptr+nv);
            bool state=std::find(wanted.begin(),wanted.end(),prefix)!=wanted.end();
            pj e;
            if(state)e=hs_smol_capture_owned(ctx,observer.path,int(j),-1,owned);
            else{
                namespace fs=std::filesystem;fs::path folder=observer.path+".states";fs::create_directories(folder);
                auto path=folder/(std::to_string(j)+".f32");std::ofstream f(path,std::ios::binary);
                f.write((const char*)owned.data(),owned.size()*4);if(!f)throw std::runtime_error("forced vector write");
                e={{"frontier",path.generic_string()}};
            }
            e["prefix"]=prefix;entries.push_back(e);
            if(j==suffix.size())break;
            int token=suffix[j];if(token<0||token>=nv)throw std::runtime_error("forced token");
            all.push_back(token);prefix.push_back(token);
            observer.begin(ctx,llama_batch_get_one(&all.back(),1));
            if(!common_prompt_batch_decode(ctx,all,1,n_past,512,"",false))throw std::runtime_error("forced decode");
            observer.end(ctx,0);
        }
        pj result={{"role","forced_reference"},{"received_forced_tape",true},{"candidate_values_received",false},{"prompt_ids",input},{"prefixes",entries},{"trace",observer.trace}};
        std::ofstream f(observer.path);f<<result.dump(2)<<"\n";f.close();
        std::cout<<"HS_RESULT "<<pj({{"request_id",req.at("request_id")},{"forced_tokens",suffix.size()}}).dump()<<"\n"<<std::flush;
        continue;
    }
'''
def stage(name='forced-reference01',bulk=False):
 d=SROOT/name;d.mkdir()
 for n in ('target.cpp','native.cpp','observer.h','CMakeLists.txt'):shutil.copyfile(SMOL/'source/pr63-original-front'/n,d/n)
 shutil.copyfile(HERE/'smol_capture.hpp',d/'smol_capture.hpp')
 if bulk:
  shutil.copyfile(HERE/'smol_bulk.hpp',d/'smol_bulk.hpp')
  cm=d/'CMakeLists.txt';cm.write_text(cm.read_text()+'\ntarget_compile_definitions(b570-closeout-target PRIVATE SMOL_BULK_OBSERVER)\ntarget_include_directories(b570-closeout-target PRIVATE "${PINNED_SOURCE}/src" "${PINNED_SOURCE}/ggml/src")\ntarget_compile_options(b570-closeout-target PRIVATE /utf-8)\n')
 p=d/'target.cpp';s=p.read_text();s=s.replace('using json = nlohmann::ordered_json;','using json = nlohmann::ordered_json;\n#include "smol_capture.hpp"');anchor='    std::vector<llama_token> generated;';assert s.count(anchor)==1;s=s.replace(anchor,FORCED+'\n'+anchor);p.write_text(s)
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 command(['cmake','--build',d/'build','--config','Release','--target','b570-closeout-target','--parallel','4'],d/'compile.log')
 bins=d/'build/Release'
 for p in (SROOT/'original-runtime').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.exe','.dll')]))
 write(d/'SOURCE.json',dict(worker_sha256=sha(d/'target.cpp'),original_target_source_sha256=sha(SMOL/'source/pr63-original-front/target.cpp'),original_prompt_producer_unchanged=True,continuation_caller=1,output_flags='one last row each call',no_candidate_logits_or_state_import=True))
def jobs():
 a=read(SROOT/'qual02-0-heavy-capture.json');prompt=a['prompt_ids'];prefixes={tuple(x['prefix']) for x in a['full_target_vectors']+a['committed_states']};maximal=[]
 for p in sorted(prefixes,key=lambda x:(-len(x),x)):
  if not any(q[:len(p)]==p for q in maximal):maximal.append(p)
 result=[]
 for j,p in enumerate(sorted(maximal)):
  result.append(dict(request_id='forced01-0-'+str(j),prompt_ids=prompt,forced_suffix=list(p[len(prompt):]),state_prefixes=[x['prefix'] for x in a['committed_states']],output=str(SROOT/('forced01-0-'+str(j)+'-capture.json'))))
 write(SROOT/'FORCED_JOBS-0.json',dict(jobs=result,request_reservation=len(result),token_rows=sum(len(x['prompt_ids'])+len(x['forced_suffix']) for x in result),derived_only_from_native_tokens=True));print('Independent reference paths:',len(result))
def execute():
 data=read(SROOT/'FORCED_JOBS-0.json');template=read(SROOT/'units/old-R-0/SUPERVISOR.json')['argv']
 for j,job in enumerate(data['jobs']):
  name=job['request_id'];req=SROOT/(name+'-request.json');req.write_text(json.dumps(job)+'\n');env=SROOT/(name+'-env.json');write(env,dict(HS_PREFILL_OUTPUT=job['output'],HS_PREFILL_UB='128',HS_NO_TRANSFER='1'))
  argv=list(template);argv[0]=str(SROOT/'forced-reference01/build/Release/b570-closeout-target.exe')
  unit,rc=supervised(name,SROOT/'forced-reference01/FILES.json',argv,dict(requests=1,token_rows=len(job['prompt_ids'])+len(job['forced_suffix']),operators=0),stdin_file=req,environment_file=env);assert rc==0
  for p in sorted(Path(job['output']+'.states').glob('*.bin')):pack(p)
def check():
 a=read(SROOT/'qual02-0-heavy-capture.json');free=read(SROOT/'observer-R-0-capture.json');bank={};duplicate=0
 for job in read(SROOT/'FORCED_JOBS-0.json')['jobs']:
  r=read(native_path(job['output']));assert r['role']=='forced_reference' and r['candidate_values_received'] is False
  for x in r['prefixes']:
   key=tuple(x['prefix']);front=native_path(x['frontier']).read_bytes()
   if key in bank:assert front==native_path(bank[key]['frontier']).read_bytes();duplicate+=1
   if key not in bank or 'sequence' in x:bank[key]=x
 vector_matches=[]
 for x in a['full_target_vectors']:
  y=bank[tuple(x['prefix'])];aa=native_path(x['path']).read_bytes();bb=native_path(y['frontier']).read_bytes();assert len(aa)==49152*4
  assert np.isfinite(np.frombuffer(aa,dtype='<f4')).all();vector_matches.append(aa==bb)
 state_matches=[]
 for x in a['committed_states']:
  y=bank[tuple(x['prefix'])];v,_=decode(load(x['sequence']));w,_=decode(load(y['sequence']));state_matches.append(np.array_equal(v,w) and native_path(x['frontier']).read_bytes()==native_path(y['frontier']).read_bytes())
 for i,x in enumerate(free['state_snapshots']):
  key=tuple(free['prompt_ids']+free['ids'][:i])
  if key in bank:assert native_path(x['frontier']).read_bytes()==native_path(bank[key]['frontier']).read_bytes()
 write(SROOT/'QUALIFICATION-0.json',dict(status='FINITE_NATIVE_CAPTURE_MATCH' if all(vector_matches+state_matches) else 'NUMERICAL_MISMATCH',contract='T',full_conditional_vectors=len(vector_matches),vectors_equal=sum(vector_matches),committed_states=len(state_matches),states_equal=sum(state_matches),independent_forced_paths=len(read(SROOT/'FORCED_JOBS-0.json')['jobs']),duplicate_reference_prefixes_checked=duplicate,autonomous_reference_never_received_candidate_tape=True,heavy_off_final_state_equal=read(SROOT/'COMMITTED_STATE_CHECK-0.json')['heavy_off_final_equal'],scope='One exposed historical development input, repaired whole-prompt draft UB1; not a main-panel qualification or performance claim'))
if __name__=='__main__':
 {'stage':stage,'jobs':jobs,'run':execute,'check':check}[sys.argv[1]]()
