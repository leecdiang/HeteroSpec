"""Combined arithmetic policy plus explicit bounded graph metadata capacity."""
from pathlib import Path
import argparse,json
from reference_q8 import apply as q8
from prefix_extent import apply as prefix

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);a=p.parse_args();source=Path(a.source)
    q8(source);receipt=prefix(source)
    p=source/'src/llama-context.cpp';s=p.read_text(encoding='utf-8');anchor='    uint32_t n_sampling_nodes = 0;'
    assert s.count(anchor)==1
    s=s.replace(anchor,'''    // Small-batch prefix groups add views, materialized masks, attention
    // subgraphs and concatenations. Reserve up to 64 metadata nodes per
    // layer and query for this bounded q2..q4 domain, before any forward.
    // Scalar contexts retain their original capacity. This is not a
    // numerical operation, fallback, or increase of the admitted KV extent.
    if (cparams.n_ubatch > 1 && cparams.n_ubatch <= 4) {
        res += 64u * model.hparams.n_layer * cparams.n_ubatch;
    }

'''+anchor)
    p.write_text(s,encoding='utf-8',newline='\n');receipt['graph_metadata_capacity']='Additional 64 * layers * ubatch nodes for admitted ubatch2..4; scalar contexts unchanged; allocation charged to normal context lifecycle.';print(json.dumps(receipt,indent=2))
