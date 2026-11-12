from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
p=Path('C:/Users/ASUS/.codex/.codex-global-state.json')
d=json.loads(p.read_bytes())
needle='af436df989570ad882db65bd8a4b265b9e8cfdae'
found=[]
def walk(v,path):
    if isinstance(v,dict):
        for k,x in v.items():walk(x,path+[k])
    elif isinstance(v,list):
        for i,x in enumerate(v):walk(x,path+[i])
    elif isinstance(v,str) and needle in v:
        i=v.index(needle);found.append({'key_path':path,'bytes':len(v.encode()),'excerpt':v[max(0,i-180):i+len(needle)+300],'full':v})
walk(d,[])
(HERE/'private/GLOBAL_MATCHES.json').write_text(json.dumps(found,indent=2),encoding='utf8')
print(json.dumps([{k:v for k,v in x.items() if k!='full'} for x in found],ensure_ascii=True,indent=2))
for key in ('client-thread-bindings-v1','thread-descriptions-v1','draft-thread-identities-v1','thread-user-activity-times-v1'):
    val=d.get('electron-persisted-atom-state',{}).get(key)
    if isinstance(val,dict):
        matches={k:v for k,v in val.items() if '6af43373' in k or 'HeteroSpec' in json.dumps(v)}
        print(json.dumps({'key':key,'matches':matches},ensure_ascii=True,indent=2))
