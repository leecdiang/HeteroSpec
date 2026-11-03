"""Build compact tables from native logs and registered pairs, for the result PR."""
from paths import *
from recompute import recompute,gmean
from contrast import crossing_contrast
import statistics,random,math
def intervals(rows):
    by={}
    for r in rows:by.setdefault(r['key'][1],[]).append(math.log(r['ratio']))
    # Equal input weight. Restrict uncertainty estimation to complete six-session inputs.
    x=[statistics.mean(v) for v in by.values() if len(v)==6]
    if len(x)<2:return dict(inputs=len(x),interval=None)
    rng=random.Random(169);boots=sorted(math.exp(statistics.mean(rng.choices(x,k=len(x)))) for _ in range(5000))
    return dict(inputs=len(x),interval=[boots[125],boots[4874]],equal_input_ratio=math.exp(statistics.mean(x)))
def traces():
    out=[]
    for p in sorted(ROOT.glob('DIAG-candidate-profile-*.json')):
        for arm,r in read(p).items():
            nodes=r['layer0_nodes'];mm=[]
            for z in nodes:
                src=z.get('sources',[])
                if z.get('op')=='MUL_MAT' and len(src)==2 and 'ffn_' in src[0]['name'] and '.weight' in src[0]['name']:
                    mm.append({'weight':src[0]['name'],'width':src[1]['ne'][1]})
            mask={};concat={}
            for k,v in r['gpu_microseconds'].items():
                if k.startswith('CONT') and 'mask' in k.lower():mask[k]=v
                if k.startswith('CONCAT'):concat[k]=v
            out.append(dict(trace=p.name,arm=arm,calls=r['trace_calls'],ffn=mm,
                kernel_dispatches=r['dispatches'],attention=r['attn'],mask_copy_us=sum(mask.values()),concat_us=sum(concat.values()),
                mask_timestamp_groups=len(mask),concat_timestamp_groups=len(concat),timestamp_groups=len(r['gpu_microseconds'])))
    return out
def report():
    dest=HERE/'evidence';dec=recompute(ROOT,True)
    times=[r for p in ROOT.glob('TIMES-*.json') for r in read(p)]
    dx=crossing_contrast(times)
    ret={}
    for family in sorted({x['key'][0] for x in dx}):
        for q in (2,4,8,16,32):
            rows=[x for x in dx if x['key'][0]==family and x['key'][3]==q]
            if rows:ret[f'{family}/q{q}']=dict(blocks=len(rows),cross=gmean([r['cross'] for r in rows]),inside=gmean([r['inside'] for r in rows]),incremental=gmean([r['ratio'] for r in rows]),cross_WB_slower=sum(r['cross']>1 for r in rows))
    summary=dict(controls=dec['controls'],fixed_work=ret,natural=[dict(**{k:v for k,v in x.items() if k!='pairs'},**intervals(x['pairs'])) for x in dec['natural']],
                 forecast={k:{j:v for j,v in val.items() if j!='rows'} for k,val in dec['held_out_forecast'].items()},process_seconds=dec['process_seconds'],owned_seconds=dec['owned_seconds'],units=dec['units'],unsuccessful_units=dec['unsuccessful_units'],raw_validation=dec['raw_validation'],objects=dec['verified_unique_vectors'])
    for name,v in [('summary.json',summary),('dispatch.json',traces())]:
        if (dest/name).exists():assert read(dest/name)==v
        else:write(dest/name,v)
    return summary
if __name__=='__main__':print(json.dumps(report(),indent=2))
