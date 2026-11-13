"""Genuine kernel/sealed seqpacket substitute and numeric checker; no GPU link."""
import argparse,ast,hashlib,importlib.util,json,os,re,subprocess,time
from pathlib import Path
def main(config):
 here=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('controller',here/'controller.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);cfg=json.loads(Path(config).read_text());base=Path(cfg['root']);src=Path(cfg['host_root'])/'run-01/stage-03/sources/reference';records=[]
 for p in here.glob('*.py'):ast.parse(p.read_text())
 numeric=base/'raw-cpu-checker';compile=['g++','-std=c++17','-O2','-I'+str(src/'vendor'),str(here/'raw_cpu.cpp'),'-o',str(numeric)];r=subprocess.run(compile,capture_output=True,text=True,check=True,timeout=60);c.write(base/'RAW_CPU_BUILD.json',dict(argv=compile,stderr=r.stderr,sha256=c.sha(numeric),GPU_calls=0))
 # Actual independent finite/tie/short-write regression over raw scalar files.
 import struct
 fixture=base/'raw-cpu-tests';fixture.mkdir(mode=0o700);v=[0.0]*151936;v[10]=v[11]=2.0;(fixture/'tie.f32').write_bytes(struct.pack('<151936f',*v));(fixture/'nan.kv').write_bytes(struct.pack('<H',0x7c00));(fixture/'short.f32').write_bytes(b'1234')
 for name,file,type_,size,expected in [('tie','tie.f32','F32',151936*4,0),('nonfinite','nan.kv','F16',2,1),('short','short.f32','F32',151936*4,1)]:
  job=fixture/(name+'.json');job.write_text(json.dumps([dict(path=str(fixture/file),name=file,type=type_,bytes=size)]));q=subprocess.run([str(numeric),str(job)],capture_output=True,text=True,timeout=10)
  if bool(q.returncode)!=bool(expected) or name=='tie' and json.loads(q.stdout)['files'][0]['greedy']!=10:raise RuntimeError('independent scalar regression '+name)
  records.append(dict(test=name,returncode=q.returncode,stdout=q.stdout,stderr=q.stderr,model_calls=0))
 for number,bad in [(1,False),(2,True)]:
  root=base/('cpu-bridge%02d'%number);root.mkdir(mode=0o700);(root/'MANIFEST.json').write_bytes((base/'MANIFEST.json').read_bytes());test=dict(cfg,run_id=cfg['run_id']+'-cpu%02d'%number,root=str(root),parent_ledger_path=None);c.initialize(test,cpu=True);c.write(root/'CONTROLLER_IDENTITY.json',dict(pid=os.getpid(),sources={str(p):c.sha(p) for p in here.glob('*') if p.is_file()}));exe=root/'std-probe';argv=['g++','-std=c++17','-O2','-I'+str(src/'vendor'),'-DHS_LIVE_ROOT='+json.dumps(str(root)),'-DHS_LIVE_MANIFEST_SHA='+json.dumps(c.sha(root/'MANIFEST.json')),'-DHS_LIVE_KIND="CPU"',str(here/'cpu_probe.cpp'),'-o',str(exe)];q=subprocess.run(argv,capture_output=True,text=True,check=True,timeout=60);libs=c.cmd(['readelf','-d',str(exe)]).stdout
  if set(re.findall(r'Shared library: \[([^]]+)\]',libs))-{'libstdc++.so.6','libgcc_s.so.1','libc.so.6','libm.so.6'}:raise RuntimeError('CPU probe has backend/CUDA dependency')
  c.write(root/'COMPILE.json',dict(argv=argv,stdout=q.stdout,stderr=q.stderr,readelf=libs,sha256=c.sha(exe)));c.run_worker(test,dict(role='CPU',kind='CPU',first_operation=0,end_operation=1),dict(path=str(exe),sha256=c.sha(exe)),cpu=True,bad_nonce=bad);records.append(dict(test='actual-kernel-peer-'+('reject-nonce' if bad else 'accept-row-poison'),state=json.loads((root/'STATE.json').read_text()),unit_exit=json.loads((root/'CPU/UNIT_EXIT.json').read_text()),models=0,GPU_contexts=0))
 c.write(base/'CPU_CHECK_RESULT.json',dict(status='PASS_REAL_KERNEL_PREEXEC_PEER_FAIL_CLOSED_AND_INDEPENDENT_RAW_SCALARS',checks=records,GPU_contexts=0,model_objects=0,placements=0,forwards=0,limitation='std-only substitute, not native numerical qualification'))
 print('REAL_CPU_CHECK_PASS')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();main(a.config)
