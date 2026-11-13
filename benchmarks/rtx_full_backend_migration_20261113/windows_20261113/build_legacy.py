from pathlib import Path
import subprocess,json,shutil,hashlib,time,sys
p=Path(__file__).resolve().parent;study=p.parent;old=study/'repo/work/native-original-v4';out=p/(sys.argv[1] if len(sys.argv)>1 else 'build-R');out.mkdir(exist_ok=False);bin=out/'bin';bin.mkdir()
for name in ['native_worker.cpp','native_reference.cpp']:shutil.copy2(p/name,out/name)
zig=Path('D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe');core=old/'core';src=old/'source';libs=[core/'src/libllama.a',core/'ggml/src/ggml.a',core/'ggml/src/ggml-base.a',core/'vendor/hash/libvendor-hash.a'];results=[]
for stem,name in [('native_worker','rtx244_worker'),('native_reference','rtx244_reference')]:
 cmd=[str(zig),'c++','-std=c++17','-O3','-DNDEBUG','-DHS_LEGACY_R=1','-DGGML_BACKEND_DL','-D_CRT_SECURE_NO_WARNINGS','-I'+str(src/'include'),'-I'+str(src/'ggml/include'),'-I'+str(src/'vendor'),str(p/(stem+'.cpp')),*[str(x) for x in libs],'-lpsapi','-lws2_32','-lbcrypt','-o',str(bin/(name+'.exe'))]
 started=time.monotonic();cp=subprocess.run(cmd,capture_output=True,timeout=300,creationflags=0x08000000);(out/(name+'.stdout.log')).write_bytes(cp.stdout);(out/(name+'.stderr.log')).write_bytes(cp.stderr);results.append(dict(argv=cmd,returncode=cp.returncode,seconds=time.monotonic()-started));print(json.dumps(results[-1]),flush=True)
 if cp.returncode:break
manifest=json.loads(Path('D:/rtx192-review-v2/R-Qwen/BUILD.json').read_bytes())['modules'];copied=[]
if all(r['returncode']==0 for r in results):
 for name,h in manifest.items():
  q=Path('D:/rtx192-review-v2/R-Qwen/bin')/name;actual=hashlib.sha256(q.read_bytes()).hexdigest();assert actual==h,name;shutil.copy2(q,bin/name);copied.append(dict(name=name,sha256=h))
(out/'BUILD.json').write_text(json.dumps(dict(stages=results,restored_core=str(old),unchanged_static_libraries=[dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest()) for q in libs],unchanged_runtime=copied,model_loads=0,CUDA_initializations=0),indent=2),encoding='utf8')
