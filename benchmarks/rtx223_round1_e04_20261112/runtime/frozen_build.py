"""Freeze copied code-generation inputs, then build fresh objects without DLL loading."""
from pathlib import Path
import concurrent.futures,ctypes,datetime,hashlib,json,os,re,shutil,subprocess,time,sys
from input_closure import ReadFreeze,parse_nvcc_dep

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OLD=ROOT.parent/'rtx223-round1-resume-20261112-e03'
SRC=HERE/'source-v1'; TC=HERE/'toolchain-v1'; OUT=HERE/'build-v1'
FREEZE=ROOT/'e04/freeze'
SDKVER='10.0.26100.0'
CUDA=TC/'cuda'; VC=TC/'vc'; SDK=TC/'sdk'
PY=Path(sys.executable)

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def absolute(p):
    text=str(Path(p).resolve())
    if text.startswith('\\\\?\\UNC\\'):text='\\\\'+text[8:]
    elif text.startswith('\\\\?\\'):text=text[4:]
    return Path(text)
def xp(p):
    text=str(absolute(p))
    return Path('\\\\?\\UNC\\'+text[2:] if text.startswith('\\\\') else '\\\\?\\'+text)
def sha(p):
    h=hashlib.sha256()
    with xp(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def write(p,obj):xp(p).parent.mkdir(parents=True,exist_ok=True);xp(p).write_text(json.dumps(obj,indent=2),encoding='utf8')
def files(root):
    for d,ds,fs in os.walk(xp(root)):
        ds.sort()
        for name in sorted(fs):yield absolute(Path(d)/name)
def rows(root):return {p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':xp(p).stat().st_size} for p in files(root)}
def copytree(origin,dest):
    if xp(dest).exists():raise RuntimeError('refuse existing input destination '+str(dest))
    if absolute(origin)==absolute(dest) or absolute(origin) in absolute(dest).parents:raise RuntimeError('unsafe copy target')
    xp(dest).mkdir(parents=True)
    before=rows(origin)
    for rel in before:
        target=dest/rel;xp(target).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(xp(origin/rel),xp(target))
    after=rows(dest)
    if before!=after:raise RuntimeError('copy hash mismatch '+str(origin))
    print(json.dumps({'copied':str(origin),'files':len(before),'bytes':sum(r['bytes'] for r in before.values())}),flush=True)
    return {'origin':str(origin),'destination':str(dest),'files':after}
def split_windows(command):
    dll=ctypes.WinDLL('shell32',use_last_error=True)
    fn=dll.CommandLineToArgvW;fn.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];fn.restype=ctypes.POINTER(ctypes.c_wchar_p)
    count=ctypes.c_int();argv=fn(command,ctypes.byref(count))
    if not argv:raise ctypes.WinError(ctypes.get_last_error())
    result=[argv[i] for i in range(count.value)]
    free=ctypes.WinDLL('kernel32').LocalFree;free.argtypes=[ctypes.c_void_p];free.restype=ctypes.c_void_p;free(argv)
    return result
def environment():
    # Only effective compiler inputs are inherited; arbitrary NVCC/CL/LINK flags are absent.
    env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE','PROCESSOR_IDENTIFIER','OS')}
    env['PATH']=';'.join(map(str,[VC/'bin/Hostx64/x64',SDK/f'bin/{SDKVER}/x64',CUDA/'bin',Path(os.environ['SystemRoot'])/'System32',Path(os.environ['SystemRoot'])]))
    env['INCLUDE']=';'.join(map(str,[VC/'include',*[SDK/f'Include/{SDKVER}/{x}' for x in ('ucrt','shared','um','winrt','cppwinrt')]]))
    env['LIB']=';'.join(map(str,[VC/'lib/x64',SDK/f'Lib/{SDKVER}/ucrt/x64',SDK/f'Lib/{SDKVER}/um/x64',CUDA/'lib/x64']))
    env['CUDA_PATH']=str(CUDA);env['VSLANG']='1033'
    return env
def makecommands():
    original=json.loads((HERE/'inputs/compile_commands.original.json').read_bytes());commands=[]
    for item in original:
        if not item['file'].endswith('.cu'):continue
        rel=Path(item['file']).relative_to(Path('F:/rtx184/loop/native-arms/backend_loop4'))
        source=SRC/rel;obj=OUT/'objects'/rel.with_suffix('.cu.obj');index=len(commands)
        dep=OUT/'deps'/f'{index:03d}.d';keep=OUT/'generated'/f'{index:03d}'
        mapped=[]
        for token in split_windows(item['command']):
            if token=='-DGGML_CUDA_USE_GRAPHS' or token.startswith('-Xcompiler=-Fd'):continue
            token=token.replace('F:/rtx184/loop/native-arms/backend_loop4',str(SRC)).replace('F:\\rtx184\\loop\\native-arms\\backend_loop4',str(SRC))
            token=token.replace('D:/rtx184-tools/cuda',str(CUDA)).replace('D:\\rtx184-tools\\cuda',str(CUDA))
            mapped.append(token)
        mapped[0]=str(CUDA/'bin/nvcc.exe');mapped[mapped.index('-o')+1]=str(obj)
        mapped+=['-DNOMINMAX','-DGGML_CUDA_NO_VMM','-ccbin',str(VC/'bin/Hostx64/x64'),'-MD','-MF',str(dep),'-MT',str(obj),'--keep','--keep-dir',str(keep),'-Xcompiler=/showIncludes']
        commands.append({'index':index,'kind':'CUDA','source':str(source),'object':str(obj),'dependency':str(dep),'generated':str(keep),'argv':mapped})
    for name in ('hs_e03_runtime.cpp','hs_launch_budget.cu'):
        source=SRC/'ggml/src/ggml-cuda'/name;index=len(commands);obj=OUT/'objects'/Path(name).with_suffix('.obj');dep=OUT/'deps'/f'{index:03d}.json'
        argv=[str(VC/'bin/Hostx64/x64/cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc','/TP','/DNOMINMAX','/DGGML_BACKEND_BUILD','/DGGML_BACKEND_SHARED','/I'+str(source.parent),'/sourceDependencies',str(dep),'/showIncludes','/c',str(source),'/Fo:'+str(obj)]
        commands.append({'index':index,'kind':'HOST','source':str(source),'object':str(obj),'dependency':str(dep),'argv':argv})
    if len(commands)!=145:raise RuntimeError('expected145 translation units')
    if any('HS_LB_CPU_TEST_ONLY' in t or 'GGML_CUDA_USE_PDL' in t for j in commands for t in j['argv']):raise RuntimeError('forbidden build profile')
    return commands
def linkcommand(commands):
    libs=[HERE/'inputs/ggml-base.lib',*[CUDA/f'lib/x64/{x}' for x in ('cudart.lib','cublas.lib','cuda.lib','cublasLt.lib','cudadevrt.lib','cudart_static.lib')]]
    windows=('kernel32.lib','user32.lib','gdi32.lib','winspool.lib','shell32.lib','ole32.lib','oleaut32.lib','uuid.lib','comdlg32.lib','advapi32.lib')
    return [str(VC/'bin/Hostx64/x64/link.exe'),'/DLL','/MACHINE:X64','/INCREMENTAL:NO','/VERBOSE:LIB','/OUT:'+str(OUT/'bin/ggml-cuda.dll'),'/IMPLIB:'+str(OUT/'ggml-cuda.lib'),*[j['object'] for j in commands],*map(str,libs),*windows]
def prepare():
    FREEZE.mkdir(parents=True,exist_ok=True);HERE.mkdir(exist_ok=True)
    if OUT.exists():raise RuntimeError('build output already exists')
    inventory=[]
    inventory.append(copytree(OLD/'runtime/final-source',SRC))
    expected=json.loads((OLD/'runtime/FINAL_SOURCE_IDENTITIES.json').read_bytes())['source_files_sha256']
    if {r:v['sha256'] for r,v in inventory[0]['files'].items()}!=expected:raise RuntimeError('e03 uniform source mismatch')
    inventory.append(copytree(Path('D:/rtx184-tools/cuda'),CUDA))
    inventory.append(copytree(Path('D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207'),VC))
    for rel in (f'Include/{SDKVER}',f'Lib/{SDKVER}/ucrt/x64',f'Lib/{SDKVER}/um/x64',f'bin/{SDKVER}/x64'):
        inventory.append(copytree(Path('D:/rtx184-tools/msvc/Windows Kits/10')/rel,SDK/rel))
    (HERE/'inputs').mkdir()
    for old,new in [(Path('D:/rtx184-operator/cuda-v2/compile_commands.json'),'compile_commands.original.json'),(Path('D:/rtx184-operator/cuda-v2/ggml/src/ggml-base.lib'),'ggml-base.lib'),(OLD/'runtime/AS_BUILT_BINDINGS_FINAL.json','e03_AS_BUILT_BINDINGS_FINAL.json'),(OLD/'runtime/FINAL_SOURCE_IDENTITIES.json','e03_FINAL_SOURCE_IDENTITIES.json')]:
        shutil.copy2(xp(old),xp(HERE/'inputs'/new))
    finalize(inventory,expected)

def finalize(inventory=None,expected=None):
    if OUT.exists():raise RuntimeError('no input repair after compiler work')
    if inventory is None:
        provisional=FREEZE/'FREEZE.json'
        if not provisional.exists():raise RuntimeError('copy preparation receipt missing')
        previous=json.loads(provisional.read_bytes());inventory=previous['copy_inventory']
        expected=json.loads((HERE/'inputs/e03_FINAL_SOURCE_IDENTITIES.json').read_bytes())['source_files_sha256']
        archive=ROOT/'e04/preflight-v1/provisional-freeze';archive.mkdir(exist_ok=False)
        for path in FREEZE.iterdir():
            if path.is_file():shutil.move(str(path),str(archive/path.name))
    fixture=ROOT/'e04/preflight/RESULT.json'
    if not fixture.exists() or json.loads(fixture.read_bytes()).get('status')!='PASS':raise RuntimeError('new parser/owned-lock preflight required')
    commands=makecommands();env=environment();link=linkcommand(commands)
    write(FREEZE/'COMMANDS.json',commands);write(FREEZE/'ENVIRONMENT.json',env);write(FREEZE/'LINK_COMMAND.json',link)
    recipe={'frozen_build.py':sha(__file__),'python_executable':str(PY),'python_sha256':sha(PY),'python_version':sys.version,'cwd':str(OUT),'workers':2,'no_reused_objects':True,'native_loading':False,'native_GPU_execution':False}
    write(FREEZE/'RECIPE.json',recipe)
    all_rows={str(p):{'sha256':sha(p),'bytes':xp(p).stat().st_size} for root in (SRC,TC,HERE/'inputs') for p in files(root)}
    source_actual={str(Path(p).relative_to(SRC)).replace('\\','/'):row['sha256'] for p,row in all_rows.items() if SRC in Path(p).parents}
    if source_actual!=expected:raise RuntimeError('uniform complete source changed before final freeze')
    for name in ('COMMANDS.json','ENVIRONMENT.json','LINK_COMMAND.json','RECIPE.json'):p=FREEZE/name;all_rows[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
    for p in (HERE/'input_closure.py',ROOT/'e04/preflight/RESULT.json'):
        all_rows[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
    all_rows[str(Path(__file__).resolve())]={'sha256':sha(__file__),'bytes':Path(__file__).stat().st_size}
    freeze={'schema':'heterospec.e04.full-codegen-input-freeze.v1','created_utc':now(),'complete_source_files':len(expected),'input_files':len(all_rows),'input_bytes':sum(x['bytes'] for x in all_rows.values()),'copy_inventory':inventory,'inputs':all_rows,'limits':['Windows OS loader/system components and hardware are not copied or immutable. Compiler and SDK codegen inputs are isolated copies, deny-write locked during build, and rehashed afterward. Directory creation by administrator cannot be prevented; actual dependency paths must resolve inside this recorded set.','e03 partial catalog and provider sync exception remain preserved, not retroactively fixed.'],'no_GPU_or_numerical_load':True}
    write(FREEZE/'FREEZE.json',freeze)
    print(json.dumps({'stage':'FROZEN','files':len(all_rows),'sha256':sha(FREEZE/'FREEZE.json'),'utc':now()}),flush=True)

def lock_inputs(manifest):
    held=ReadFreeze()
    try:
        for path,row in manifest['inputs'].items():
            if sha(path)!=row['sha256']:raise RuntimeError('prefreeze input changed '+path)
            held.add(path)
        held.add(FREEZE/'FREEZE.json')
        return held
    except:
        held.release()
        raise

def dependency_audit(receipts,manifest):
    pinned={str(absolute(p)).casefold():row['sha256'] for p,row in manifest['inputs'].items()}
    units=[];unbound=[];missing=[]
    for receipt in receipts:
        paths={receipt['source']}
        log=Path(receipt['log']).read_text(encoding='utf8',errors='replace')
        for line in log.splitlines():
            marker='Note: including file:'
            if marker in line:
                candidate=line.split(marker,1)[1].strip()
                if candidate:paths.add(candidate)
        dep=Path(receipt['dependency'])
        if not dep.exists():missing.append(str(dep))
        elif receipt['kind']=='HOST':
            try:
                data=json.loads(dep.read_bytes())['Data']
                if absolute(data['Source'])!=absolute(receipt['source']) or not isinstance(data.get('Includes'),list) or not data['Includes']:raise ValueError('host source identity or header list mismatch')
                paths.add(data['Source']);paths.update(data['Includes'])
            except Exception as exc:unbound.append({'index':receipt['index'],'dependency_parse_error':repr(exc)})
        else:
            try:paths.update(parse_nvcc_dep(dep.read_text(encoding='utf8',errors='strict'),receipt['object'],receipt['source']))
            except Exception as exc:unbound.append({'index':receipt['index'],'dependency_parse_error':repr(exc)})
        bound=[];generated=[];unknown=[]
        for name in sorted(paths):
            path=absolute(name);key=str(path).casefold()
            if key in pinned:bound.append({'path':str(path),'sha256':pinned[key]})
            elif receipt['kind']=='CUDA' and declared_generated(path,receipt) and xp(path).is_file():
                generated.append({'path':str(path),'sha256':sha(path),'generator_argv':receipt['argv'],'generator_index':receipt['index']})
            else:unknown.append(str(path));unbound.append({'index':receipt['index'],'path':str(path)})
        units.append({'index':receipt['index'],'source':receipt['source'],'dependency_recipe':receipt['dependency'],'dependency_sha256':receipt.get('dependency_sha256'),'bound_inputs':bound,'generated_inputs':generated,'unbound':unknown})
    return {'schema':'heterospec.e04.actual-dependency-closure.v1','status':'PASS' if not unbound and not missing else 'FAIL','units':units,'missing_dependency_files':missing,'unbound_inputs':unbound,'scope':'nvcc -MD with system headers plus English MSVC /showIncludes; host /sourceDependencies; generated nvcc intermediates retained and hashed after generation'}

def declared_generated(path,receipt):
    expected_suffixes=('.cpp1.ii','.cpp4.ii','.cudafe1.cpp','.cudafe1.stub.c','.cudafe1.gpu','.cudafe1.c','.fatbin.c','.module_id','.ptx','.cubin','.fatbin')
    own_keep=Path(receipt['generated']);own_temp=OUT/'temp'/str(receipt['index'])
    if path.parent not in (own_keep,own_temp):return False
    stem=Path(receipt['source']).stem
    return (path.name.startswith(stem+'.') or path.name.startswith('tmpxft_')) and path.name.endswith(expected_suffixes)

def runbuild():
    freeze_digest=sha(FREEZE/'FREEZE.json');manifest=json.loads((FREEZE/'FREEZE.json').read_bytes());held=lock_inputs(manifest)
    start=time.monotonic();started=now();receipts=[]
    try:
        OUT.mkdir(exist_ok=False)
        for name in ('objects','logs','deps','generated','temp','bin'):(OUT/name).mkdir()
        commands=json.loads((FREEZE/'COMMANDS.json').read_bytes());env=json.loads((FREEZE/'ENVIRONMENT.json').read_bytes())
        membership_before={str(p) for root in (SRC,TC,HERE/'inputs') for p in files(root)}
        membership_expected={p for p in manifest['inputs'] if any(root==absolute(p) or root in absolute(p).parents for root in (SRC,TC,HERE/'inputs'))}
        if membership_before!=membership_expected:raise RuntimeError('input directory membership changed before compilation')
        if sha(FREEZE/'FREEZE.json')!=freeze_digest:raise RuntimeError('freeze metadata changed while locking')
        write(OUT/'ADMISSION.json',{'utc':started,'input_locks':len(held.handles),'file_sharing':'GENERIC_READ and FILE_SHARE_READ only: denies writes/deletes to isolated input files while handles held','source_freeze_sha256':freeze_digest,'fresh_build':True,'workers':2,'no_GPU':True})
        def one(job):
            i=job['index'];log=OUT/'logs'/f'{i:03d}-{Path(job["source"]).name}.log';temp=OUT/'temp'/str(i);temp.mkdir();Path(job['object']).parent.mkdir(parents=True,exist_ok=True)
            if job.get('generated'):Path(job['generated']).mkdir()
            local=env.copy();local['TEMP']=local['TMP']=str(temp);t=time.monotonic();error=None
            try:
                with log.open('xb') as f:r=subprocess.run(job['argv'],cwd=OUT,env=local,stdout=f,stderr=subprocess.STDOUT,timeout=900)
                code=r.returncode
            except Exception as exc:code=None;error=repr(exc)
            result={**job,'returncode':code,'error':error,'seconds':time.monotonic()-t,'log':str(log),'log_sha256':sha(log)}
            if Path(job['object']).exists():result['object_sha256']=sha(job['object'])
            if Path(job['dependency']).exists():result['dependency_sha256']=sha(job['dependency'])
            return result
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            for future in concurrent.futures.as_completed([pool.submit(one,j) for j in commands]):
                result=future.result();receipts.append(result)
                with (OUT/'PROGRESS.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps({'index':result['index'],'source':result['source'],'code':result['returncode'],'seconds':result['seconds']})+'\n')
                print(json.dumps({'compiled':len(receipts),'total':145,'source':Path(result['source']).name,'code':result['returncode']}),flush=True)
        receipts.sort(key=lambda x:x['index']);write(OUT/'COMPILE_RECEIPTS.json',receipts)
        failed=[r for r in receipts if r['returncode']!=0]
        closure=dependency_audit(receipts,manifest);write(OUT/'DEPENDENCY_CLOSURE.json',closure)
        summary={'schema':'heterospec.e04.fresh-frozen-numerical-build.v1','started_utc':started,'compiler_workers':2,'translation_units':145,'fresh_translation_units':len(receipts),'reused_objects':0,'compile_failures':len(failed),'numerical_DLL_linked':False,'DLL_loaded':False,'model_requests':0,'target_draft_rows':0,'GPU_launches':0,'native_configure':'-6 NATIVE_BLOCKED','input_locks':len(held.handles),'freeze_metadata_sha256_before':freeze_digest}
        summary['dependency_closure']=closure['status']
        if not failed and closure['status']=='PASS':
            link=json.loads((FREEZE/'LINK_COMMAND.json').read_bytes());rsp=OUT/'LINK.rsp';rsp.write_text('\n'.join(subprocess.list2cmdline([x]) for x in link[1:]),encoding='utf8')
            t=time.monotonic()
            with (OUT/'link.log').open('xb') as f:r=subprocess.run([link[0],'@'+str(rsp)],cwd=OUT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
            write(OUT/'LINK.json',{'argv':link,'actual_argv':[link[0],'@'+str(rsp)],'response_sha256':sha(rsp),'returncode':r.returncode,'seconds':time.monotonic()-t,'log_sha256':sha(OUT/'link.log')})
            summary['link_returncode']=r.returncode;summary['numerical_DLL_linked']=r.returncode==0
            if (OUT/'bin/ggml-cuda.dll').exists():summary['DLL_sha256']=sha(OUT/'bin/ggml-cuda.dll');summary['DLL_bytes']=(OUT/'bin/ggml-cuda.dll').stat().st_size
        else:summary['failed_sources']=[r['source'] for r in failed]
        changes=[p for p,row in manifest['inputs'].items() if sha(p)!=row['sha256']]
        membership_after={str(p) for root in (SRC,TC,HERE/'inputs') for p in files(root)}
        summary['input_membership_added']=sorted(membership_after-membership_expected);summary['input_membership_removed']=sorted(membership_expected-membership_after)
        summary['freeze_metadata_sha256_after']=sha(FREEZE/'FREEZE.json')
        if summary['freeze_metadata_sha256_after']!=freeze_digest:changes.append(str(FREEZE/'FREEZE.json'))
        generated={str(p.relative_to(OUT)): {'sha256':sha(p),'bytes':xp(p).stat().st_size} for root in (OUT/'generated',OUT/'deps') for p in files(root)}
        write(OUT/'GENERATED_IDENTITIES.json',generated)
        summary.update({'completed_utc':now(),'wall_seconds':time.monotonic()-start,'input_posthash_changes':changes,'status':'LINKED_NOT_LOADED_NOT_QUALIFIED' if summary['numerical_DLL_linked'] and not changes and membership_after==membership_expected else 'FAILED_OR_INPUT_CHANGED'})
        write(OUT/'BUILD.json',summary);print(json.dumps(summary),flush=True)
    finally:
        held.release()

if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('prepare','finalize','build'):raise SystemExit('use prepare, finalize or build')
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='finalize':finalize()
    else:runbuild()
