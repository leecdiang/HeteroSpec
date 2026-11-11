import ast,hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from observer_policy import profile,violations,MiB
from startup_preflight import ENTRIES,authenticate,probe_entries
from review_entry import command
HERE=Path(__file__).parent

class EntryLaunchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=(Path(self.tmp.name)/'task with spaces').resolve();(self.root/'source').mkdir(parents=True);(self.root/'src/rev2').mkdir(parents=True)
        for n in (*ENTRIES,'entry_bootstrap.py','observer_policy.py','job_census.py','source_guard.py','process_registry.py'):shutil.copyfile(HERE/n,self.root/'source'/n)
        # This fake backend tests REAL subprocess/entry resolution only. It is NOT a Win32 test.
        for n in ('win','guards','history','verify'):(self.root/'src/rev2'/(n+'.py')).write_text('# import-only fixture\n')
        shutil.copyfile(HERE.parent/'src/rev2/exception_policy.py',self.root/'src/rev2/exception_policy.py')
        self.foreign=Path(self.tmp.name)/'foreign';self.foreign.mkdir()
        (self.foreign/'win.py').write_text("raise RuntimeError('cwd shadow imported')\n")
    def test_all_four_actual_entry_processes_from_foreign_cwd(self):
        rows=probe_entries(self.root,Path(sys.executable),self.foreign)
        self.assertEqual(len(rows),4)
        self.assertTrue(all(r.get('identity_checked') for r in rows),rows)
        self.assertFalse((self.root/'development').exists())
        self.assertFalse((self.root/'processes').exists())
    def test_historical_missing_path_is_detected_in_real_child(self):
        p=self.root/'source/stall_supervisor.py';s=p.read_text()
        s=s.replace('DEPLOYED_ROOT=bootstrap(__file__)','')
        p.write_text(s)
        rows=probe_entries(self.root,Path(sys.executable),self.foreign)
        self.assertEqual(rows[-1]['entry'],'stall_supervisor.py')
        self.assertNotEqual(rows[-1]['exit_code'],0)
        self.assertIn("No module named 'win'",rows[-1]['stderr'])
    def test_missing_operational_dependency_rejected(self):
        (self.root/'source/observer_policy.py').unlink()
        rows=probe_entries(self.root,Path(sys.executable),self.foreign)
        self.assertNotEqual(rows[0]['exit_code'],0)
        self.assertIn('observer_policy',rows[0]['stderr'])
    def test_broken_later_entry_dependency_rejected(self):
        (self.root/'source/source_guard.py').write_text("raise RuntimeError('broken dependency')\\n")
        rows=probe_entries(self.root,Path(sys.executable),self.foreign)
        self.assertEqual(rows[-1]['entry'],'outer_watchdog.py')
        self.assertNotEqual(rows[-1]['exit_code'],0)
    def test_missing_runtime_rejected(self):
        shutil.rmtree(self.root/'src/rev2')
        rows=probe_entries(self.root,Path(sys.executable),self.foreign)
        self.assertIn('DEPLOYED_RUNTIME_MISSING',rows[0]['stderr'])
    def test_import_failure_cannot_be_readiness(self):
        (self.root/'src/rev2/win.py').write_text("raise RuntimeError('native import failed')\n")
        rows=probe_entries(self.root,Path(sys.executable),self.foreign)
        self.assertNotEqual(rows[0]['exit_code'],0)
    def test_extra_operational_arguments_rejected(self):
        cp=subprocess.run([sys.executable,'-I','-B',str(self.root/'source/stall_harness.py'),'--startup-check',str(self.root)],capture_output=True,text=True)
        self.assertNotEqual(cp.returncode,0)
        self.assertFalse((self.root/'development').exists())
    def test_manifest_replacement_and_extra_source_rejected(self):
        files={p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*.py')}
        m=self.root/'ENTRY_SOURCE_MANIFEST.json';m.write_text(json.dumps({'files':files}));sha=hashlib.sha256(m.read_bytes()).hexdigest()
        authenticate(self.root,m,sha)
        (self.root/'source/extra.py').write_text('x=1')
        with self.assertRaisesRegex(ValueError,'inventory'):authenticate(self.root,m,sha)
        m.write_text('{}')
        with self.assertRaisesRegex(ValueError,'digest'):authenticate(self.root,m,sha)

class ObserverPolicyTests(unittest.TestCase):
    def members(self,n,rss=10*MiB):return [dict(pid=i,rss_bytes=rss) for i in range(n)]
    def test_ten_helpers_do_not_hit_actor_limit(self):
        self.assertEqual(violations(profile('review',900),self.members(10),10*MiB),[])
        self.assertIn('live_process_count',violations(profile('case',900),self.members(10),10*MiB))
    def test_review_still_bounded(self):
        self.assertIn('live_process_count',violations(profile('review',900),self.members(33),10*MiB))
    def test_review_per_process_limit(self):
        self.assertIn('per_process_rss',violations(profile('review',900),self.members(1,2048*MiB+1),10*MiB))
    def test_review_aggregate_limit(self):
        self.assertIn('aggregate_rss',violations(profile('review',900),self.members(5,1024*MiB),10*MiB))
    def test_observer_limit_unchanged(self):
        self.assertIn('observer_rss',violations(profile('review',900),[],512*MiB+1))
    def test_invalid_deadlines(self):
        for v in (0,-1,901,float('nan'),float('inf')):
            with self.assertRaises(ValueError):profile('review',v)
    def test_review_entry_always_selects_review(self):
        c=command(Path('task'),'review1',900,['reviewer','exec'],Path(sys.executable))
        self.assertEqual(c[c.index('--kind')+1],'review')
        self.assertEqual(c[-2:],['reviewer','exec'])
    def test_actual_observer_records_decision_before_rejection(self):
        # Check the actual branch's data flow, not a parallel policy implementation.
        tree=ast.parse((HERE/'observe.py').read_text())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        decisions=[n for n in calls if n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='LIMIT_DECISION']
        self.assertEqual(len(decisions),1)
        source=(HERE/'observe.py').read_text()
        self.assertLess(source.index("M.emit('LIMIT_DECISION'"),source.index("need(not bad"))

class CensusTests(unittest.TestCase):
    def api(self):
        from types import SimpleNamespace
        self.closed=[]
        return SimpleNamespace(job_pids=lambda j:list(range(1,11)),open_process=lambda *args:args[-1],
             os_times=lambda h:dict(created_filetime=str(h)),alive=lambda h:True,rss=lambda h:10*MiB,
             close=lambda h:self.closed.append(h) or True,checked=lambda value,message:value)
    def test_nested_children_are_counted_even_without_debug_events(self):
        from job_census import census
        api=self.api();snapshot=census('job',api)
        self.assertEqual(len(snapshot['members']),10)
        self.assertEqual(self.closed,list(range(1,11)))
        self.assertIn('live_process_count',violations(profile('case',900),snapshot['members'],MiB,len(snapshot['job_pids'])))
    def test_live_resource_failure_is_not_ignored(self):
        from job_census import census
        api=self.api()
        def failed(h):raise OSError('read failure')
        api.rss=failed
        with self.assertRaises(OSError):census('job',api)
        self.assertEqual(self.closed,[1])
    def test_membership_open_failure_rejects(self):
        from job_census import census
        api=self.api();api.open_process=lambda *args:None
        with self.assertRaisesRegex(RuntimeError,'OPEN_FAILED'):census('job',api)


class SmokeAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name)
        limits=profile('case',30)
        self.events=[dict(event='OBSERVER_START',process_kind='case',limits=limits,seconds=30)]
        for pid in range(1,10):
            self.events.append(dict(event='PROCESS_CREATE',pid=pid,created_filetime=str(pid)))
            self.events.append(dict(event='PROCESS_CLOSED',pid=pid,created_filetime=str(pid),exit_filetime=str(pid+100)))
        self.events.append(dict(event='FAILURE_JOB_EMPTY',active_pids=[]))
        self.samples=[dict(event='LIMIT_DECISION',limits=limits,job_pids=list(range(1,10)),
                     members=[dict(pid=i,created_filetime=str(i),rss_bytes=MiB) for i in range(1,10)],observer_rss=MiB,violations=['live_process_count'])]
        (self.folder/'INCOMPLETE.json').write_text(json.dumps(dict(error='COMMAND_RESOURCE_LIMIT:live_process_count',cleanup_confirmed=True,unclosed=[],cleanup_error=None)))
    def check(self):
        from check_observer_smoke import check
        for name,rows in [('OS_EVENTS.jsonl',self.events),('RESOURCES.jsonl',self.samples)]:
            (self.folder/name).write_text(''.join(json.dumps(dict(r,seq=i+1))+'\n' for i,r in enumerate(rows)))
        return check(self.folder,'case',True)
    def test_expected_limit_requires_actual_closure(self):self.assertEqual(self.check()['closed'],9)
    def test_actual_isolated_checker_cli(self):
        self.check()
        cp=subprocess.run([sys.executable,'-I','-B',str(HERE/'check_observer_smoke.py'),'--folder',str(self.folder),'--kind','case','--expect-rejection'],cwd=self.folder,capture_output=True,text=True)
        self.assertEqual(cp.returncode,0,cp.stderr)
        self.assertEqual(json.loads(cp.stdout)['status'],'OBSERVER_SMOKE_PASS')
    def test_missing_exit_is_not_clean(self):
        self.events=[r for r in self.events if not(r['event']=='PROCESS_CLOSED' and r['pid']==9)]
        with self.assertRaisesRegex(ValueError,'exit coverage'):self.check()
    def test_enlarged_profile_rejected_even_if_internally_consistent(self):
        self.events[0]['limits']['live']=64
        self.samples[0]['limits']['live']=64
        with self.assertRaisesRegex(ValueError,'noncanonical'):self.check()
    def test_sampled_identity_without_exit_rejected(self):
        self.events=[r for r in self.events if r.get('pid')!=9]
        with self.assertRaisesRegex(ValueError,'sampled identity'):self.check()
    def test_wrong_failure_reason_rejected(self):
        (self.folder/'INCOMPLETE.json').write_text(json.dumps(dict(error='OTHER_FAILURE',cleanup_confirmed=True,unclosed=[],cleanup_error=None)))
        with self.assertRaisesRegex(ValueError,'wrong rejection'):self.check()
    def test_false_resource_decision_rejected(self):
        self.samples[0]['violations']=['aggregate_rss']
        with self.assertRaisesRegex(ValueError,'reconstruction'):self.check()




class TypedHistoryTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0,str(HERE.parent/'src/rev2'))
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        (self.root/'src/rev2').mkdir(parents=True);(self.root/'src/rev2/actor.py').write_bytes(b'actor')
        self.folder=self.root/'development/freeze-r1';self.folder.mkdir(parents=True)
        expected={'source_and_manifest':'FREEZE_REPLACED','before_child_manifest':'initial freeze digest mismatch',
                  'source_only':'SOURCE_DRIFT','missing_pin':'initial freeze digest required'}
        for mode,reason in expected.items():
            f=self.folder/mode;(f/'sacrifice/src/rev2').mkdir(parents=True)
            (f/'sacrifice/CAPABILITY_FREEZE.json').write_bytes(b'{}')
            (f/'sacrifice/src/rev2/actor.py').write_bytes(b'actor\n# sacrificial mutation\n')
            rows=[dict(event='CASE_BEGIN',case=mode,pid=123)]
            if mode in ('source_only','source_and_manifest'):rows.append(dict(event='INITIAL_BASELINE_ACCEPTED'))
            rows += [dict(event='ACTUAL_MUTATION',mode=mode,initial_sha256='0'*64,current_sha256=hashlib.sha256(b'{}').hexdigest()),
                     dict(event='EXPECTED_DETECTOR',reason=reason),dict(event='CASE_CLOSED',case=mode,status='PASS')]
            (f/'EVENTS.jsonl').write_text(''.join(json.dumps(dict(r,seq=i+1,at_ns=i))+'\n' for i,r in enumerate(rows)))
        self.registration=dict(revision=0,run='development/freeze-r1',case_attempts=4,kind='in_process_freeze')
        (self.root/'development/REVISION_FREEZE.json').write_text(json.dumps(self.registration))
        (self.root/'development/REVISION_STALL.json').write_text(json.dumps(dict(revision=0,run='development/stall-r2-a1',case_attempts=2,kind='watchdog')))
    def budget(self):
        from history import development_budget
        return development_budget(self.root,self.root/'development/stall-r2-a1')
    def test_freeze_before_stall_uses_actual_schema_and_keeps_charge(self):
        out=self.budget()
        self.assertEqual(out['reserved_development_cases'],6)
        self.assertEqual(out['coverage'][0]['in_process_cases'],4)
        self.assertEqual(out['current_case_reservation'],2)
        self.assertFalse((self.folder/'WATCHDOG.jsonl').exists())
    def test_watchdog_kind_still_requires_watchdog_evidence(self):
        self.registration['kind']='watchdog'
        (self.root/'development/REVISION_FREEZE.json').write_text(json.dumps(self.registration))
        with self.assertRaisesRegex(ValueError,'watchdog evidence'):self.budget()
    def test_missing_freeze_closure_rejected(self):
        f=self.folder/'source_only/EVENTS.jsonl';lines=f.read_text().splitlines();f.write_text('\n'.join(lines[:-1])+'\n')
        with self.assertRaisesRegex(ValueError,'event schema'):self.budget()
    def test_missing_actual_mutation_rejected(self):
        (self.folder/'source_only/sacrifice/src/rev2/actor.py').write_bytes(b'actor')
        with self.assertRaisesRegex(ValueError,'mutation absent'):self.budget()
    def test_observer_smoke_attempt_is_counted_from_actual_start(self):
        from source_guard import actual_d0
        self.root=self.root/'isolated-smoke';folder=self.root/'processes/smoke';folder.mkdir(parents=True)
        (folder/'OS_EVENTS.jsonl').write_text('{"event":"OBSERVER_START"}\n')
        r=dict(revision=0,run='processes/smoke',kind='observed_command',case_attempts=1)
        self.assertEqual(actual_d0(self.root,[r])['actual'],1)

if __name__=='__main__':unittest.main()
