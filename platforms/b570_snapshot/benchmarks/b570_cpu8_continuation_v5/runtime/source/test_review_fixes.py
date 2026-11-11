"""Post-review fault tests of production raw gates; synthetic tests are never native qualification."""
import copy,hashlib,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'source'),str(ROOT/'src/rev2')]
import cpu8_monitor,source_guard,tool_binding,integration_gates
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x),encoding='utf8')
def jsonl(p,x):p.write_text(''.join(json.dumps(r)+'\n' for r in x),encoding='utf8')
class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tmp');self.addCleanup(self.tmp.cleanup);self.r=Path(self.tmp.name)
        for n in ['SUPERVISOR.jsonl','WATCHDOG.jsonl','HEARTBEATS.jsonl','SAMPLES.jsonl','WATCHDOG_SAMPLES.jsonl']:
            shutil.copyfile(ROOT/'development/healthy-r0-a1'/n,self.r/n)
    def mutate(self,n,fn):
        rows=cpu8_monitor.records(self.r/n);fn(rows);jsonl(self.r/n,rows)
    def check(self):return cpu8_monitor.check(self.r)
    def test_actual_healthy_raw_streams(self):self.assertEqual(self.check()['status'],'OUTER_MONITOR_RECONSTRUCTED')
    def test_empty_supervisor_stream(self):
        (self.r/'SAMPLES.jsonl').write_bytes(b'')
        with self.assertRaisesRegex(ValueError,'empty'):self.check()
    def test_missing_watchdog_stream(self):
        (self.r/'WATCHDOG_SAMPLES.jsonl').unlink()
        with self.assertRaisesRegex(ValueError,'missing'):self.check()
    def test_no_sample_rows(self):
        self.mutate('SAMPLES.jsonl',lambda rs:rs.__setitem__(slice(None),[dict(rs[0],event='RESOURCE_EXIT_RACE')]))
        with self.assertRaisesRegex(ValueError,'missing SAMPLE'):self.check()
    def test_genuine_overfive_gap(self):
        def f(rs):
            for r in rs:r['begin_ns']-=6_000_000_000
        self.mutate('SAMPLES.jsonl',f)
        with self.assertRaisesRegex(ValueError,'gap'):self.check()
    def test_bad_progress_link(self):
        self.mutate('SAMPLES.jsonl',lambda rs:rs[0].update(watchdog_progress_seq=999999))
        with self.assertRaisesRegex(ValueError,'progress linkage'):self.check()
    def test_resource_excess(self):
        self.mutate('WATCHDOG_SAMPLES.jsonl',lambda rs:rs[0].update(watchdog_rss=513*1024**2))
        with self.assertRaisesRegex(ValueError,'resource limit'):self.check()
    def test_wrong_writer(self):
        self.mutate('SAMPLES.jsonl',lambda rs:rs[0].update(writer_pid=-1))
        with self.assertRaisesRegex(ValueError,'writer'):self.check()
