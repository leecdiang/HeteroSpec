"""Audit actual retained log timer scope, separate from a component decomposition."""
from evidence import *
import re

def main():
    begin('log_timers');ledger=[json.loads(s) for s in read('LEDGER.jsonl').decode().splitlines()];starts=[r for r in ledger if r['event']=='REQUEST_START'];rows=[]
    sessions=sorted({r['session'] for r in starts if '/candidate/' in r['unit_id']})
    for session in sessions:
        ss=[r for r in starts if r['session']==session];log=read('sessions/'+session+'/stderr.log').decode('utf-8');load('sessions/'+session+'/SESSION.json')
        blocks=re.split(r'decoded\s+(\d+) tokens in',log)[1:];assert len(blocks)//2==len(ss)
        for i,r in enumerate(ss):
            count=int(blocks[2*i]);block=blocks[2*i+1];sampling=re.search(r'common_perf_print:\s+sampling time\s*=\s*([0-9.]+) ms',block);chain=re.search(r'common_perf_print:\s+samplers time\s*=\s*([0-9.]+) ms',block)
            if r['warm']:continue
            receipt=load('raw/'+digest(r['unit_id'].encode())[:20]+'/RESULT.json');assert count==receipt['metrics']['raw_count'] and sampling and chain
            rows.append(dict(unit_id=r['unit_id'],target_common_sampling_ms_printed=float(sampling.group(1)),target_sampler_chain_ms_printed=float(chain.group(1)),resolution_ms=.01,scope='fresh per-request target common_sampler t_total_us; synchronizations before tm excluded; no draft samplers, vector copies, clone, KV or full host cost',context_perf_scope='cumulative session counters; no request reset; not component-duration decomposition'))
    assert len(rows)==30;table('SAMPLER_TIMER_AUDIT.csv',rows)
    source=read('candidate-common/sampling.cpp').decode();native=read('candidate-front/native.cpp').decode();assert 'llama_perf_context_reset' not in native and 'common_sampler_init(model_tgt' in native
    write('LOG_TIMER_AUDIT.json',dict(status='PASS',requests=30,target_common_sampling_ms_min=min(x['target_common_sampling_ms_printed'] for x in rows),target_common_sampling_ms_max=max(x['target_common_sampling_ms_printed'] for x in rows),target_common_sampling_ms_sum=sum(x['target_common_sampling_ms_printed'] for x in rows),independent_scope='target common sampling timer only, printed at .01ms; fresh target sampler each request; synchronize before timer excluded',full_component_breakdown_available=False,target_context_perf='cumulative; misleading prompt/eval/total labels cannot be differenced into mutually exclusive per-request GPU components',draft_perf='no usable independent per-request draft-only duration retained',source_anchors='candidate-common/sampling.cpp:541-604; candidate-front/native.cpp:250-259,695-704'))
    finish('log_timers')
    manifest=json.loads((OUT/'UNIT_MANIFEST.json').read_text());manifest['log_timers']['output_hashes']={n:digest((OUT/n).read_bytes()) for n in ['SAMPLER_TIMER_AUDIT.csv','LOG_TIMER_AUDIT.json']};write('UNIT_MANIFEST.json',manifest);event('CPU_OUTPUT_BINDING',stage='log_timers',output_hashes=manifest['log_timers']['output_hashes'])
    print('Scoped target sampler log timers',len(rows),'requests; full decomposition unavailable')
if __name__=='__main__':main()
