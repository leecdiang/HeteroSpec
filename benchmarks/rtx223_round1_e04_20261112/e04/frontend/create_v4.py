from pathlib import Path
import json
p=Path(__file__).resolve().parent
s=(p/'frozen_build_v3.py').read_text()
replacements=[
    ("def prepare(version='v3'", "def prepare(version='v4'"),
    ('fresh v3 complete owned-copy','fresh v4 complete owned-copy'),
    ('frozen_build_v3.py','frozen_build_v4.py'),
    ('dep_witness_v2','dep_witness_v3'),
    ("default='v3'","default='v4'"),
]
for old,new in replacements:
    if old not in s:raise RuntimeError('missing expected source anchor: '+old)
    s=s.replace(old,new)
with (p/'frozen_build_v4.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
d=(p/'dep_witness_v2.py').read_text()
old="    lines=[line for line in lines if '-cc1' in line];need(len(lines)==1,'one actual cc1 invocation required')"
new="    # Clang -v also prints its version with a '-cc1' token; this exact diagnostic is not an invocation.\n    lines=[line for line in lines if '-cc1' in line and not (len(line)>=3 and line[:3]==['clang','-cc1','version'])]\n    need(len(lines)==1 and len(lines[0])>2 and lines[0][1]=='-cc1','one actual cc1 invocation required')"
if old not in d:raise RuntimeError('CPU invocation anchor missing')
d=d.replace(old,new).replace('    return values\n','    return [[k,v] for k,v in values]\n')
with (p/'dep_witness_v3.py').open('x',encoding='utf8',newline='\n') as f:f.write(d)
with (p/'run-v3/FAILED_BUILD.json').open('x',encoding='utf8',newline='\n') as f:
    json.dump({'status':'FAILED_AFTER_LOOP4_COMPILE_BEFORE_LINK','reason':'actual -v trace includes clang -cc1 version diagnostic; strict parser counted it as second invocation','additional_prevented_bug':'tuple/list serialization mismatch repaired in v4 parser','freeze_retained':True,'native_requests':0,'GPU_launches':0,'DLL_loads':0,'worker_EXE_runs':0,'next_version':'v4'},f,indent=2)
