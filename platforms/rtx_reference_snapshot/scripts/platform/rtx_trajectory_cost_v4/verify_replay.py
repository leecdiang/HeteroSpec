"""Independent standard-library evidence verifier. Imports no execution code."""
import argparse,hashlib,json,re
from pathlib import Path
from itertools import zip_longest
def require(ok,message):
    if not ok:raise ValueError(message)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(v):return json.dumps(v,separators=(',',':'),ensure_ascii=True).encode('utf-8')
def arr(v):return hashlib.sha256(dump(v)).hexdigest()
def difference(a,b):
    for i,(x,y) in enumerate(zip_longest(a,b)):
        if x!=y:return {'index':i,'left_id':x,'right_id':y}
    return None
TOKEN=re.compile(r'ubatch_print:\s+\d+: id =\s+(\d+) \([\s\S]*?\), pos =\s+(\d+), n_seq_id =\s+(\d+), seq_id = \[([^\]]*)\], output = (\d+)')
def native_prompt(text):
    n=re.search(r'new prompt,.*task.n_tokens = (\d+)',text);require(n,'native input length missing');count=int(n.group(1))
    tail=text[n.end():];end=tail.find('slot process_toke:');require(end>=0,'missing first native commit')
    seen={}
    for m in TOKEN.finditer(tail[:end]):
        token,pos,seqnum,seqs,mask=m.groups();pos=int(pos)
        require(seqnum=='1' and seqs=='0','input sequence identity')
        if pos<count:
            require(pos not in seen or seen[pos]==int(token),'native prompt aliases disagree');seen[pos]=int(token)
    require(set(seen)==set(range(count)),'actual native prompt IDs incomplete')
    return [seen[i] for i in range(count)]
def native_commits(text):
    ids=[]
    for line in text.splitlines():
        if 'process_toke:' not in line or 'n_gen =' not in line or 'next token:' not in line:continue
        index=int(line.split('n_gen =',1)[1].split(',',1)[0]);remaining=int(line.split('n_remaining =',1)[1].split(',',1)[0]);token=int(line.split('next token:',1)[1].strip().split(' ',1)[0])
        require(index==len(ids)+1 and remaining==128-index,'native commit continuity/budget');ids.append(token)
    require(1<=len(ids)<=128,'native endpoint length')
    stop=re.findall(r'process_toke:.*stopped by (EOS|limit)',text)
    eog_ids={128247,151643,151645,151662,151663,151664}
    terminal_eog=ids[-1] in eog_ids
    require(not any(t in eog_ids for t in ids[:-1]),'native first EOG was not inclusive endpoint')
    if len(ids)==128:require(stop==(['limit','EOS'] if terminal_eog else ['limit']),'native cap/EOG stop observations')
    else:require(stop==['EOS'] and terminal_eog,'native early inclusive EOG stop')
    reason='EOS' if terminal_eog else 'limit'
    count=re.findall(r'slot print_timing: id\s+0 \| task \d+ \|\s+eval time\s*=\s*[\d.]+ ms /\s*(\d+) tokens',text);require(count==[str(len(ids))],'native event count differs')
    return ids,reason
def check_tape(path,task,rep):
    rows=[];previous='0'*64
    with Path(path).open('rb') as f:
        for line in f:
            v=json.loads(line);h=v.pop('event_sha256');require(arr(v)==h,'tape digest invalid');require(v['previous_event_hash']==previous,'tape predecessor invalid');previous=h
            require(v['task_id']==task and v['repetition']==rep and v['round']==len(rows),'tape task/round identity')
            q=v['request'];require(set(q)=={'op','round','position','pending','proposal_ids'},'future or answer input in R request');require(q['op']=='verify' and q['round']==len(rows),'R tape operation')
            require(len(q['proposal_ids'])<=2,'proposal width');tokens=[q['pending']]+q['proposal_ids']
            require(v['tokens']==tokens and v['positions']==list(range(q['position'],q['position']+len(tokens))) and v['sequence_ids']==[[0] for _ in tokens] and v['logits_mask']==[1]*len(tokens),'fixed target batch fields differ')
            v['event_sha256']=h;rows.append(v)
    return rows
