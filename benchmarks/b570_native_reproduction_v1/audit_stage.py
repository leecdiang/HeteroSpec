"""Independent raw-byte replay audit with real-request causal-mask binding."""
from pathlib import Path
import argparse,hashlib,json,struct,math
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def check(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--replay',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();check(not a.out.exists(),'Existing audit receipt')
    req=read(a.request/'result.json');qb=req['requests'][2];cycle=qb['cycles'][0]
    check(qb['input_id']=='HumanEval/115' and qb['arm']=='QB','Capture input/arm')
    check(cycle['base']==349 and cycle['q_caller']==2,'First natural verification cycle')
    records=[]
    for key in ['Q','K','V','mask','qk','softmax','av','final']:
        meta=read(a.fixture/(key+'.json'));data=(a.fixture/(key+'.bin')).read_bytes()
        width={'f32':4,'f16':2}[meta['type']]
        span=width+sum((n-1)*s for n,s in zip(meta['ne'],meta['nb']))
        check(len(data)==meta['span_bytes']==span,'Physical span '+key)
        records.append({'name':key,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'ne':meta['ne'],'nb':meta['nb']})
    mask=read(a.fixture/'mask.json');raw=(a.fixture/'mask.bin').read_bytes()
    check(mask['ne']==[512,1,1,2],'Mask shape')
    visible=[]
    for q in range(2):
        vals=[struct.unpack_from('<f',raw,q*mask['nb'][3]+i*4)[0]for i in range(512)]
        count=cycle['base']+q+1
        check(all(v==0 for v in vals[:count]) and all(v==-math.inf for v in vals[count:]),'Causal visibility')
        visible.append(count)
    n=read(a.replay/'result.json');check(n['status']=='STAGE_REPLAY_PASS' and len(n['rows'])==4,'Replay status')
    comparisons=[]
    check({(x['q'],x['arm'])for x in n['rows']}=={(q,arm)for q in [1,2]for arm in ['PQ','QB']},'Replay coordinate inventory')
    for row in n['rows']:
        for stage in ['qk','softmax','av','final']:
            expected=(a.fixture/(stage+'.bin')).read_bytes();actual=(a.replay/(f"q{row['q']}-{row['arm']}-{stage}.bin")).read_bytes()
            expected=expected[:len(expected)//2] if row['q']==1 else expected
            check(actual==expected and bool(actual),'Stage byte mismatch')
            comparisons.append({'q':row['q'],'arm':row['arm'],'stage':stage,'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest()})
    out={'status':'REAL_STAGE_REPLAY_AUDIT_PASS','request':str(a.request),'fixture':str(a.fixture),'replay':str(a.replay),'provenance':'new capture, QB first VERIFY at layer0; q1 is first-query slice','input_id':qb['input_id'],'cycle':cycle,'visible_keys':visible,'records':records,'comparisons':comparisons,'comparisons_passed':len(comparisons),'performance_claim':False}
    a.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('PASS: 16 raw stage comparisons, visible keys',visible)
if __name__=='__main__':main()
