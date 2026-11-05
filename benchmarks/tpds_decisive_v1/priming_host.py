"""Qualify the exact cold-load, immediate warmup, resident-reset timing history."""
from native_adapter import *
from active_kv import parse
from common import digest,check_blob
from qualify_host import QUAL
def check_clean(native,case,names):
    capture=json.loads((case/'candidate/capture.json').read_bytes());states=capture['states'];last=states[-1]
    bank=json.loads((case/'bank/capture.json').read_bytes());ref=next(x for x in bank['prefixes'] if x['prefix']==last['prefix'])
    profile=json.loads((case/'profile.json').read_bytes());expected=json.loads((case/'candidate-row.json').read_bytes())['endpoint'];rows=[]
    for name in names:
        r=json.loads((native/(name+'.json')).read_bytes());assert r['endpoint']==expected
        path=native/name/'target/state/final-clean';raw=(path/'sequence.bin').read_bytes();can,scope=parse(raw,list(range(len(last['prefix']))),profile)
        assert __import__('hashlib').sha256(can).hexdigest()==ref['active_kv']['sha256'];assert sha(path/'frontier.f32')==ref['frontier']['sha256']
        rows.append(dict(record=name,endpoint_equal=True,active_kv_equal=True,frontier_equal=True,service_s=r['service_seconds']))
    return rows
def main():
    for ix in range(4):
        suffix='' if ix==0 else '-root'+str(ix)
        for arm in ('M','D1','D2','D4'):
            case=QUAL/(arm+suffix);assert json.loads((case/'QUALIFICATION.json').read_bytes())['clean_final_state_and_frontier_match']
            out=execute(draft_job('priming-v3-'+arm+'-root'+str(ix),arm,('warmup','measure'),ix))
            rows=check_clean(out/'native',case,('warmup','measure'));put(out/'PRIMING_QUALIFICATION.json',dict(rows=rows,independent_bank_sha256=sha(case/'bank/capture.json'),lifecycle='fresh model load and original four resident pools; immediate same-arm warmup then resident reset; both final active states/frontiers independently matched'))
            print('priming qualified',ix,arm,flush=True)
if __name__=='__main__':main()
