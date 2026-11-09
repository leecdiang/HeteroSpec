"""Separate offline operand-observer ELF and original typed-recipe verifier."""
from pathlib import Path
import argparse,shutil
from build import read,sha,save,command
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--builds',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();r,b,o=a.root,a.builds,a.out;src=Path(__file__).parent
 f=o/'frontend';shutil.copytree(b/'frontend',f);shutil.copy2(src/'operand_observer.hpp',f/'operand_observer.hpp');shutil.copy2(src/'operand_verify.cpp',o/'operand_verify.cpp')
 path=f/'geometry_observer.hpp';s=path.read_text();anchor='q32_operand_copy(t);return false;';assert s.count(anchor)==1;s=s.replace(anchor,'q32_operand_copy(t);return true;',1);path.write_text(s)
 save(o/'CALLBACK_CORRECTION.json',dict(scope='Offline observer only; main qualified/timing ELF unchanged',contract='ggml_backend scheduler breaks the split when its post-compute callback returns false; return true after the requested copy to continue computing the complete model',original_clean_BUILD_sha256=sha(b/'packed/BUILD.json'),full_model_R_bridge_still_required=True))
 path=f/'worker.cpp';s=path.read_text();anchor='#include "geometry_observer.hpp"';assert s.count(anchor)==1;s=s.replace(anchor,'#define Q32_OFFLINE_OPERANDS 1\n'+anchor,1);path.write_text(s)
 path=f/'entry.cpp';s=path.read_text();anchor='fs::create_directories(root);';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'if(job.value("capture_real_operands",false))q32_operand_dir=root/"operands";',1);path.write_text(s)
 path=f/'m1_capability.hpp';s=path.read_text();anchor='"proposal_tape_requests","cuda_graphs"};';assert s.count(anchor)==1;s=s.replace(anchor,'"proposal_tape_requests","cuda_graphs","capture_real_operands"};',1);path.write_text(s)
 old=b/'packed';native=r/'run-01/build-packed-01/native'
 for role in('observer','verifier'):
  dest=o/role;dest.mkdir();compile_record=old/'compile-frontend/command.json';compile_record=compile_record if compile_record.exists()else old/'compile/command.json';args=read(compile_record)['argv'];args=[s.replace(str(b/'frontend'),str(f))for s in args];args[args.index('-o')+1]=str(dest/'frontend.o');args[args.index('-MF')+1]=str(dest/'frontend.d')
  if role=='verifier':args[args.index('-c')+1]=str(o/'operand_verify.cpp')
  command(args,native,dest/'compile');link_record=old/'link-frontend/command.json';link_record=link_record if link_record.exists()else old/'link/command.json';args=read(link_record)['argv'];args=[s.replace(str(old/'frontend.o'),str(dest/'frontend.o')).replace(str(old/'transfer-worker'),str(dest/'transfer-worker'))for s in args];command(args,native,dest/'link')
  deps=read(old/'DEPENDENCIES.json');names=dict(deps['files'])
  for s in(dest/'frontend.d').read_text().replace('\\\n',' ').split(':',1)[1].split():
   p=Path(s);p=p if p.is_absolute()else native/p;names[str(p.resolve())]=sha(p)
  for p in [dest/'frontend.o',dest/'transfer-worker.map',*f.rglob('*'),o/'operand_verify.cpp',dest/'compile/command.json',dest/'link/command.json']:
   if p.is_file():names[str(p.resolve())]=sha(p)
  save(dest/'DEPENDENCIES.json',{**deps,'files':names});base=read(old/'BUILD.json');exe=dest/'transfer-worker';save(dest/'BUILD.json',{**base,'role':'packed','executable':str(exe),'executable_sha256':sha(exe),'dependency_closure_sha256':sha(dest/'DEPENDENCIES.json'),'status':'Q32_OFFLINE_REAL_OPERAND_'+role.upper()+'_NOT_QUALIFIED','clean_timing_eligible':False,'original_clean_BUILD_sha256':sha(old/'BUILD.json')});print('Q32_OPERAND_ELF_BUILT',role,sha(exe),flush=True)
 save(o/'COMPLETE.json',dict(passed=True,clean_timing_eligible=False,full_model_qualification=False,originals_modified=False))
if __name__=='__main__':main()
