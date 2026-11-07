"""Original Smol free-R observer derivative and actual byte correspondence."""
from smol import *
def stage():
 dest=SROOT/'reference-observer01';dest.mkdir()
 source=SMOL/'source/pr63-original-front';bindings=read(SMOL/'CPU_CLOSEOUT_SOURCE_BINDINGS.json')['sources']
 for name in ('target.cpp','native.cpp','observer.h','CMakeLists.txt'):
  p=source/name;key=p.relative_to(SMOL).as_posix();assert sha(p)==bindings[key]['sha256']
  shutil.copyfile(p,dest/name)
 shutil.copyfile(HERE/'smol_capture.hpp',dest/'smol_capture.hpp')
 p=dest/'observer.h';s=p.read_text();s=s.replace('struct prefill_observer {','#include "smol_capture.hpp"\nstruct prefill_observer {\n    bool hs_state=false;pj hs_snapshots=pj::array();')
 old='void reset(const pj &req){path=req.at("output");';assert s.count(old)==1
 s=s.replace(old,old+'hs_state=req.value("heavy_state",false);hs_snapshots=pj::array();')
 old='        std::ofstream f(path,std::ios::binary);f<<j.dump(2)';assert s.count(old)==1
 s=s.replace(old,'        if(hs_state)j["state_snapshots"]=hs_snapshots;\n'+old)
 p.write_text(s)
 p=dest/'target.cpp';s=p.read_text();old='        int top1=-1,top2=-1;';assert s.count(old)==1
 s=s.replace(old,'        if(observer.hs_state)observer.hs_snapshots.push_back(hs_smol_capture(ctx,observer.path,i,-1));\n'+old)
 p.write_text(s)
 command(['cmake','-S',dest,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64'],dest/'configure.log')
 command(['cmake','--build',dest/'build','--config','Release','--target','b570-closeout-target','--parallel','4'],dest/'compile.log')
 bins=dest/'build/Release'
 for p in (SROOT/'original-runtime').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(dest/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.dll','.exe')]))
 write(dest/'SOURCE.json',dict(original_source_sha256=bindings['source/pr63-original-front/target.cpp']['sha256'],observer_source_sha256=sha(dest/'target.cpp'),capture_sha256=sha(dest/'smol_capture.hpp'),numeric_dll_changes=False,extra_requested_rows=0,extra_forward_calls=0))
def run_observer(index):
 old=SROOT/'units'/('old-R-'+str(index));argv=read(old/'SUPERVISOR.json')['argv'];argv[0]=str(SROOT/'reference-observer01/build/Release/b570-closeout-target.exe')
 inp=read(SMOL/'SMOL_DISCOVERY_INPUTS.json')[index];out=SROOT/('observer-R-'+str(index)+'-capture.json');request=SROOT/('observer-R-'+str(index)+'-request.json')
 request.write_text(json.dumps(dict(request_id='observer-R-'+str(index),prompt_ids=inp['prompt_ids'],output=str(out),heavy_state=True))+'\n')
 env=SROOT/('observer-R-'+str(index)+'-env.json');write(env,dict(HS_PREFILL_OUTPUT=str(out),HS_PREFILL_UB='128',HS_NO_TRANSFER='1'))
 unit,rc=supervised('observer-R-'+str(index),SROOT/'reference-observer01/FILES.json',argv,dict(requests=1,token_rows=len(inp['prompt_ids'])+128,operators=0),stdin_file=request,environment_file=env);assert rc==0
 a=read(out);b=read(SROOT/('old-R-'+str(index)+'-capture.json'))
 assert {k:v for k,v in a.items() if k!='state_snapshots'}==b
 assert len(a['state_snapshots'])==len(a['ids'])
 for i,x in enumerate(a['state_snapshots']):
  assert x['position_min']==0 and x['position_max']==len(a['prompt_ids'])+i-1
  assert Path(x['frontier']).stat().st_size==49152*4 and Path(x['sequence']).stat().st_size==x['sequence_bytes']
 write(SROOT/('OBSERVER_BRIDGE-'+str(index)+'.json'),dict(status='ORIGINAL_AVAILABLE_FIELDS_BYTE_MATCH',input_id=inp['id'],original_capture_sha256=sha(SROOT/('old-R-'+str(index)+'-capture.json')),observer_capture_sha256=sha(out),owned_full_vectors=len(a['state_snapshots']),owned_sequence_states=len(a['state_snapshots']),new_state_observation_not_old_raw_state=True,finite_single_input_scope=True))
if __name__=='__main__':
 if sys.argv[1]=='stage':stage()
 else:run_observer(int(sys.argv[2]))
