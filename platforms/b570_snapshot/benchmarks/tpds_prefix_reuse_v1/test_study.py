"""Synthetic CPU fixtures only. No experimental output or native qualification."""
import copy
from collections import Counter
import math
import unittest
import study as s

H='a'*64

def manifest(n=50):
    rows=[]
    for i in range(n):
        h=230+i;prefix=list(range(h));req=prefix+list(range(700,900))
        rows.append({'id':f'msg-{i}','root_id':f'root-{i}','cached_ids':prefix,
                     'request_ids':req,'effective_head':h,'physical_head':h,
                     'native_dense_verified':True,'source_sha256':H,'history_exposed':False})
    return {'schema_version':1,'native_tokenization':True,'corpus_revision':s.CFG['corpus_revision'],
            'tokenizer_sha256':H,'template_sha256':H,'exposure_audit_sha256':H,
            'deployment_id':'SYNTHETIC_TEST_ONLY','capacity':1024,'padding':256,'qmax':32,
            'output_cap':128,'cache_granule':1,'reuse_policy':'exact_lcp','rows':rows}

def results(p,auto=9.0):
    out=s.schedule(p);out.update(source_freeze_sha256=H,oracle_sha256=H,selector_sha256=H)
    for r in out['records']:
        r.update(seconds=auto if r['arm']=='AUTO' else 10.,qualified=True,
                 actual_output_sha256=H,expected_output_sha256=H,source_freeze_sha256=H,oracle_sha256=H)
    return out

class Geometry(unittest.TestCase):
    def test_lcp(self):self.assertEqual(s.lcp([1,2,3],[1,2,4]),2)
    def test_boundary(self):self.assertEqual(s.groups(253,8),[3,5])
    def test_exact_boundary(self):self.assertEqual(s.groups(256,32),[32])
    def test_capacity_clamp(self):self.assertEqual(s.groups(1016,8,256,1024),[8])
    def test_overflow(self):
        with self.assertRaises(ValueError):s.plan(1000,100,'QB',capacity=1024)
    def test_wb_reset(self):
        old=s.plan(253,100,'WB-cut');new=s.plan(253,100,'WB-rechunk')
        self.assertEqual([r['width'] for r in old],[3,29,32,32,4])
        self.assertEqual([r['width'] for r in new],[3,32,32,32,1])
    def test_aligned_same(self):
        for n in [1,8,32,63,256,511]:
            self.assertEqual(s.plan(256,n,'WB-cut'),s.plan(256,n,'WB-rechunk'))
    def test_multiboundary_rechunk(self):
        self.assertLess(len(s.plan(253,800,'WB-rechunk')),len(s.plan(253,800,'WB-cut')))
    def test_conservation_exhaustive(self):
        for h in range(256):
            for n in [1,3,4,8,31,32,33,100,600]:
                for a in s.FIXED:
                    p=s.plan(h,n,a)
                    self.assertEqual(sum(x['width'] for x in p),n)
                    self.assertEqual(p[0]['head'],h)
                    for x,y in zip(p,p[1:]):self.assertEqual(x['head']+x['width'],y['head'])
                    if a!='QB':self.assertTrue(all(len(s.groups(x['head'],x['width']))==1 for x in p))
    def test_bool_rejected(self):
        with self.assertRaises(ValueError):s.groups(True,8)

class Selection(unittest.TestCase):
    def test_counts(self):
        p=s.select(manifest());self.assertEqual(len(p['test']),32);self.assertEqual(len(p['calibration']),12)
    def test_order_independent(self):
        m=manifest();p=s.select(m);m['rows'].reverse();q=s.select(m)
        self.assertEqual(p['test'],q['test']);self.assertEqual(p['calibration'],q['calibration'])
    def test_shortfall(self):
        with self.assertRaises(ValueError):s.select(manifest(43))
    def test_root_grouping(self):
        m=manifest();m['rows'][0]['root_id']=m['rows'][1]['root_id']
        p=s.select(m);self.assertEqual(len({r['root_id'] for r in p['test']+p['calibration']}),44)
    def test_outcome_leakage(self):
        m=manifest();m['rows'][0]['seconds']=3
        with self.assertRaises(ValueError):s.select(m)
    def test_not_native(self):
        m=manifest();m['native_tokenization']=False
        with self.assertRaises(ValueError):s.select(m)
    def test_fake_physical_head(self):
        m=manifest();m['rows'][0]['physical_head']+=1
        with self.assertRaises(ValueError):s.select(m)
    def test_cache_granule(self):
        m=manifest();m.update(reuse_policy='floor_lcp',cache_granule=32)
        for r in m['rows']:r['effective_head']=r['physical_head']=len(r['cached_ids'])//32*32
        self.assertEqual(s.inspect_manifest(m)['crossed_requests'],0)
    def test_wrong_effective_prefix(self):
        m=manifest();m['rows'][0]['effective_head']-=1
        with self.assertRaises(ValueError):s.select(m)
    def test_exposure_excluded(self):
        m=manifest();m['rows'][0]['history_exposed']=True
        p=s.select(m);self.assertFalse(any(r['id']=='msg-0' for r in p['test']+p['calibration']))
    def test_no_output_based_length_truncation(self):
        m=manifest();m['rows'][0]['request_ids']+=list(range(600))
        c=s.inspect_manifest(m);self.assertEqual(c['rejected'][0]['reason'],'prompt plus cap exceeds capacity')

