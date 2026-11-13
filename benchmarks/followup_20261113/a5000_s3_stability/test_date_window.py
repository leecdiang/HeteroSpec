"""Calendar admission and continuation tests; no native subprocess is invoked."""
import datetime as dt
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import native
import analyze

RealDatetime = dt.datetime


class AfterAllDates(RealDatetime):
    @classmethod
    def now(cls, tz=None):
        return RealDatetime(2026, 11, 16, tzinfo=dt.timezone.utc)


class BetweenStartAndFinishLimits(RealDatetime):
    @classmethod
    def now(cls, tz=None):
        return RealDatetime(2026, 11, 14, 20, tzinfo=dt.timezone.utc)


class DateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.outputs = self.root / 'outputs'
        (self.outputs / 'R1').mkdir(parents=True)
        native.write(self.outputs / 'R1/START.json', dict(utc='2026-11-13T19:00:00+00:00'))
        native.write(self.outputs / 'R1/STATUS.json', dict(status='COMPLETE', utc='2026-11-14T02:00:00+00:00'))

    def tearDown(self):
        self.temp.cleanup()

    def test_remaining_queue_uses_completion_and_skips_finished_panels(self):
        config = self.root / 'config.json'
        native.write(config, dict(output_root=str(self.outputs)))
        records = []
        argv = ['run_campaign.py', '--config', str(config), '--from-panel', 'R2']
        with patch.object(sys, 'argv', argv), patch('datetime.datetime', AfterAllDates), \
             patch.object(native, 'write', side_effect=lambda p, x: records.append(x.copy())), \
             patch('subprocess.call', return_value=0) as call, patch.object(analyze, 'analyze', return_value={}):
            runpy.run_path(str(Path(__file__).with_name('run_campaign.py')), run_name='__main__')
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.args[0][-2:], ['--panel', 'R2'])
        self.assertEqual(records[0]['scheduled_utc'], '2026-11-15T02:00:01+00:00')

    def test_native_gate_rejects_24h_from_start_but_18h_from_completion(self):
        plans = self.root / 'plans/R2'
        plans.mkdir(parents=True)
        native.write(plans / 'MANIFEST.json', dict(roots=dict(inputs=[]), workers=[]))
        campaign = native.Campaign.__new__(native.Campaign)
        campaign.root = self.outputs
        campaign.c = dict(plans=str(plans.parent), activity_lock=str(self.root / 'activity.lock'),
                          gpu_lock=str(self.root / 'gpu.lock'))
        campaign.preflight = lambda: {}
        campaign.launch = Mock(side_effect=AssertionError('No native launch permitted'))
        with patch('datetime.datetime', BetweenStartAndFinishLimits):
            with self.assertRaisesRegex(ValueError, '24h date separation'):
                campaign.panel('R2')
        campaign.launch.assert_not_called()
        self.assertFalse((self.outputs / 'requests.jsonl').exists())


if __name__ == '__main__': unittest.main()
