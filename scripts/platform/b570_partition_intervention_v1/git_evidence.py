"""Retain Git commit/tree/blob objects for offline checkpoint membership checks."""
import hashlib, json, subprocess
from pathlib import Path

PREFIXES=('benchmarks/b570_partition_intervention_v1/','scripts/platform/b570_partition_intervention_v1/')
def command(root,*args):return subprocess.check_output(['git',*args],cwd=root)
def trees(data):
    entries={};i=0
    while i<len(data):
        space=data.index(b' ',i);nul=data.index(b'\0',space)
        mode=data[i:space].decode();name=data[space+1:nul].decode('utf-8');oid=data[nul+1:nul+21].hex()
        entries[name]=(mode,oid);i=nul+21
    return entries

def export_proof(root,staging):
    root=Path(root);staging=Path(staging);out=staging/'provenance/git_objects';out.mkdir(parents=True,exist_ok=True)
    base=command(root,'rev-parse','origin/main').decode().strip()
    commits=command(root,'rev-list','--reverse',base+'..HEAD').decode().splitlines()
    objects={};records={}
    def retain(kind,oid):
        key=kind+':'+oid
        if key not in objects:
            data=command(root,'cat-file',kind,oid)
            assert hashlib.sha1(kind.encode()+b' '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid
            path=out/(kind+'-'+oid);path.write_bytes(data)
            objects[key]={'kind':kind,'oid':oid,'file':path.relative_to(staging).as_posix()}
        return (staging/objects[key]['file']).read_bytes()
    for oid in [base]+commits:
        raw=retain('commit',oid);lines=raw.decode().splitlines();tree=lines[0].split()[1]
        parents=[x.split()[1] for x in lines if x.startswith('parent ')]
        record={'tree':tree,'parents':parents,'files':{}};records[oid]=record
        if oid==base:continue
        names=command(root,'ls-tree','-r','--name-only',oid,'--',*PREFIXES).decode().splitlines()
        for name in names:
            current=tree;chain=[]
            for j,part in enumerate(name.split('/')):
                chain.append(current);entries=trees(retain('tree',current));mode,child=entries[part]
                if j==len(name.split('/'))-1:
                    data=retain('blob',child);record['files'][name]={'blob':child,'tree_chain':chain,'sha256':hashlib.sha256(data).hexdigest()}
                else:current=child
    proof={'base':base,'head':command(root,'rev-parse','HEAD').decode().strip(),'commits':records,'objects':objects,
        'limits':'Retained Git objects prove file membership and parent ancestry, not an independent wall-clock or server push timestamp.'}
    dest=staging/'provenance/GIT_CHECKPOINTS.json';dest.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')

def verify_proof(root):
    root=Path(root);file=root/'provenance/GIT_CHECKPOINTS.json'
    if not file.exists():return [] # live checkout uses its real Git below
    proof=json.loads(file.read_text(encoding='utf-8'));errors=[];data={}
    for key,o in proof['objects'].items():
        b=(root/o['file']).read_bytes();data[key]=b
        actual=hashlib.sha1(o['kind'].encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
        if actual!=o['oid']:errors.append('Git object hash '+key)
    def file_bytes(oid,name):
        tree=proof['commits'][oid]['tree']
        for j,part in enumerate(name.split('/')):
            mode,child=trees(data['tree:'+tree])[part]
            if j==len(name.split('/'))-1:return data['blob:'+child]
            tree=child
    for oid,c in proof['commits'].items():
        raw=data['commit:'+oid].decode();header=raw.split('\n\n',1)[0].splitlines()
        if header[0]!='tree '+c['tree']:errors.append('Git root tree '+oid)
        if [x.split()[1] for x in header if x.startswith('parent ')]!=c['parents']:errors.append('Git parents '+oid)
        for name,meta in c['files'].items():
            b=file_bytes(oid,name)
            if hashlib.sha256(b).hexdigest()!=meta['sha256']:errors.append('Git file membership '+oid+' '+name)
    def ancestor(a,b):
        pending=[b];seen=set()
        while pending:
            oid=pending.pop()
            if oid==a:return True
            if oid in seen:continue
            seen.add(oid);pending.extend(proof['commits'].get(oid,{}).get('parents',[]))
        return False
    p=root/'benchmarks/b570_partition_intervention_v1';q=json.loads((p/'TECHNICAL_QUALIFICATION.json').read_text(encoding='utf-8'))
    engineering=q['engineering_freeze_commit']
    name='benchmarks/b570_partition_intervention_v1/ENGINEERING_PLAN.md'
    if file_bytes(engineering,name)!=(root/name).read_bytes():errors.append('engineering freeze exact bytes')
    for start in (root/'artifacts/b570_partition_intervention_v1/raw/r0').glob('*/start.json'):
        row=json.loads(start.read_text(encoding='utf-8'))
        if not ancestor(engineering,row['study_head']):errors.append('engineering freeze ancestry '+str(start))
    execution=p/'FORMAL_EXECUTION.json'
    if execution.exists():
        e=json.loads(execution.read_text(encoding='utf-8'));freeze=e['freeze_commit'];name='benchmarks/b570_partition_intervention_v1/FORMAL_FREEZE.json'
        if file_bytes(freeze,name)!=(root/name).read_bytes():errors.append('formal freeze exact Git bytes')
        if not ancestor(engineering,freeze):errors.append('engineering/formal chain')
        for row in e['executions']:
            if not ancestor(freeze,row['study_head']):errors.append('formal freeze/run source ancestry')
    return errors
