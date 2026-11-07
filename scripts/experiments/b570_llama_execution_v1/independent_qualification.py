"""Standalone raw reconstruction; imports no study audit/design/transaction code."""
from pathlib import Path
from array import array
import argparse,hashlib,json,math,sys

def require(ok,msg):
    if not ok:raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def endpoint(r):
    require(all(type(t)is int and 0<=t<128256 for t in r['ids']) and all(type(e)is bool for e in r['eog']),'token/EOG types')
    require(len(r['ids'])==len(r['eog'])==r['length'] and 1<=r['length']<=128,'length')
    require(not any(r['eog'][:-1]) and (r['eog'][-1] or r['length']==128),'terminal extent')
    require(r['terminal_id']==r['ids'][-1] and r['stop_reason']==('EOG' if r['eog'][-1] else 'CAP'),'terminal identity')
    return {k:r[k] for k in ('ids','eog','length','terminal_id','stop_reason')}
def transactions(r):
    mapping={0:'initial'};expected={'target/initial.f32':r['ids'][0]}
    if not r['slot']['arm'].startswith('C_'):
        require(not r['cycles'],'ordinary transactions')
        for i,t in enumerate(r['ids'][1:],1):mapping[i]=f'ordinary-{i}';expected[f'target/ordinary-{i}.f32']=t
        return mapping,expected
    emitted=[r['ids'][0]];base=len(r['prompt_ids'])
    for ci,c in enumerate(r['cycles']):
        require(c['cycle']==ci and c['base']==base and c['output_begin']==len(emitted),'actual cycle coordinates')
        proposals=c['proposals'];decisions=c['decisions'];require(len(proposals)==3 and len(decisions)==4 and c['verify_ids']==[emitted[-1]]+proposals,'pending/proposals')
        for j,t in enumerate(proposals):expected[f'draft/proposal-{ci}-{j}.f32']=t
        for j,t in enumerate(decisions):expected[f'target/verify-{ci}-{j}.f32']=t
        accepted=0;part=[];bonus=False
        for j in range(4):
            if j==3:bonus=True
            elif decisions[j]==proposals[j]:accepted+=1
            part.append(decisions[j]);index=len(emitted)+len(part)-1
            require(index<r['length'],'transaction beyond endpoint')
            if r['eog'][index] or index==127 or j<3 and decisions[j]!=proposals[j]:break
        require(c['accepted']==accepted and c['bonus']==bonus and c['emitted']==part,'acceptance/correction/bonus')
        for j,t in enumerate(part):mapping[len(emitted)]=f'verify-{ci}-{j}';emitted.append(t)
        base+=1+accepted
        require(c['keep']==base and c['target_kv_max']==c['draft_kv_max']==base-1,'retained KV ownership')
    require(emitted==r['ids'],'full reconstructed output');return mapping,expected
def record(path):
    r=read(path);ep=endpoint(r);mapping,expected=transactions(r);slot=r['slot'];vectors={}
    require(slot['input']['id']==r['input_id'] and slot['input']['prompt_ids']==r['prompt_ids'],'input binding')
    require(not r['diagnostic'] and not slot.get('trace',False) and slot.get('probe_cycle',-1)<0,'diagnostic exclusion')
    if slot['observer']=='heavy':
        root=Path(path).with_suffix('');actual={p.relative_to(root).as_posix():p for role in ('target','draft') for p in (root/role).glob('*.f32')}
        require(set(actual)==set(expected),'full vector inventory')
        for name,p in actual.items():
            b=p.read_bytes();require(len(b)==128256*4,'complete vocabulary');v=array('f');v.frombytes(b)
            if sys.byteorder!='little':v.byteswap()
            require(all(math.isfinite(x) for x in v),'finite vocabulary');require(max(range(len(v)),key=v.__getitem__)==expected[name],'independent saved argmax');vectors[name]=hashlib.sha256(b).hexdigest()
        require((root/'target_final.state').is_file(),'target state missing')
        if slot['arm'].startswith('C_'):require((root/'draft_final.state').is_file(),'draft state missing')
        require(r['geometry'] and all(g.get('scheduler_backend') for g in r['geometry']),'actual scheduler evidence')
        if slot['arm']!='R':
            prefix='hs_qb_qk-' if slot['arm'].endswith('QB') else 'hs_pq_qk-';nodes=[g for g in r['geometry'] if g['name'].startswith(prefix)]
            require({int(g['name'].rsplit('-',1)[1]) for g in nodes}==set(range(32)),'all layer transform evidence')
            for g in nodes:
                n,q,h,b=g['ne'];require(n in (256,512,768,1024) and q==1 and h==32 and (2<=b<=4 if slot['arm'].endswith('QB') else b==1),'admitted actual query geometry')
    r.pop('geometry',None)
    return {'record':r,'endpoint':ep,'mapping':mapping,'vectors':vectors,'record_sha256':sha(path)}