class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tmp');self.addCleanup(self.tmp.cleanup);self.r=Path(self.tmp.name)
        write(self.r/'legacy/ROOT_BINDING.json',dict(task_root=str(ROOT)))
        shutil.copytree(ROOT/'preflight',self.r/'preflight')
        self.run='formal/test-parser-only';self.sha='a'*64;self.py=json.loads((ROOT/'preflight/TOOLS.json').read_bytes())['python']['path']
        self.argv=[self.py,'-B',str(ROOT/'source/outer_watchdog.py'),'--root',str(ROOT),'--run',self.run,'--mode','cpu8','--phase-limit','1800','--supervisor-script',str(ROOT/'source/cpu8_supervisor.py'),'--freeze-sha256',self.sha]
        import subprocess
        cmdline=subprocess.list2cmdline(self.argv)
        self.start=dict(command=cmdline,command_sha256=hashlib.sha256(cmdline.encode()).hexdigest(),image=self.py,pid=123)
        env=dict(TEMP=str(ROOT/'tmp'),TMP=str(ROOT/'tmp'))
        req=dict(cmd='$env:TEMP='+tool_binding.quote(env['TEMP'])+'; $env:TMP='+tool_binding.quote(env['TMP'])+'; & '+' '.join(tool_binding.quote(x) for x in self.argv),shell=json.loads((ROOT/'preflight/TOOLS.json').read_bytes())['powershell']['path'],workdir=str(ROOT),login=False)
        self.intent=dict(argv=self.argv,environment=env,freeze_sha256=self.sha,request=req)
        self.initial=dict(request=req,response=dict(exit_code=0,output=json.dumps(dict(watchdog_closed=True,error=None,run=self.run))))
        self.receipt=dict(watchdog_pid=123,outer_job_empty=True,owned_handles_closed=True,error=None)
        self.binding=dict(intent_path='intent.json',initial_path='initial.json',final_path='initial.json',session_id=None)
    def check(self):
        for n,v in [('intent.json',self.intent),('initial.json',self.initial),('binding.json',self.binding)]:write(self.r/n,v)
        return tool_binding.check(self.r,self.run,self.sha,dict(python=self.py),self.start,self.receipt,'binding.json')
    def test_immediate_terminal_api(self):self.assertEqual(self.check()['status'],'TOOL_WATCHDOG_BOUND')
    def test_session_terminal_api(self):
        self.initial['response']=dict(session_id=456);self.binding.update(session_id=456,final_path='last.json')
        write(self.r/'last.json',dict(request=dict(session_id=456),response=dict(exit_code=0,output=json.dumps(dict(watchdog_closed=True,error=None,run=self.run)))))
        self.assertEqual(self.check()['session_id'],456)
    def test_substring_unrelated_command(self):
        self.intent['request']['cmd']='echo '+self.sha
        with self.assertRaisesRegex(ValueError,'unrelated'):self.check()
    def test_wrong_real_watchdog_command(self):
        self.start['command']+=' --wrong yes';self.start['command_sha256']=hashlib.sha256(self.start['command'].encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,'actual watchdog command'):self.check()
    def test_wrong_output_run(self):
        self.initial['response']['output']=json.dumps(dict(watchdog_closed=True,error=None,run='other'))
        with self.assertRaisesRegex(ValueError,'terminal output'):self.check()
    def test_unclosed_api_session(self):
        self.initial['response'].pop('exit_code')
        with self.assertRaisesRegex(ValueError,'immediate tool closure'):self.check()
class ReservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tmp');self.addCleanup(self.tmp.cleanup);self.r=Path(self.tmp.name);self.path=self.r/'processes/unknown/OS_EVENTS.jsonl';self.path.parent.mkdir(parents=True)
        self.row=dict(event='OBSERVER_START');jsonl(self.path,[self.row]);self.reg=dict(run='processes/unknown',case_attempts=1,registered_utc='2026-01-01T00:00:00Z')
    def test_unregistered_actual_observer_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNREGISTERED_D0_START'):source_guard.actual_d0(self.r,[])
    def test_registered_start_before_case_charged(self):self.assertEqual(source_guard.actual_d0(self.r,[self.reg])['actual'],1)
    def test_late_reservation_rejected(self):
        jsonl(self.path,[self.row,dict(event='ROOT_CREATED_SUSPENDED',created_filetime='133801632000000000')]);self.reg['registered_utc']='2027-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'NON_PROSPECTIVE'):source_guard.actual_d0(self.r,[self.reg])
    def test_actual_all_attempts_including_preentry(self):
        regs=json.loads((ROOT/'D0_RESERVATIONS.json').read_bytes());r=source_guard.actual_d0(ROOT,regs)
        self.assertEqual(r['actual'],18)
class D0Tests(unittest.TestCase):
    def setUp(self):
        self.s=ROOT/'D0_EVIDENCE_SNAPSHOT';m=self.s/'legacy/AUDIT_INPUT_MANIFEST-normal-readonly-final.json'
        self.b=dict(d0_snapshot='D0_EVIDENCE_SNAPSHOT',d0_manifest=m.name,d0_manifest_sha256=integration_gates.sha(m),d0_expected_sha256=integration_gates.sha(self.s/'EXPECTED.json'))
    def test_actual_original_raw_reconstruction(self):self.assertEqual(len(integration_gates.d0_reconstruct(ROOT,self.b)),2)
    def test_replaced_snapshot_manifest_rejected(self):
        self.b['d0_manifest_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'snapshot binding'):integration_gates.d0_reconstruct(ROOT,self.b)
    def test_replaced_summary_not_trusted(self):
        self.b['d0_expected_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'snapshot binding'):integration_gates.d0_reconstruct(ROOT,self.b)
if __name__=='__main__':unittest.main()
