"""Source-only counterfactuals. All process/provider records below are SYNTHETIC.

No runtime entrypoint, Win32 API, model, actor or subprocess is executed.
Pass the separately hash-verified v6 extraction via --historical-root.
"""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
index = sys.argv.index('--historical-root')
HISTORICAL = Path(sys.argv[index + 1]).resolve()
del sys.argv[index:index + 2]
sys.path[:0] = [str(BASE/'source_candidate/source'), str(HISTORICAL/'source')]
import delivery_binding_v6 as binding
import verify_cpu8 as verifier
import budget_v6


class Accounting(unittest.TestCase):
    def event(self,stamp='2026-10-19T00:00:01Z',code=0,sid=9):
        return dict(observed_utc=stamp,request={'session_id':sid},response={'session_id':sid,'exit_code':code})

    def test_negative_elapsed_cannot_reduce_total_charge(self):
        with self.assertRaisesRegex(ValueError,'capture clock'):
            budget_v6.captured_interval({'registered_utc':'2026-10-19T00:00:02Z'},[self.event()])

    def test_failed_operation_is_charged_with_ceiling(self):
        self.assertEqual(budget_v6.captured_interval({'registered_utc':'2026-10-19T00:00:00.5Z'},[self.event(code=124)]),1)

    def test_settlement_timezone_required(self):
        with self.assertRaisesRegex(ValueError,'capture timezone'):
            budget_v6.captured_interval({'registered_utc':'2026-10-19T00:00:00'},[self.event()])

    def test_settlement_session_change_rejected(self):
        with self.assertRaisesRegex(ValueError,'actual session'):
            budget_v6.captured_interval({'registered_utc':'2026-10-19T00:00:00Z'},[self.event(code=None),self.event(sid=10)])


