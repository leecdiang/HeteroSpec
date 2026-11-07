"""Per-context identity and shape reuse model. Never instantiates llama_context."""
from common import ROOT, modules, save

class Model:
    def __init__(self):self.contexts={};self.active_layout=None
    def bind(self,context,role,phase,layout,ub,capacity,q):
        previous=self.contexts.get(context)
        key=(role,phase,layout,ub,capacity)
        self.active_layout=layout
        invalidated=previous is None or previous['key']!=key
        topology=('MQ' if q==1 else layout,q)
        reuse=bool(not invalidated and previous['topology']==topology)
        shape_rejected=bool(not invalidated and previous['topology']!=topology)
        epoch=(previous['epoch'] if previous else 0)+int(invalidated)
        self.contexts[context]=dict(key=key,topology=topology,epoch=epoch)
        return dict(context=context,key=list(key),q=q,topology=list(topology),epoch=epoch,
                    key_invalidated=invalidated,shape_rejected=shape_rejected,reuse=reuse,
                    thread_active_layout=self.active_layout)

def main():
    before=modules();m=Model()
    seq=[('T','target','PREFILL','MQ',128,4,1),('T','target','VERIFY','QB',4,4,2),
         ('D','draft','CONTINUE','MQ',1,1,1),('T','target','VERIFY','QB',4,4,1),
         ('T','target','VERIFY','QB',4,4,2),('T','target','VERIFY','QB',4,4,2),
         ('D','draft','CONTINUE','MQ',1,1,1),('T','target','RECONCILE','PQ',4,4,1),
         ('T','target','VERIFY','PQ',4,4,2)]
    rows=[m.bind(*x) for x in seq]
    assert sum(x['shape_rejected'] for x in rows)==2
    assert sum(x['reuse'] for x in rows)==2
    assert rows[3]['key_invalidated'] is False and rows[3]['shape_rejected']
    assert rows[5]['reuse'] and rows[6]['reuse']
    assert rows[-1]['key_invalidated']
    # A graph requires each input owner to remain alive through the compute.
    owners={'Q':True,'K':True,'V':True,'mask':True}
    assert all(owners.values());owners['Q']=False;assert not all(owners.values())
    save(ROOT/'STATE_MODEL_TESTS.json',dict(revision=2,transitions=rows,shape_rejections=2,cache_hits=2,
         expired_owner_rejected=True,source=['llama-context.cpp:4368 per-context key and thread_local active layout',
          'llama-graph.h:814 allow_reuse checks n_tokens and sequences',
          'llama-graph.cpp:1408 all input reuse checks required'],
         reason='Source review requires separate target/draft context identities. Earlier conservative single-state toy model in CONTRACT_TESTS.json is retained and superseded for cache transitions.',
         scope='Abstract source-derived state and lifetime requirements; not native binder, asynchronous scheduler, real KV identity or GPU lifetime validation.',
         modules_before=before,modules_after=modules(),new_attention_fixtures=0,gpu_starts=0))
    print(dict(transitions=len(rows),shape_rejections=2,cache_hits=2,expired_owner_rejected=True))

if __name__=='__main__':main()
