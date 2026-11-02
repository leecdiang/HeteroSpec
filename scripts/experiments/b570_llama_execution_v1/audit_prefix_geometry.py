"""Bind maximal prefix groups to actual native cycles and scheduler assignments."""
from pathlib import Path
import argparse,collections,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

def audit(epoch,out):
    epoch=Path(epoch);results=[]
    for i,x in enumerate(read(epoch/'DEV.json')):
        for arm in ('C_PQ','C_QB'):
            p=epoch/f'units/baseline-candidate/native/baseline/i{i}/{arm}/heavy.json';r=read(p);groups=collections.defaultdict(list);backend=collections.Counter()
            for g in r['geometry']:
                if g['name'].startswith(('hs_prefix_attention-','hs_qb_','hs_pq_')):backend[g['scheduler_backend']]+=1;need(g['scheduler_backend']=='Vulkan0','unexpected CPU or other backend in scoped attention')
                if g['phase']=='VERIFY' and g['name'].startswith('hs_prefix_attention-'):
                    layer=int(g['name'].rsplit('-',1)[1]);groups[g['caller_base'],layer].append(g)
            grouped=[]
            for base in sorted({base for base,layer in groups}):
                matches=[c for c in r['cycles'] if c['base']==base];need(len(matches)==1,'unique actual cycle');cycle=matches[0]
                require_widths=None
                for layer in range(32):
                    nodes=groups[base,layer];widths=[g['ne'][1] for g in nodes];need(sum(widths)==4 and all(g['caller_ids']==cycle['verify_ids'] for g in nodes),'complete actual query grouping')
                    if require_widths is None:require_widths=widths
                    need(widths==require_widths,'consistent all-layer partition')
                scalar_extents=[max(256,((base+j+1+255)//256)*256) for j in range(4)];expected=[]
                for n in scalar_extents:
                    if expected and expected[-1][0]==n:expected[-1][1]+=1
                    else:expected.append([n,1])
                need(require_widths==[v[1] for v in expected] and len(expected)>1,'maximal adjacent equal scalar extents')
                grouped.append({'actual_cycle':cycle['cycle'],'actual_base':base,'verify_ids':cycle['verify_ids'],'widths':require_widths,'scalar_prefix_extents':scalar_extents,'all_layers':32,'scheduler_backend':'Vulkan0'})
            crossing=[c['cycle'] for c in r['cycles'] if (c['base']//256)!=((c['base']+3)//256)]
            need(crossing==[g['actual_cycle'] for g in grouped],'actual dense causal boundary left ungrouped')
            results.append({'input_id':x['id'],'arm':arm,'record_sha256':sha(p),'grouped_actual_cycles':grouped,'actual_boundary_cycles':crossing,'scoped_attention_scheduler_counts':dict(backend),'nontrigger_if_empty':'No actual verification batch straddled a scalar physical-prefix boundary in this trajectory.'})
    need(any(x['grouped_actual_cycles'] for x in results),'grouping never observed');write(out,{'status':'ACTUAL_PREFIX_GROUP_GEOMETRY_PASS','rows':results,'scope':'Actual cycle/base/query IDs, all-layer maximal grouping and scheduler evidence. Scheduler assignment is not mislabeled shader/pipeline tracing.'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--epoch',required=True);p.add_argument('--out',required=True);a=p.parse_args();audit(a.epoch,a.out)
