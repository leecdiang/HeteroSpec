"""Independent arithmetic, resource, ownership and corrupted-trace tests."""
import copy
from fractions import Fraction
import json
import random
import unittest
import fp32
import checker
from model import simulate,MAPPINGS

ONE=0x3f800000
def workload(q=1,k=2,c=1):return dict(id='test',owner='A',epoch=7,q=q,keys=k,channels=c,P=[[ONE]*k for _ in range(q)],V=[[ONE]*c for _ in range(k)])
def resource(**kw):
    return dict(lanes=4,issue_rate=1,compute_latency=2,contexts=8,context_ports=4,context_write_ports=4,
        buffer_bytes=512,banks=4,bank_ports=4,broadcast_words=8,memory_ports=4,memory_latency=2,queue_depth=8,
        output_ports=4,output_latency=1,store_queue_depth=4,extra_issue_latency=0)|kw
def run(w,r,m='B1_PACKED_MULTICAST'):
    result=simulate(w,r,m);check=checker.validate(w,r,result['trace'],result['output']);return result,check

class Arithmetic(unittest.TestCase):
    def test_ties_subnormal_signed_zero(self):
        self.assertEqual(fp32.add(ONE,0x33800000),ONE)
        self.assertEqual(fp32.add(ONE,0x33800001),ONE+1)
        self.assertEqual(fp32.mul(1,0x3f000000),0)
        self.assertEqual(fp32.mul(3,0x3f000000),2)
        self.assertEqual(fp32.mul(0x80000000,ONE),0x80000000)
        self.assertEqual(fp32.add(0x80000000,0x80000000),0x80000000)
        self.assertEqual(fp32.add(ONE,ONE|0x80000000),0)
    def test_association_counterexample(self):
        a,b,c=0x4b800000,ONE,0xcb800000
        self.assertEqual(fp32.add(fp32.add(a,b),c),0)
        self.assertEqual(fp32.add(a,fp32.add(b,c)),ONE)
    def test_fma_counterexample(self):
        a,b,c=0x3f800001,0x3f7ffffe,0xbf800000
        self.assertEqual(fp32.add(fp32.mul(a,b),c),0)
        self.assertEqual(checker.round_fraction(checker.value(a)*checker.value(b)+checker.value(c)),0xa8800000)
    def test_invalid_overflow(self):
        for x in (True,-1,2**32,0x7f800000,0xff800000,0x7fc00000):
            with self.assertRaises(ValueError):fp32.decode(x)
            with self.assertRaises(ValueError):checker.value(x)
        with self.assertRaises(OverflowError):fp32.mul(0x7f7fffff,0x40000000)
        with self.assertRaises(OverflowError):checker.product(0x7f7fffff,0x40000000)
    def test_random_independent_fraction_oracle(self):
        rng=random.Random(20261015)
        words=[0,0x80000000,1,0x80000001,0x007fffff,0x00800000]
        words += [(rng.randrange(2)<<31)|(rng.randrange(40,180)<<23)|rng.randrange(1<<23) for _ in range(3000)]
        for a,b in zip(words,words[1:]+words[:1]):
            self.assertEqual(fp32.add(a,b),checker.summed(a,b))
            self.assertEqual(fp32.mul(a,b),checker.product(a,b))

