"""Import this host's real Ninja/Clang dependency and link reports into v2."""
from host_rtx import *
import ctypes,re
import build_freeze
NINJA='D:/HeteroSpec-PC/.venv-analysis/Scripts/ninja.exe'

def argv(text):
    n=ctypes.c_int();f=ctypes.windll.shell32.CommandLineToArgvW
    f.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];f.restype=ctypes.POINTER(ctypes.c_wchar_p)
    p=f(text,ctypes.byref(n));assert p
    try:return [p[i] for i in range(n.value)]
    finally:ctypes.windll.kernel32.LocalFree(p)
def resolved(p,base):
    p=Path(p);return (p if p.is_absolute() else base/p).resolve()

def response(recipe):
    core=ROOT/f'build-v{VERSION}'/recipe;p=core/'src/libllama.a';before=sha(p);backup=core/'src/libllama.before-response-retention.a'
    assert p.resolve().is_relative_to(ROOT.resolve()) and not backup.exists()
    p.rename(backup)
    command(core,'archive-response-retention',[NINJA,'-C',str(core),'-d','keeprsp','src/libllama.a'])
    after=sha(p)
    put(core/'ARCHIVE_RESPONSE_RETENTION.json',dict(original_archive_sha256=before,replayed_archive_sha256=after,byte_identical=before==after,original_archive_preserved=str(backup),native_runtime_bytes_unchanged=True,reason='Retain actual Ninja-generated response input using the same compiled objects and archive command. No numerical rebuild/replacement.'))
    assert before==after,'Archive identity changed; retain both, rebind/relink as a new candidate version'
    assert list(core.rglob('*.rsp'))

def dependencies(recipe):
    core=ROOT/f'build-v{VERSION}'/recipe;runtime=ROOT/f'runtime-v{VERSION}-{recipe}';dest=ROOT/'build-closure'/recipe;dest.mkdir(parents=True,exist_ok=False)
    depraw=subprocess.check_output([NINJA,'-C',str(core),'-t','deps'],text=True,encoding='utf8')
    cmds=subprocess.check_output([NINJA,'-C',str(core),'-t','commands','llama','vendor-hash'],text=True,encoding='utf8')
    (dest/'compiler-deps.ninja.txt').write_text(depraw,encoding='utf8');(dest/'executed-target-commands.txt').write_text(cmds,encoding='utf8')
    blocks={};current=None
    for line in depraw.splitlines():
        m=re.match(r'^(.+): #deps ',line)
        if m:current=str(resolved(m[1],core)).casefold();blocks[current]=[]
        elif line.startswith('    ') and current:blocks[current].append(str(resolved(line.strip(),core)))
    units=[];compile_commands=[];objects=[];archives=[]
    for line in cmds.splitlines():
        if ' -c ' not in line:continue
        a=argv(line);src=resolved(a[a.index('-c')+1],core);obj=resolved(a[a.index('-o')+1],core)
        assert obj.exists();deps=blocks[str(obj).casefold()];assert deps and str(src) in deps
        units.append(dict(source=str(src),dependencies=list(dict.fromkeys(deps))));compile_commands.append(dict(source=str(src),argv=a,working_directory=str(core),compiler_path=a[0]));objects.append(str(obj))
    raw=(runtime/'worker.d').read_text(encoding='utf8').replace('\\\n',' ').replace('\\\r\n',' ')
    body=re.split(r':\s+',raw,maxsplit=1)[1]
    deps=[str(resolved(x.replace('\\ ',' ').replace('\\#','#'),core)) for x in re.findall(r'(?:\\[ \t#]|[^\s])+',body)]
    worker=read(runtime/'worker.json');a=worker['argv'];src=str(resolved(a[a.index('-c')+1],core));assert src in deps
    units.append(dict(source=src,dependencies=list(dict.fromkeys(deps))));compile_commands.append(dict(source=src,argv=a,working_directory=worker['working_directory'],compiler_path=a[0]));objects.append(str(runtime/'worker.obj'))
    report=dict(source='compiler_depfile',original_reports=[str(dest/'compiler-deps.ninja.txt'),str(core/'.ninja_deps'),str(runtime/'worker.d')],units=units,explanation='Ninja deps log contains compiler -MD/-MF dependencies for every actually compiled target unit. Frontend uses its actual original Clang -MD report. Original reports and exact target commands are retained.')
    put(dest/'DEPENDENCIES.json',report);put(dest/'COMPILE_AND_LINK.json',dict(compile_commands=compile_commands,object_files=objects,original_target_commands=str(dest/'executed-target-commands.txt'),frontend_link=read(runtime/'link.json')))
    print(recipe,'real compiler closure:',len(units),'translation units',flush=True)

