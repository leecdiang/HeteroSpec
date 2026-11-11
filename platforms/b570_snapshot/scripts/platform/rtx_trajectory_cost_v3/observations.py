"""Reconstruct observed native allocator batches and worker decode/graph metadata."""
import json,re
from pathlib import Path
from verify_common import require
from verify_replay import TOKEN
def native(path):
    text=Path(path).read_bytes().replace(b'\r\n',b'\n').decode('latin-1');groups=[]
    headers=list(re.finditer(r'^.*ubatch_print:\s+equal_seqs\s*=\s*(\d+).*$',text,re.M))
    line=1;last_start=0
    for i,h in enumerate(headers):
        end=headers[i+1].start() if i+1<len(headers) else len(text);chunk=text[h.end():end]
        previous_start=text.rfind('\n',0,max(0,h.start()-1))+1;previous=text[previous_start:h.start()].rstrip('\r\n')
        line+=text.count('\n',last_start,h.start());last_start=h.start()
        count=re.search(r'ubatch_print:\s+n_tokens\s*=\s*(\d+)',chunk);require(count,'batch size absent')
        g={'kind':'physical_split' if 'added ubatch to split:' in previous else 'logical_batch','raw_start_line':line,'native_log_clock':h.group(0).split(' ',1)[0],'equal_seqs':int(h[1]),'n_tokens':int(count[1]),'tokens':[]}
        for m in TOKEN.finditer(chunk):
            token,pos,num,seqs,mask=m.groups();g['tokens'].append({'token_id':int(token),'position':int(pos),'sequence_count':int(num),'sequence_ids':[int(x) for x in seqs.split(',') if x.strip()],'logits_mask':int(mask)})
        require(len(g['tokens'])==g['n_tokens'],'batch metadata token rows incomplete');groups.append(g)
    prompt=re.search(r'new prompt,.*task.n_tokens = (\d+)',text);prompt_length=int(prompt[1]) if prompt else None
    for g in groups:
        g['phase']='prefill' if prompt_length and all(x['position']<prompt_length for x in g['tokens']) else 'generation_or_state_update'
        g['model_role']=None
    physical=[g for g in groups if g['kind']=='physical_split'];logical=[g for g in groups if g['kind']=='logical_batch']
    return {'logical_batches':logical,'physical_groups':physical,'physical_group_sizes':sorted({g['n_tokens'] for g in physical}),'prompt_length':prompt_length,'limitations':['Original batch logger does not label target/draft context; model role is not inferred','Allocator events are input/partition metadata, not per-kernel timing','Original CLI does not expose exact per-decode host UTC endpoints or target full logits']}
def worker(path):
    events=[json.loads(x) for x in Path(path).read_bytes().splitlines()];rows=[]
    for e in events:
        if e['event'] in ['request_sent','startup','close']:continue
        v=e['response'];decodes=([v['decode']] if 'decode' in v else [])+v.get('decodes',[])
        for j,d in enumerate(decodes):rows.append({'role':e['role'],'pid':e['pid'],'operation':e['event'],'event_sequence':e['event_sequence'],'subdecode':j,'captured_after_utc':e['utc'],'tokens':d['tokens'],'positions':list(range(d['positions_start'],d['positions_start']+len(d['tokens']))),'sequence_ids':[[0] for _ in d['tokens']],'logits_mask':d['logits_mask'],'graphs':d['graphs'],'phase':'prefill' if e['event']=='init' else 'generation_or_state_update'})
    return {'logical_forwards':rows,'forward_count':len(rows),'limitations':['Metadata callback always returns false and reads no tensor data','Full sampled logits bytes omitted after byte hash/top scores; no offline authentication of omitted logits bytes','Response UTC bounds completion; no exact worker per-decode UTC measurement']}