def audit(epoch,panel,out,development=False):
    epoch=Path(epoch);inputs=read(panel);units=('baseline-oracle','baseline-candidate') if development else ('confirm-oracle','confirm-candidate');tables=[];receipts=[]
    for unit in units:
        path=epoch/'units'/unit;receipt=read(path/'RECEIPT.json');supervisor=read(path/'SUPERVISOR.json');slots=read(path/'SLOTS.json');native=read(path/'native/result.json')
        require(receipt['success'] and supervisor['status']=='complete' and supervisor['job_accounting']['active_processes']==0 and native['normal_cleanup_returned'],'supervisor cleanup')
        require(len(native['records'])==len(slots)==receipt['completed_model_requests'],'complete request accounting');table={}
        for slot in slots:
            p=path/'native'/(slot['id']+'.json');a=record(p);require(a['record']['slot']==slot,'schedule identity');key=(slot['input']['id'],slot['arm'],slot['observer']);require(key not in table,'duplicate cell');table[key]=a
        tables.append(table);receipts.append({'unit':unit,'supervisor_sha256':sha(path/'SUPERVISOR.json'),'receipt_sha256':sha(path/'RECEIPT.json')})
    original,candidate=tables;ids={x['id'] for x in inputs};arms=('R','M_PQ','M_QB','C_PQ','C_QB');obs=('off','heavy')
    require(set(original)=={(i,'R',o) for i in ids for o in obs} and set(candidate)=={(i,a,o) for i in ids for a in arms for o in obs},'full rectangular matrix')
    cells=[]
    for i in sorted(ids):
        ref=original[i,'R','heavy'];require(ref['endpoint']==original[i,'R','off']['endpoint'],'reference observer')
        for arm in arms:
            heavy=candidate[i,arm,'heavy'];off=candidate[i,arm,'off'];require(heavy['endpoint']==off['endpoint']==ref['endpoint'] and heavy['record']['cycles']==off['record']['cycles'],'endpoint/observer correspondence')
            committed=[]
            for index,key in heavy['mapping'].items():
                expected='initial' if index==0 else f'ordinary-{index}';require(heavy['vectors']['target/'+key+'.f32']==ref['vectors']['target/'+expected+'.f32'],'committed scalar-reference full vector difference')
                committed.append(heavy['vectors']['target/'+key+'.f32'])
            cells.append({'input_id':i,'arm':arm,'record_sha256':heavy['record_sha256'],'saved_vectors':len(heavy['vectors']),'committed_vectors':len(committed),'complete_scalar_vectors_equal':True})
        for stem in ('M_','C_'):
            pq=candidate[i,stem+'PQ','heavy'];qb=candidate[i,stem+'QB','heavy'];require(pq['vectors']==qb['vectors'] and pq['record']['cycles']==qb['record']['cycles'],'full PQ/QB correspondence including rejected rows')
    save(out,{'status':'INDEPENDENT_COMPLETE_QUALIFICATION_PASS','inputs':len(ids),'model_requests':len(original)+len(candidate),'saved_vectors':sum(len(x['vectors']) for t in tables for x in t.values()),'committed_candidate_vectors':sum(x['committed_vectors'] for x in cells),'panel_sha256':sha(panel),'cells':cells,'supervisors':receipts,'implementation':'Standalone standard-library reconstruction; no imports from study common/audit/design/cycle functions'})
    print('INDEPENDENT_COMPLETE_QUALIFICATION_PASS',len(ids),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--epoch',required=True);p.add_argument('--panel',required=True);p.add_argument('--out',required=True);p.add_argument('--development',action='store_true');a=p.parse_args();audit(a.epoch,a.panel,a.out,a.development)
