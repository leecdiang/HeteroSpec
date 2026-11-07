"""CPU-only real admission/metric/comparator/ledger negatives; no native launches."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import run_e1 as r

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.snap=self.root/'snap';self.snap.mkdir()
        self.context=dict(layer=0,phase='prefill',q=1,min_key=0)
        def tensor(name,dtype,ne):
            size=4 if dtype==0 else 2;nb=[size]
            for n in ne[:-1]:nb.append(nb[-1]*n)
            body=b'\0'*(nb[-1]*ne[-1]);(self.snap/(name+'.bin')).write_bytes(body)
            return dict(file=name+'.bin',type=dtype,ne=ne,nb=nb,bytes=len(body))
        m=dict(layer=0,phase='prefill',q_occupancy=1,captured_key_extent=2)
        for name,dtype,ne in [('Q',0,[2,1,2,1]),('K',1,[2,2,1,1]),('V',1,[2,2,1,1]),('mask',0,[2,1,1,1]),
                              ('native_QK',0,[2,1,2,1]),('native_softmax',0,[2,1,2,1]),('native_AV',0,[2,1,2,1])]:m[name]=tensor(name,dtype,ne)
        r.e.save(self.snap/'snapshot.json',m);self.meta=m
        self.registry={p.name:r.e.sha(p) for p in self.snap.iterdir()}
    def tearDown(self):self.temp.cleanup()
    def test_real_snapshot_gate_rejects_mask_mutation(self):
        r.admit_snapshot(self.snap,self.registry,self.context)
        p=self.snap/'mask.bin';p.write_bytes(b'\1'+p.read_bytes()[1:])
        with self.assertRaises(ValueError):r.admit_snapshot(self.snap,self.registry,self.context)
    def test_wrong_observed_position_or_selector_rejected(self):
        for key,value in [('layer',1),('phase','continuation'),('q',2),('min_key',128)]:
            c=self.context|{key:value}
            with self.assertRaises(ValueError):r.admit_snapshot(self.snap,self.registry,c)
    def test_own_path_and_repeatability_gate_then_counterexample(self):
        replays=self.root/'replays'
        for arm in ('MQ','PQ','QB'):
            for repeat in (0,1):
                out=replays/f'{arm}-r{repeat}';out.mkdir(parents=True)
                r.e.save(out/'REPLAY.json',dict(arm=arm,backend='CUDA0',fixed_inputs={name:self.meta[name]|dict(readback_bitwise_equal=True) for name in ('Q','K','V','mask')}))
                for s in r.STAGES:(out/(s+'.bin')).write_bytes(r.e.canonical(self.snap,self.meta['native_'+s]))
        result=r.numerical(self.snap,replays);self.assertEqual(result['qualification']['qualification'],'PASS')
        for repeat in (0,1):
            p=replays/f'PQ-r{repeat}'/'QK.bin';p.write_bytes(struct.pack('<f',1.0)+p.read_bytes()[4:])
        result=r.numerical(self.snap,replays)
        self.assertEqual(result['qualification']['qualification'],'PASS')
        self.assertEqual(result['pairs'][0]['first_divergence_operator'],'QK')
        p=replays/'MQ-r1'/'AV.bin';p.write_bytes(struct.pack('<f',2.0)+p.read_bytes()[4:])
        result=r.numerical(self.snap,replays);self.assertEqual(result['qualification']['qualification'],'NOT_ADMITTED');self.assertEqual(result['pairs'],[])

class MetricsLedgerTests(unittest.TestCase):
    def test_ULP_signed_zero_nonfinite_are_explicit(self):
        a=struct.pack('<IIII',0x3f800000,0,0x7f800000,0x7fc00001)
        b=struct.pack('<IIII',0x3f800001,0x80000000,0x7f800000,0x7fc00002)
        x=r.distance(a,b);self.assertFalse(x['bitwise_equal']);self.assertEqual(x['max_ULP'],1)
        self.assertEqual(x['nonfinite_pairs'],2);self.assertEqual(x['nonfinite_bit_mismatches'],1)
    def test_no_retry_request_worker_operator_and_lifetime_caps(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=r.Ledger(Path(d));ledger.charge('F','e1','request','first')
            with self.assertRaises(ValueError):ledger.charge('F','e1','request','first')
            for kind,n in [('request',216),('load',72),('operator',432)]:
                ledger.events=[dict(kind=kind,slot=f'old{i}') for i in range(n)]
                with self.assertRaises(ValueError):ledger.charge('F','e1',kind,'new')
            ledger.events=[];ledger.life=21600
            with self.assertRaises(ValueError):ledger.charge('F','e1','load','new')
if __name__=='__main__':unittest.main(verbosity=2)
