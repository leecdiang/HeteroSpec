"""Read-only, fail-closed full-byte and state comparison to PR134 references."""
from pathlib import Path
import argparse, hashlib, json
ENDPOINT=['ids','eog','length','terminal_id','stop_reason']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(ok,msg):
    if not ok:raise ValueError(msg)
def audit(actual,reference):
    a=read(actual/'result.json');r=read(reference/'result.json')
    check(a['status']==r['status']=='QUALIFICATION_PASS','Qualification status')
    check(a['normal_cleanup_returned'] is True,'Cleanup')
    check(len(a['requests'])==len(r['requests'])==3,'Request count')
    rows=[]
    for i,(new,old) in enumerate(zip(a['requests'],r['requests'])):
        for key in ENDPOINT+['cycles','arm','input_id','target_calls','draft_calls']:
            check(new[key]==old[key],f'Historical {key} mismatch for arm {i}')
        check(new['actual_signatures']==old['actual_signatures'],f'Historical descriptors mismatch for arm {i}')
        for key in ENDPOINT:check(new[key]==a['requests'][0][key],f'R endpoint {key}')
        if i==2:check(new['cycles']==a['requests'][1]['cycles'],'PQ QB complete state')
        an=actual/f'qual-{i}';rn=reference/f'qual-{i}'
        files=sorted(p.relative_to(an).as_posix() for p in an.rglob('*.f32'))
        expected=sorted(p.relative_to(rn).as_posix() for p in rn.rglob('*.f32'))
        check(files==expected and bool(files),'Raw file inventory')
        for f in files:check((an/f).read_bytes()==(rn/f).read_bytes(),'Historical full logits '+f)
        if i==2:
            for f in files:check((an/f).read_bytes()==(actual/'qual-1'/f).read_bytes(),'PQ QB full logits '+f)
        decode_files=sorted(p.name for p in (an/'target').glob('decode-*.json'))
        check(decode_files==sorted(p.name for p in (rn/'target').glob('decode-*.json')),'Decode capture inventory')
        for f in decode_files:check(read(an/'target'/f)==read(rn/'target'/f),'Historical per-decode geometry '+f)
        layers=set();shapes=set()
        for j in new['actual_signatures']:
            check('B570' in j['device'],'Device placement')
            if j['name'].startswith('hs_qb_qk'):
                check(j['ne'][0] in (256,512) and j['ne'][1:]==[1,32,2],'Natural q2 shape')
                check(j['sources'][0]['ne']==[128,j['ne'][0],8,1],'GQA 32/8')
                layers.add(int(j['name'].split('-')[-1]));shapes.add(tuple(j['ne']))
        if i==2:check(layers==set(range(36)),'All 36 target layers')
        rows.append({'arm':new['arm'],'input':new['input_id'],'historical_full_vectors':len(files),'output_tokens':new['length'],'stop_reason':new['stop_reason'],'cycles':len(new['cycles']),'natural_q2_layers':len(layers),'shapes':sorted(shapes)})
    return {'status':'HISTORICAL_REQUEST_REPLAY_PASS','actual':str(actual),'reference':str(reference),'actual_result_sha256':sha(actual/'result.json'),'reference_result_sha256':sha(reference/'result.json'),'rows':rows,'full_vector_count':sum(x['historical_full_vectors'] for x in rows),'cost_claim':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--actual',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    check(not a.out.exists(),'Existing audit receipt')
    try:r=audit(a.actual,a.reference)
    except Exception as e:
        r={'status':'FAILED','error':str(e)};a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');raise
    a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))
if __name__=='__main__':main()
