"""Real production-policy CPU integration, plus exact-ns boundary tests."""
import base64
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
import unittest
from common import BASE,DESIGN,HERE,load,write_new,sha,need,Journal
from storage import production_allowed,parse_notifications,Watch
from timing import Coverage

ROUND=None
PS='C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
receipts=[]

class EngineeringTests(unittest.TestCase):
    def run_case(self,name,expect,**extra):
        folder=ROUND/name;folder.mkdir(exist_ok=False)
        case=dict(purpose='CPU_INTEGRATION',case_dir=str(folder),journal_dir=str(folder/'native'),
            active=str(BASE/'outputs'/(ROUND.name+'__'+name)),
            protected_roots=[str(DESIGN),str(BASE/'sources'),str(BASE/'outputs')],
            launcher_log_dir=str(folder/'launcher'),launcher_seconds=15,
            required_modules=[dict(path=sys.executable,sha256=sha(sys.executable))],**extra)
        if case.get('wrong_module'):
            case['required_modules'][0]['sha256']='0'*64
        if case.pop('stress',False):
            case['protected_roots'].append('C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/host_outputs/supervised_numerical_v4/SCALING_TREE')
        path=folder/'CASE.json';write_new(path,case)
        command=[PS,'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(HERE/'launch.ps1'),'-CasePath',str(path)]
        begin=time.monotonic_ns();p=subprocess.run(command,capture_output=True,timeout=25)
        (folder/'POWERSHELL.stdout.log').write_bytes(p.stdout);(folder/'POWERSHELL.stderr.log').write_bytes(p.stderr)
        result=load(folder/'CONTROLLER_RESULT.json') if (folder/'CONTROLLER_RESULT.json').exists() else None
        closed=load(folder/'launcher/CLOSED.json') if (folder/'launcher/CLOSED.json').exists() else None
        receipt=dict(name=name,expected=expect,command=command,wall_seconds=(time.monotonic_ns()-begin)/1e9,exit_code=p.returncode,
            result=result,launcher=closed,CPU_only=True,GPU_queries=0,model_requests=0)
        write_new(folder/'TEST_RECEIPT.json',receipt);receipts.append(receipt)
        self.assertIsNotNone(result,(p.stdout+p.stderr).decode(errors='replace'))
        self.assertEqual(result['result']['status'],expect,str(result))
        self.assertEqual(p.returncode,0 if expect=='ADMITTED' else 90)
        self.assertEqual(closed['readers_completed'],2)
        self.assertIsNone(closed['error'])
        return case,result['result'],folder
    def test_normal_append_active_and_postaudit(self):
        case,r,p=self.run_case('normal','ADMITTED',post_hash_delay=1.25)
        self.assertGreater((p/'native/stdout.log').stat().st_size,1000)
        self.assertGreater((p/'native/stderr.log').stat().st_size,100)
        self.assertGreater(r['post_exit_audit_seconds'],1)
        self.assertGreaterEqual(r['post_exit_audit_begin_ns'],r['exit_observed_ns'])
        for row in [json.loads(s) for s in (p/'native/MONITOR.jsonl').read_text().splitlines()]:
            if row['event']=='READ_END':self.assertLessEqual(row['end_ns'],r['exit_observed_ns'])
    def test_identity_wait_still_observed(self):
        case,r,p=self.run_case('slow_identity','ADMITTED',identity_delay=1.25)
        a=[json.loads(s) for s in (p/'native/MONITOR.jsonl').read_text().splitlines()]
        self.assertGreaterEqual(sum(x['event']=='READ_END' and x['stream']=='resource' for x in a),8)
    def denied_path(self,name,path):
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(b'CPU_FROZEN_BASELINE')
        case,r,p=self.run_case(name,'FAILED',bad_path=str(path))
        decisions=[];buffers=[]
        for f in (p/'native').glob('WATCH_*.jsonl'):
            for row in [json.loads(s) for s in f.read_text().splitlines()]:
                if row['event']=='RAW_NOTIFY':buffers.append(row)
                if row['event']=='NOTIFY_DECISION' and not row['allowed']:decisions.append(row)
        self.assertTrue(buffers);self.assertTrue(decisions)
        self.assertTrue(all('action' in x and 'relative_path' in x and x['writing_PID'] is None for x in decisions))
        self.assertTrue(any(base64.b64decode(x['raw_base64']) for x in buffers))
    def test_sealed_source_results_rejected(self):
        self.denied_path('sealed_results',DESIGN/'cpu_fixture_results'/ROUND.name/'illegal.log')
    def test_inactive_output_rejected(self):
        self.denied_path('inactive',BASE/'outputs'/'INACTIVE_CPU_FIXTURES'/ROUND.name/'old.record')
    def test_frozen_input_rejected(self):
        self.denied_path('frozen_input',BASE/'sources'/'CPU_INPUT_FIXTURES'/ROUND.name/'frozen.bin')
    def test_overflow_retains_acknowledged_frames(self):
        case,r,p=self.run_case('overflow','FAILED',frames=10000,payload=4000,interval=0,native_log_soft=32768)
        self.assertIn('log',r['error'])
        raw=(p/'native/stdout.log').read_bytes();present=set()
        for line in raw.split(b'\n')[:-1]:
            x=json.loads(line)
            if x['event']=='FRAME':present.add(x['index'])
        ack=(Path(case['active'])/'PRODUCER_ACK.txt').read_bytes()
        complete=[int(x) for x in ack.split(b'\n')[:-1]]
        self.assertTrue(complete);self.assertTrue(set(complete)<=present)
        self.assertLessEqual(len(raw),32768+131072)
    def test_resource_failure(self):
        self.run_case('resource_failure','FAILED',resource_failure=True)
    def test_real_observer_timeout(self):
        self.run_case('observer_timeout','FAILED',monitor_stall=True,frames=80)
    def test_wrong_loaded_module_rejected_before_go(self):
        case,r,p=self.run_case('module_mismatch','FAILED',wrong_module=True)
        self.assertFalse((Path(case['active'])/'DATA.bin').exists())
        self.assertIn('module',r['error'])
    def test_truncated_output_fails_post_audit(self):
        case,r,p=self.run_case('truncated','FAILED',truncate_output=True)
        self.assertIn('truncated',r['error'])
    def test_notification_loss_fails(self):
        case,r,p=self.run_case('notification_loss','FAILED',notification_loss=True)
        self.assertIn('loss',r['error'])
    def test_child_timeout(self):
        self.run_case('child_timeout','FAILED',timeout_child=True,native_timeout=1)
    def test_abnormal_exit(self):
        self.run_case('abnormal_exit','FAILED',abnormal_exit=True)
    def test_quick_exit_is_not_fabricated_qualification(self):
        case,r,p=self.run_case('quick_exit','FAILED',quick_exit=True)
        self.assertIsNotNone(r['PID']);self.assertIsNotNone(r['exit_observed_ns'])
    def test_real_late_panel_topology(self):
        case,r,p=self.run_case('late_panel','ADMITTED',stress=True)
        self.assertEqual(r['coverage']['directory']['valid_reads']>0,True)
        reads=[json.loads(s) for s in (p/'native/MONITOR.jsonl').read_text().splitlines()]
        values=[x for x in reads if x['event']=='READ_END' and x['stream']=='directory']
        self.assertTrue(values);self.assertTrue(all(x['values']['historical_files_scanned']==0 for x in values))
    def test_exact_clock_boundary(self):
        for gap,passes in [(999999999,True),(1000000000,True),(1000000001,False)]:
            c=Coverage(0)
            for stream in ('resource','directory'):
                c.event(dict(event='READ_BEGIN',stream=stream,begin_ns=0))
                event=dict(event='READ_END',stream=stream,begin_ns=0,end_ns=gap)
                if passes:c.event(event)
                else:
                    with self.assertRaises(ValueError):c.event(event)
            terminal=Coverage(0)
            for stream in ('resource','directory'):
                terminal.event(dict(event='READ_BEGIN',stream=stream,begin_ns=0))
                terminal.event(dict(event='READ_END',stream=stream,begin_ns=0,end_ns=0))
            if passes:terminal.terminal(gap)
            else:
                with self.assertRaises(ValueError):terminal.terminal(gap)
    def test_production_policy_no_cpu_root_exception(self):
        active=BASE/'outputs'/'sample/data'
        self.assertFalse(production_allowed(BASE/'outputs'/'unexpected',active))
        self.assertFalse(production_allowed(DESIGN/'results',active))
        self.assertTrue(production_allowed(active/'vector.bin',active))
        for data in (b'',b'a',struct.pack('<III',0,9,0)):
            with self.assertRaises(ValueError):parse_notifications(data)

if __name__=='__main__':
    revision=int(sys.argv.pop(1));need(revision in (0,1),'at most2 integration revisions')
    ROUND=BASE/'journals'/('S0_revision'+str(revision));ROUND.mkdir(exist_ok=False)
    with (ROUND/'SUITE.stderr.log').open('x',encoding='utf-8') as stream:
        result=unittest.TextTestRunner(verbosity=2,stream=stream).run(unittest.defaultTestLoader.loadTestsFromTestCase(EngineeringTests))
    write_new(ROUND/'SUITE.json',dict(tests=result.testsRun,errors=len(result.errors),failures=len(result.failures),passed=result.wasSuccessful(),
        failure_details=[dict(test=str(t),traceback=s) for t,s in result.failures],error_details=[dict(test=str(t),traceback=s) for t,s in result.errors],
        receipts=receipts,source_hashes={p.name:sha(p) for p in HERE.glob('*') if p.is_file()},CPU_only=True,GPU_queries=0,model_requests=0))
    print('CPU integration revision',revision,'tests',result.testsRun,'failures',len(result.failures),'errors',len(result.errors))
    raise SystemExit(0 if result.wasSuccessful() else 1)
