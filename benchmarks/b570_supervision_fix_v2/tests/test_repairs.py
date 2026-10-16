"""Portable regression tests. No Windows integration, models or GPU access."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'host'))
sys.path.insert(0,str(HERE))
from admission import Admission
from output_integrity import positive_output, capture_files
from snapshot_sources import source_members
from diagnostics import diagnostic
from live_budget import anchor, elapsed, OuterBudget
from storage_policy import notification_kind, injection_target
from storage_policy import checked_path, identity, authorize, NOTIFY_FILTER
from evidence_io import Evidence, strict_json
from audit_integrity import watch_lifetimes, round_integrity, sequence
from coverage import evaluate, boundary_tests, pre_injection
from packaged_source import verify as verify_packaged
from audit_integrity import validate_pending_probe
import common


def watch_fixture():
    events=[]
    def add(at,event,**kw):events.append(dict(at_ns=at,event=event,**kw))
    def arm(at,key,root,kind):
        add(at,'WATCH_ARMED',watch_id=key,root=root,owner='a' if key.startswith('a:') else key,kind=kind)
        add(at+1,'IO_ARMED',watch_id=key)
    def close(at,key):
        add(at,'WATCH_CLOSE_BEGIN',watch_id=key,pending=True)
        add(at+1,'CANCEL_ISSUED',watch_id=key,success=True,error=0)
        add(at+2,'IO_COMPLETION',watch_id=key,success=False,error=995)
        add(at+3,'WATCH_CLOSED',watch_id=key,directory_closed=True,event_closed=True,pending=False)
    arm(0,'a:content:0','C:/test/protected/slots/a','content')
    arm(2,'meta:rootmeta:0','C:/test/protected/slots','rootmeta')
    arm(25,'a:sealed:1','C:/test/protected/slots/a','sealed')
    close(27,'a:content:0');close(60,'a:sealed:1');close(70,'meta:rootmeta:0')
    add(74,'WATCH_STREAM_CLOSED',error=None)
    return renumber(sorted(events,key=lambda r:r['at_ns']))


def renumber(rows):
    return [dict(r,seq=i+1) for i,r in enumerate(rows)]


def round_fixture():
    cfg={'round':0,'registry':{'a':{'path':'C:/test/protected/slots/a'}},
         'cases':[{'id':'normal_single','kind':'positive','target':'positive','detector':'NORMAL_COMPLETE'}]}
    rows=renumber([
        dict(event='ROUND_STARTED',at_ns=0),
        dict(event='CASE_BEGIN',case_id='normal_single',at_ns=10),
        dict(event='SLOT_STATE',slot='a',previous='PREPARED',state='ACTIVE',at_ns=12),
        dict(event='GO_SENT',slot='a',at_ns=15),
        dict(event='SLOT_STATE',slot='a',previous='ACTIVE',state='CLOSING',at_ns=25),
        dict(event='SLOT_STATE',slot='a',previous='CLOSING',state='SEALED',handoff={'old':'a:content:0','new':'a:sealed:1'},at_ns=31),
        dict(event='CASE_CLOSED',case_id='normal_single',cleanup_complete=True,at_ns=35),
        dict(event='ROUND_CLOSE_BEGIN',at_ns=36),dict(event='ROUND_CLOSED',at_ns=100)])
    end={'error':None,'CPU_only':True,'finished_ns':101}
    launch={'exit_code':0,'end_ns':102}
    closed={'status':'CLOSED_SUCCESS','controller_exit_code':0,'error':None,'stop_reason':None,'readers_completed':2}
    return cfg,rows,watch_fixture(),end,launch,closed


class AdmissionTests(unittest.TestCase):
    def test_reject_first_prevents_go(self):
        a=Admission();a.begin();a.reject();calls=[]
        self.assertFalse(a.send(None,b'GO',lambda:calls.append('record')))
        self.assertEqual(calls,[])
    def test_send_first_serializes_rejection(self):
        a=Admission();a.begin();entered=threading.Event();release=threading.Event();events=[]
        class Pipe:
            def write(self,data):entered.set();self_ok=release.wait(2);assert self_ok;events.append('write')
            def flush(self):events.append('flush')
        sender=threading.Thread(target=lambda:a.send(Pipe(),b'GO',lambda:events.append('record')))
        sender.start();self.assertTrue(entered.wait(2))
        rejector=threading.Thread(target=lambda:(a.reject(),events.append('reject')))
        rejector.start();release.set();sender.join(2);rejector.join(2)
        self.assertFalse(sender.is_alive() or rejector.is_alive())
        self.assertEqual(events,['write','flush','record','reject'])
    def test_record_failure_latches_fatal(self):
        a=Admission();a.begin()
        class Pipe:
            def write(self,b):pass
            def flush(self):pass
        def fail():raise OSError('journal failed')
        with self.assertRaises(OSError):a.send(Pipe(),b'GO',fail)
        a.end(True)
        with self.assertRaises(RuntimeError):a.begin()
    def test_late_rejection_cannot_be_reset(self):
        a=Admission();a.begin();a.end(True);a.reject()
        with self.assertRaises(RuntimeError):a.begin()
    def test_expected_case_rejection_can_close(self):
        a=Admission();a.begin();a.reject();a.end(True);a.begin()
        self.assertFalse(a.blocked)


class StorageTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
    def tearDown(self):self.temp.cleanup()
    def test_active_regular_file_allowed(self):
        p=self.root/'file';p.write_bytes(b'x')
        self.assertTrue(authorize(p,self.root,'content','ACTIVE')[0])
    def test_symlink_ancestor_rejected_before_resolve(self):
        active=self.root/'active';active.mkdir();outside=self.root/'other';outside.mkdir();(outside/'f').write_bytes(b'x')
        (active/'link').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):authorize(active/'link/f',active,'content','ACTIVE')
    def test_symlink_leaf_rejected(self):
        p=self.root/'f';p.write_bytes(b'x');(self.root/'link').symlink_to(p)
        with self.assertRaises(ValueError):identity(self.root/'link')
    def test_outside_registered_root_rejected(self):
        root=self.root/'a';root.mkdir();p=self.root/'f';p.write_bytes(b'x')
        with self.assertRaises(ValueError):authorize(p,root,'content','ACTIVE')
    def test_equal_content_replacement_never_allowed_in_closing(self):
        p=self.root/'f';p.write_bytes(b'x');old=identity(p)
        q=self.root/'q';q.write_bytes(b'x');q.replace(p)
        self.assertNotEqual(old['file_id'],identity(p)['file_id'])
        self.assertFalse(authorize(p,self.root,'content','CLOSING')[0])
    def test_metadata_filter_retains_attributes_and_write_time(self):
        self.assertEqual(NOTIFY_FILTER & (4|0x10),4|0x10)
    def test_prepared_and_sealed_never_allowed(self):
        p=self.root/'f';p.write_bytes(b'x')
        for state in ['PREPARED','CLOSING','SEALED','FAILED','FROZEN']:
            self.assertFalse(authorize(p,self.root,'content',state)[0])


class ManifestTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve();self.p=self.root/'data';self.p.write_bytes(b'abc');self.m=self.root/'manifest.json'
    def tearDown(self):self.temp.cleanup()
    def manifest(self,rows=None):
        self.m.write_text(json.dumps({'members':rows if rows is not None else [{'path':'data','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}]}))
        return Evidence(self.root,self.m)
    def test_bound_input_reads(self):self.assertEqual(self.manifest().bytes(self.p),b'abc')
    def test_empty_manifest_rejected(self):
        with self.assertRaises(ValueError):self.manifest([])
    def test_consumed_unlisted_file_rejected(self):
        reader=self.manifest();p=self.root/'unlisted';p.write_bytes(b'not authenticated')
        with self.assertRaises(ValueError):reader.bytes(p)
    def test_duplicate_member_rejected(self):
        r={'path':'data','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}
        with self.assertRaises(ValueError):self.manifest([r,r])
    def test_member_changed_after_initial_verification_rejected(self):
        reader=self.manifest();self.p.write_bytes(b'new')
        with self.assertRaises(ValueError):reader.bytes(self.p)
    def test_manifest_changed_after_initial_verification_rejected(self):
        reader=self.manifest();self.m.write_text('{}')
        with self.assertRaises(ValueError):reader.bytes(self.m)
    def test_duplicate_json_cannot_hide_failure(self):
        with self.assertRaises(ValueError):strict_json('{"pass":false,"pass":true}')
    def test_partial_journal_rejected(self):
        self.p.write_bytes(b'{}');self.m.write_text(json.dumps({'members':[{'path':'data','bytes':2,'sha256':hashlib.sha256(b'{}').hexdigest()}]}))
        with self.assertRaises(ValueError):Evidence(self.root,self.m).rows(self.p)


class LifecycleTests(unittest.TestCase):
    def test_valid_watch_lifetimes(self):self.assertTrue(watch_lifetimes(watch_fixture()))
    def test_cancel_is_not_completion(self):
        rows=renumber([r for r in watch_fixture() if not(r['event']=='IO_COMPLETION' and r['watch_id']=='a:content:0')])
        with self.assertRaises(ValueError):watch_lifetimes(rows)
    def test_closed_flag_not_proof(self):
        rows=renumber([r for r in watch_fixture() if r['event']!='WATCH_CLOSE_BEGIN'])
        with self.assertRaises(ValueError):watch_lifetimes(rows)
    def test_watch_missing_final_close_rejected(self):
        with self.assertRaises(ValueError):watch_lifetimes(watch_fixture()[:-1])
    def test_journal_sequence_gap_rejected(self):
        rows=watch_fixture();rows[1]['seq']=99
        with self.assertRaises(ValueError):sequence(rows)
    def test_valid_round_fixture(self):self.assertTrue(round_integrity(*round_fixture()))
    def test_failed_launcher_rejected_even_with_closed_children(self):
        args=list(round_fixture());args[-1]['status']='FAILED'
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_controller_failure_rejected(self):
        args=list(round_fixture());args[3]['error']='late error'
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_missing_round_close_rejected(self):
        args=list(round_fixture());args[1].pop()
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_failed_slot_needs_same_handoff_evidence(self):
        args=list(round_fixture());state=next(r for r in args[1] if r.get('state')=='SEALED');state['state']='FAILED';state['handoff']['new']='missing'
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_outside_case_detector_rejected(self):
        args=list(round_fixture());args[1].insert(-1,dict(event='DETECTOR',at_ns=90,case_id='normal_single',code='SEALED_WRITE_REJECTED',target='x'))
        args[1]=renumber(args[1])
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_second_unrelated_detector_rejected(self):
        args=list(round_fixture());args[1].insert(4,dict(event='DETECTOR',at_ns=20,case_id='normal_single',code='OTHER_FAILURE',target='x'))
        args[1]=renumber(args[1])
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_missing_parent_metadata_guard_rejected(self):
        args=list(round_fixture());args[2]=renumber([r for r in args[2] if r.get('watch_id')!='meta:rootmeta:0'])
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_dangling_sample_rejected(self):
        rows=[dict(event='READ_BEGIN',begin_ns=0),dict(event='READ_END',begin_ns=0,end_ns=1),dict(event='READ_BEGIN',begin_ns=2)]
        self.assertFalse(evaluate(rows,0,3)['valid'])
    def test_boundary_contract_unchanged(self):self.assertEqual([r['valid'] for r in boundary_tests()],[True,True,False])


class RealJournalFailureTests(unittest.TestCase):
    def test_failure_on_actual_journal_calls_independent_sink_once(self):
        with tempfile.TemporaryDirectory() as d,patch.object(common,'BASE',Path(d).resolve()):
            journal=common.Journal(Path(d)/'RESOURCE.jsonl');errors=[]
            journal.on_failure=lambda path,error:errors.append((path,type(error).__name__))
            journal.emit('READ_BEGIN',begin_ns=0);journal.f.close()
            for _ in range(2):
                with self.assertRaises((ValueError,OSError)):journal.emit('READ_END',begin_ns=0,end_ns=1)
            self.assertEqual(len(errors),1);self.assertTrue(journal.failed)
            self.assertEqual(len((Path(d)/'RESOURCE.jsonl').read_bytes().splitlines()),1)



class ReviewRegressionTests(unittest.TestCase):
    def test_new_root_fixture_is_injectable_without_old_name(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d).resolve()/'b570-supervision-fix-v2-20261016';fixture=base/'runs'/'one'/'protected';fixture.mkdir(parents=True)
            target=fixture/'input';target.write_bytes(b'x')
            self.assertEqual(injection_target(target,fixture,base),(target,fixture))
            (base/'runs'/'other').mkdir()
            with self.assertRaises(ValueError):injection_target(target,fixture,base/'runs'/'other')

    def test_replacement_guard_cannot_close_before_round_close(self):
        args=list(round_fixture())
        for row in args[2]:
            if row.get('watch_id')=='a:sealed:1' and row['event'].startswith(('WATCH_CLOSE','CANCEL','IO_COMPLETION')):
                row['at_ns']-=30
        args[2]=renumber(sorted(args[2],key=lambda r:r['at_ns']))
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_replacement_guard_cannot_watch_other_root(self):
        args=list(round_fixture())
        next(r for r in args[2] if r.get('watch_id')=='a:sealed:1' and r['event']=='WATCH_ARMED')['root']='C:/other'
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_namespace_and_parent_share_metadata_policy(self):
        self.assertEqual(notification_kind('namespace',3,True),notification_kind('rootmeta',3,True))
        for kind in ['namespace','rootmeta']:
            for action in [1,2,4,5]:self.assertEqual(notification_kind(kind,action,True),kind)
    def test_live_elapsed_uses_monotonic_time(self):
        sample=anchor(116444736010000000,2_000_000_000,10)
        self.assertEqual(elapsed(sample,1_000_000_010),2)
    def budget(self):
        return OuterBudget({'task_begin_ns':0,'outer_processes':[{'pid':1,'created_filetime':116444736000000000}]},1,116444736000000000,0,0)
    def test_outer_charge_blocks_before_child_only_budget(self):
        self.assertTrue(self.budget().exceeded(1,43199,0,2_000_000_000))
    def test_outer_charge_allows_small_complete_budget(self):
        self.assertFalse(self.budget().exceeded(1,1,1,2_000_000_000))
    def test_missing_broker_prevents_admission(self):
        with self.assertRaises(ValueError):OuterBudget({'task_begin_ns':0,'outer_processes':[]},1,1,0,0)


class SecondReviewRegressionTests(unittest.TestCase):
    def test_interrupted_read_is_reconciled_separately(self):
        for event in ['READ_ERROR','READ_END','READ_DISCARDED']:
            rows=[dict(event='READ_BEGIN',begin_ns=0),dict(event='READ_END',begin_ns=0,end_ns=1),dict(event='READ_BEGIN',begin_ns=2),dict(event=event,begin_ns=2,end_ns=10)]
            result=pre_injection(rows,0,3,require_crossing=True)
            self.assertTrue(result['valid']);self.assertEqual(result['interrupted_reads'],1)
    def test_unrelated_unclosed_read_remains_invalid(self):
        rows=[dict(event='READ_BEGIN',begin_ns=0),dict(event='READ_END',begin_ns=0,end_ns=1),dict(event='READ_BEGIN',begin_ns=2)]
        self.assertFalse(pre_injection(rows,0,3,require_crossing=True)['valid'])
    def test_import_shadow_and_bytecode_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'host').mkdir();(root/'host/raw_audit.py').write_bytes(b'x')
            bound={'host/raw_audit.py':hashlib.sha256(b'x').hexdigest()}
            self.assertEqual(verify_packaged(root,bound),bound)
            for name in ['audit_integrity.py','host/shadow.py','host/cache.pyc']:
                p=root/name;p.write_bytes(b'x')
                with self.assertRaises(ValueError):verify_packaged(root,bound)
                p.unlink()
    def probe(self):
        h=dict(watch_id='probe',owner='pending_probe',kind='sealed',root='C:/root/sealed',at_ns=11)
        permanent=dict(watch_id='permanent',owner='results',kind='sealed',root='C:/root/sealed',at_ns=0)
        cfg={'cases':[{'id':'terminal_pending_completion','target':'C:/root/sealed/file'}]}
        rows=[dict(event='CASE_BEGIN',case_id='terminal_pending_completion',at_ns=10),dict(event='CASE_CLOSED',case_id='terminal_pending_completion',at_ns=20)]
        watch=[dict(event='PENDING_PROBE_READY',watch_id='probe',at_ns=12),dict(event='PENDING_COMPLETION_SIGNALED',watch_id='probe',at_ns=13)]
        return cfg,rows,watch,h,{'probe':h,'permanent':permanent},{'probe':14,'permanent':30},25
    def test_temporary_probe_may_close_inside_case(self):validate_pending_probe(*self.probe())
    def test_temporary_probe_never_replaces_permanent_guard(self):
        args=list(self.probe());args[5]['permanent']=13
        with self.assertRaises(ValueError):validate_pending_probe(*args)


class ThirdReviewRegressionTests(unittest.TestCase):
    def output(self):
        records=[dict(event='READY',pid=7,source_sha256='source'),dict(event='WORKING',pid=7)]+[dict(event='FRAME',index=i,payload='x'*128) for i in range(4)]+[dict(event='COMPLETE',frames=4)]
        lines=[(json.dumps(r)+'\n').encode() for r in records];stdout=b''.join(lines);stderr=b'CPU_STDERR_FRAME\n'*4
        ack=b''.join((json.dumps(dict(index=i,bytes=len(line),sha256=hashlib.sha256(line).hexdigest()))+'\n').encode() for i,line in enumerate(lines[2:6]))
        return [stdout,stderr,ack,records,7,'source',dict(stdout=len(stdout),stderr=len(stderr))]
    def test_real_output_bytes_reconcile(self):self.assertTrue(positive_output(*self.output()))
    def test_missing_and_truncated_stdout_cannot_pass(self):
        for value in [b'',self.output()[0][:-1]]:
            args=self.output();args[0]=value;self.assertFalse(positive_output(*args))
    def test_controller_only_complete_is_insufficient(self):
        args=self.output();args[3][-1]['frames']=5;self.assertFalse(positive_output(*args))
    def test_actual_io_must_precede_old_close(self):
        args=list(round_fixture())
        for row in args[2]:
            if row.get('watch_id')=='a:sealed:1' and row['event']=='IO_ARMED':row['at_ns']=29
        args[2]=renumber(sorted(args[2],key=lambda r:r['at_ns']))
        with self.assertRaises(ValueError):round_integrity(*args)
    def test_watch_cannot_close_without_any_io(self):
        rows=renumber([dict(event='WATCH_ARMED',watch_id='empty',at_ns=0),dict(event='WATCH_CLOSE_BEGIN',watch_id='empty',pending=False,at_ns=1),dict(event='WATCH_CLOSED',watch_id='empty',pending=False,directory_closed=True,event_closed=True,at_ns=2),dict(event='WATCH_STREAM_CLOSED',error=None,at_ns=3)])
        with self.assertRaises(ValueError):watch_lifetimes(rows)


class SourceOnlyBuildTests(unittest.TestCase):
    def test_compiled_bytes_retained_outside_source_import_tree(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);design=root/'design';host=design/'host';host.mkdir(parents=True);snapshot=root/'snapshot';snapshot.mkdir()
            dll=host/'LauncherCapture.dll';dll.write_bytes(b'compiled fixture');(host/'LauncherCapture.cs').write_bytes(b'source')
            members=source_members(design,snapshot,True)
            self.assertNotIn(dll,members);self.assertIn(host/'LauncherCapture.cs',members)
            self.assertEqual((snapshot/'compiled/LauncherCapture.dll').read_bytes(),dll.read_bytes())
            receipt=json.loads((snapshot/'compiled/BUILD_ARTIFACT.json').read_text())
            self.assertEqual(receipt['sha256'],hashlib.sha256(dll.read_bytes()).hexdigest())
            self.assertEqual(dll.read_bytes(),b'compiled fixture')
    def test_full_confirmation_keeps_frozen_dll_path(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'host').mkdir();dll=root/'host/LauncherCapture.dll';dll.write_bytes(b'fixture')
            self.assertIn(dll,source_members(root,root,False))


class FailedCaptureTests(unittest.TestCase):
    def test_missing_diagnostics_are_identical_after_relocation(self):
        outcomes=[]
        for _ in range(2):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d).resolve();(root/'bound').write_bytes(b'x');manifest=root/'manifest.json'
                manifest.write_text(json.dumps({'members':[dict(path='bound',bytes=1,sha256=hashlib.sha256(b'x').hexdigest())]}))
                outcomes.append(capture_files(Evidence(root,manifest),dict(data=root/'DATA.bin')))
        self.assertEqual(outcomes[0],outcomes[1]);self.assertEqual(outcomes[0][1],['DATA.bin'])

    def test_absent_early_failure_outputs_are_reportable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();stdout=root/'stdout.log';stdout.write_bytes(b'READY only')
            manifest=root/'manifest.json';manifest.write_text(json.dumps({'members':[dict(path='stdout.log',bytes=10,sha256=hashlib.sha256(b'READY only').hexdigest())]}))
            captured,missing=capture_files(Evidence(root,manifest),dict(stdout=stdout,data=root/'DATA.bin',ack=root/'ACK.jsonl'))
            self.assertEqual(captured,{'stdout':b'READY only'});self.assertEqual(missing,['DATA.bin','ACK.jsonl'])
    def test_missing_output_does_not_mask_unlisted_present_capture(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();(root/'bound').write_bytes(b'x');(root/'stdout.log').write_bytes(b'x')
            manifest=root/'manifest.json';manifest.write_text(json.dumps({'members':[dict(path='bound',bytes=1,sha256=hashlib.sha256(b'x').hexdigest())]}))
            with self.assertRaises(ValueError):capture_files(Evidence(root,manifest),dict(data=root/'absent',stdout=root/'stdout.log'))


class WindowsDiagnosticTests(unittest.TestCase):
    def test_missing_controller_receipt_is_stable_across_windows_roots(self):
        first=diagnostic(FileNotFoundError(2,'No such file or directory',r'C:\hs\task\runs\one\external\CONTROLLER_END.json'),r'C:\hs\task')
        second=diagnostic(FileNotFoundError(2,'No such file or directory',r'D:\download\extracted\runs\one\external\CONTROLLER_END.json'),r'D:\download\extracted')
        self.assertEqual(first,second)
        self.assertEqual(json.loads(first)['filename'],'$EVIDENCE_ROOT/runs/one/external/CONTROLLER_END.json')
    def test_posix_missing_receipt_is_stable_after_extraction(self):
        self.assertEqual(diagnostic(FileNotFoundError(2,'missing','/a/task/receipt'),'/a/task'),diagnostic(FileNotFoundError(2,'missing','/b/extracted/receipt'),'/b/extracted'))

if __name__=='__main__':unittest.main()
