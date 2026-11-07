import json,unittest
from wire import NativeWire,serialize,environment,recipe,command
class Wire(unittest.TestCase):
    def test_strict_ids_cap_and_capacity(self):
        for t in ([True],[1.0],[],[-1]):
            with self.assertRaises(ValueError):serialize(dict(prompt_ids=t,cap=128),'counts')
        with self.assertRaises(ValueError):serialize(dict(prompt_ids=[1],cap=True),'counts')
        with self.assertRaises(ValueError):serialize(dict(prompt_ids=[1]*900,cap=128),'counts')
    def test_draft_free_effective_zero(self):
        for name in ('R','R_SHADOW','M_QB'):
            r=recipe(name);self.assertFalse(r['spec']);self.assertEqual(r['effective_k'],0)
        for name in ('C_PQ','C_QB'):
            r=recipe(name);self.assertTrue(r['spec']);self.assertEqual((r['effective_k'],r['mask']),(3,3))
    def test_no_QH_without_complete_selection(self):
        with self.assertRaises(ValueError):recipe('C_QH')
        with self.assertRaises(ValueError):recipe('C_QH','PQ')
    def test_sanitizer(self):
        parent=dict(HS_E1_Q='4',HS_Q95_CAPTURE='wrong',LLAMA_ARG_MODEL='wrong',GGML_BAD='1',CUDA_BAD='1',PATH='kept')
        e=environment(parent,recipe('C_QH','QH_D'),'fixed_trace');self.assertEqual(e['HS_Q95_LAYOUT'],'QH_D');self.assertEqual(e['HS_SCOPE_MASK'],'3')
        self.assertEqual(e['PATH'],'kept');self.assertNotIn('HS_E1_Q',e);self.assertNotIn('GGML_BAD',e)
    def test_send_same_admitted_object(self):
        w=serialize(dict(prompt_ids=[3,1,4],cap=128),'counts')
        class Fake:
            def open(self,req,timeout):self.data=req.data;return 'mock'
        o=Fake();self.assertEqual(w.send(o,'http://127.0.0.1:18789/completion',dict(stage='S2',authenticated_F0_commit='unit-only',author_message_sha256='unit-only')),'mock');self.assertIs(o.data,w.wire)
    def test_missing_authorization(self):
        with self.assertRaises(ValueError):serialize(dict(prompt_ids=[1],cap=128),'counts').send(None,'http://127.0.0.1',{})
if __name__=='__main__':unittest.main(verbosity=2)
