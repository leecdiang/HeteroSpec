"""Counted source derivation; no original reference or planner file changes."""
import argparse,json,hashlib
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def derive(here,host,out):
 here=Path(here);host=Path(host);out=Path(out);original=host/'pr210-stage-b-build-02/frontend/resident_context.hpp'
 if sha(original)!='02b361035da2baa586e7c2192ca05a87036ef4336a478f954ee1a006fa6b8647':raise RuntimeError('original planner identity differs')
 text=original.read_text();old='need(!all||ids.size()<=size_t(phase_target_reserve),"requested outputs exceed actual M2 output reserve");'
 if text.count(old)!=1:raise RuntimeError('unknown output reservation guard')
 text=text.replace(old,'need(ids.size()<=4096,"qualification caller exceeds capacity");')
 old='owner.obs.phase=phase;'
 if text.count(old)!=1:raise RuntimeError('unknown group point')
 text=text.replace(old,'need(wanted.size()<=size_t(phase_target_reserve),"physical output reservation exceeded");\n                '+old)
 (out/'resident_phase_derived.hpp').write_text(text)
 source=(here/'lifecycle.cpp').read_text()
 def replace(a,b):
  nonlocal source
  if source.count(a)!=1:raise RuntimeError('source derivation point differs: '+a[:80])
  source=source.replace(a,b)
 replace('static std::string output;','static std::string output;\n#include "strong_support.hpp"')
 begin=source.index('static std::vector<float> step(');end=source.index('static void snap(',begin);source=source[:begin]+'#include "strong_step.inc"\n'+source[end:]
 replace('durable(output+"/"+n,std::string(static_cast<const char*>(p),b));','durable(output+"/"+n,std::string(static_cast<const char*>(p),b));auto reference=std::filesystem::path(output).parent_path()/"R"/n;need(std::filesystem::exists(reference),"strict reference capture missing");std::ifstream file(reference,std::ios::binary);size_t offset=0;char block[65536];while(offset<b){size_t count=std::min<size_t>(sizeof block,b-offset);file.read(block,count);need(size_t(file.gcount())==count,"strict reference capture short");for(size_t i=0;i<count;++i)if(block[i]!=static_cast<const char*>(p)[offset+i]){js("FIRST_DIFFERENCE.json",{{"capture",n},{"byte",offset+i},{"left_reference_byte",uint8_t(block[i])},{"right_candidate_byte",uint8_t(static_cast<const char*>(p)[offset+i])},{"rule","STRICT_FINITE_RAW_BITS"}});throw Blocked("strict candidate/reference raw difference");}offset+=count;}need(file.peek()==std::char_traits<char>::eof(),"strict reference capture longer");')
 replace('role=="R"||role=="REPEAT"||role=="COLD"','role=="STRONG"||role=="LOCAL"')
 replace('cp.n_ubatch=1;','cp.n_ubatch=32;');replace('cp.n_outputs_max=1;cp.n_outputs_max_per_seq=1;','cp.n_outputs_max=32;cp.n_outputs_max_per_seq=32;')
 replace('gate.before_context(role);','owner.model=model.get();phase_target_reserve=32;phase_lowering=role=="STRONG"?"SIMPLE":"LOCAL";hsc::begin("heavy",0);cp.cb_eval=QualObserver::callback;cp.cb_eval_user_data=&owner.obs;gate.before_context(role);')
 replace('llama_n_ubatch(ctx.get())==1','llama_n_ubatch(ctx.get())==32');replace('auto c=ctx.get();js','auto c=ctx.get();owner.c=c;js');replace('{"n_ubatch",1},{"output_reserve",1}','{"n_ubatch",32},{"output_reserve",32}')
 replace('for(int p=k;p<int(q.size());++p)step(c,{q[p]},p,id+"-q-"+std::to_string(p));','phase_step(c,std::vector<int>(q.begin()+k,q.end()),k,id+"-q-",true);')
 replace('gate.guard();model_stat();js("RESULT.json",','gate.guard();model_stat();js("DISPATCH.json",{{"physical",physical_trace},{"plan",owner.plan.executions},{"GPU_nodes",owner.obs.gpu_nodes},{"loop4_marked_nodes",owner.obs.loop4_nodes},{"projection_nodes",owner.obs.projection_nodes},{"physical_rows",hsc::w.physical_rows},{"physical_calls",hsc::w.physical_calls}});js("RESULT.json",')
 source=source.replace('gate.begin(role+', 'gate.begin(j.at("request_prefix").get<std::string>()+')
 (out/'strong.cpp').write_text(source)
 receipt=dict(original_planner_sha256=sha(original),derived_planner_sha256=sha(out/'resident_phase_derived.hpp'),reference_driver_sha256=sha(here/'lifecycle.cpp'),derived_driver_sha256=sha(out/'strong.cpp'),changes=['original planner groups/math retained','output reserve32 checked per physical group; qualification caller ownership may hold more copied rows across groups','same initial producer and q1 supplied body; whole suffix caller for strong/LOCAL','complete raw comparison inline stops first mismatch','real backend physical counters and GPU placement observer'],qualification_only=True)
 (out/'STRONG_DERIVATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--host-root',required=True);p.add_argument('--out',required=True);a=p.parse_args();derive(Path(__file__).resolve().parent,a.host_root,a.out)