class Schedule(unittest.TestCase):
    def setUp(self):self.p=s.select(manifest());self.sch=s.schedule(self.p)['records']
    def test_complete(self):self.assertEqual(len(self.sch),1024)
    def test_immediate_warmup(self):
        for a,b in zip(self.sch[::2],self.sch[1::2]):
            self.assertEqual(a['kind'],'warmup');self.assertEqual(b['kind'],'measure')
            self.assertEqual({k:v for k,v in a.items() if k!='kind'},{k:v for k,v in b.items() if k!='kind'})
    def test_position_balance(self):
        for r in self.p['test']:
            rows=[x for x in self.sch if x['id']==r['id'] and x['kind']=='measure']
            for a in s.ARMS:self.assertEqual(sorted(x['position'] for x in rows if x['arm']==a),[0,1,2,3])
    def test_predecessor_balance(self):
        for r in self.p['test']:
            pairs=[]
            for session in range(4):
                rows=[x['arm'] for x in self.sch if x['id']==r['id'] and x['session']==session and x['kind']=='measure']
                pairs.extend(zip(rows,rows[1:]))
            self.assertEqual(len(set(pairs)),12)
    def test_panel_leakage(self):
        self.p['test'][0]['root_id']=self.p['calibration'][0]['root_id']
        with self.assertRaises(ValueError):s.schedule(self.p)

class Analysis(unittest.TestCase):
    def setUp(self):self.p=s.select(manifest());self.r=results(self.p)
    def test_positive(self):
        a=s.analyze(self.r,self.p,draws=100)
        self.assertTrue(a['engineering_screen_pass'])
        self.assertAlmostEqual(a['contrasts'][0]['baseline_over_AUTO'],10/9)
        self.assertAlmostEqual(a['contrasts'][0]['time_reduction_pct'],10)
    def test_negative(self):
        a=s.analyze(results(self.p,11),self.p,draws=100);self.assertFalse(a['engineering_screen_pass'])
    def test_parity_is_not_success(self):self.assertFalse(s.analyze(results(self.p,10),self.p,draws=100)['engineering_screen_pass'])
    def test_one_stronger_baseline_blocks_claim(self):
        for r in self.r['records']:
            if r['arm']=='WB-rechunk':r['seconds']=8
        self.assertFalse(s.analyze(self.r,self.p,draws=100)['engineering_screen_pass'])
    def test_missing(self):
        self.r['records'].pop()
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_duplicate(self):
        self.r['records'].append(self.r['records'][0])
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_nonfinite(self):
        self.r['records'][1]['seconds']=float('nan')
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_unqualified(self):
        self.r['records'][1]['qualified']=False
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_wrong_output(self):
        self.r['records'][1]['actual_output_sha256']='b'*64
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_source_drift(self):
        self.r['records'][1]['source_freeze_sha256']='b'*64
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_panel_binding(self):
        self.r['panel_sha256']='b'*64
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_no_request_bootstrap(self):
        a=s.analyze(self.r,self.p,draws=100)
        self.assertEqual(a['independent_roots'],32);self.assertIn('all four',a['resampling_unit'])
    def test_warmup_failure_blocks(self):
        self.r['records'][0]['seconds']=None
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_different_oracle_outputs(self):
        self.r['records'][0]['actual_output_sha256']=self.r['records'][0]['expected_output_sha256']='b'*64
        with self.assertRaises(ValueError):s.analyze(self.r,self.p,draws=100)
    def test_budget(self):
        b=s.CFG['requests'];self.assertEqual(sum(b[k] for k in ('development','calibration','main_qualification','main_cost_and_warmup','aligned_control')),b['planned']);self.assertLessEqual(b['planned'],b['initial_tranche'])


class Selector(unittest.TestCase):
    def setUp(self):
        import selector
        self.selector=selector;self.p=s.select(manifest());self.c={'stage':'calibration','panel_sha256':s.digest(self.p),'deployment_id':self.p['deployment_id'],'source_freeze_sha256':H,'calibration_total_seconds':1000,'records':[]}
        for r in self.p['calibration']:
            for session in range(2):
                for arm in s.FIXED:
                    for kind in ('warmup','measure'):
                        self.c['records'].append({'id':r['id'],'root_id':r['root_id'],'session':session,'arm':arm,'kind':kind,'seconds':10.,'qualified':True,'source_freeze_sha256':H})
    def test_tie_fallback(self):self.assertEqual(self.selector.fit(self.c,self.p)['global_fixed_arm'],'WB-rechunk')
    def test_fit_all_complete(self):self.assertEqual(len(self.c['records']),144);self.selector.fit(self.c,self.p)
    def test_missing_no_fit(self):
        self.c['records'].pop()
        with self.assertRaises(ValueError):self.selector.fit(self.c,self.p)
    def test_no_test_id(self):
        self.c['records'][0]['id']=self.p['test'][0]['id']
        with self.assertRaises(ValueError):self.selector.fit(self.c,self.p)
    def test_cost_not_free(self):
        self.c['calibration_total_seconds']=None
        with self.assertRaises(ValueError):self.selector.fit(self.c,self.p)
    def test_deployment_guard(self):
        pol=self.selector.fit(self.c,self.p)
        with self.assertRaises(ValueError):self.selector.choose(pol,'another_gpu',extra_calls=1,qb_calls=8)
    def test_lookup(self):
        pol=self.selector.fit(self.c,self.p)
        for x in [0,1,2,10]:self.assertEqual(self.selector.choose(pol,self.p['deployment_id'],extra_calls=x,qb_calls=8),'WB-rechunk')
    def test_invalid_feature(self):
        pol=self.selector.fit(self.c,self.p)
        with self.assertRaises(ValueError):self.selector.choose(pol,self.p['deployment_id'],extra_calls=1,qb_calls=0)

if __name__=='__main__':unittest.main()
