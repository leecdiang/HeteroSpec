"""Separate observed frontends; keep primary clean binaries unchanged."""
from native_host import *
from stage_costs import once

def build(stage,arm):
 d=ROOT/'observed02'/f'{stage}-{arm}'
 if (d/'FILES.json').exists():return d
 base=ROOT/('resident04' if stage=='resident' else 'parallel04')/f'{arm}-mode1';d.mkdir(parents=True)
 for p in base.iterdir():
  if p.is_file() and p.suffix.lower() in ('.cpp','.h','.hpp','.txt'):shutil.copyfile(p,d/p.name)
 shutil.copyfile(HERE/'native/trim_trace.hpp',d/'trim_trace.hpp')
 replacements=0
 if arm!='M':
  p=d/'native.cpp';s=p.read_text();replacements=s.count('llama_memory_seq_rm(');assert replacements>0
  s=s.replace('llama_memory_seq_rm(','economics_trim(')
  s=once(s,'#include "economics_phase.hpp"','#include "economics_phase.hpp"\n#include "trim_trace.hpp"');p.write_text(s)
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 command(['cmake','--build',d/'build','--config','Release','--target','b570-closeout-'+('target' if arm=='M' else 'native'),'--parallel','4'],d/'compile.log')
 bins=d/'build/Release'
 for p in (base/'build/Release').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in bins.iterdir() if p.suffix.lower() in ('.exe','.dll')]))
 write(d/'SOURCE.json',dict(files={p.name:sha(p) for p in d.iterdir() if p.suffix in ('.cpp','.h','.hpp','.txt')},base=str(base),diagnostic_only=True,actual_trim_call_sites=replacements,no_new_model_calls_or_drains=True))
 return d

if __name__=='__main__':
 for s in ('resident','parallel'):
  for a in ('M','H1','C4U4','C4U1'):print(build(s,a),flush=True)
