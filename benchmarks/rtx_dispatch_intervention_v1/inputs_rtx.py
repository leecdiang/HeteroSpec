"""CPU-only exact logical-to-physical strided materialization, no GPU imports."""
import copy,itertools,struct,time,os
from pathlib import Path
from common import V,load,save,sha
ROLES=['Q','K','V','mask']
def span(m):return (2 if m['type']==1 else 4)+sum((a-1)*b for a,b in zip(m['ne'],m['nb']))
def offset(m,ix):return sum(a*b for a,b in zip(ix,m['nb']))
def materialize(src,sm,dm,role):
    word=2 if sm['type']==1 else 4;out=bytearray(span(dm))
    if role=='mask':out[:]=struct.pack('<f',float('-inf'))*(len(out)//4)
    for rev in itertools.product(*(range(n) for n in reversed(sm['ne']))):
        ix=rev[::-1];a=offset(sm,ix);b=offset(dm,ix);out[b:b+word]=src[a:a+word]
    return bytes(out)
def verify(src,sm,dst,dm,role):
    assert len(src)==span(sm) and len(dst)==span(dm)
    word=2 if sm['type']==1 else 4;checked=padding=0
    for rev in itertools.product(*(range(n) for n in reversed(dm['ne']))):
        ix=rev[::-1];b=offset(dm,ix)
        if all(i<n for i,n in zip(ix,sm['ne'])):
            a=offset(sm,ix);assert dst[b:b+word]==src[a:a+word],'logical word mutation';checked+=1
        else:
            assert dst[b:b+word]==(struct.pack('<f',float('-inf')) if role=='mask' else bytes(word)),'padding';padding+=1
    return checked,padding

def prepare():
    r=Path(load(V/'LOCAL_RUN.json')['root']);parent=Path('D:/hs122-5e483f69-dac1-41a4-a046-14401910e6e5');plan=load(V/'PLAN.json');save(r/'plan.json',plan);rows={};provenance=[]
    for c in plan['cells']:
        cid=c['id'];parentid=f"q2-k{c['logical']}-v{c['value']}" if c['panel']=='B0' else f"q{c['q']}-k256-v{c['value']}"
        srcroot=parent/'inputs'/parentid;original=load(srcroot/'snapshot.json')
        for ai,arm in enumerate(c['arms']):
            if ai==1:continue
            key=cid+'/'+arm['name'];dest=r/'inputs'/cid/arm['name'];dest.mkdir(parents=True);m=copy.deepcopy(original);S=arm['physical']
            if c['panel']=='B0':
                m['K']['ne'][1]=S;m['K']['nb']=[2,2048,256,128*S*8*2]
                m['V']['ne'][0]=S;m['V']['nb']=[2,2*S,2*S*128,2*S*128*8]
                m['mask']['ne'][0]=S;m['mask']['nb']=[4,S*4,S*c['q']*4,S*c['q']*4]
            if arm['storage']=='compact':m['Q']['nb']=[4,128*4,128*c['q']*4,128*c['q']*32*4]
            checks={};start=time.perf_counter()
            for role in ROLES:
                m[role]['bytes']=span(m[role]);data=materialize((srcroot/(role+'.bin')).read_bytes(),original[role],m[role],role)
                checks[role]=verify((srcroot/(role+'.bin')).read_bytes(),original[role],data,m[role],role)
                (dest/(role+'.bin')).write_bytes(data)
            save(dest/'snapshot.json',m)
            row=dict(id=key,case_id=key,root=str(dest),q=c['q'],logical=c['logical'],physical=S,storage=arm['storage'],panel=c['panel'],cell=cid,arm=arm['name'],realization=c['value'],metadata=m,logical_root=str(srcroot),layouts=[arm['layout']],references={arm['layout']:dict(path=str(r/'references'/ (cid+'.bin')),sha256=None)},producer_source=str(r/'inputs'/cid/'QB_A'/'Q.bin') if c['panel']=='T0' else None)
            row['inputs']=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in dest.iterdir()]
            rows[key]=row;provenance.append(dict(case=key,parent=parentid,parent_files={role:sha(srcroot/(role+'.bin')) for role in ROLES},logical_words_and_padding=checks,CPU_materialization_seconds=time.perf_counter()-start))
        base=rows[cid+'/'+c['arms'][0]['name']];serial=[]
        for j in range(c['q']):
            old=srcroot/f'serial{j}';new=r/'serial'/cid/str(j);new.mkdir(parents=True)
            for n in ['Q.bin','K.bin','V.bin','mask.bin','snapshot.json']:
                os.link(old/n,new/n);assert sha(old/n)==sha(new/n)
            one=copy.deepcopy(base);one.update(id=cid+f'/serial{j}',q=1,root=str(new),physical=c['logical'],metadata=load(new/'snapshot.json'),inputs=[dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in new.iterdir()],layouts=['PQ']);serial.append(one)
        save(r/'serial'/cid/'INDEX.json',serial)
    save(r/'INPUTS.json',rows);save(r/'INPUT_PROVENANCE.json',dict(parent_closed_sha256=sha(parent/'GPU_EXECUTION_CLOSED.json'),parent_index_sha256=sha(parent/'INPUTS.json'),old_outputs_imported=False,rows=provenance,GPU_calls=0))
if __name__=='__main__':prepare()
