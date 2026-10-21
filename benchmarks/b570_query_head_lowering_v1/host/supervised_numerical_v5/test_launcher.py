"""Real PowerShell redirection, bounded capture and production-watch CPU E2E."""
import json
import pathlib
import subprocess
import time
import unittest
from legacy import HERE,OUT,ROOT,load,save,sha,need

EVIDENCE=None
POWERSHELL='C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'

class Tests(unittest.TestCase):
    def case(self,behavior,late=False,outer_redirection=False):
        root=EVIDENCE/behavior;root.mkdir();source=root/'protected_source';out=root/'protected_output'
        (source/'results').mkdir(parents=True);(source/'inputs').mkdir();(out/'inactive').mkdir(parents=True)
        (source/'CPU_MODULE.bin').write_bytes(b'CPU-HASH-MODULE');(source/'inputs/frozen.input').write_bytes(b'IMMUTABLE-CPU-INPUT');(out/'inactive/old.bin').write_bytes(b'OLD-CPU-RESULT')
        roots=[str(source),str(out)]
        if late:
            oldtree=ROOT/'host_outputs/supervised_numerical_v4/SCALING_TREE'
            need(oldtree.is_dir(),'read-only existing v4 late fixture required');roots.append(str(oldtree))
        cfg=dict(purpose='CPU_LAUNCH_TEST',behavior=behavior,case_root=str(root),external_log_root=str(root/'external_logs'),protected_roots=roots,
            launcher_seconds=15,log_soft_bytes=32768 if behavior=='log_limit' else 1048576)
        save(root/'CASE.json',cfg)
        command=[POWERSHELL,'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(HERE/'launch.ps1'),'-CpuCasePath',str(root/'CASE.json')]
        begin=time.monotonic_ns()
        if outer_redirection:
            with (source/'results/outer.log').open('xb') as f,(source/'results/outer.err').open('xb') as e:r=subprocess.run(command,stdout=f,stderr=e,timeout=25)
            stdout=stderr='Stored in deliberately forbidden outer redirect files'
        else:
            r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=25);stdout,stderr=r.stdout,r.stderr
        save(root/'POWERSHELL_PROCESS.json',dict(command=command,returncode=r.returncode,stdout=stdout,stderr=stderr,wall_seconds=(time.monotonic_ns()-begin)/1e9,CPU_only=True))
        return root,r
    def closed(self,root):
        c=load(root/'external_logs/CLOSED.json')
        for row in c['files']:
            p=root/'external_logs'/row['name'];self.assertEqual(p.stat().st_size,row['bytes']);self.assertEqual(sha(p),row['sha256'])
        self.assertLess(sum(p.stat().st_size for p in (root/'external_logs').iterdir()),16*1024**2)
        self.assertEqual(c['readers_completed'],2)
        return c
    def test_normal_active_writes_and_real_powershell_append(self):
        root,r=self.case('normal');self.assertEqual(r.returncode,0,r.stderr);c=self.closed(root)
        result=load(root/'CPU_CONTROLLER_RESULT.json');self.assertIsNone(result['exception']);self.assertIsNone(result['lifecycle']['stop'])
        for name in ('stdout','stderr'):
            b=(root/'external_logs'/('CONTROLLER.'+name+'.log')).read_bytes()
            self.assertIn(b'LOG_AFTER_WATCH_READY',b);self.assertGreater(b.count(b'APPEND'),10)
        events=[json.loads(s) for s in (root/'external_logs/LAUNCH_EVENTS.jsonl').read_text().splitlines()]
        observations=[x['data'] for x in events if x['event_name']=='LOG_APPEND_OBSERVATION']
        self.assertGreater(len(observations),2);self.assertGreater(observations[-1]['stdout_bytes'],observations[0]['stdout_bytes'])
    def test_protected_results_write_rejected(self):
        root,r=self.case('source_results');self.assertNotEqual(r.returncode,0);self.closed(root)
        c=load(root/'CPU_CONTROLLER_RESULT.json');self.assertIn('sealed storage changed',c['lifecycle']['stop']);self.assertTrue(c['mutation']['after_watch'])
    def test_inactive_slot_write_rejected(self):
        root,r=self.case('inactive');self.assertNotEqual(r.returncode,0);self.closed(root)
        self.assertIn('sealed storage changed',load(root/'CPU_CONTROLLER_RESULT.json')['lifecycle']['stop'])
    def test_frozen_input_write_rejected(self):
        root,r=self.case('frozen_input');self.assertNotEqual(r.returncode,0);self.closed(root)
        self.assertIn('sealed storage changed',load(root/'CPU_CONTROLLER_RESULT.json')['lifecycle']['stop'])
    def test_log_limit_kills_owned_job_and_preserves_pipe_tail(self):
        root,r=self.case('log_limit');self.assertNotEqual(r.returncode,0);c=self.closed(root)
        self.assertIn('soft byte ceiling',c['stop_reason']);self.assertIsNone(c['error'])
        self.assertLessEqual(c['stdout_bytes'],32768+4096+c['stdout_pipe_capacity'])
        self.assertLessEqual(c['stderr_bytes'],32768+4096+c['stderr_pipe_capacity'])
        self.assertTrue(c['soft_limit_terminates_job_then_drains'])
        acknowledgments=(root/'protected_output/active/PRODUCER_ACK.jsonl').read_bytes().splitlines()
        for line in acknowledgments:
            try:row=json.loads(line)
            except json.JSONDecodeError:continue # A kill may interrupt the last acknowledgment write.
            label=b'OUT' if row['stream']=='stdout' else b'ERR';header=label+b'_SEQ='+str(row['index']).zfill(4).encode()+b';'
            frame=header+b'X'*(4096-len(header));content=(root/'external_logs'/('CONTROLLER.'+row['stream']+'.log')).read_bytes()
            self.assertIn(frame,content,'every fully acknowledged produced frame must survive capture')
    def test_real_resource_failure_stops(self):
        root,r=self.case('resource_failure');self.assertNotEqual(r.returncode,0);self.closed(root)
        self.assertIn('resource read failure',load(root/'CPU_CONTROLLER_RESULT.json')['lifecycle']['stop'])
    def test_real_monitor_timeout_stops(self):
        root,r=self.case('monitor_timeout');self.assertNotEqual(r.returncode,0);self.closed(root)
        self.assertIn('observation gap',load(root/'CPU_CONTROLLER_RESULT.json')['lifecycle']['stop'])
    def test_actual_watch_notification_loss_parser_stops(self):
        root,r=self.case('notification_loss');self.assertNotEqual(r.returncode,0);self.closed(root)
        c=load(root/'CPU_CONTROLLER_RESULT.json');self.assertIn('overflow/loss',str(c['exception'])+str(c['lifecycle']))
    def test_real_exit_race_and_cleanup_errors_retained(self):
        for name in ('exit_race','cleanup_failure'):
            root,r=self.case(name);self.assertNotEqual(r.returncode,0);self.closed(root)
            c=load(root/'CPU_CONTROLLER_RESULT.json');self.assertIsNotNone(c['lifecycle']['stop']);self.assertIsNotNone(c['lifecycle']['pid'])
    def test_late_tree_referenced_without_copy_and_bounded_scan(self):
        root,r=self.case('late_tree',late=True);self.assertEqual(r.returncode,0,r.stderr);self.closed(root)
        m=[json.loads(s) for s in (root/'protected_output/active/MONITOR.jsonl').read_text().splitlines()]
        reads=[x for x in m if x.get('stream')=='directory' and x['event']=='READ_END']
        self.assertGreater(len(reads),3);self.assertTrue(all(x['values']['historical_files_scanned']==0 for x in reads))
        save(root/'LATE_SCALE.json',dict(history_fixture='read-only v4 SCALING_TREE, 8000files/262144000bytes',live_directory_read_count=len(reads),max_read_ns=max(x['end_ns']-x['begin_ns'] for x in reads),history_was_not_copied=True))
    def test_outer_powershell_redirect_into_protected_root_blocks_before_controller(self):
        root,r=self.case('outer_redirect',outer_redirection=True);self.assertNotEqual(r.returncode,0)
        self.assertFalse((root/'CPU_CONTROLLER_RESULT.json').exists());self.assertFalse((root/'external_logs').exists())
