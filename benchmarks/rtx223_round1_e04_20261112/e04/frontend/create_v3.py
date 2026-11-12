from pathlib import Path
import json
p=Path(__file__).resolve().parent
s=(p/'frozen_build_v2.py').read_text()
replacements=[
    ("def prepare(version='v2'", "def prepare(version='v3'"),
    ('if path.is_relative_to(run):continue','if path.is_relative_to(run) or path.is_relative_to(tool):continue'),
    ('fresh v2 complete owned-copy','fresh v3 complete owned-copy'),
    ('frozen_build_v2.py','frozen_build_v3.py'),
    ("default='v2'","default='v3'"),
    ("obj={'path':info['object'],'bytes':Path(info['object']).stat().st_size,'sha256':sha(info['object'])}","obj=snapshot([Path(info['object'])])[0]"),
]
for old,new in replacements:
    if old not in s:raise RuntimeError('missing expected source anchor: '+old)
    s=s.replace(old,new)
with (p/'frozen_build_v3.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
with (p/'run-v2/PROVISIONAL_ONLY.json').open('x',encoding='utf8',newline='\n') as f:
    json.dump({'status':'PREPARE_FAILED_BEFORE_FREEZE','reason':'reused owned toolchain was wrongly treated as external dependency; strict initial scan retained','codegen_started':False,'GPU_launches':0,'next_version':'v3','other_prebuild_repair':'generated object snapshot now includes mtime_ns'},f,indent=2)
