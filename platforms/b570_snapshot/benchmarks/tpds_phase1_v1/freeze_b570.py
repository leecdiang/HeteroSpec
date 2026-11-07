"""Import real compiler/linker output and observed modules before B570 timing."""
from host_b570 import *
import ctypes,re
_write_new=write
def write(p,j):
 if Path(p).exists():assert read(p)==j,('immutable metadata differs',str(p));return
 _write_new(p,j)
def split_windows(s):
 api=ctypes.windll.shell32.CommandLineToArgvW;api.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];api.restype=ctypes.POINTER(ctypes.c_wchar_p)
 n=ctypes.c_int();p=api(s,ctypes.byref(n));assert p
 try:return [p[i] for i in range(n.value)]
 finally:
  free=ctypes.windll.kernel32.LocalFree;free.argtypes=[ctypes.c_void_p];free.restype=ctypes.c_void_p;free(p)
def capture():
 assert not nh.LOCK.exists() and read(ROOT/'QUALIFICATION.json')['status']=='QUALIFIED' and read(ROOT/'CLEAN_OBSERVER_QUALIFIED.json')['status']=='QUALIFIED' and read(ROOT/'CLEAN_BUILD_QUALIFIED.json')['status']=='FRESH_DIRECTORY_COMPILE_AND_NATIVE_BRIDGE_PASS'
 d=ROOT/'native02';b=d/'build01';files={};paths={}
 def key(p):return os.path.normcase(str(Path(p).resolve()))
 def add(p,role):
  p=Path(p).resolve();assert p.is_file(),p;k=key(p)
  if k in paths:return paths[k]
  ident='input-'+hashlib.sha256(k.encode()).hexdigest()[:20];paths[k]=ident;files[ident]=dict(path=str(p),role=role);return ident
 units={};originals=[]
 for depdir in ('deps01','deps02'):
  for p in sorted((d/depdir).glob('*.dependencies.json')):
   z=read(p)['Data'];cmd=read(p.with_name(p.name.replace('.dependencies.json','.command.json')))
   originals.append(str(p));add(p,'dependency_report');add(p.with_name(p.name.replace('.dependencies.json','.command.json')),'build_config')
   units[key(z['Source'])]=(z,cmd)
 commands=[];normalized=[]
 for z,c in units.values():
  add(z['Source'],'source')
  for p in z['Includes']:add(p,'generated' if 'generated' in Path(p).parts else 'header')
  normalized.append(dict(source=z['Source'],dependencies=z['Includes']))
  commands.append(dict(source=z['Source'],argv=c['argv'],working_directory=c['cwd'],compiler=add(c['argv'][0],'toolchain'),response_files=[]))
 report=ROOT/'COMPILER_DEPENDENCIES.json';write(report,dict(source='msvc_source_dependencies',original_reports=originals,units=normalized));report_id=add(report,'dependency_report')
 # The verbose final link output supplies the real link argv AND library searches.
 log=d/'finish.log';lines=log.read_text(encoding='utf-8',errors='replace').splitlines();add(log,'build_config');links=[]
 library_paths=set()
 for line in lines:
  found=re.search(r'([A-Za-z]:[\\/].+\.lib):\s*$',line)
  if found and Path(found[1]).is_file():library_paths.add(str(Path(found[1]).resolve()))
 assert library_paths,'No actual /VERBOSE:LIB paths'
 for line in lines:
  if not (line.startswith('C:') and 'link.exe /nologo' in line):continue
  end=line.index('link.exe')+len('link.exe');linker=line[:end];argv=[linker]+split_windows('dummy '+line[end:])[1:];inputs=[];responses=[]
  expanded=[]
  for a in argv[1:]:
   if a.startswith('@'):
    p=b/a[1:];responses.append(add(p,'response'));expanded+=split_windows('dummy '+p.read_text().replace('\n',' '))[1:]
   else:expanded.append(a)
  for a in expanded:
   if a.startswith('/') or not a.lower().endswith(('.obj','.lib')):continue
   p=b/a
   if p.is_file():inputs.append(add(p,'link_input'))
   elif Path(a).is_file():inputs.append(add(a,'link_input'))
   else:
    matches=[p for p in library_paths if Path(p).name.lower()==Path(a).name.lower()];assert matches,(a,library_paths);inputs.extend(add(p,'link_input') for p in matches)
  inputs.extend(add(p,'link_input') for p in sorted(library_paths))
  links.append(dict(argv=argv,working_directory=str(b),linker=add(linker,'toolchain'),inputs=sorted(set(inputs)),response_files=responses,library_search_binding='all final-link observed searched libraries conservatively bound, including default library resolution'))
 assert len(links)==5,len(links)
 # Explicit CMake/Ninja/generated/launcher inputs, not inferred from five sources.
 configs=[];generated=[]
 for p in d.iterdir():
  if p.is_file() and (p.suffix in ('.cpp','.hpp','.py','.cmd') or p.name=='CMakeLists.txt'):configs.append(add(p,'source' if p.suffix in ('.cpp','.hpp','.py') else 'build_config'))
 for p in b.rglob('*'):
  if p.is_file() and (p.suffix in ('.ninja','.cmake','.rsp') or p.name in ('CMakeCache.txt','CMakeCXXCompiler.cmake','CMakeSystem.cmake')):configs.append(add(p,'response' if p.suffix=='.rsp' else 'build_config'))
 for line in (b/'build.ninja').read_text().splitlines():
  if not line.startswith('build build.ninja: RERUN_CMAKE '):continue
  encoded=line.split('RERUN_CMAKE ',1)[1].replace('$ ','\x01').replace('$:',':').replace('$$','$')
  for word in encoded.split():
   if word in ('|','||'):continue
   p=Path(word.replace('\x01',' '));p=p if p.is_absolute() else b/p
   if p.is_file():configs.append(add(p,'build_config'))
 for p in (d/'inputs/generated').rglob('*'):
  if p.is_file():generated.append(add(p,'generated'))
 for p in HERE.glob('*.py'):configs.append(add(p,'source'))
 modules={};clean_sets={}
 for cap in (1024,4096):
  for method in ('R','S','L'):
   receipt=ROOT/'units'/f'clean-native02-C{cap}-{method}'/'SUPERVISOR.json';r=read(receipt);assert r['cleanup_verified']
   observed={key(z['path']):z['sha256'] for z in r['loaded_module_hashes']};clean_sets[f'{cap}-{method}']=observed
   add(receipt,'runtime_report')
   for z in r['loaded_module_hashes']:modules[key(z['path'])]=dict(path=str(Path(z['path']).resolve()),sha256=z['sha256'])
 # Original R_d' ordinary control is part of the qualification module set too.
 for cap in (1024,4096):
  r=read(ROOT/'units'/f'ordinary-native02-C{cap}-R'/'SUPERVISOR.json')
  for z in r['loaded_module_hashes']:modules[key(z['path'])]=dict(path=str(Path(z['path']).resolve()),sha256=z['sha256'])
 for z in modules.values():assert sha(z['path'])==z['sha256'];add(z['path'],'executable' if Path(z['path']).suffix.lower()=='.exe' else 'runtime_module')
 runtime=ROOT/'ACTUAL_MODULES.json';write(runtime,dict(observed_after_qualification=True,modules=list(modules.values()),source='actual suspended/owned worker process observations, not a directory listing'));runtime_id=add(runtime,'runtime_report');write(ROOT/'CLEAN_MODULE_SETS.json',clean_sets)
 c=commands[0];cl=Path(files[c['compiler']]['path']);toolroot=cl.parent
 for p in toolroot.iterdir():
  if p.is_file() and p.suffix.lower() in ('.dll','.exe'):add(p,'toolchain')
 add(shutil.which('cmake'),'toolchain');add(shutil.which('ninja'),'toolchain');add(sys.executable,'toolchain')
 env=next(iter(units.values()))[1]['environment'];env={k:v for k,v in env.items() if k in ('PATH','INCLUDE','LIB','LIBPATH','VULKAN_SDK')}
 config=dict(schema='phase1.build-inputs.v2',phase='after_native_qualification_before_formal_timing',files=files,dependency_report=report_id,compile_commands=commands,link_commands=links,generated_files=generated,build_configuration_files=configs,runtime_report=runtime_id,build_environment=env,qualification_binding=sha(ROOT/'QUALIFICATION.json')+':'+sha(ROOT/'CLEAN_OBSERVER_QUALIFIED.json'))
 sys.path.insert(0,str(HERE));import build_freeze
 frozen=build_freeze.capture(config);write(ROOT/'BUILD_INPUTS.json',config);write(ROOT/'BUILD_FREEZE.json',frozen);build_freeze.verify(config,frozen)
 inputs=[Path(m['path']) for m in read(ROOT/'HOST_BINDINGS.json')['models']]+[ROOT/'TOKEN_TAPE.json',ROOT/'REFERENCE_DEFINITION.json']
 for cap in (1024,4096):
  inputs.append(ROOT/f'REFERENCES_C{cap}.json');inputs.extend(Path(x['reference']+'.initial.bin') for x in read(ROOT/f'REFERENCES_C{cap}.json')['checks'])
 write(ROOT/'INPUT_FREEZE.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in inputs]))
 write(ROOT/'FORMAL_FREEZE.json',dict(protocol='review-v2',native_version='native02',qualification_sha256=sha(ROOT/'QUALIFICATION.json'),clean_observer_sha256=sha(ROOT/'CLEAN_OBSERVER_QUALIFIED.json'),ordinary_controls_sha256=sha(ROOT/'ORDINARY_CONTROLS.json'),clean_build_sha256=sha(ROOT/'CLEAN_BUILD_QUALIFIED.json'),build_freeze_sha256=sha(ROOT/'BUILD_FREEZE.json'),input_freeze_sha256=sha(ROOT/'INPUT_FREEZE.json'),schedule_sha256=sha(ROOT/'SCHEDULE.json'),slots=216,measurements=108,warmups=108,arms=['REFERENCE_CONTINUATION','SIMPLE','LOCAL'],original_R_unchanged=True,new_capacity_reference_fixed_before_candidate_outputs=True,cost_window='native append only after valid prepared state, includes bind/reserve/sync/required output copy',timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),no_timing_samples_started=True,append_device_kernel_time=None,plan_mask_concat_extraction_split_times=None,untimed_costs_are_null=True))
 print('BUILD_AND_FORMAL_FROZEN',len(units),'translation units',len(files),'bound inputs',len(modules),'actual modules',flush=True)
if __name__=='__main__':
 started=time.monotonic();ok=False
 try:capture();ok=True
 finally:_write_new(ROOT/'driver-costs'/('freeze-'+str(time.time_ns())+'.json'),dict(success=ok,wall_seconds=time.monotonic()-started,model_requests=0,scope='CPU hash/dependency and freeze validation'))
