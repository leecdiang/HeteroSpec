import gzip,collections
from host import *
def prepare():
    p=ROOT/'oasst.messages.jsonl.gz';assert sha(p)=='2ff4aa8999c911ffec7972ddf70359f220b3da184b731f3649f68b1391e19341'
    with gzip.open(p,'rt',encoding='utf8') as f:rows=[json.loads(s) for s in f]
    byid={x['message_id']:x for x in rows}; paths=[];excluded=[]
    for row in rows:
        if row['role']!='prompter':continue
        chain=[];x=row;seen=set();reason=None
        while x:
            if x['message_id'] in seen:reason='cycle';break
            seen.add(x['message_id']);chain.append(x)
            parent=x.get('parent_id')
            if parent and parent not in byid:reason='missing_parent';break
            x=byid.get(parent)
        chain.reverse()
        if not reason:
            if len(chain)<3:reason='no_prior_assistant'
            elif any(x['lang']!='en' or x.get('deleted') or x.get('synthetic') for x in chain):reason='language_deleted_synthetic'
            elif any(x['role']!=('prompter' if i%2==0 else 'assistant') for i,x in enumerate(chain)):reason='not_alternating'
        if reason:excluded.append(dict(id=row['message_id'],reason=reason));continue
        paths.append(dict(id=row['message_id'],root_id=chain[0]['message_id'],source_sha256=hashlib.sha256(json.dumps(chain,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),messages=[dict(role='user' if x['role']=='prompter' else 'assistant',content=x['text']) for x in chain],message_ids=[x['message_id'] for x in chain]))
    put(ROOT/'corpus-exclusions.json',excluded)
    put(ROOT/'corpus-paths.json',dict(mode='tokenize',rows=paths))
    print(len(paths),collections.Counter(x['reason'] for x in excluded))
if __name__=='__main__':prepare();run('tokenize01','candidate01',read(ROOT/'corpus-paths.json'))
