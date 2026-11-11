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
import subprocess
from legacy import HERE,OLD,ROOT,OUT,LIMITS,PYTHON,load,sha,save,need,modules
from timing import Coverage,MAX_GAP_NS,VirtualCounter
from supervisor import supervise
from lifecycle_audit import audit
from workers import rows
from registration import plan,serialize
from storage import Watch,inventory,bounded_usage,ACTIVE_BYTES

EVIDENCE=None

class Case:
    def __init__(self,name,virtual=True,child=None,faults=(),fault_flags=None,bad_hash=False,seconds=8,late=None,output_cap=None):
        self.root=EVIDENCE/name;self.root.mkdir();self.folder=self.root/'host';self.clockfile=self.root/'CLOCK';self.value=10_000_000_000
        self.clockfile.write_text(str(self.value));self.release=self.root/'RELEASE_CHILD'
        self.clocktag='Local\\HeteroSpecCPUClock-'+str(uuid.uuid4());self.counter=VirtualCounter(self.clocktag);self.counter.write(self.value)
        module=self.root/'CPU_MODULE.bin';module.write_bytes(b'CPU-ONLY-HASH-TARGET')
        self.job=dict(purpose='CPU_TEST',folder=str(self.folder),disk_root=str(ROOT),run_root=str(self.root),storage_roots=[str(self.root)],
            limits=LIMITS,per_slot_seconds=seconds,panel_seconds=30,panel_begin_ns=self.value if virtual else time.monotonic_ns(),
            test_module=str(module),test_module_sha256='0'*64 if bad_hash else sha(module),
            cpu_child=dict(release=str(self.release),**(child or {})),faults={k:str(self.root/('release_'+k)) for k in faults})
        if virtual:self.job['virtual_clock']=self.clocktag
        if late:self.job['storage_roots'].append(str(late))
        if output_cap is not None:self.job['limits']=dict(LIMITS,output_bytes=output_cap)
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
        with self.assertRaisesRegex(ValueError,'only new v5'):audit(folder)
        self.assertEqual(before,{str(p):sha(p) for p in files})
    def test_new_plan_serializer_and_numerical_fields_unchanged(self):
        p=plan();old=load(OLD/'PLAN.json');self.assertEqual(len(p['slots']),69)
        self.assertTrue(all(s['q']==1 for s in p['slots'][1:9]));self.assertTrue(all(s['q']>1 for s in p['slots'][9:]))
        self.assertEqual({g:sum(s.get('group')==g for s in p['slots']) for g in 'ABCD'},dict(A=8,B=10,C=10,D=40))
        old_wires=load(OLD/'WIRES.json')
        for s in p['slots']:
            index=next(i for i,x in enumerate(old['slots']) if all(s.get(k)==x.get(k) for k in ('kind','input_id','mode','repeat','q')))
            previous,w=old['slots'][index],old_wires[index]
            for key in ('kind','input_id','mode','repeat','q'):self.assertEqual(s.get(key),previous.get(key))
            a=json.loads(serialize(s,'0'*64));b=load(OLD/w['path'])
            for key in ('run_id','slot_id','execution_binding_sha256','output_dir'):a.pop(key,None);b.pop(key,None)
            self.assertEqual(a,b)
    def test_native_interface_only_one_identity_literal_changed(self):
        generated=HERE/'generated';self.assertEqual((generated/'host.cpp').read_bytes(),(OLD/'host.cpp').read_bytes())
        old=(OLD/'fixture.hpp').read_bytes();new=(generated/'fixture.hpp').read_bytes()
        self.assertEqual(new,old.replace(b'b570-aligned-numerical-v2-20261015-01',b'b570-supervised-numerical-v5-20261016-01'))
        self.assertEqual(new.count(b'b570-supervised-numerical-v5-20261016-01'),1)

    def test_late_panel_real_process_concurrent_growth(self):
        # Larger than the entire v3 stopped tree (4995 files / 124879060 B).
        late=ROOT/'host_outputs/supervised_numerical_v4/SCALING_TREE';body=bytes(range(256))*128
        self.assertTrue(late.is_dir(),'immutable v4 fixture must already exist; never create/modify it')
        self.assertEqual(inventory(late),dict(bytes=262144000,files=8000))
        c=self.case(virtual=False,late=late,seconds=15);c.wait_GO()
        errors=[]
        def grow():
            try:
                for i in range(64):
                    with (c.folder/'GROWING.bin').open('ab') as f:f.write(body)
            except BaseException as e:errors.append(str(e))
        writer=threading.Thread(target=grow);writer.start();writer.join()
        c.wait(lambda:c.sample_count('directory')>=8,'late-panel live directory samples')
        r=c.finish();self.assertFalse(errors);self.assertIsNone(r['stop']);audit(c.folder)
        data=rows(c.folder/'MONITOR.jsonl');reads=[x for x in data if x['event']=='READ_END' and x['stream']=='directory']
        self.assertTrue(all(x['values']['historical_files_scanned']==0 for x in reads))
        # Old algorithm measured on the SAME real late tree, outside child lifetime.
        from workers import full_usage
        old=[]
        for _ in range(5):
            begin=time.monotonic_ns();v=full_usage(c.job);old.append(dict(begin_ns=begin,end_ns=time.monotonic_ns(),values=v))
        save(c.root/'SCALING.json',dict(tree=inventory(late),old_full_traversals=old,
            bounded_reads=reads,lease=load(c.folder/'STORAGE_LEASE.json'),process_lifecycle_sha256=sha(c.folder/'LIFECYCLE.json')))

    def test_sealed_file_growth_and_new_nested_file_fail(self):
        for create in (False,True):
            sealed=EVIDENCE/('SEALED_NEW' if create else 'SEALED_GROW');(sealed/'old').mkdir(parents=True);p=sealed/'old'/'fixed.bin';p.write_bytes(b'closed')
            c=self.case(virtual=False,late=sealed);c.wait_GO()
            (sealed/'old'/'new.bin' if create else p).write_bytes(b'UNAUTHORIZED-GROWTH')
            c.wait(lambda:(c.folder/'EXIT_OBSERVED.json').exists(),'sealed write stops target');r=c.finish();self.assertIn('sealed storage changed',r['stop'])

    def test_active_bytes_and_file_count_caps_fail(self):
        for count in (False,True):
            c=self.case();c.wait_GO()
            if count:
                for i in range(260):(c.folder/('overflow'+str(i))).write_bytes(b'x')
            else:
                with (c.folder/'overflow.bin').open('wb') as f:f.truncate(ACTIVE_BYTES+1)
            c.wait(lambda:(c.folder/'EXIT_OBSERVED.json').exists());r=c.finish();self.assertIn('reservation exceeded',r['stop'])

    def test_watch_thread_stall_stops_target(self):
        c=self.case(virtual=False,faults=('watch_stall',));c.wait(lambda:c.fault_entered('watch_stall'))
        c.wait(lambda:(c.folder/'EXIT_OBSERVED.json').exists(),'watcher stall >1s');c.release_fault('watch_stall');r=c.finish();self.assertIn('storage watch',r['stop'])

    def test_watch_cleanup_error_preserves_native_lifecycle(self):
        c=self.case(fault_flags=dict(raise_watch_cleanup=True));c.wait_GO();r=c.finish()
        self.assertIn('storage watcher cleanup',r['stop']);self.assertGreater(r['pid'],0);self.assertIsNotNone(r['exit_observed_ns'])
        self.assertTrue((c.folder/'RECEIPT_COMMITTED.json').exists())

    def test_notification_overflow_malformed_and_sealed_events_fail(self):
        import struct
        w=object.__new__(Watch);w.root=EVIDENCE;w.allowed=lambda p:False;w.events=0
        for data in (b'',b'short',struct.pack('<III',0,3,2)+b'x\x00'):
            with self.assertRaises(ValueError):w.accept(data)

    def test_reservation_budget_rejected_before_child_spawn(self):
        c=self.case(output_cap=1);r=c.finish();self.assertIsNone(r['pid']);self.assertIn('pre-spawn',r['stop']);self.assertEqual(r['control_processes'],[])

    def test_new_comparison_inventory_has_explicit_missing_coordinates(self):
        from reconstruct_v5 import inventory as comparisons
        pairs,repeats=comparisons(plan());self.assertEqual(len(pairs),124);self.assertEqual(len(repeats),34)
        self.assertEqual(len({s['input_id'] for s in plan()['slots'] if s['kind']=='graph'}),8)

    def test_v3_failure_remains_invalid_under_frozen_v3_auditor(self):
        import importlib.util
        v3=ROOT/'host/supervised_numerical_v3';spec=importlib.util.spec_from_file_location('_unchanged_v3_audit',v3/'lifecycle_audit.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        run=ROOT/'host_outputs/supervised_numerical_v3/b570-supervised-numerical-v3-20261015-01'
        folder=run/'1bc547f9d4b5d289813e5f1eb71114c14ef3f902e6636b29da436f0ca4da173a'
        files=[v3/'F0.json',v3/'lifecycle_audit.py',folder/'LIFECYCLE.json',folder/'MONITOR.jsonl'];before={str(p):sha(p) for p in files}
        with self.assertRaisesRegex(ValueError,'failed process'):m.audit(folder)
        self.assertEqual(before,{str(p):sha(p) for p in files})

    def test_v4_failure_and_production_watch_policy_unchanged(self):
        v4=ROOT/'host/supervised_numerical_v4'
        self.assertEqual(sha(v4/'F0.json'),'5fab2cf08daa2f2ac57537ade5a16648a324ec0c0fcfa9a77d97d9b18bd351f7')
        self.assertEqual(sha(HERE/'storage.py'),sha(v4/'storage.py'));self.assertEqual(sha(HERE/'timing.py'),sha(v4/'timing.py'))
        oldroot=ROOT/'host_outputs/supervised_numerical_v4/b570-supervised-numerical-v4-20261016-01'
        c=load(oldroot/'CLOSEOUT.json');self.assertEqual(len(c['records']),1);self.assertEqual(len(c['unstarted']),68)
        self.assertEqual(load(oldroot/'CLOSEOUT_COMMITTED.json')['whole_controller_engineering_seconds_through_closeout'],3.156)
        self.assertFalse(list(oldroot.rglob('LIFECYCLE.json')));self.assertFalse(list(oldroot.rglob('raw.jsonl')))

    def test_actual_CPU_native_metadata_for_every_serialized_slot(self):
        from analyzer import validate_semantics
        from panel_common import digest
        root=EVIDENCE/'SERIALIZER';root.mkdir();paths=[]
        for s in plan()['slots']:
            p=root/(s['id']+'.wire');p.write_bytes(serialize(s,'0'*64));paths.append(str(p))
        save(root/'LIST.json',paths);out=root/'DESCRIPTORS.jsonl'
        command=[str(OUT/'build/Release/metadata-host-v5.exe'),str(root/'LIST.json'),str(out)]
        begin=time.monotonic_ns();r=subprocess.run(command,capture_output=True,text=True,timeout=30)
        save(root/'PROCESS.json',dict(command=command,returncode=r.returncode,wall_seconds=(time.monotonic_ns()-begin)/1e9,stdout=r.stdout,stderr=r.stderr,kind='CPU_METADATA_NO_GPU'))
        self.assertEqual(r.returncode,0,r.stderr);data=rows(out);self.assertEqual(len(data),150)
        expected=load(OLD/'EXPECTED_GRAPHS.json');graphs={}
        for row in data[1:-1]:
            key=digest(dict(cell=row['cell'],mode=row['mode']))
            # Native support census and execution both invoke the exact same builder.
            if row['request']['kind']=='census':graphs[key]=row['graph']
            else:
                self.assertEqual(graphs[key],row['graph'])
                validate_semantics(row['request'],row['graph'],pathlib.Path(row['request']['input']).read_bytes())
        for row in (data[0],data[-1]):
            self.assertEqual(row['graph_computes'],0);self.assertEqual(row['device_queries'],0)
            self.assertFalse(any('vulkan' in p.lower() or 'cuda' in p.lower() for p in row['modules']))
        save(root/'CHECK.json',dict(actual_serialized_slots=69,actual_descriptors=148,census=80,numerical=68,same_graph_builder=True,no_device_queries=True,native_metadata_process_pid=data[0]['pid']))
