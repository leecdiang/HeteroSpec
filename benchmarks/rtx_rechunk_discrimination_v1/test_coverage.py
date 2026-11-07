import copy,unittest
from coverage import plan,select,ARMS

def fixture(n=10):
    rows=[]
    for i in range(n):
        rows.append(dict(id=f'p{i}',root_id=f'r{i}',source_sha256='a'*64,
                         physical_head=205,effective_head=205,prompt_tokens=289,append_tokens=84,
                         request_token_sha256='b'*64,cached_token_sha256='c'*64))
    census=dict(capacity=4096,padding=256,cache_granule=1,eligible=rows)
    prior=dict(calibration=[{'root_id':f'old-c{i}'} for i in range(12)],test=[{'root_id':f'old-t{i}'} for i in range(32)])
    exclusions=dict(root_ids=[],evidence=['synthetic test; no native provenance'])
    return census,prior,exclusions
class CoverageTests(unittest.TestCase):
    def test_known_active(self):
        self.assertEqual([w for _,w in plan(205,84,'WB-cut')],[32,19,13,20])
        self.assertEqual([w for _,w in plan(205,84,'WB-rechunk')],[32,19,32,1])
    def test_same_short_cross(self):self.assertEqual(plan(249,9,'WB-cut'),plan(249,9,'WB-rechunk'))
    def test_aligned(self):self.assertEqual(plan(256,320,'WB-cut'),plan(256,320,'WB-rechunk'))
    def test_coverage(self):
        for h in range(257):
            for n in (1,8,31,32,33,64,84,257):
                for a in ARMS:
                    p=plan(h,n,a);self.assertEqual(sum(w for _,w in p),n)
                    self.assertTrue(all(1<=w<=32 for _,w in p))
                    self.assertEqual([s for s,_ in p],[h+sum(w for _,w in p[:i]) for i in range(len(p))])
                    if a!='QB':self.assertTrue(all(s//256==(s+w-1)//256 for s,w in p))
    def test_max8(self):self.assertEqual(len(select(*fixture())['selected']),8)
    def test_small_stop(self):self.assertEqual(select(*fixture(3))['status'],'STOP_NO_GPU')
    def test_exclusions(self):
        c,p,e=fixture();e['root_ids']=['r0','r1','r2'];out=select(c,p,e)
        self.assertEqual(len(out['selected']),7);self.assertTrue(all(r['root_id'] not in e['root_ids'] for r in out['selected']))
    def test_prior_block(self):
        c,p,e=fixture();p['test'][0]['root_id']='r0';self.assertNotIn('r0',[r['root_id'] for r in select(c,p,e)['selected']])
    def test_order_independent(self):
        c,p,e=fixture();a=select(c,p,e)['selected'];c['eligible'].reverse();self.assertEqual(a,select(c,p,e)['selected'])
    def test_outcome_refusal(self):
        c,p,e=fixture();c['eligible'][0]['seconds']=1
        with self.assertRaises(ValueError):select(c,p,e)
    def test_duplicate_refusal(self):
        c,p,e=fixture();c['eligible'].append(c['eligible'][0])
        with self.assertRaises(ValueError):select(c,p,e)
    def test_bad_capacity(self):
        c,p,e=fixture();c['capacity']=1024
        with self.assertRaises(ValueError):select(c,p,e)
    def test_bad_tokens(self):
        c,p,e=fixture();c['eligible'][0]['request_token_sha256']='x'*64
        with self.assertRaises(ValueError):select(c,p,e)
    def test_no_provenance(self):
        c,p,e=fixture();e['evidence']=[]
        with self.assertRaises(ValueError):select(c,p,e)
    def test_no_crossing(self):
        c,p,e=fixture()
        for r in c['eligible']:r.update(physical_head=32,effective_head=32,prompt_tokens=116)
        self.assertEqual(select(c,p,e)['status'],'STOP_NO_GPU')
    def test_no_path_cherry_pick(self):
        c,p,e=fixture();r=copy.deepcopy(c['eligible'][0]);r['id']='other';r.update(physical_head=32,effective_head=32,prompt_tokens=116);c['eligible'].append(r)
        out=select(c,p,e);self.assertEqual(out['roots_seen'],10)
        self.assertLessEqual(sum(r['root_id']=='r0' for r in out['selected']),1)
if __name__=='__main__':unittest.main()