class ResourceAndTrace(unittest.TestCase):
    def test_tiny_independent_critical_path_bound(self):
        # fetch0 -> fill/mul1 -> done/add2 -> done/store3 -> commit4.
        w=workload(k=1);r=resource(memory_latency=1,compute_latency=1)
        a,b=run(w,r);self.assertEqual(a['cycles'],4);self.assertEqual(b['micro_operations'],2)
    def test_all_mappings_q1_q4_parity_and_input_immutable(self):
        for q in (1,4):
            w=workload(q=q,k=3,c=2);before=json.dumps(w,sort_keys=True)
            results=[run(w,resource(),m)[0] for m in MAPPINGS]
            self.assertTrue(all(x==results[0] for x in results));self.assertEqual(before,json.dumps(w,sort_keys=True))
    def test_candidate_overhead_erases_parity(self):
        w=workload(q=4,k=4,c=2);a,_=run(w,resource());b,_=run(w,resource(extra_issue_latency=1),'C_JOINT')
        self.assertGreater(b['cycles'],a['cycles']);self.assertEqual(a['output'],b['output'])
    def test_banks_queues_write_ports(self):
        w=workload(q=4,k=4,c=2)
        a,_=run(w,resource());b,_=run(w,resource(banks=1,bank_ports=2))
        c,z=run(w,resource(memory_ports=1,broadcast_words=2,queue_depth=2,context_write_ports=1,store_queue_depth=1,output_ports=1))
        self.assertGreaterEqual(b['cycles'],a['cycles']);self.assertGreaterEqual(c['cycles'],a['cycles'])
        self.assertGreater(b['waits'].get('bank',0)+b['waits'].get('fill_bank',0),0)
        self.assertLessEqual(z['queue_peak'],2);self.assertLessEqual(z['buffer_peak_bytes'],512)
    def test_capacity_and_unsupported_staging_rejected(self):
        for kw in (dict(buffer_bytes=100),dict(contexts=1),dict(bank_ports=1),dict(broadcast_words=1)):
            with self.assertRaises(ValueError):simulate(workload(q=4,c=2),resource(**kw),'C_JOINT')
    def reject(self,mutation):
        w=workload(q=2,k=3,c=2);r=resource();result,_=run(w,r);trace=copy.deepcopy(result['trace']);mutation(trace)
        with self.assertRaises((AssertionError,KeyError,ValueError,IndexError)):checker.validate(w,r,trace,result['output'])
    def test_corrupt_fill_payload(self):self.reject(lambda t:next(e for e in t if e['kind']=='FILL').update(bits=0))
    def test_corrupt_fill_uses(self):self.reject(lambda t:next(e for e in t if e['kind']=='FILL').update(uses=999))
    def test_wrong_owner_same_address(self):self.reject(lambda t:next(e for e in t if e['kind']=='FETCH').update(owner='B'))
    def test_stale_epoch_same_address(self):self.reject(lambda t:next(e for e in t if e['kind']=='FILL').update(epoch=6))
    def test_missing_owner(self):self.reject(lambda t:t[0].pop('owner'))
    def test_missing_epoch(self):self.reject(lambda t:t[0].pop('epoch'))
    def test_stale_uid(self):self.reject(lambda t:next(e for e in t if e['kind']=='ISSUE').update(uid='stale'))
    def test_duplicate_done(self):
        def mutate(t):
            i=next(i for i,e in enumerate(t) if e['kind']=='DONE');t.insert(i+1,copy.deepcopy(t[i]))
        self.reject(mutate)
    def test_missing_done(self):self.reject(lambda t:t.pop(next(i for i,e in enumerate(t) if e['kind']=='DONE')))
    def test_duplicate_commit(self):self.reject(lambda t:t.append(copy.deepcopy(t[-1])))
    def test_early_completion(self):self.reject(lambda t:next(e for e in t if e['kind']=='DONE').update(cycle=0))
    def test_illegal_dependency_and_rounding(self):
        self.reject(lambda t:next(e for e in t if e['kind']=='ISSUE' and e['op']=='ADD').update(t=2))
        self.reject(lambda t:next(e for e in t if e['kind']=='ISSUE' and e['op']=='ADD').update(bits=0))
    def test_checker_detects_resource_violation(self):
        w=workload(q=4,k=2,c=2);r=resource();a,_=run(w,r)
        for changed in (dict(context_write_ports=1),dict(context_ports=1),dict(buffer_bytes=100),dict(memory_ports=1),dict(bank_ports=1),dict(broadcast_words=1)):
            with self.assertRaises(AssertionError):checker.validate(w,r|changed,a['trace'],a['output'])
if __name__=='__main__':unittest.main(verbosity=2)
