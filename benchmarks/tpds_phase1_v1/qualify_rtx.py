"""Finite original-R qualification of actual review-v2 native combinations."""
from host_rtx import *
import numpy as np
import qualification as q
from active_kv import parse
from normalize import trace_from_row
from storage import read_bytes as saved_bytes
ARMS={'W_L4':('loop4','SIMPLE'),'W_P':('packed','SIMPLE'),'L_L4':('loop4','LOCAL'),'L_P':('packed','LOCAL')}
REFERENCE_CHUNKS={}
class RelocatedHistoricalChunks(q.HistoricalChunks):
    def read(self,container,spec):
        cache=ROOT/'reference-payloads'/spec['sha256'];cache.parent.mkdir(exist_ok=True)
        if cache.exists():raw=cache.read_bytes()
        elif (container/spec['path']).exists():raw=(container/spec['path']).read_bytes()
        else:
            row=self.rows[spec['sha256']];parts=[]
            for h in row['chunks']:
                options=[self.store/'chunks'/h[:2]/h,Path('D:/rtx184-D-chunks')/h[:2]/h,Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx184-O-chunks')/h[:2]/h]
                p=next((p for p in options if p.exists()),None);assert p is not None,('Retained missing reference chunk',h)
                data=__import__('zlib').decompress(p.read_bytes());assert hashlib.sha256(data).hexdigest()==h;parts.append(data);REFERENCE_CHUNKS[h]=str(p)
            raw=b''.join(parts)
        assert len(raw)==spec['bytes'] and hashlib.sha256(raw).hexdigest()==spec['sha256']
        if not cache.exists():
            with cache.open('xb') as f:f.write(raw)
        return raw
q.HistoricalChunks=RelocatedHistoricalChunks

def roots(family):return read(P190/(family+'-EXPOSED-ROOTS.json'))['inputs']
def dedup():
    pool=ROOT/'evidence-cas';pool.mkdir(exist_ok=True);seen={}
    for p in (ROOT/'runs').rglob('*'):
        if not p.is_file() or p.suffix not in ('.bin','.f32'):continue
        st=p.stat();identity=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
        if identity not in seen:seen[identity]=sha(p)
        h=seen[identity];dest=pool/h[:2]/h;dest.parent.mkdir(exist_ok=True)
        if not dest.exists():os.link(p,dest)
        elif not os.path.samefile(p,dest):
            assert sha(dest)==h;temporary=p.with_name(p.name+'.verified-dedup');os.link(dest,temporary);os.replace(temporary,p)
def finished(label,recipe,family,payload,reservation):
    out=ROOT/'runs'/label
    if out.exists():
        assert (out/'COMPLETE.json').exists(),'Retain failure, diagnose and use a distinct attempt/version'
        assert read(out/'job.json')==dict(MODEL[family],**payload)
        name=recipe if recipe.startswith('R-') else f'runtime-v{VERSION}-'+recipe
        assert read(out/'binding.json')['exe']==sha(ROOT/name/'bin/worker.exe')
        return out
    out=execute(label,recipe,family,payload,reservation);dedup();return out
def teacher(label,name,family,payload,reservation,output=None):
    assert output is None
    return finished(label,name,family,payload,reservation)
q.ROOT=ROOT;q.roots=roots;q.finished=teacher;q.dedup=dedup
q.VERSIONS={'R-Qwen':'R-Qwen','R-Smol':'R-Smol'}

class Bank(q.Bank):
    def __init__(self,family,ix):
        super().__init__(family,ix,P190/'runs'/(family+'-old-free')/'native'/f'r{ix}-heavy')
        original=read(ROOT/('R-'+family)/'BUILD.json')
        # Same immutable independent R, not same-candidate qualification reuse.
        # These reference prefixes remain valid inputs to the new comparisons.
        for out in sorted((P190/'runs').glob(f'{family}-teacher-r{ix}-*')):
            if not (out/'COMPLETE.json').exists():continue
            assert read(out/'binding.json')['exe']==original['exe']
            for one in read(out/'job.json')['cases']:
                tape=sum((x['ids'] for x in one['forced']),[])
                for n in one['observe_positions']:
                    prefix=tuple(tape[:n]);directory=out/'native'/one['name']/'captures'/str(n)
                    if prefix in self.entries:assert (directory/'frontier.f32').read_bytes()==self.vector(prefix)
                    entry=self.entries.setdefault(prefix,{});entry['frontier_file']=str(directory/'frontier.f32')
                    if n in one['state_positions']:entry['sequence_file']=str(directory/'sequence.bin')

def tape(family):
    if family=='Qwen':
        j=read('D:/rtx184-runs/D-main-forced-10/job.json')['forced'];return j['prompt_ids']+j['paths'][0]['suffix']
    r=read(P190/'runs/Smol-old-free/native/r0-heavy/receipt.json');t=r['prompt_ids']+r['ids'];return (t*((800+len(t)-1)//len(t)))[:800]
def cases(family):
    t=tape(family);out=[]
    for width in (4,8,32):
        for relation in ('inside','crossing'):
            h=768-width if relation=='inside' else 767
            out.append(dict(name=f'q{width}-{relation}',forced=[dict(ids=t[:h],phase='PREFILL',all=False),dict(ids=t[h:h+width],phase='VERIFY',all=False)],observe_positions=[h,h+width],state_positions=[h+width]))
    return out
def matrix(family):
    cc=cases(family);payload=dict(lowering='SIMPLE',cases=cc);reserve=dict(requests=len(cc),token_rows=sum(sum(len(x['ids']) for x in c['forced']) for c in cc),operators=0)
    ref=finished(f'{family}-v2-matrix-R','R-'+family,family,payload,reserve)
    profile=q.profile(prior.native_fields(ref/'native/result.json',['model_structure']),family)
    for arm,(recipe,lowering) in ARMS.items():
        out=finished(f'{family}-v2-matrix-{arm}',recipe,family,dict(lowering=lowering,cases=cc),reserve);rows=[]
        for c in cc:
            for n in c['observe_positions']:
                a=out/'native'/c['name']/'captures'/str(n);b=ref/'native'/c['name']/'captures'/str(n)
                av=(a/'frontier.f32').read_bytes();bv=(b/'frontier.f32').read_bytes();row=dict(case=c['name'],prefix=n,requested_frontier_equal=av==bv,actual_sha256=hashlib.sha256(av).hexdigest(),reference_sha256=hashlib.sha256(bv).hexdigest())
                if av!=bv:
                    aa=np.frombuffer(av,dtype='<f4');bb=np.frombuffer(bv,dtype='<f4');i=int(np.flatnonzero(aa.view('u4')!=bb.view('u4'))[0]);row['first_difference']=dict(index=i,actual=float(aa[i]),reference=float(bb[i]))
                if n in c['state_positions']:row['active_KV_equal']=parse((a/'sequence.bin').read_bytes(),list(range(n)),profile)[0]==parse((b/'sequence.bin').read_bytes(),list(range(n)),profile)[0]
                rows.append(row)
        result=dict(reference=str(ref),candidate=str(out),family=family,arm=arm,rows=rows,passed=all(all(v for k,v in r.items() if k.endswith('_equal')) for r in rows),mask='last-only at every controlled wide append; original R remains scalar output reserve1',scope='All originally requested frontiers; complete active KV at each controlled append end')
        p=ROOT/f'{family}-v2-matrix-{arm}-QUALIFICATION.json'
        if not p.exists():put(p,result)
        assert result['passed'],'Retained original-R numerical mismatch'
        print(family,arm,'actual matrix qualification passed',flush=True)

def natural(family,arm,target_only=False,draft=False):
    recipe,lowering=ARMS[arm];name=f'{family}-v2-'+('target-only-' if target_only else 'matched-')+arm+('-D4' if draft else '-M')
    inputs=[dict(name=f'r{i}-{kind}',capture=kind=='heavy',input=row) for i,row in enumerate(roots(family)) for kind in ('heavy','clean')]
    payload=dict(lowering=lowering,residency='target_only' if target_only else 'matched',draft=draft,draft_width=4 if draft else 1,inputs=inputs)
    reserve=dict(requests=len(inputs),token_rows=sum(2*len(x['input']['prompt_ids'])+8*(x['input']['cap']-1) if draft else len(x['input']['prompt_ids'])+x['input']['cap']-1 for x in inputs),operators=0)
    out=finished(name,recipe,family,payload,reserve);rows=[]
    for ix,item in enumerate(roots(family)):
        base=out/'native'/f'r{ix}-heavy';r=read(base/'receipt.json');clean=read(out/'native'/f'r{ix}-clean/receipt.json');bank=Bank(family,ix);r['study_cap']=item['cap']
        _,d=trace_from_row(r,r['prompt_ids'],bank.meta['vocab'],bank.meta['eog_ids'],'rtx');teachers=bank.fill(r,d);vectors=[]
        for use in d['vector_uses']:
            key=use['key'];label='initial' if key=='initial' else ('verify-'+key[4:].replace('/','-') if draft else 'ordinary-'+str(int(key[4:].split('/')[0])+1))
            raw=(base/'target'/(label+'.f32')).read_bytes();expected=bank.vector(use['prefix'])
            vectors.append(dict(key=key,prefix=len(use['prefix']),equal=raw==expected,actual_sha256=hashlib.sha256(raw).hexdigest(),reference_sha256=hashlib.sha256(expected).hexdigest()))
        selected=[('initial',d['states'][0]),('terminal',d['states'][-1])]+([('commit-0',d['states'][1])] if r['cycles'] else []);states=[]
        for key,s in selected:
            prefix=s['prefix'];p=base/'target/state'/key
            states.append(dict(key=key,prefix=len(prefix),active_KV_equal=parse((p/'sequence.bin').read_bytes(),list(range(len(prefix))),bank.p)[0]==bank.state(prefix),frontier_equal=(p/'frontier.f32').read_bytes()==bank.vector(prefix),next_pending=s['next_pending'],unmaterialized_suffix=s['unmaterialized_suffix'],terminal=s['terminal']))
        api=clean['observed_API_calls_within_service'];row=dict(root=item['id'],endpoint_equal=r['endpoint']==clean['endpoint']==bank.endpoint,independent_trace_valid=True,vectors=vectors,states=states,clean_API_calls=api,teacher_jobs=teachers)
        row['passed']=row['endpoint_equal'] and all(v==0 for v in api.values()) and all(v['equal'] for v in vectors) and all(s['active_KV_equal'] and s['frontier_equal'] for s in states);rows.append(row)
    result=dict(candidate=str(out),rows=rows,passed=all(r['passed'] for r in rows),original_R='PR190 immutable original executable/observer, existing free prefixes plus newly charged forced-R paths',finite_boundaries=['initial','first speculative commit if present','terminal'],all_requested_vectors_including_rejected_branches=True,real_clean_mode='counts without heavy observer',target_only=target_only,draft=draft)
    p=ROOT/(name+'-QUALIFICATION.json')
    if not p.exists():put(p,result)
    assert result['passed'],'Retained original-R natural/state mismatch'
    if REFERENCE_CHUNKS:
        p=ROOT/(name+'-REFERENCE-CHUNKS.json')
        if not p.exists():put(p,dict(verified_chunk_locations=REFERENCE_CHUNKS,complete_payload_hashes_checked=True,old_files_unchanged=True,source_reader_repair_only=True,new_native_model_requests=0))
    print(name,'actual full-vector/state qualification passed',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['matrix','natural']);p.add_argument('family');p.add_argument('--arm',choices=list(ARMS));p.add_argument('--target-only',action='store_true');p.add_argument('--draft',action='store_true');a=p.parse_args()
    if a.action=='matrix':matrix(a.family)
    else:natural(a.family,a.arm,a.target_only,a.draft)
