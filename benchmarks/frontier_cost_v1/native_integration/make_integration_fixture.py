"""Create new untrained Llama fixtures with an explicit SPM vocabulary and EOS."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gguf-python', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); a.out.mkdir(exist_ok=False)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(a.gguf_python.resolve()))
    import gguf
    import numpy as np
    records = []
    for variant in ('target','draft_mismatch'):
        name = variant+'.gguf'; w = gguf.GGUFWriter(str(a.out/name), 'llama')
        w.add_name('Untrained CPU worker integration fixture '+variant)
        w.add_vocab_size(128); w.add_context_length(1024); w.add_embedding_length(256)
        w.add_block_count(2); w.add_feed_forward_length(768); w.add_head_count(8); w.add_head_count_kv(8)
        w.add_layer_norm_rms_eps(1e-5); w.add_rope_dimension_count(32); w.add_file_type(0)
        w.add_tokenizer_model('llama')
        tokens = [f't{i:03d}' for i in range(128)]
        tokens[0]='<unk>'; tokens[1]='<s>'; tokens[2]='<0x0A>'; tokens[127]='</s>'
        types = [1]*128; types[0]=2; types[1]=3; types[2]=6; types[127]=3
        w.add_token_list(tokens); w.add_token_scores([0.0]*128); w.add_token_types(types)
        w.add_bos_token_id(1); w.add_eos_token_id(127); w.add_unk_token_id(0)
        w.add_add_bos_token(False); w.add_add_eos_token(False)
        rng = np.random.default_rng(20261111)
        embedding=np.zeros((128,256),dtype='<f4')
        for i in range(128): embedding[i,i]=1.0
        output=np.zeros((128,256),dtype='<f4')
        transitions=[]
        for i in range(128):
            nxt=min(127,i+1)
            if variant=='draft_mismatch' and i%5==1: nxt=min(127,i+2)
            output[nxt,i]=1.0; transitions.append(nxt)
        w.add_tensor('token_embd.weight',embedding);w.add_tensor('output.weight',output)
        def norm(name): w.add_tensor(name,np.ones((256,),dtype='<f4'))
        def weight(name,shape): w.add_tensor(name,rng.uniform(-.002,.002,shape).astype('<f4'))
        norm('output_norm.weight')
        for i in range(2):
            pre=f'blk.{i}.';norm(pre+'attn_norm.weight');norm(pre+'ffn_norm.weight')
            for n in ['attn_q.weight','attn_k.weight','attn_v.weight','attn_output.weight']:weight(pre+n,(256,256))
            for n in ['ffn_gate.weight','ffn_up.weight']:weight(pre+n,(768,256))
            weight(pre+'ffn_down.weight',(256,768))
        w.write_header_to_file();w.write_kv_data_to_file();w.write_tensors_to_file();w.close()
        blob=(a.out/name).read_bytes()
        records.append({'name':name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),
                        'designed_token_transition':transitions})
    result={'schema':'heterospec.cpu-worker-fixture.v1','trained':False,'synthetic_seed':20261111,
            'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'numpy_version':np.__version__,'layers':2,'embedding':256,'vocab':128,'eos_id':127,
            'tokenizer':'SPM metadata; requests use explicit token IDs, not text tokenization',
            'weights':'F32; nonzero random attention/FFN and designed dominant output transition',
            'models':records,'acceptance_scope':'Actual greedy native vectors determine acceptance; designed transitions are not substituted in the worker'}
    (a.out/'FIXTURE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'models':[{'name':r['name'],'bytes':r['bytes'],'sha256':r['sha256']} for r in records]}))


if __name__=='__main__':main()
