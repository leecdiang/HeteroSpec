"""Actual CPU subprocess fault injection plus exact policy-clock boundaries."""
import copy
import json
import os
import pathlib
import threading
import time
import unittest
import ctypes
import mmap
import uuid
from legacy import HERE,OLD,ROOT,OUT,LIMITS,PYTHON,load,sha,save,need,modules
from timing import Coverage,MAX_GAP_NS,VirtualCounter
from supervisor import supervise
from lifecycle_audit import audit
from workers import rows
from registration import plan,serialize

EVIDENCE=None

class Case:
    def __init__(self,name,virtual=True,child=None,faults=(),fault_flags=None,bad_hash=False,seconds=8):
        self.root=EVIDENCE/name;self.root.mkdir();self.folder=self.root/'host';self.clockfile=self.root/'CLOCK';self.value=10_000_000_000
        self.clockfile.write_text(str(self.value));self.release=self.root/'RELEASE_CHILD'
        self.clocktag='Local\\HeteroSpecCPUClock-'+str(uuid.uuid4());self.counter=VirtualCounter(self.clocktag);self.counter.write(self.value)
        module=self.root/'CPU_MODULE.bin';module.write_bytes(b'CPU-ONLY-HASH-TARGET')
        self.job=dict(purpose='CPU_TEST',folder=str(self.folder),disk_root=str(ROOT),run_root=str(self.root),storage_roots=[str(self.root)],
            limits=LIMITS,per_slot_seconds=seconds,panel_seconds=30,panel_begin_ns=self.value if virtual else time.monotonic_ns(),
            test_module=str(module),test_module_sha256='0'*64 if bad_hash else sha(module),
            cpu_child=dict(release=str(self.release),**(child or {})),faults={k:str(self.root/('release_'+k)) for k in faults})
        if virtual:self.job['virtual_clock']=self.clocktag
        self.job['faults'].update(fault_flags or {})
        self.result=None;self.error=None
        def run():
            try:self.result=supervise(self.job,[str(PYTHON),str(HERE/'cpu_child.py'),str(self.folder/'CHILD.json')])
            except BaseException as e:self.error=e
        self.thread=threading.Thread(target=run,name='CPU_TEST_COORDINATOR');self.thread.start()
    def wait(self,condition,why='barrier',timeout=8):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            if condition():return
            if self.error:raise self.error
            time.sleep(.005)
        raise AssertionError('CPU test barrier timeout: '+why)
    def advance(self,ns):
        self.value+=ns;self.counter.write(self.value)
        with (self.root/'CLOCK_ADVANCES.jsonl').open('a') as f:f.write(json.dumps(dict(virtual_ns=self.value))+'\n')
    def release_fault(self,name):pathlib.Path(self.job['faults'][name]).write_text('release')
    def fault_entered(self,name):return pathlib.Path(self.job['faults'][name]).with_suffix('.entered').exists()
    def sample_count(self,kind):return len([r for r in rows(self.folder/'MONITOR.jsonl') if r.get('stream')==kind and r['event']=='READ_END'])
    def wait_GO(self):self.wait(lambda:(self.folder/'EXECUTED').exists(),'actual child GO')
    def finish(self):
        self.release.write_text('exit');self.wait(lambda:not self.thread.is_alive(),'supervisor complete');self.thread.join()
        if self.error:raise self.error
        return self.result

