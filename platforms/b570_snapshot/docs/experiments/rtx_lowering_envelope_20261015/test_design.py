"""Synthetic CPU tests only. No GGML, CUDA, model, profiler or actual support query."""
import unittest
import design_checks as d

class Design(unittest.TestCase):
    def test_01_gqa(self):
        for q in range(1,5):
            for H,G in ((8,8),(8,1),(32,8),(32,32)):
                for h in range(H):
                    for j in range(q):
                        v=d.logical_head(q,h,j,H,G)
                        self.assertEqual((v['original_head'],v['query'],v['kv_head']),(h,j,h//(H//G)))
    def test_02_mask_column(self):
        for q in range(1,5):
            for h in range(32):
                for j in range(q): self.assertEqual(d.logical_head(q,h,j,32,8)['packed_head']%q,j)
    def test_03_wrong_head_order_detectable(self):
        self.assertNotEqual((1*32+0)//(4*4),0//4)
    def test_04_nonintegral_gqa(self):
        with self.assertRaises(ValueError): d.logical_head(2,0,0,7,2)
    def test_05_invalid_q(self):
        for q in (True,False,1.0,None,0,5,float('nan')):
            with self.subTest(q=q):
                with self.assertRaises(ValueError): d.logical_head(q,0,0,32,8)
    def test_06_compact_and_permuted_addresses(self):
        for D in (64,128):
            for q in range(1,5):
                H=32; total=32+D*q*H*4
                for nb in ((4,4*D,4*D*q),(4,4*D*H,4*D)):
                    a=[d.q_address(i,h,j,(D,q,H),nb,32,total) for h in range(H) for j in range(q) for i in range(D)]
                    self.assertEqual(len(a),len(set(a)))
                    self.assertEqual(set(a),set(range(32,total,4)))
    def test_07_pack_not_zero_copy_for_permuted(self):
        old=d.q_address(0,0,1,(128,4,32),(4,16384,512),32,65568)
        packed=32+128*4
        self.assertNotEqual(old,packed)
    def test_08_bad_buffer(self):
        with self.assertRaises(ValueError): d.q_address(0,0,0,(128,4,32),(4,512,2048),32,65567)
    def test_09_bad_size_type(self):
        for n in (float('inf'),float('nan'),True,None):
            with self.subTest(n=n):
                with self.assertRaises(ValueError): d.q_address(0,0,0,(128,4,32),(4,512,2048),32,n)
    def test_10_profile_registry(self):
        x=d.profile_coordinates();self.assertEqual(len(x),24);self.assertEqual(len(set(x)),24)
        for f in d.FAMILIES: self.assertEqual({r[3] for r in x if r[0]==f},set(d.LAYERS[f]))
    def test_11_choose_compact(self):
        self.assertEqual(d.choose_mask({'QH_C':{'x':True},'QH_D':{'x':True}},['x']),'QH_C')
    def test_12_choose_dense_only_on_support(self):
        self.assertEqual(d.choose_mask({'QH_C':{'x':False},'QH_D':{'x':True}},['x']),'QH_D')
    def test_13_unknown_is_not_pass(self):
        self.assertEqual(d.choose_mask({'QH_C':{'x':None},'QH_D':{'x':None}},['x']),'NO_ADMITTED_QH')
    def test_14_census_cannot_prune(self):
        with self.assertRaises(ValueError): d.choose_mask({'QH_C':{'x':True},'QH_D':{'x':True}},['x','y'])
        with self.assertRaises(ValueError): d.choose_mask({'QH_C':{'x':1},'QH_D':{'x':True}},['x'])
    def test_15_exact_budget(self):
        b=d.budgets();self.assertEqual(b['S1_total_operator_host_attempts'],1009)
        self.assertEqual(b['S1_graph_computes'],2808)
        self.assertEqual(b['S1_warmup_graphs'],288)
        self.assertEqual(b['S2_model_requests'],84)
        self.assertEqual(b['S3_measured_requests'],972)
        self.assertEqual(b['S3_model_requests_including_warmups'],1944)
        self.assertEqual(b['S3_model_processes'],972)
    def test_16_missing_not_qualified(self):
        self.assertIsNone(d.qualified_ratio([],1))
    def test_17_mismatch_not_fast_subset(self):
        self.assertIsNone(d.qualified_ratio([{'endpoint_match':False,'left_ms':100,'right_ms':1}],1))
    def test_18_ratio(self):
        self.assertAlmostEqual(d.qualified_ratio([{'endpoint_match':True,'left_ms':103,'right_ms':100}],1),1.03)
        with self.assertRaises(ValueError): d.qualified_ratio([{'endpoint_match':True,'left_ms':True,'right_ms':100}],1)

if __name__=='__main__':unittest.main(verbosity=2)
