from pathlib import Path
import hashlib,json,os,subprocess,time

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'diagnostic-v1'
OUT.mkdir(exist_ok=False)
ZIG=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx221-round1-20261112/request/compiler_copy/zig.exe')
header=ROOT/'request/timeline.hpp'
raw=header.read_bytes()
record={'timeline':{'path':str(header),'bytes':len(raw),'prefix_hex':raw[:48].hex(),'sha256':hashlib.sha256(raw).hexdigest(),'UTF8_roundtrip':raw.decode('utf8').encode()==raw,'NUL_count':raw.count(b'\0')},'commands':[]}
(OUT/'minimal.cpp').write_text('int value(){return 17;}\n',encoding='utf8')
env=os.environ.copy();env.update(ZIG_LIB_DIR=str(ZIG.parent/'lib'),ZIG_GLOBAL_CACHE_DIR=str(OUT/'global-cache'),ZIG_LOCAL_CACHE_DIR=str(OUT/'local-cache'),TEMP=str(OUT/'temp'),TMP=str(OUT/'temp'))
(OUT/'temp').mkdir()
for label,args,input_data in [
 ('version',[str(ZIG),'version'],None),
 ('help',[str(ZIG),'--help'],None),
 ('file',[str(ZIG),'c++','-std=c++17','-c',str(OUT/'minimal.cpp'),'-o',str(OUT/'minimal.obj')],None),
 ('stdin',[str(ZIG),'c++','-std=c++17','-x','c++','-','-c','-o',str(OUT/'stdin.obj')],b'int value(){return 17;}\n'),
 ('clang',[str(ZIG),'clang','-std=c++17','-c',str(OUT/'minimal.cpp'),'-o',str(OUT/'clang.obj')],None),
 ]:
    before=time.monotonic();p=subprocess.run(args,cwd=OUT,env=env,input=input_data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
    (OUT/(label+'.log')).write_bytes(p.stdout)
    record['commands'].append({'label':label,'argv':args,'returncode':p.returncode,'seconds':time.monotonic()-before,'stdout':p.stdout.decode('utf8',errors='replace')})
(OUT/'DIAGNOSIS.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(record,indent=2))