class Tests(unittest.TestCase):
    def setUp(self):self.cases=[]
    def case(self,*args,**kwargs):
        c=Case(self.id().split('.')[-1]+'_'+str(len(self.cases)),*args,**kwargs);self.cases.append(c);return c
    def tearDown(self):
        for c in self.cases:
            if c.thread.is_alive():
                c.release.write_text('cleanup')
                for k,v in c.job['faults'].items():
                    if isinstance(v,str):c.release_fault(k)
                if 'virtual_clock' in c.job:c.advance(200*10**9)
                c.thread.join(timeout=10)
                self.assertFalse(c.thread.is_alive(),'CPU test process cleanup must finish')
    def test_normal_real_clock_and_no_GPU_modules(self):
        c=self.case(virtual=False);c.wait_GO();r=c.finish();self.assertIsNone(r['stop']);audit(c.folder)
        self.assertGreater(r['exit_observed_ns'],r['spawn_returned_ns'])
        for stream in ('resource','directory'):self.assertGreater(r['coverage'][stream]['valid_reads'],0)
        self.assertGreater(r['process_times']['exit_FILETIME'],0)
        self.assertTrue(rows(c.folder/'raw.jsonl')[0]['modules'])
    def test_post_exit_audit_over_one_second_is_separate(self):
        c=self.case(faults=('post_audit',));c.wait_GO();c.release.write_text('exit')
        c.wait(lambda:c.fault_entered('post_audit'),'post-exit audit barrier')
        exit_ns=load(c.folder/'EXIT_OBSERVED.json')['exit_observed_ns'];c.advance(2*10**9);c.release_fault('post_audit')
        r=c.finish();self.assertIsNone(r['stop']);self.assertEqual(r['post_exit_audit_seconds'],2)
        self.assertEqual(r['exit_observed_ns'],exit_ns);audit(c.folder)
        self.assertTrue(all(row.get('end_ns',exit_ns)<=exit_ns for row in rows(c.folder/'MONITOR.jsonl') if row['event']=='READ_END'))
    def test_real_running_resource_stall_over_one_second_fails(self):
        c=self.case(virtual=False,faults=('before_resource',));c.wait(lambda:c.fault_entered('before_resource'))
        c.wait(lambda:(c.folder/'EXIT_OBSERVED.json').exists(),'real >1s supervisor invalidation')
        c.release_fault('before_resource');r=c.finish();self.assertIsNotNone(r['stop']);self.assertIn('observation gap',r['stop'])
        self.assertFalse((c.folder/'EXECUTED').exists());self.assertGreaterEqual(r['observed_native_lifetime_seconds'],1)
    def test_slow_wait_GO_identity_gate_still_monitored(self):
        c=self.case(faults=('gate_audit',));c.wait(lambda:c.fault_entered('gate_audit'))
        for step in range(20):
            current=c.value
            c.wait(lambda:all(any(r['event']=='READ_END' and r.get('stream')==kind and r['end_ns']==current for r in rows(c.folder/'MONITOR.jsonl')) for kind in ('resource','directory')),'fresh samples during slow gate')
            self.assertFalse((c.folder/'EXECUTED').exists());c.advance(100_000_000)
        c.release_fault('gate_audit');c.wait_GO();r=c.finish();self.assertIsNone(r['stop']);audit(c.folder)
        self.assertGreaterEqual(r['coverage']['resource']['valid_reads'],20)
    def test_module_hash_mismatch_blocks_GO(self):
        c=self.case(bad_hash=True);r=c.finish();self.assertIsNotNone(r['stop']);self.assertFalse(r['GO_sent']);self.assertFalse((c.folder/'EXECUTED').exists())
    def test_missing_and_truncated_outputs_fail_after_good_monitoring(self):
        for child in (dict(missing_output=True),dict(truncated=True)):
            c=self.case(child=child);c.wait_GO();r=c.finish();self.assertIn('audit',r['stop']);self.assertEqual(r['returncode'],0)
    def test_closing_module_hash_mismatch_fails_after_exit(self):
        c=self.case(faults=('post_audit',));c.wait_GO();c.release.write_text('exit');c.wait(lambda:c.fault_entered('post_audit'))
        pathlib.Path(c.job['test_module']).write_bytes(b'changed');c.release_fault('post_audit');r=c.finish();self.assertIn('hash mismatch',r['stop'])
    def test_exit_between_poll_and_resource_read_is_not_fake_sample(self):
        signal=EVIDENCE/(self.id().split('.')[-1]+'-EXIT')
        c=self.case(child=dict(exit_before_GO_when=str(signal)),faults=('before_resource',))
        c.wait(lambda:c.fault_entered('before_resource'));signal.write_text('exit')
        c.wait(lambda:(c.folder/'EXIT_OBSERVED.json').exists());c.release_fault('before_resource');r=c.finish()
        self.assertIsNotNone(r['stop']);self.assertGreater(r['pid'],0);self.assertGreater(r['process_times']['exit_FILETIME'],0)
        discarded=[x for x in rows(c.folder/'MONITOR.jsonl') if x['event']=='READ_DISCARDED']
        self.assertTrue(discarded);self.assertTrue(all('values' not in x for x in discarded))
    def test_fast_exit_before_GO_and_abnormal_exit_are_retained(self):
        for child in (dict(exit_early=True),dict(exit_before_GO=True),dict(exit_code=7)):
            c=self.case(child=child);r=c.finish();self.assertIsNotNone(r['stop']);self.assertGreater(r['pid'],0)
            self.assertGreater(r['process_times']['exit_FILETIME'],0)
    def test_engineering_timeout_kills_and_records_process(self):
        c=self.case(virtual=False,seconds=.7);c.wait(lambda:not c.thread.is_alive(),'timeout path');r=c.result
        self.assertIn('timeout',r['stop']);self.assertGreater(r['pid'],0);self.assertIsNotNone(r['exit_observed_ns'])
    def test_monitor_process_abnormal_exit_stops_live_target(self):
        c=self.case(virtual=False);c.wait_GO();pid=load(c.folder/'CONTROL_PIDS.json')['monitor']
        os.kill(pid,15)
        c.wait(lambda:(c.folder/'EXIT_OBSERVED.json').exists(),'monitor crash terminates CPU target')
        r=c.finish();self.assertIsNotNone(r['stop']);self.assertTrue(any(p['role']=='monitor' and p['returncode']!=0 for p in r['control_processes']))
    def test_slow_directory_scan_does_not_suspend_resource_reader(self):
        c=self.case(faults=('before_directory',));c.wait(lambda:c.fault_entered('before_directory'))
        for _ in range(3):
            current=c.value;c.wait(lambda:any(r['event']=='READ_END' and r.get('stream')=='resource' and r['end_ns']==current for r in rows(c.folder/'MONITOR.jsonl')))
            c.advance(100_000_000)
        c.advance(1_000_000_001);c.wait(lambda:(c.folder/'EXIT_OBSERVED.json').exists());c.release_fault('before_directory');r=c.finish()
        self.assertIsNotNone(r['stop']);self.assertGreaterEqual(c.sample_count('resource'),3);self.assertFalse(r['GO_sent'])
    def test_resource_read_failure_is_not_missing_or_zero_RSS(self):
        c=self.case(fault_flags=dict(raise_resource=True));r=c.finish();self.assertIsNotNone(r['stop']);self.assertFalse(r['GO_sent'])
        failures=[x for x in rows(c.folder/'MONITOR.jsonl') if x['event']=='READ_ERROR']
        self.assertTrue(failures);self.assertTrue(all('values' not in x for x in failures))
    def test_exact_one_second_policy_boundaries_and_long_read(self):
        for delta,ok in ((-1,True),(0,True),(1,False)):
            coverage=Coverage(0)
            for kind in ('resource','directory'):
                coverage.event(dict(event='READ_BEGIN',stream=kind,begin_ns=0))
                row=dict(event='READ_END',stream=kind,begin_ns=0,end_ns=MAX_GAP_NS+delta)
                if ok:coverage.event(row)
                else:
                    with self.assertRaises(ValueError):coverage.event(row)
            if ok:coverage.terminal(MAX_GAP_NS+delta)
        coverage=Coverage(0)
        for kind in ('resource','directory'):
            coverage.event(dict(event='READ_BEGIN',stream=kind,begin_ns=0));coverage.event(dict(event='READ_END',stream=kind,begin_ns=0,end_ns=1))
        with self.assertRaises(ValueError):coverage.terminal(MAX_GAP_NS+1)
        with self.assertRaises(ValueError):coverage.live(MAX_GAP_NS+1)
    def test_old_invalid_receipt_still_fails_old_auditor(self):
        from native_audit import audit_lifecycle
        raw_root=ROOT/'host_outputs/aligned_numerical_v2/b570-aligned-numerical-v2-20261015-01'
        closed=load(raw_root/'CLOSEOUT.json');slot=closed['failed_or_invalid'][0];folder=raw_root/slot
        files=[folder/'LIFECYCLE.json',OLD/'controller.py',OLD/'native_audit.py',OLD/'F0.json',OLD/'results/RESULT.json'];before={str(p):sha(p) for p in files}
        with self.assertRaisesRegex(ValueError,'final observer gap'):audit_lifecycle(load(folder/'LIFECYCLE.json'),rows(folder/'raw.jsonl'),load(OLD/'F0.json'))
        with self.assertRaisesRegex(ValueError,'only new v3'):audit(folder)
        self.assertEqual(before,{str(p):sha(p) for p in files})
    def test_new_plan_serializer_and_numerical_fields_unchanged(self):
        p=plan();old=load(OLD/'PLAN.json');self.assertEqual(len(p['slots']),161)
        self.assertTrue(all(s['q']==1 for s in p['slots'][1:41]));self.assertTrue(all(s['q']>1 for s in p['slots'][41:]))
        old_wires=load(OLD/'WIRES.json')
        for s,previous,w in zip(p['slots'],old['slots'],old_wires):
            for key in ('kind','input_id','mode','repeat','q'):self.assertEqual(s.get(key),previous.get(key))
            a=json.loads(serialize(s,'0'*64));b=load(OLD/w['path'])
            for key in ('run_id','slot_id','execution_binding_sha256','output_dir'):a.pop(key,None);b.pop(key,None)
            self.assertEqual(a,b)
    def test_native_interface_only_one_identity_literal_changed(self):
        generated=HERE/'generated';self.assertEqual((generated/'host.cpp').read_bytes(),(OLD/'host.cpp').read_bytes())
        old=(OLD/'fixture.hpp').read_bytes();new=(generated/'fixture.hpp').read_bytes()
        self.assertEqual(new,old.replace(b'b570-aligned-numerical-v2-20261015-01',b'b570-supervised-numerical-v3-20261015-01'))
        self.assertEqual(new.count(b'b570-supervised-numerical-v3-20261015-01'),1)