class Roles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'original'
        self.root.mkdir()
        (self.root/'CAMPAIGN.json').write_text(json.dumps({'original_root': str(self.root)}))

    def test_original_reconstruct_cannot_bypass_current_process_rejection(self):
        with patch('identity_v6.check', return_value={}), patch('campaign_budget.process_check', side_effect=ValueError('CURRENT_PROCESS_REJECT')):
            with self.assertRaisesRegex(ValueError, 'CURRENT_PROCESS_REJECT'):
                verifier.audit(self.root, 'absent', mode='reconstruct')

    def test_original_reconstruct_cannot_bypass_current_storage_rejection(self):
        with patch('identity_v6.check', return_value={}), patch('campaign_budget.process_check', return_value={}), patch('campaign_budget.storage_check', side_effect=ValueError('CURRENT_STORAGE_REJECT')):
            with self.assertRaisesRegex(ValueError, 'CURRENT_STORAGE_REJECT'):
                verifier.campaign_snapshot(self.root, mode='reconstruct')

    def test_original_reconstruct_cannot_bypass_protected_budget(self):
        with patch('identity_v6.check', return_value={}), patch('campaign_budget.process_check', return_value={}), patch('campaign_budget.storage_check', return_value={}), patch('budget_v6.snapshot', side_effect=ValueError('PROTECTED_RESERVE_REJECT')):
            with self.assertRaisesRegex(ValueError, 'PROTECTED_RESERVE_REJECT'):
                verifier.audit(self.root, 'absent', mode='reconstruct')

    def test_original_false_relocation_rejected_before_native_calls(self):
        with patch('identity_v6.check', side_effect=AssertionError('native call')):
            with self.assertRaisesRegex(ValueError, 'cannot claim relocation'):
                verifier.audit(self.root, 'absent', relocated=True)

    def test_original_live_checks_native_identity_first(self):
        with patch('identity_v6.check', side_effect=ValueError('IDENTITY_REJECT')):
            with self.assertRaisesRegex(ValueError, 'IDENTITY_REJECT'):
                verifier.audit(self.root, 'absent', mode='live')

    def test_restored_cannot_claim_live(self):
        moved = Path(self.temp.name)/'restored'
        moved.mkdir()
        (moved/'CAMPAIGN.json').write_bytes((self.root/'CAMPAIGN.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'live original root required'):
            verifier.audit(moved, 'absent', mode='live')

    def test_restored_reconstruction_never_loads_native_checks(self):
        moved = Path(self.temp.name)/'restored'
        moved.mkdir()
        (moved/'CAMPAIGN.json').write_bytes((self.root/'CAMPAIGN.json').read_bytes())
        with patch('campaign_budget.config', return_value=({}, moved.parent)) as config, patch('identity_v6.check', side_effect=AssertionError('native call')):
            self.assertIsNone(verifier.role_checks(moved, True, 'reconstruct'))
            config.assert_called_once_with(moved, read_only=True)

    def test_relocation_requires_explicit_reconstruction(self):
        moved = Path(self.temp.name)/'restored'
        moved.mkdir()
        (moved/'CAMPAIGN.json').write_bytes((self.root/'CAMPAIGN.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'relocated reconstruction required'):
            verifier.audit(moved, 'absent')


class Receipts(unittest.TestCase):
    """This fixture is a data structure, never a record of an actual execution."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'candidate'
        self.ext = Path(self.temp.name)/'capture-owned'
        self.root.mkdir(); self.ext.mkdir()
        self.op = 'synthetic-source-test'
        self.python = 'C:/Synthetic/python.exe'
        self.origin = '2026-10-19T00:00:00+00:00'
        ft = int((datetime.datetime(2026,10,19,tzinfo=datetime.timezone.utc)-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds())*10**7
        self.put('CAMPAIGN.json', dict(original_root=str(self.root), external_root=str(self.ext)))
        self.put('preflight/TOOLS.json', {'python': {'path': self.python, 'sha256': 'SYNTHETIC'}})
        self.argv = [self.python, '-I', '-S', '-B', str(self.root/'source/probe.py')]
        self.operation = dict(id=self.op, root=str(self.root), argv=self.argv, registered_utc=self.origin)
        self.put('tools/'+self.op+'.operation.json', self.operation)
        digest = binding.h(self.root/'tools'/(self.op+'.operation.json'))
        guard_argv = [self.python, '-I', '-S', '-B', str(self.root/'source/operation_guard.py'), '--intent', str(self.root/'tools'/(self.op+'.operation.json')), '--intent-sha256', digest]
        command = subprocess.list2cmdline(guard_argv)
        self.request = dict(cmd=binding.guarded_request(self.root, self.op, digest, self.python), shell='C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', login=False, workdir=str(self.root), max_output_tokens=2000, yield_time_ms=10000)
        self.intent = dict(operation_sha256=digest, request=self.request, registered_utc=self.origin)
        self.put('tools/'+self.op+'.intent.json', self.intent)
        self.receipt = dict(status='CLOSED', job_empty=True, error=None, child_exit_code=0, intent_sha256=digest, member_exits_complete=True, total_job_processes=1)
        self.events = [
            dict(event='GUARD_START', image=self.python, pid=11, created_filetime=str(ft+100), command=command, command_sha256=hashlib.sha256(command.encode()).hexdigest(), intent_sha256=digest),
            dict(event='OP_CREATED_SUSPENDED', argv=self.argv, command=subprocess.list2cmdline(self.argv), image=self.python, pid=12, parent_pid=11, created_filetime=str(ft+200)),
            dict(event='MEMBER_IDENTITY', pid=12, created_filetime=str(ft+200)),
            dict(event='OP_OS_EXIT', pid=12, created_filetime=str(ft+200), exit_filetime=str(ft+300), exit_code=0),
            dict(event='MEMBER_TERMINAL_OS', pid=12, created_filetime=str(ft+200), exit_filetime=str(ft+300), exit_code=0),
            dict(event='MEMBER_HANDLES_CLOSED', count=1, complete=True),
            dict(event='OP_JOB_HANDLE_CLOSED', job_empty=True),
            dict(event='GUARD_END', receipt=self.receipt),
        ]
        self.output = json.dumps(dict(operation=self.op, status='CLOSED', error=None, job_empty=True, child_exit_code=0))+'\r\n'
        self.response = dict(session_id=19, output=self.output, exit_code=0, chunk_id='SYNTHETIC_CHUNK')
        self.capture = dict(id=self.op, kind='initial', request=self.request, response=self.response, observed_utc='2026-10-19T00:00:00.001+00:00', capture_meta=dict(callId='SYNTHETIC', itemId='SYNTHETIC'))
        self.report = self.root/'operations'/self.op/'stdout.log'
        self.report.parent.mkdir(parents=True)
        self.report.write_bytes(b'SYNTHETIC CHILD OUTPUT\n')
        self.persist()

    def put(self, rel, obj):
        path = self.root/rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj), encoding='utf-8')
        return path

    def persist(self):
        self.put('tools/'+self.op+'.intent.json', self.intent)
        self.put('operations/'+self.op+'/RECEIPT.json', self.receipt)
        path = self.root/'operations'/self.op/'EVENTS.jsonl'
        records = [dict(row, seq=i+1, at_ns=i+1, writer_pid=11) for i,row in enumerate(self.events)]
        path.write_text(''.join(json.dumps(x)+'\n' for x in records))
        self.save_capture(self.capture)

    def save_capture(self, data):
        path = self.put('tools/'+self.op+'.'+data['kind']+'.json', data)
        index = self.ext/'capture-index'/path.name
        index.parent.mkdir(exist_ok=True)
        index.write_text(json.dumps(dict(path=str(path), sha256=binding.h(path), bytes=path.stat().st_size, capture_meta=data['capture_meta'])))

    def call(self):
        self.persist()
        return binding.invocation(self.root, self.op, self.argv, self.report)

    def test_consistent_synthetic_fixture_and_id_labels(self):
        result = self.call()
        self.assertEqual(result['provider_call_id'], 'UNKNOWN_NOT_EXPOSED')
        self.assertEqual(result['provider_chunk_ids'], ['SYNTHETIC_CHUNK'])

    def test_substitute_intent_and_captured_command_together(self):
        self.request['cmd'] = '& arbitrary-command'
        with self.assertRaisesRegex(ValueError, 'actual guarded request'): self.call()

    def test_valid_terminal_exit_with_forged_output_rejected(self):
        self.response['output'] = '{"operation":"other"}\n'
        with self.assertRaisesRegex(ValueError, 'provider terminal output'): self.call()

    def test_native_guard_command_substitution(self):
        self.events[0]['command'] = 'arbitrary-command'
        self.events[0]['command_sha256'] = hashlib.sha256(b'arbitrary-command').hexdigest()
        with self.assertRaisesRegex(ValueError, 'guard native command'): self.call()

    def test_guard_digest_substitution(self):
        self.events[0]['command_sha256'] = 'f'*64
        with self.assertRaisesRegex(ValueError, 'guard command digest'): self.call()

    def test_receipt_boolean_without_all_member_exits_rejected(self):
        self.receipt['member_exits_complete'] = False
        with self.assertRaisesRegex(ValueError, 'native member closure'): self.call()

    def test_missing_member_terminal(self):
        self.events = [x for x in self.events if x['event']!='MEMBER_TERMINAL_OS']
        with self.assertRaisesRegex(ValueError, 'member exit inventory'): self.call()

    def test_unobserved_job_start_rejected(self):
        self.receipt['total_job_processes'] = 2
        with self.assertRaisesRegex(ValueError, 'complete start inventory'): self.call()

    def test_extra_environment_fields_rejected(self):
        self.request['env'] = {'PYTHONPATH': 'arbitrary'}
        with self.assertRaisesRegex(ValueError, 'tool request fields'): self.call()

    def test_provider_error_even_with_zero_exit(self):
        self.response['isError'] = True
        with self.assertRaisesRegex(ValueError, 'provider error'): self.call()

    def test_tool_capture_before_native_exit_rejected(self):
        self.capture['observed_utc'] = self.origin
        with self.assertRaisesRegex(ValueError, 'native/provider prospective interval'): self.call()

    def test_registered_after_native_birth_rejected(self):
        self.intent['registered_utc'] = '2026-10-19T00:00:00.0005+00:00'
        with self.assertRaisesRegex(ValueError, 'native/provider prospective interval'): self.call()

    def test_late_registration_rejected(self):
        self.intent['registered_utc'] = '2026-10-19T00:00:01+00:00'
        with self.assertRaisesRegex(ValueError, 'capture order'): self.call()

    def test_incomplete_session_rejected(self):
        del self.response['exit_code']
        with self.assertRaisesRegex(ValueError, 'missing actual completion'): self.call()

    def test_changed_poll_session_rejected(self):
        del self.response['exit_code']; self.response['output'] = ''
        poll = copy.deepcopy(self.capture)
        poll.update(kind='poll1', request={'session_id': 20}, response={'session_id':19, 'exit_code':0, 'output':self.output})
        self.save_capture(poll)
        with self.assertRaisesRegex(ValueError, 'actual poll session'): self.call()

    def test_completed_two_chunk_session(self):
        del self.response['exit_code']; self.response['output'] = ''
        poll = copy.deepcopy(self.capture)
        poll.update(kind='poll1', request={'session_id':19}, response={'session_id':19, 'exit_code':0, 'output':self.output})
        self.save_capture(poll)
        self.assertEqual(self.call()['session_id'], 19)

    def test_output_digest_is_child_bytes(self):
        self.assertEqual(self.call()['report_sha256'], hashlib.sha256(self.report.read_bytes()).hexdigest())


if __name__ == '__main__':
    with patch('subprocess.Popen', side_effect=AssertionError('source tests must not spawn')):
        result = unittest.main(verbosity=2, exit=False).result
    if 'win' in sys.modules:
        raise AssertionError('source tests imported native execution module')
    sys.exit(0 if result.wasSuccessful() else 1)
