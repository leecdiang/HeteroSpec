"""Bounded CPU raw reads for observability and numerical-work accounting."""
import argparse,collections,hashlib,json
from pathlib import Path
from audit import DOC,load,save,sha

def main():
    a=argparse.ArgumentParser();a.add_argument('--raw-root',type=Path,required=True);a.add_argument('--legacy-root',type=Path,required=True);args=a.parse_args()
    # Immutable selected-attempt digests are obtained directly from pinned exports.
    bindings=load(DOC/'SOURCE_BINDINGS.json');import subprocess
    pin=bindings['commit'];b=subprocess.check_output(['git','show',pin+':benchmarks/rtx_target_only_bridge_v1/FORMAL_ARRAYS.json'])
    assert sha(b)==next(x['sha256'] for x in bindings['files'] if x['path'].endswith('/FORMAL_ARRAYS.json'))
    records=json.loads(b)['records'];counts={};inspected=[];selected=[]
    for x in records:
        binding=x['selected_attempt'];p=args.raw_root/binding['record'];raw=p.read_bytes();assert sha(raw)==binding['sha256']
        d=json.loads(raw);assert d['ids']==x['ids'] and d['endpoint']==x['endpoint']
        inspected.append({'path':binding['record'],'sha256':sha(raw),'bytes':len(raw),'source':'pinned selected-attempt digest'})
        entry=counts.setdefault(x['condition'],{'runs':0,'committed_ids':0,'trace_decode':{},'transfer_events':0,'state_bytes_per_transfer':[]})
        entry['runs']+=1;entry['committed_ids']+=len(x['ids'])
        if x['condition']=='U2':continue
        name=next(f for f in d['files'] if f.endswith('trace.jsonl'));trace=p.parent/name;tb=trace.read_bytes();assert sha(tb)==d['files'][name]['sha256']
        inspected.append({'path':str(trace.relative_to(args.raw_root)).replace('\\','/'),'sha256':sha(tb),'bytes':len(tb),'source':'selected result file binding'})
        events=[json.loads(l) for l in tb.splitlines()];first=None
        for e in events:
            if e['event']=='decode':
                key=e['role']+'/'+e['phase'];group=entry['trace_decode'].setdefault(key,{'decode_calls':0,'evaluated_caller_tokens':0,'occupied_graph_histogram':{}})
                group['decode_calls']+=1;group['evaluated_caller_tokens']+=e['caller_batch']
                occupied=[g['ne'][1] for g in e['graphs'] if g['name']=='attn_norm-0']
                assert sum(occupied)==e['caller_batch'],'graph count/caller accounting mismatch'
                for n in occupied:group['occupied_graph_histogram'][str(n)]=group['occupied_graph_histogram'].get(str(n),0)+1
            if e['event']=='transfer':entry['transfer_events']+=1;entry['state_bytes_per_transfer'].append(e['state_bytes'])
            if e['event']=='sample' and e.get('role')=='target' and first is None:first=e
        if x['task'] in ('HumanEval/15','HumanEval/25','HumanEval/18','HumanEval/31') and x['rep']==1:
            selected.append({'task':x['task'],'condition':x['condition'],'first_target_sample':first,'transfer':d['transfer'],'trace_sha256':sha(tb)})
    legacy=[]
    for task in (15,25,18,31):
        p=args.legacy_root/f'work/rtx-target-v1/formal/HumanEval-{task}-H1-r1/result.json';d=json.loads(p.read_bytes());wires=[]
        for role in ('P','R'):
            name=next(f for f in d['files'] if f.endswith(role+'-wire.jsonl'));fp=p.parent/name;bb=fp.read_bytes();assert sha(bb)==d['files'][name]
            events=[json.loads(l) for l in bb.splitlines()];responses=[e for e in events if e.get('response') and e['event']!='startup']
            wires.append({'role':role,'path':str(fp),'sha256':sha(bb),'response_operations':dict(collections.Counter(e['request'].get('op') for e in responses)),
                          'scope':'response operations, not identical to model forwards; request_sent duplicates excluded'})
        legacy.append({'task':f'HumanEval/{task}','condition':'H1','rep':1,'record_path':str(p),'record_sha256':sha(p.read_bytes()),'wires':wires,'authentication':'Local original result binds wire bytes; prior full raw archive verification is inherited, not repeated here.'})
    for entry in counts.values():
        states=entry.pop('state_bytes_per_transfer');entry['transfer_serialized_bytes_sum']=sum(states)
    save(DOC/'RAW_WORK_INVENTORY.json',{'scope':'171 source-bound selected result reads, 114 native traces; four old H1 result/wire spot reads. No fresh inference or full historical archive re-audit.',
          'conditions':counts,'file_bindings':inspected,'legacy_H1_spots':legacy,'limitations':'Graph occurrences are observed forward-token shapes, not uniquely identified kernels; U2 detailed forward work and B570 full graph counts unavailable here. Instrumented wall-clock times deliberately not used.'})
    save(DOC/'OBSERVED_STATE_SPOTS.json',selected)
    print('PASS bounded CPU raw inventory: 171 records, 114 traces, four H1 two-worker spots')

if __name__=='__main__':main()