def freeze(recipe,qualification,runtime_attempt,label):
    core=ROOT/f'build-v{VERSION}'/recipe;runtime=ROOT/f'runtime-v{VERSION}-{recipe}';closure=ROOT/'build-closure'/recipe
    stage_native.snapshot(read(ROOT/'NATIVE_REVISION_2.json')['source_snapshot'])
    commands=read(closure/'COMPILE_AND_LINK.json');report=read(closure/'DEPENDENCIES.json');observed=read(Path(runtime_attempt)/'ACTUAL_MODULES.json')['modules_after']
    dest=ROOT/'freezes'/label;dest.mkdir(parents=True,exist_ok=False);files={};keys={}
    def add(p,role):
        p=Path(p).resolve();assert p.is_file(),p
        k=str(p).casefold()
        if k in keys:return keys[k]
        name='f-'+hashlib.sha256(k.encode()).hexdigest()[:24];keys[k]=name;files[name]=dict(path=str(p),role=role);return name
    def source_role(p):
        if p.name=='CMakeLists.txt' or p.suffix in ('.cmake','.in','.json','.cmd','.bat'):return 'build_config'
        return 'header' if p.suffix in ('.h','.hpp','.cuh','.inc') else 'source'
    configs=[];generated=[]
    for base in (ROOT/f'native-v{VERSION}'/'cores'/recipe,ROOT/f'native-v{VERSION}'/'frontend'):
        for p in sorted(base.rglob('*')):
            if p.is_file():
                # Upstream docs contain an unused Keynote .key presentation.
                # It stays hash-bound by the COMPLETE source snapshot; it is
                # not a compiler input and is not treated as a credential file.
                if p.suffix.lower() in ('.key','.pem') or p.name in ('.env','credentials'):continue
                role=source_role(p);key=add(p,role)
                if role=='build_config':configs.append(key)
    for unit in report['units']:
        add(unit['source'],'source')
        for p in unit['dependencies']:add(p,'header')
    report_id=add(closure/'DEPENDENCIES.json','dependency_report')
    for p in report['original_reports']:add(p,'dependency_report')
    add(closure/'executed-target-commands.txt','build_config');add(core/'compile_commands.json','build_config')
    configs.append(add(ROOT/'NATIVE_REVISION_2.json','build_config'))
    for p in core.rglob('*'):
        if p.is_file() and (p.suffix in ('.cmake','.rsp','.cmd') or p.name in ('CMakeCache.txt','build.ninja')):
            key=add(p,'response' if p.suffix=='.rsp' else 'build_config');configs.append(key)
        elif p.is_file() and p.suffix in ('.h','.hpp','.c','.cpp'):
            generated.append(add(p,'generated'))
    compiler=add(commands['compile_commands'][0]['compiler_path'],'toolchain')
    for p in (NINJA,read(core/'configure.json')['argv'][0]):add(p,'toolchain')
    for c in commands['compile_commands']:
        c['compiler']=add(c.pop('compiler_path'),'toolchain')
    inputs=[add(p,'link_input') for p in commands['object_files']]
    inputs += [add(p,'link_input') for p in [core/'src/libllama.a',core/'ggml/src/ggml.a',core/'ggml/src/ggml-base.a',core/'vendor/hash/libvendor-hash.a']]
    # Zig's real -v output exposes integrated lld and its implicit CRT/C++ inputs.
    verbose=(runtime/'link.log').read_text(encoding='utf8');lines=[x for x in verbose.splitlines() if x.startswith('lld-link ')];assert len(lines)==1
    lld=argv(lines[0])
    for x in lld[1:]:
        p=Path(x)
        if p.is_file() and p.suffix in ('.obj','.lib','.a'):inputs.append(add(p,'link_input'))
    link=commands['frontend_link'];links=[dict(argv=link['argv'],working_directory=link['working_directory'],linker=compiler,inputs=list(dict.fromkeys(inputs)),integrated_lld_argv=lld)]
    # Original archive invocations and the actual response inputs remain bound.
    for line in (closure/'executed-target-commands.txt').read_text(encoding='utf8').splitlines():
        if ' qc ' in line or ' ar ' in line:links.append(dict(argv=argv(line),working_directory=str(core),linker=compiler,inputs=list(dict.fromkeys(inputs))))
    for row in observed:add(row['path'],'executable' if Path(row['path']).suffix.lower()=='.exe' else 'runtime_module')
    module_report=dest/'ACTUAL_QUALIFIED_MODULES.json';put(module_report,dict(observed_after_qualification=True,modules=observed,source_attempt=str(runtime_attempt)))
    runtime_id=add(module_report,'runtime_report');add(qualification,'build_config');add(runtime/'BUILD.json','build_config')
    config=dict(schema='phase1.build-inputs.v2',phase='after_native_qualification_before_formal_timing',files=files,dependency_report=report_id,compile_commands=commands['compile_commands'],link_commands=links,generated_files=list(dict.fromkeys(generated)),build_configuration_files=list(dict.fromkeys(configs)),runtime_report=runtime_id,qualification_binding=str(qualification),build_environment={k:v for k,v in os.environ.items() if k in build_freeze.ENV_KEYS})
    # The compiler cache/temp roots are explicit argv/runtime paths; no secrets.
    config['build_environment'].update(ZIG_GLOBAL_CACHE_DIR=str(ROOT/'compiler-cache'),TEMP=str(ROOT/'temp'),TMP=str(ROOT/'temp'))
    put(dest/'BUILD_INPUTS.json',config);put(dest/'BUILD_FREEZE.json',build_freeze.capture(config))
    print('Frozen actual complete compiler/link/module closure',label,len(files),'files',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['response','dependencies','freeze']);p.add_argument('recipe');p.add_argument('--qualification');p.add_argument('--attempt');p.add_argument('--label');a=p.parse_args()
    if a.action=='response':response(a.recipe)
    elif a.action=='dependencies':dependencies(a.recipe)
    else:freeze(a.recipe,a.qualification,a.attempt,a.label)
