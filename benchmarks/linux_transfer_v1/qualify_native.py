"""Finite native Linux qualification against the already frozen pristine R.

All evidence flags below are calculated from actual bytes, independently rebuilt
transactions, observed native work and separate R jobs. No helper-test receipts
are accepted as numerical evidence.
"""
from pathlib import Path
from collections import Counter
import argparse, copy, hashlib, json
from common import need, read, save, sha, verify_tree
from host import run
from native_checks import legacy_readers, gguf_structure, profile, vector_pair, state_pair, review_writers

ARMS={'W_L4_M':('loop4','SIMPLE',False),'W_P_M':('packed','SIMPLE',False),
      'L_L4_M':('loop4','LOCAL',False),'L_P_M':('packed','LOCAL',False),
      'W_L4_D4':('loop4','SIMPLE',True),'L_P_D4':('packed','LOCAL',True)}

def endpoint(r):
 if 'terminal_kind' in r:return {'ids':r['ids'],'eog':r['eog'],'stop_reason':r['terminal_kind']}
 return {k:r[k] for k in ('ids','eog','stop_reason')}

class Study:
 def __init__(self,w,repo,epoch):
  self.w=Path(w).resolve();self.repo=Path(repo).resolve();self.out=self.w/epoch
  need(not self.out.exists(),'Preserve failed qualification epochs');self.out.mkdir()
  self.cfg=self.w/'config-reference-frozen-01.json';need(read(read(self.cfg)['reference_freeze'])['status']=='REFERENCE_FROZEN','Freeze independent R first')
  self.models=read(self.w/'inputs-01/MODELS.json');self.trace,self.parse=legacy_readers(self.repo);self.counter=0;self.modules={};self.reports=[]
  save(self.out/'WRITER_REVIEW.json',review_writers(self.w/'stage-04'))
  builds={};toolchains=[]
  for role in ('reference','loop4','packed'):
   stage=self.w/('stage-03' if role=='reference' else 'stage-04');path=self.w/('build-R-01' if role=='reference' else f'build-{role}-01')/'BUILD.json';b=read(path);lock=read(stage/'SOURCE_LOCK.json')
   need(b['cuda'] and b['dependency_closure_complete'] and sha(stage/'SOURCE_LOCK.json')==b['source_lock_sha256'],'Incomplete or changed numerical-source build')
   verify_tree(stage/'sources'/role,lock['sources'][role]);deps=read(path.parent/'DEPENDENCIES.json')
   need(deps['cuda_translation_units']>0 and not deps['unresolved_compiler_dependencies'],'No actual complete CUDA compilation')
   builds[role]={'build_sha256':sha(path),'source_lock_sha256':b['source_lock_sha256'],'executable_sha256':b['executable_sha256'],'architecture':b['architecture'],
                 'cuda_translation_units':deps['cuda_translation_units'],'compiled_dependency_files':len(deps['files'])}
   toolchains.append({k:v['sha256'] for k,v in b['tools'].items()})
  need(toolchains[0]==toolchains[1]==toolchains[2],'Toolchain changed between numerical roles')
  lock=read(self.w/'stage-04/SOURCE_LOCK.json');aa=lock['sources']['loop4'];bb=lock['sources']['packed']
  need([k for k in sorted(set(aa)|set(bb)) if aa.get(k)!=bb.get(k)]==['src/llama-graph.cpp'],'Unregistered candidate backend/core difference')
  save(self.out/'SOURCE_REVIEW.json',{'passed':True,'builds':builds,'candidate_backend_source_identical':True,'only_candidate_core_difference':'src/llama-graph.cpp',
      'actual_source_archive_sha256':lock['archive_sha256'],'reference_commit':lock['reference_commit'],'port_numerical_core_edits':False,
      'CUDA_instantiation_review':'Pinned CMake globs compile mmq/mmf/attention instances; MMVQ type/width specializations are in mmvq.cu, including the existing Q8_0 dispatch. Observed arch86; inherited -use_fast_math remains unchanged for all roles.',
      'coordinator_sources':{p.name:sha(p) for p in Path(__file__).parent.glob('*.py')}})
  self.profiles={};self.structures={};self.ref_build=self.w/'build-R-01/BUILD.json'
  for family,m in self.models.items():
   structure=gguf_structure(m['target_model']);self.structures[family]=structure
   self.profiles[family]=profile(m['target_model'],m['target_sha256'],self.w/'stage-04/sources/reference/src/llama-kv-cache.cpp',structure)
  save(self.out/'MODEL_STRUCTURES.json',self.structures);save(self.out/'STATE_PROFILES.json',self.profiles)

 def execute(self,label,family,job,core='reference'):
  need('/' not in label and '..' not in label,'Safe native label')
  base=copy.deepcopy(self.models[family]);base.update(job)
  if core=='reference' or base.get('residency')=='target_only':
   base.pop('draft_model',None);base.pop('draft_sha256',None);base.update(residency='target_only',draft=False)
  path=self.out/'jobs'/(label+'.json');save(path,base)
  build=self.ref_build if core=='reference' else self.w/f'build-{core}-01/BUILD.json';dest=self.out/'runs'/label
  run(self.cfg,build,path,dest,'reference' if core=='reference' else 'development')
  key=(core,family);self.modules.setdefault(key,dest/'LOADED_MODULES.json')
  need(read(self.modules[key])==read(dest/'LOADED_MODULES.json'),'Native module identities changed within a model family qualification')
  return dest

 def report(self,name,data):
  p=self.out/(name+'.json');save(p,data);self.reports.append(p);need(data['passed'],'Retained native qualification failure: '+str(p));return p

 def matrix(self,family):
  cases=read(self.w/'inputs-01'/(family+'-GEOMETRY.json'))['cases'];ref=self.execute(family+'-matrix-R',family,{'cases':cases})
  for arm,(core,cut,draft) in ARMS.items():
   if draft:continue
   actual=self.execute(family+'-matrix-'+arm,family,{'cases':cases,'lowering':cut,'residency':'target_only','draft':False,'draft_width':1},core)
   native=read(actual/'native/result.json');need(native['model_structure']=={k:self.structures[family][k] for k in native['model_structure']},'Actual model topology differs from independent GGUF header')
   rows=[]
   for i,c in enumerate(cases):
    executed=native['cases'][i]['executions'];need(executed and sum(x['width'] for x in executed)==sum(len(x['ids']) for x in c['forced']),'Missing actual occupied physical rows')
    need(all(0<x['width']<=32 and x['active_cells']==x['position']+x['width'] for x in executed),'Actual dense append mapping/physical widths')
    for n in c['observe_positions']:
     aa=actual/'native'/c['name']/'captures'/str(n);bb=ref/'native'/c['name']/'captures'/str(n)
     row={'case':c['name'],'position':n,'vector':vector_pair(aa/'frontier.f32',bb/'frontier.f32',native['vocab'])}
     if n in c['state_positions']:row['active_KV']=state_pair(aa/'sequence.bin',bb/'sequence.bin',n,self.parse,self.profiles[family])
     rows.append(row)
   self.report(family+'-matrix-'+arm+'-CHECKED',{'passed':all(r['vector']['equal'] and r.get('active_KV',{'equal':True})['equal'] for r in rows),'family':family,'arm':arm,'rows':rows,
       'actual_native_result_sha256':sha(actual/'native/result.json'),'separate_R_launch_sha256':sha(ref/'launch.json'),'scope':'All requested full vectors and final committed active states at the fixed geometry cases; actual native append execution and GPU graph placement guarded'})

 @staticmethod
 def physical(r,input,draft):
  executions=r['executions'];need(executions,'No native physical execution records')
  expected=Counter(str(x['width']) for x in executions);observed={k:v for k,v in r['target_physical_width_hist'].items() if v}
  need(dict(expected)==observed,'Frontend/core physical counter identity or actual widths differ')
  total=len(input['prompt_ids'])+(4*len(r['cycles']) if draft else len(r['ids'])-1)
  need(sum(x['width'] for x in executions)==total,'Actual target decoded rows differ from transaction')
  need(all(x['active_cells']==x['position']+x['width'] and 0<x['width']<=32 for x in executions),'Native active frontier mapping')
  if draft:
   need(r['draft_ubatch']==4,'D4 does not mean k4')
   need(sum(int(k)*v for k,v in r['draft_physical_width_hist'].items())==len(input['prompt_ids'])+4*len(r['cycles']),'Actual draft physical rows')
   need(r['draft_physical_width_hist'].get('4',0)>=len(input['prompt_ids'])//4,'Draft prefill did not physically occupy UB4')
  else:need(not r['draft_physical_width_hist'] and r['draft_calls']==0,'Real target-only M unexpectedly executes draft')
  return {'target_histogram':observed,'draft_histogram':r['draft_physical_width_hist'],'target_rows':total,'graphs_built':r['graphs_built'],'graphs_reused':r['graphs_reused']}

 def natural(self,family):
  roots=read(self.w/'inputs-01'/(family+'-DEVELOPMENT.json'))['inputs'];banks={}
  free=self.execute(family+'-free-independent-R',family,{'inputs':[{'name':f'dev-{i}','input':x,'capture':True} for i,x in enumerate(roots)]})
  for i,x in enumerate(roots):banks[i]=Bank(self,family,i,x,free/'native'/f'dev-{i}')
  cap_input=dict(roots[0],cap=1)
  cap_ref=self.execute(family+'-cap1-independent-R',family,{'inputs':[{'name':'cap1','input':cap_input,'capture':True}]})
  for arm,(core,cut,draft) in ARMS.items():
   inputs=[{'name':f'dev-{i}-{kind}','input':x,'capture':kind=='heavy'} for i,x in enumerate(roots) for kind in ('heavy','clean')]
   inputs += [{'name':'cap1-'+kind,'input':cap_input,'capture':kind=='heavy'} for kind in ('heavy','clean')]
   actual=self.execute(family+'-natural-'+arm,family,{'inputs':inputs,'lowering':cut,'draft':draft,'draft_width':4 if draft else 1,'residency':'matched' if draft else 'target_only','profile':False},core)
   meta=read(actual/'native/result.json');need(meta['total_observed_API_calls']['context_creates']==(2 if draft else 1),'Unexpected model/context residency')
   rows=[]
   for i,x in enumerate(roots):rows.append(banks[i].check(actual/'native'/f'dev-{i}-heavy',actual/'native'/f'dev-{i}-clean',meta,draft))
   cap=read(actual/'native/cap1-heavy/receipt.json');clean=read(actual/'native/cap1-clean/receipt.json');r=read(cap_ref/'native/cap1/receipt.json')
   need(endpoint(cap)==endpoint(clean)==endpoint(r),'cap1 native pending/EOG/cap contract')
   need(not cap['cycles'] and cap['target_final_kv']=={'min':0,'max':len(cap_input['prompt_ids'])-1},'cap1 materializes a pending output')
   need(all(v==0 for v in clean['observed_API_calls_within_service'].values()),'cap1 clean observer/state work')
   cap_physical=self.physical(cap,cap_input,draft);self.physical(clean,cap_input,draft)
   for row in (cap,clean):row['study_cap']=1;self.trace(row,cap_input['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
   cap_vector=vector_pair(actual/'native/cap1-heavy/target/initial.f32',cap_ref/'native/cap1/captures'/str(len(cap_input['prompt_ids']))/'frontier.f32',meta['vocab'])
   cap_state=state_pair(actual/'native/cap1-heavy/target/state/terminal/sequence.bin',cap_ref/'native/cap1/captures'/str(len(cap_input['prompt_ids']))/'sequence.bin',len(cap_input['prompt_ids']),self.parse,self.profiles[family])
   self.report(family+'-natural-'+arm+'-CHECKED',{'passed':all(r['passed'] for r in rows) and cap_vector['equal'] and cap_state['equal'],'family':family,'arm':arm,'roots':rows,
       'cap1':{'full_vector':cap_vector,'active_state':cap_state,'physical':cap_physical,'actual_termination':r['terminal_kind']},'actual_module_map_sha256':sha(actual/'LOADED_MODULES.json'),
       'target_only':not draft,'context_creates':meta['total_observed_API_calls']['context_creates'],'complete_native_controls':True})

class Bank:
 def __init__(self,study,family,index,input,free):
  self.s=study;self.family=family;self.index=index;self.input=input;self.free=free;self.entries={};self.teacher_count=0;self.ep=read(free/'receipt.json')
  prompt=input['prompt_ids'];ids=self.ep['ids'];cases=[{'name':'greedy-trunk','forced':[{'ids':prompt,'phase':'PREFILL','all':False},{'ids':ids,'phase':'FORCED','all':False}],
      'observe_positions':list(range(len(prompt),len(prompt)+len(ids)+1)),'state_positions':list(range(len(prompt),len(prompt)+len(ids)+1))}]
  out=study.execute(family+f'-root{index}-R-trunk',family,{'cases':cases});self.add(out,cases)
  # Separate free-reference outputs remain the endpoint oracle, never a forced job.
  for n in range(len(ids)):
   a=free/'captures'/str(len(prompt)+n)/'frontier.f32';b=Path(self.entries[tuple(prompt+ids[:n])]['vector'])
   need(a.read_bytes()==b.read_bytes(),'Independent free/forced R frontier disagrees')

 def add(self,out,cases):
  for c in cases:
   tape=sum((call['ids'] for call in c['forced']),[])
   for n in c['observe_positions']:
    key=tuple(tape[:n]);d=out/'native'/c['name']/'captures'/str(n);entry=self.entries.setdefault(key,{})
    if 'vector' in entry:need(Path(entry['vector']).read_bytes()==(d/'frontier.f32').read_bytes(),'Unstable independent R at reused prefix')
    entry['vector']=str(d/'frontier.f32')
    if n in c['state_positions']:entry['state']=str(d/'sequence.bin')

 def fill(self,d):
  missing={tuple(x['prefix']) for x in d['vector_uses'] if tuple(x['prefix']) not in self.entries}
  missing_states={tuple(x['prefix']) for x in d['states'] if 'state' not in self.entries.get(tuple(x['prefix']),{})}
  wanted=missing|missing_states
  maximal=[]
  for x in sorted(wanted,key=lambda x:(-len(x),x)):
   if not any(y[:len(x)]==x for y in maximal):maximal.append(x)
  assignments={x:[] for x in maximal}
  for x in wanted:assignments[next(y for y in maximal if y[:len(x)]==x)].append(x)
  prompt=self.input['prompt_ids'];cases=[]
  for i,x in enumerate(maximal):
   need(list(x[:len(prompt)])==prompt,'Reference forced-prefix producer changed')
   calls=[{'ids':prompt,'phase':'PREFILL','all':False}]
   if len(x)>len(prompt):calls.append({'ids':list(x[len(prompt):]),'phase':'FORCED','all':False})
   cases.append({'name':f'path-{i}','forced':calls,'observe_positions':sorted(len(y) for y in assignments[x]),'state_positions':sorted(len(y) for y in assignments[x] if y in missing_states)})
  for start in range(0,len(cases),12):
   group=cases[start:start+12];self.teacher_count+=1
   out=self.s.execute(self.family+f'-root{self.index}-R-branches-{self.teacher_count}',self.family,{'cases':group});self.add(out,group)
  need(all(tuple(x['prefix']) in self.entries for x in d['vector_uses']),'Missing original requested branch vector')
  need(all('state' in self.entries.get(tuple(x['prefix']),{}) for x in d['states']),'Missing independent committed state')

 def check(self,heavy,clean,meta,draft):
  r=read(heavy/'receipt.json');c=read(clean/'receipt.json');prompt=self.input['prompt_ids']
  r['study_cap']=c['study_cap']=self.input['cap']
  _,d=self.s.trace(r,prompt,meta['vocab'],meta['eog_ids'],'rtx');_,dc=self.s.trace(c,prompt,meta['vocab'],meta['eog_ids'],'rtx')
  need(endpoint(r)==endpoint(c)==endpoint(self.ep),'Independent free endpoint differs')
  need(d==dc,'Heavy/clean native transactions differ')
  need(all(v==0 for v in c['observed_API_calls_within_service'].values()),'Online heavy observer/state transfer in clean service')
  physical=self.s.physical(c,self.input,draft);self.s.physical(r,self.input,draft)
  self.fill(d);vectors=[];states=[];vocab=meta['vocab']
  for use in d['vector_uses']:
   key=use['key'];name='initial' if key=='initial' else ('verify-'+key[4:].replace('/','-') if draft else 'ordinary-'+str(int(key[4:].split('/')[0])+1))
   pair=vector_pair(heavy/'target'/(name+'.f32'),self.entries[tuple(use['prefix'])]['vector'],vocab);vectors.append({'key':key,'prefix_tokens':len(use['prefix']),**pair})
  for i,state in enumerate(d['states']):
   name='initial' if i==0 else ('commit-'+str(i-1) if draft else 'ordinary-'+str(i));directory=heavy/'target/state'/name;entry=self.entries[tuple(state['prefix'])]
   state_check=state_pair(directory/'sequence.bin',entry['state'],len(state['prefix']),self.s.parse,self.s.profiles[self.family])
   frontier=vector_pair(directory/'frontier.f32',entry['vector'],vocab)
   text={k:v for k,v in (line.split('=',1) for line in (directory/'capture.txt').read_text().splitlines() if '=' in line)}
   need(int(text['position_min'])==0 and int(text['position_max'])==len(state['prefix'])-1,'Observed native KV frontier differs')
   if i and draft:
    cycle=r['cycles'][i-1];need(cycle['keep']==len(state['prefix']) and cycle['target_after']=={'min':0,'max':len(state['prefix'])-1},'Actual target rollback/trim frontier')
    need(cycle['draft_after']==cycle['target_after'] and cycle['pending_after']==state['next_pending'] and cycle['output_length']==state['output_count'],'Actual draft rollback/pending boundary')
   states.append({'key':name,'active_KV':state_check,'frontier':frontier,'unmaterialized_suffix':state['unmaterialized_suffix'],'next_pending':state['next_pending'],'terminal':state['terminal']})
  terminal=heavy/'target/state/terminal';last=d['states'][-1];entry=self.entries[tuple(last['prefix'])]
  ts=state_pair(terminal/'sequence.bin',entry['state'],len(last['prefix']),self.s.parse,self.s.profiles[self.family]);tv=vector_pair(terminal/'frontier.f32',entry['vector'],vocab)
  need(r['target_final_kv']=={'min':0,'max':len(last['prefix'])-1},'Terminal native frontier')
  return {'root':self.input['id'],'passed':all(v['equal'] for v in vectors) and all(s['active_KV']['equal'] and s['frontier']['equal'] for s in states) and ts['equal'] and tv['equal'],
      'independent_trace_valid':True,'endpoint_equal':True,'vectors':vectors,'states':states,'terminal_active_KV':ts,'terminal_frontier':tv,
      'physical':physical,'clean_API_calls':c['observed_API_calls_within_service'],'rejection_cycles':[x['cycle'] for x in r['cycles'] if x['rejected']],
      'terminal_kind':self.ep['terminal_kind'],'heavy_receipt_sha256':sha(heavy/'receipt.json'),'clean_receipt_sha256':sha(clean/'receipt.json')}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True);p.add_argument('--repo',required=True);p.add_argument('--epoch',default='qualification-01');a=p.parse_args()
 s=Study(a.work,a.repo,a.epoch)
 for family in ('Qwen','Smol'):s.matrix(family)
 for family in ('Qwen','Smol'):s.natural(family)
 reports=[read(p) for p in s.reports];natural=[x for x in reports if 'roots' in x]
 need(len(natural)==12 and all(x['passed'] for x in reports),'All controls/model geometries required')
 eog=[{'family':x['family'],'arm':x['arm'],'root':r['root']} for x in natural for r in x['roots'] if r['terminal_kind']=='EOG']
 rejects=[r['rejection_cycles'] for x in natural for r in x['roots'] if r['rejection_cycles']]
 need(eog,'Native EOG not observed; no EOG qualification claim')
 need(any(len(x)>=2 for x in rejects),'First/later rejection not both observed')
 summary=s.out/'NATIVE_CHECKS_COMPLETE.json';save(summary,{'passed':True,'finite_only':True,'native_EOG_observed':eog,'first_and_later_rejections_observed':True,
       'proofs':[{'path':str(p),'sha256':sha(p)} for p in s.reports],'all_committed_boundaries_observed':True,'all_original_requested_vectors_compared':True})
 kinds={'source_freeze','whole_prompt_producer','full_requested_logits','active_KV','frontier','pending','rollback','cap','native_EOG','clean_no_state_transfer','physical_work','actual_module_map','all_fixed_controls'}
 registry={'contract_checks':{'linux_reference_precedes_candidate_outputs':True},'checks':{k:{'passed':True,'evidence':str(summary)} for k in kinds},
           'executables':[{'build':str(s.w/f'build-{core}-01/BUILD.json'),'loaded_modules':str(s.modules[(core,'Qwen')])} for core in ('loop4','packed')]}
 registry['checks']['source_freeze']['evidence']=str(s.out/'SOURCE_REVIEW.json')
 save(s.out/'REGISTRY.json',registry);print('FINITE_NATIVE_QUALIFICATION_COMPLETE',flush=True)

if __name__=='__main__':main()
