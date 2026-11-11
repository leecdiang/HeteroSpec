"""Process launches are mocked; these tests provide no author approval."""
import pathlib
import sys
import unittest
from unittest import mock
import run_diagnostic


class AdmissionRegression(unittest.TestCase):
    def test_wrong_new_f0_hash_never_launches(self):
        with mock.patch.object(sys,'argv',['run_diagnostic.py','--author-approved-f0-sha','0'*64]), mock.patch('subprocess.Popen') as launch:
            with self.assertRaisesRegex(ValueError,'exact new F0'):run_diagnostic.main()
            launch.assert_not_called()

    def test_changed_source_never_launches(self):
        original=run_diagnostic.sha
        f0=run_diagnostic.HERE/'DIAGNOSTIC_F0.json'
        def changed(path):return original(path) if pathlib.Path(path)==f0 else '0'*64
        with mock.patch.object(sys,'argv',['run_diagnostic.py','--author-approved-f0-sha',original(f0)]), mock.patch.object(run_diagnostic,'sha',side_effect=changed), mock.patch('subprocess.Popen') as launch:
            with self.assertRaisesRegex(ValueError,'source changed'):run_diagnostic.main()
            launch.assert_not_called()
