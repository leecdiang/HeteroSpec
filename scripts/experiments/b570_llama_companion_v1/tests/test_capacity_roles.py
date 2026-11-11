import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capacity
from common import read, write


class CapacityRolesTests(unittest.TestCase):
    def exercise(self, message):
        calls = []
        configs = {}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root/'config.json', {})

            def prepare(config, epoch):
                configs[str(epoch)] = read(config)
                epoch.mkdir()

            def execute(epoch, attempt, slots, oracle=False, admit=False):
                profile = configs[str(epoch)]
                calls.append((profile['draft_gpu_layers'], oracle))
                self.assertTrue(admit)
                self.assertEqual(slots, [])
                if oracle and profile['draft_gpu_layers'] == 999:
                    write(epoch/'units'/attempt/'native/result.json', {'error': message})
                    write(epoch/'units'/attempt/'RECEIPT.json', {'cleanup_verified': True})
                    raise ValueError(message)

            with patch.object(capacity.host, 'prepare', side_effect=prepare), patch.object(capacity.host, 'execute', side_effect=execute):
                if message == 'device-memory reserve':
                    result = capacity.admit(root/'config.json', root/'capacity')
                    self.assertEqual(result['draft_gpu_layers'], 0)
                    self.assertEqual(len(result['trials']), 1)
                    self.assertEqual(calls, [(999, False), (999, True), (0, False), (0, True)])
                else:
                    with self.assertRaisesRegex(ValueError, 'unknown failure'):
                        capacity.admit(root/'config.json', root/'capacity')
                    self.assertEqual(calls, [(999, False), (999, True)])
                    self.assertFalse((root/'capacity/SELECTED.json').exists())

    def test_oracle_capacity_failure_advances_fixed_order(self):
        self.exercise('device-memory reserve')

    def test_unknown_oracle_failure_is_not_oom(self):
        self.exercise('unrecognized driver error')


if __name__ == '__main__':
    unittest.main()