def check_run(path,tape=None,observed=True):
    path=Path(path);r=read(path/'record.json');require(r['status']=='VALID','run did not validly complete')
    for name,v in r['files'].items():
        p=path/name;require(p.is_file() and p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],'raw file integrity: '+name)
    require(sha(path/'prompt.txt')==r['input_sha256'],'input digest')
    contracts=None
    for base in [path,*path.parents]:
        for meta in [base/'metadata',base/'benchmarks/rtx_trajectory_cost_v4']:
            if (meta/'INPUT_CONTRACT.json').exists():contracts=read(meta/'INPUT_CONTRACT.json');break
        if contracts:break
    if contracts and r['task_id'].startswith('HumanEval/'):
        require(contracts['input_hashes'][r['task_id']]==r['input_sha256'],'frozen input/task association')
    expected=read(path/'generated_ids.json');require(expected==r['generated_ids'] and arr(expected)==r['array_sha256'],'declared array integrity')
    c=r['condition']
    require(r['task_id'].replace('/','-')+'-r'+str(r['repetition'])+'-'+c==r['run_id'],'task/rep/condition association')
    if c in ['REFERENCE_UB1','RTX_BATCHED_K2']:
        text=(path/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1');ids,stop=native_commits(text)
        require(ids==expected and stop==r['termination'],'native output differs')
        layers=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',text);require(layers==([('37','37')] if c=='REFERENCE_UB1' else [('37','37'),('29','29')]),'native complete model placement')
        devices=re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',text);require(len(devices)==len(layers) and all(d.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for d in devices),'native device')
        require(re.findall(r'cached n_tokens = (\d+)',text)==['0'],'native fresh context')
        ub=list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',text)));require(ub==([1] if c=='REFERENCE_UB1' else [2,2]),'native context ubatches')
        actual_prompt=native_prompt(text)
        if contracts and r['task_id'] in contracts['reserved_tokens']:require(actual_prompt==contracts['reserved_tokens'][r['task_id']]['prompt_ids'],'native reserved prompt tokenization contract')
        return {'run_id':r['run_id'],'ids':ids,'prompt_ids':actual_prompt,'condition':c,'termination':stop,'started_utc':r['started_utc'],'ended_utc':r['ended_utc']}
    events=[json.loads(line) for line in (path/'events.jsonl').read_bytes().splitlines()];roles={e['role'] for e in events};require(roles==({'P','R'} if c=='H2_P_R' else {'R'}),'role/model isolation')
    for role in roles:
        revents=[e for e in events if e['role']==role];require([e['event_sequence'] for e in revents]==list(range(1,len(revents)+1)),'native RPC event continuity')
        start=revents[0];require(start['event']=='startup' and start['response']['role']==role,'worker startup role');require(start['response']['graph_observer_enabled']==observed,'actual graph observer switch')
        model='Qwen3-0.6B-Q8_0.gguf' if role=='P' else 'Qwen3-8B-Q8_0.gguf';require(start['response']['model_open'].endswith(model),'single-model open boundary')
        require(start['request']['command'][2]==start['response']['model_open'],'model file access differs from declared process')
        cfg=start['response']['context'];require(cfg=={'n_ctx':4096,'n_batch':2048,'n_ubatch':1 if c=='R_REFERENCE_UB1' else 2,'n_seq_max':1,'threads':24,'flash_attention':'off','kv_unified':False},'actual worker context configuration')
        stderr=(path/(role+'-stderr.log')).read_bytes().decode('latin-1');actual=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',stderr);require(actual==([('29','29')] if role=='P' else [('37','37')]),'observed single-model/full-layer load')
        require(revents[-1]['event']=='close','worker lifetime did not close')
    rr=[e for e in events if e['role']=='R' and e['event']=='init'];require(len(rr)==1,'target initial prefill count');init=rr[0]['response'];ids=init['committed_ids'].copy();prompt_ids=init['prompt_ids'];pos=len(prompt_ids)
    require(arr(prompt_ids)==r['prompt_array_sha256'] and prompt_ids==r['prompt_ids'],'frontend tokenization hash')
    if contracts and r['task_id'] in contracts['reserved_tokens']:require(prompt_ids==contracts['reserved_tokens'][r['task_id']]['prompt_ids'],'worker reserved tokenization contract')
    require(init['decode']['tokens']==prompt_ids and init['decode']['logits_mask']==[0]*(pos-1)+[1],'prefill token/mask contract')
    tape_rows=check_tape(path/'tape.jsonl' if c=='H2_P_R' else tape,r['task_id'],r['repetition']) if c!='R_REFERENCE_UB1' else []
    verifies=[e for e in events if e['role']=='R' and e['event']=='verify'];require(len(verifies)==r['round_count'],'verification round count')
    terminal=init['terminal'];samples=init['samples'].copy()
    for j,e in enumerate(verifies):
        require(not terminal,'decode after endpoint');q=e['request'];v=e['response'];require(q['round']==j and q['position']==pos and q['pending']==ids[-1],'own-state target boundary')
        require(set(q)=={'op','round','position','pending','proposal_ids'},'R answer/extra input dependency')
        if tape_rows:
            t=tape_rows[j];require(t['request']==q and t['prefix_count']==len(ids) and t['prefix_sha256']==arr(ids),'past prefix/tape request differs')
            if c=='H2_P_R':
                pe=[x for x in events if x['role']=='P' and x['event']=='propose'][j];require(pe['response']['proposal_ids']==q['proposal_ids'] and arr(pe['response'])==t['P_response_sha256'],'independent P request/response digest')
                sent=[x for x in events if x['role']=='R' and x['event']=='request_sent' and x['request']==q];require(len(sent)==1 and pe['utc']<=t['sealed_utc']<=sent[0]['utc']<=e['utc'],'P/tape before R decode chronology')
                require(pe['event_sequence']==t['P_event_sequence'] and sent[0]['event_sequence']==t['R_next_event_sequence'],'causal event sequence')
        tokens=[ids[-1]]+q['proposal_ids'];d=v['decode'];require(d['tokens']==tokens and d['positions_start']==pos and d['logits_mask']==[1]*len(tokens),'actual fixed verification input')
        graph_outputs=[g['ne'][1] for g in d['graphs'] if g['name']=='result_output'];require((sum(graph_outputs)==len(tokens) and all(0<=n<=2 for n in graph_outputs)) if observed else not graph_outputs,'actual physical graph output grouping or disabled observer')
        chosen=[];accepted=0
        for k,s in enumerate(v['samples']):
            require(s['logits_index']==k,'sampled logits index');chosen.append(s['selected_id'])
            if k<len(q['proposal_ids']) and chosen[-1]==q['proposal_ids'][k]:accepted+=1
            else:require(k==len(v['samples'])-1,'sampler continued after rejection/bonus')
        require(chosen==v['sampled_ids'] and accepted==v['accepted_proposals'] and len(chosen)==accepted+1,'acceptance/correction/bonus reconstruction')
        require(v['retain_count']==len(chosen) and v['next_position']==pos+len(chosen) and v['suffix_delete_start']==v['next_position'],'KV rollback boundary')
        visible=[]
        for s in v['samples']:
            if len(ids)==128:break
            ids.append(s['selected_id']);visible.append(s['selected_id'])
            if s['eog']:terminal=True;break
        terminal=terminal or len(ids)==128;require(visible==v['committed_ids'] and terminal==v['terminal'] and len(ids)==v['committed_count'],'native commitment endpoint events')
        samples.extend(v['samples']);pos=v['next_position']
    require(terminal and ids==expected,'independently committed full array differs');require(not tape_rows or len(tape_rows)==len(verifies),'extra future tape')
    for s in samples:
        require(s['logits_bytes']==151936*4 and re.fullmatch('[0-9a-f]{64}',s['logits_sha256']),'full sampled logits byte digest contract')
        require(s['selected_id']==s['raw_top1'],'frozen identity samplers do not choose recorded raw maximum')
        require(s['raw_top1_score']>=s['raw_top2_score'],'raw score order')
    if c=='H2_P_R':
        pi=[e for e in events if e['role']=='P' and e['event']=='init'];require(len(pi)==1 and pi[0]['response']['prompt_ids']==prompt_ids,'P tokenization')
        updates=[e for e in events if e['role']=='P' and e['event']=='update'];require(len(updates)==len(verifies),'P verified-batch refresh count')
        for j,e in enumerate(updates):
            q=e['request'];v=e['response'];rv=verifies[j]['response'];rq=verifies[j]['request']
            require(q['verified_batch']==[rq['pending']]+rq['proposal_ids'] and q['position']==rq['position'] and q['retain_count']==rv['retain_count'],'P consumes only own proposal batch and past target acceptance')
            require(v['decode']['logits_mask']==[0]*(len(q['verified_batch'])-1)+[1] and v['suffix_delete_start']==rv['next_position'],'draft-simple refresh logits and rollback')
    return {'run_id':r['run_id'],'ids':ids,'prompt_ids':prompt_ids,'condition':c,'termination':r['termination'],'started_utc':r['started_utc'],'ended_utc':r['ended_utc'],'logit_limit':'full sampled-row byte digests and top scores retained; omitted full logits cannot independently authenticate digests or alternative sampler transforms offline'}
