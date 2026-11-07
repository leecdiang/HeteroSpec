"""Prospective teacher-forced probes and a single precision reversal."""
from execute import *
from audit import signature, unpack

def probe(build):
    return record_unit('probe-'+build,build,slots_for(6,[0]),PANEL,
        'Teacher-forced genuine prompt rows from MATH1804. Width2 at head254 -> [256,256], width2 at255 -> [256,512] groups1+1; unchanged512 at259 reuses graph. Same shape at261 switches precision off and must rebuild. Original numerical role executes paired rows singly.',probe=True)

def check_probes(build):
    ref=read(ROOT/'units/probe-original-probe-01/native/result.json')['probe_runs']
    unit=ROOT/'units'/('probe-'+build);cand=read(unit/'native/result.json')['probe_runs']
    log=(unit/'SUPERVISOR.stderr.log').read_text(encoding='utf-8',errors='replace')
    comparisons=[]
    for a,b in zip(ref,cand,strict=True):
        for ra,rb in zip(a['calls'],b['calls'],strict=True):
            p=rb['base'];head=b['prefix_tokens']
            assert p==ra['base'] and rb['actual_prior_max']==p-1
            equal=[x['sha256']==y['sha256'] for x,y in zip(ra['vectors'],rb['vectors'],strict=True)]
            # After the intentional off intervention different internal state is expected.
            if head==254 or p<261:assert all(equal),(head,p,equal)
            marker=f'HS_PROBE_BEGIN prefix={head} pos={p} '
            trace=log.split(marker,1)[1].split(f'HS_PROBE_END pos={p}',1)[0]
            cache=[x for x in trace.splitlines() if x.startswith(f'HS_CACHE head={p} rows=2 ')]
            attn=[x for x in trace.splitlines() if x.startswith(f'HS_ATTENTION pos={p} rows=2 ')]
            if p in (254,255):assert cache and attn
            if p==254:assert any('grouped=0 extents=256,256,' in x for x in attn)
            if p==255:assert any('grouped=1 extents=256,512,' in x for x in attn)
            if p==259:assert rb['reuse_delta']==1
            if p==261:assert rb['reuse_delta']==0 and 'HS_REUSE rejected=policy' in trace
            comparisons.append(dict(prefix=head,base=p,equal_to_scalar=equal,reuse_delta=rb['reuse_delta'],cache=cache[:1],attention=attn[:1],precision=rb['precision_enabled']))
    write(unit/'PROBE_AUDIT.json',dict(status='PHYSICAL_BOUNDARY_AND_POLICY_REUSE_PASS',rows=comparisons))

def reversal(build):
    slots=slots_for(4,[2,8],trace=True,precision=False)
    d=record_unit('precision-off-'+build,build,slots,PANEL,'Same candidate binary, original P1 construction and active prefix rule. Disabling precision alone should recover the historical P1+PQ divergence; q2 default MMVQ pipeline should return.')
    candidate=d['requests'][-1];old=read(OLD/'run-primary/B1-4/result.json')['requests'];ref=read(ROOT/'units/original-4/native/result.json')['requests'][0]
    assert signature(candidate['restored_boundary'])==signature(old[2]['boundary'])
    assert candidate['endpoint']!=ref['endpoint'] and candidate['endpoint']==old[8]['endpoint'] and candidate['cycles']==old[8]['cycles']
    assert {k:v['sha256'] for k,v in candidate['vectors'].items()}=={k:v['sha256'] for k,v in old[8]['vectors'].items()}
    unit=ROOT/'units'/('precision-off-'+build)
    unpack(candidate,unit/'payload')
    log=(unit/'SUPERVISOR.stderr.log').read_text(encoding='utf-8',errors='replace')
    assert 'retain_f32=0 selected_quant=1 pipeline=mul_mat_vec_q8_0_q8_1_f32' in log
    write(unit/'REVERSAL_AUDIT.json',dict(status='HISTORICAL_P1_PQ_FAILURE_RESTORED',saved_vectors=len(candidate['vectors']),same_state=True,all_vectors_and_transactions_equal_old_failure=True))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['probe','check','reversal']);a.add_argument('build');args=a.parse_args();{'probe':probe,'check':check_probes,'reversal':reversal}[args.action](args.build)

