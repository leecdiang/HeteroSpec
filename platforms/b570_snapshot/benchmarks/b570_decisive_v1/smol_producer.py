"""Repair the observed target producer mismatch against unchanged Smol R."""
from smol import *
def stage():
 dest=SROOT/'producer01';dest.mkdir();source=SMOL/'source/pr63-original-front'
 binding=read(SMOL/'CPU_CLOSEOUT_SOURCE_BINDINGS.json')['sources']
 for name in ('native.cpp','target.cpp','observer.h','CMakeLists.txt'):
  assert sha(source/name)==binding[(source/name).relative_to(SMOL).as_posix()]['sha256']
  shutil.copyfile(source/name,dest/name)
 p=dest/'native.cpp';s=p.read_text()
 old='    observer.decode(ctx_tgt,llama_batch_get_one( inp.data(), n_input - 1),"target");\n    observer.decode(ctx_tgt,llama_batch_get_one(&inp.back(),           1),"target");'
 assert s.count(old)==1;s=s.replace(old,'    observer.decode(ctx_tgt,llama_batch_get_one(inp.data(),n_input),"target");')
 old='pending_scores=observer.top(ctx_tgt,0);pending=common_sampler_sample(smpl,ctx_tgt,0);'
 assert s.count(old)==1;s=s.replace(old,'pending_scores=observer.top(ctx_tgt,-1);pending=common_sampler_sample(smpl,ctx_tgt,-1);')
 p.write_text(s)
 write(dest/'SOURCE.json',dict(original_native_sha256=binding['source/pr63-original-front/native.cpp']['sha256'],worker_sha256=sha(p),repair='Match original R whole-prompt caller and its last requested output row',draft_caller='unchanged whole prompt',draft_ubatch=1,reference_binary_changed=False,numerical_dlls_changed=False))
 command(['cmake','-S',dest,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64'],dest/'configure.log')
 command(['cmake','--build',dest/'build','--config','Release','--target','b570-closeout-native','--parallel','4'],dest/'compile.log')
 bins=dest/'build/Release'
 for p in (SROOT/'original-runtime').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(dest/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.exe','.dll')]))
def run_producer(index):
 inp=read(SMOL/'SMOL_DISCOVERY_INPUTS.json')[index];name='producer01-'+str(index);out=SROOT/(name+'-capture.json');req=SROOT/(name+'-request.json')
 req.write_text(json.dumps(dict(request_id=name,prompt_ids=inp['prompt_ids'],output=str(out)))+'\n')
 env=SROOT/(name+'-env.json');write(env,dict(HS_PREFILL_OUTPUT=str(out),HS_PREFILL_UB='128'))
 argv=read(SROOT/'units'/('old-N-k1-'+str(index))/'SUPERVISOR.json')['argv'];argv[0]=str(SROOT/'producer01/build/Release/b570-closeout-native.exe')
 unit,rc=supervised(name,SROOT/'producer01/FILES.json',argv,dict(requests=1,token_rows=2*len(inp['prompt_ids'])+512,operators=0),stdin_file=req,environment_file=env);assert rc==0
 a=read(out);b=read(SROOT/('old-R-'+str(index)+'-capture.json'));n=len(b['ids'])
 pairs=[(x['scores'],y['scores']) for x,y in zip(a['commits'][:n],b['commits'])]
 diff=[i for i,(x,y) in enumerate(pairs) if x!=y]
 write(SROOT/(name+'-COMPARISON.json'),dict(input_id=inp['id'],endpoint_equal=a['ids']==b['ids'] and a['eog']==b['eog'],raw_output_count=len(a['ids']),reference_output_count=n,all_sampled_target_scores_equal=len(pairs)==n and not diff,first_score_difference=diff[0] if diff else None,full_vectors_and_KV_qualification=False));print('sampled scores mismatch indices',diff)
if __name__=='__main__':
 if sys.argv[1]=='stage':stage()
 else:run_producer(int(sys.argv[2]))
