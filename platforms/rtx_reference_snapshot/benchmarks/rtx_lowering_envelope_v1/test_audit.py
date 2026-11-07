import copy,struct,unittest
import audit
class Audit(unittest.TestCase):
    def test_complete_census_rule_not_pass_booleans(self):
        rows=[]
        for i in range(168):
            for name in ('MQ','PQ','QB','QH_C','QH_D'):
                for stages in (False,True):rows.append(dict(descriptor_id=str(i),layout=name,stage_outputs=stages,nodes=[dict(id=0,op='MUL_MAT',metadata_only=False,CUDA_support=None,placement=None)],full_support=None))
        expected=dict(records=rows);actual=copy.deepcopy(expected)|dict(GPU_initializations=1,graph_computes=0)
        for r in actual['records']:r['nodes'][0]['CUDA_support']=True;r['full_support']=True
        self.assertEqual(audit.census(expected,actual)['selected_QH'],'QH_C')
        first=next(r for r in actual['records'] if r['layout']=='QH_C');first['nodes'][0]['CUDA_support']=False;first['full_support']=False
        self.assertEqual(audit.census(expected,actual)['selected_QH'],'QH_D')
        first['full_support']=True
        with self.assertRaises(AssertionError):audit.census(expected,actual)
        first['full_support']=False;actual['records'].pop()
        with self.assertRaises(AssertionError):audit.census(expected,actual)
    def test_missing_actual_modules_rejected(self):
        with self.assertRaises(AssertionError):audit.modules([],{},'.')
    def test_zero_error_not_a_tolerance(self):
        a=struct.pack('<I',0x3f800000);b=struct.pack('<I',0x3f800001)
        self.assertFalse(audit.numeric(a,b)['bitwise_equal']);self.assertEqual(audit.numeric(a,b)['max_ULP'],1)
    def test_signedzero_and_nonfinite(self):
        self.assertFalse(audit.numeric(struct.pack('<I',0),struct.pack('<I',0x80000000))['bitwise_equal'])
        self.assertEqual(audit.numeric(struct.pack('<I',0x7fc00001),struct.pack('<I',0x7fc00002))['nonfinite_mismatches'],1)
    def test_independent_completed_timer(self):
        r=dict(raw_completed_intervals=[dict(begin_ns=100,end_ns=1000100)],completed_host_wall_ms=[1.0],synchronization='cudaDeviceSynchronize')
        self.assertEqual(audit.completed_intervals(r),[1.0]);r['completed_host_wall_ms']=[.1]
        with self.assertRaises(AssertionError):audit.completed_intervals(r)
    def test_enqueue_only_is_not_completion(self):
        r=dict(raw_completed_intervals=[dict(begin_ns=0,end_ns=100)],completed_host_wall_ms=[.0001],synchronization='enqueue only')
        with self.assertRaises(AssertionError):audit.completed_intervals(r)
    def test_endpoints_complete_and_stop(self):
        a=dict(tokens=[1,2],tokens_predicted=2,truncated=False,stop_type='limit');self.assertTrue(audit.endpoints(a,a,2,{3}))
        b=a|dict(tokens=[1,4]);self.assertFalse(audit.endpoints(a,b,2,{3}))
        with self.assertRaises(AssertionError):audit.endpoints(a,a|dict(tokens_predicted=1),2,{3})
    def test_wrong_eog_not_qualified(self):
        a=dict(tokens=[1,2],tokens_predicted=2,truncated=False,stop_type='eos')
        with self.assertRaises(AssertionError):audit.endpoints(a,a,2,{3})
if __name__=='__main__':unittest.main(verbosity=2)
