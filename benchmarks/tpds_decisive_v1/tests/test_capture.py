import copy,hashlib,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from trace import reconstruct
from qualify import qualify
from active_kv import parse
from test_study import ordinary_trace,H

def blob(root,name,data):
    (root/name).write_bytes(data)
    return {'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def fixture(root):
    dirs=[root/x for x in ('c','f','r')]
    for d in dirs:d.mkdir()
    trace=ordinary_trace();derived=reconstruct(trace)
    binding={k:H for k in ('reference_identity_sha256','target_model_sha256','producer_sha256','lifecycle_sha256')}
    binding.update(input_sha256=digest(trace['prompt_ids']),cap=3,vocab=8,active_kv_bytes_per_token=4)
    common={'binding':binding,'execution':'NATIVE','completed':True,'reference_bridge_passed':True,'fallback_count':0}
    c={**common,'role':'candidate','invocation_id':'c','trace':trace,'vectors':[],'states':[]}
    f={**common,'role':'free_reference','invocation_id':'f','trace':copy.deepcopy(trace),'vectors':[],'received_forced_tape':False,'autonomous':True}
    r={**common,'role':'forced_reference','invocation_id':'r','prefixes':[]}
    for i,use in enumerate(derived['vector_uses']):
        vals=[float(-j) for j in range(8)];vals[use['decision']]=10.;raw=struct.pack('<8f',*vals)
        cb=blob(dirs[0],f'v{i}',raw);fb=blob(dirs[1],f'v{i}',raw);rb=blob(dirs[2],f'v{i}',raw)
        state=b''.join(struct.pack('<i',x) for x in use['prefix']);cs=blob(dirs[0],f's{i}',state);rs=blob(dirs[2],f's{i}',state)
        c['vectors'].append({'prefix':use['prefix'],'key':use['key'],'blob':cb})
        f['vectors'].append({'prefix':use['prefix'],'blob':fb})
        r['prefixes'].append({'prefix':use['prefix'],'frontier':rb,'active_kv':rs,'active_layout_sha256':H})
        c['states'].append({**derived['states'][i],'active_kv':cs,'frontier':cb,'active_layout_sha256':H})
    for d,obj in zip(dirs,(c,f,r)):write_new(d/'capture.json',obj)
    return [d/'capture.json' for d in dirs]

def replace_json(path,fn):
    v=read(path);fn(v);path.write_text(__import__('json').dumps(v))

class CaptureTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.paths=fixture(self.root)
    def tearDown(self):self.tmp.cleanup()
    def test_complete_fixture_not_model(self):self.assertEqual(qualify(*self.paths)['vector_uses'],3)
    def test_same_process(self):
        replace_json(self.paths[1],lambda x:x.update(invocation_id='c'))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_contaminated_free(self):
        replace_json(self.paths[1],lambda x:x.update(received_forced_tape=True))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_old_R_bridge_missing(self):
        replace_json(self.paths[0],lambda x:x.update(reference_bridge_passed=False))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_oracle_swap(self):
        replace_json(self.paths[0],lambda x:x['binding'].update(reference_identity_sha256='b'*64))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_lost_KV_even_with_new_hash(self):
        b=self.paths[0].parent/'s2';b.write_bytes(b'\0'*b.stat().st_size)
        replace_json(self.paths[0],lambda x:x['states'][2]['active_kv'].update(sha256=file_sha(b)))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_stale_frontier(self):
        replace_json(self.paths[0],lambda x:x['states'][2].update(frontier=x['states'][0]['frontier']))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_unconsumed_suffix(self):
        replace_json(self.paths[0],lambda x:x['states'][2].update(unmaterialized_suffix=[]))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_truncated_vector(self):
        (self.paths[0].parent/'v0').write_bytes(b'\0'*4)
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_nan_even_with_new_hash(self):
        b=self.paths[0].parent/'v0';b.write_bytes(struct.pack('<8f',float('nan'),0,0,10,0,0,0,0))
        replace_json(self.paths[0],lambda x:x['vectors'][0]['blob'].update(sha256=file_sha(b)))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_early_termination(self):
        replace_json(self.paths[0],lambda x:x['trace'].update(steps=[]))
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_missing_forced(self):
        replace_json(self.paths[2],lambda x:x['prefixes'].pop())
        with self.assertRaises(Invalid):qualify(*self.paths)
    def test_path_escape(self):
        replace_json(self.paths[0],lambda x:x['vectors'][0]['blob'].update(path='../f/v0'))
        with self.assertRaises(Invalid):qualify(*self.paths)


def make_state(trans=0):
    p={'format':'dense_seq_f16_v1','writer_sha256':H,'target_model_sha256':H,'layer_map_source_sha256':H,
      'host_writer_reviewed':True,'capacity':128,'layers':[{'id':0,'k_elements':2,'v_elements':3},{'id':1,'k_elements':1,'v_elements':2}]}
    raw=bytearray(struct.pack('<IiII',0xaf143cd8,0,1,3))
    for pos in range(3):raw+=struct.pack('<iIi',pos,1,0)
    raw+=struct.pack('<II',trans,2);ks=[];vs=[]
    for j,l in enumerate(p['layers']):
        b=struct.pack('<'+'H'*(3*l['k_elements']),*[100*j+i+1 for i in range(3*l['k_elements'])]);ks.append(b)
        raw+=struct.pack('<iQ',1,l['k_elements']*2)+b
    for j,l in enumerate(p['layers']):
        b=struct.pack('<'+'H'*(3*l['v_elements']),*[1000+100*j+i for i in range(3*l['v_elements'])]);vs.append(b)
        raw+=struct.pack('<i',1)
        if not trans:raw+=struct.pack('<Q',l['v_elements']*2)+b
        else:
            raw+=struct.pack('<II',2,l['v_elements'])
            raw+=b''.join(b[(t*l['v_elements']+c)*2:(t*l['v_elements']+c)*2+2] for c in range(l['v_elements']) for t in range(3))
    expected=b''.join(ks[j][t*l['k_elements']*2:(t+1)*l['k_elements']*2]+vs[j][t*l['v_elements']*2:(t+1)*l['v_elements']*2] for t in range(3) for j,l in enumerate(p['layers']))
    return bytes(raw),p,expected

class ParserTests(unittest.TestCase):
    def test_two_layouts(self):
        for trans in (0,1):
            b,p,w=make_state(trans);self.assertEqual(parse(b,[0,1,2],p)[0],w)
    def test_no_profile_assumption(self):
        b,p,_=make_state();p['host_writer_reviewed']=False
        with self.assertRaises(Invalid):parse(b,[0,1,2],p)
    def test_wrong_layer_map(self):
        b,p,_=make_state();p['layers'][0]['k_elements']=3
        with self.assertRaises(Invalid):parse(b,[0,1,2],p)
    def test_no_trailing(self):
        b,p,_=make_state()
        with self.assertRaises(Invalid):parse(b+b'xx',[0,1,2],p)
    def test_truncations(self):
        b,p,_=make_state()
        for n in range(len(b)):
            with self.assertRaises(Invalid):parse(b[:n],[0,1,2],p)
    def test_format_not_numeric_proof(self):
        b,p,w=make_state();b=b[:-1]+bytes([b[-1]^1]);self.assertNotEqual(parse(b,[0,1,2],p)[0],w)
    def test_contiguous_only(self):
        b,p,_=make_state()
        with self.assertRaises(Invalid):parse(b,[0,2,3],p)

if __name__=='__main__':unittest.main()
