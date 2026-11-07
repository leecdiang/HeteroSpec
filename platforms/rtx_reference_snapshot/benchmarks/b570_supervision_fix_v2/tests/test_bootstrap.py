import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'host'))
from cold_state import initialize,ready_receipt

class ColdInitialization(unittest.TestCase):
    def root(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
        (root/'BOOTSTRAP_REGISTRY.json').write_text(json.dumps(dict(mode='cold-win32-v1',task_begin_ns=1,ledger_parts=['task/PROCESS_LEDGER.jsonl'])))
        return root
    def test_empty_root_needs_no_predecessor(self):
        root=self.root();registry,journal=initialize(root)
        journal.write(b'actual first record\n');journal.close()
        self.assertEqual(registry['task_begin_ns'],1)
        self.assertEqual((root/'PROCESS_LEDGER.jsonl').read_bytes(),b'actual first record\n')
        self.assertFalse((root/'PROCESS_LEDGER_v2.jsonl').exists())
    def test_existing_ledger_cannot_be_reset_or_inherited(self):
        root=self.root();(root/'PROCESS_LEDGER.jsonl').write_bytes(b'old evidence')
        with self.assertRaises(FileExistsError):initialize(root)
        self.assertEqual((root/'PROCESS_LEDGER.jsonl').read_bytes(),b'old evidence')
    def test_unadmitted_registry_never_creates_ledger(self):
        root=self.root();(root/'BOOTSTRAP_REGISTRY.json').write_text('{}')
        with self.assertRaises(ValueError):initialize(root)
        self.assertFalse((root/'PROCESS_LEDGER.jsonl').exists())
    def test_ready_filetime_is_lossless_json_string(self):
        r=ready_receipt(1,134000000000000001,2,'broker.py','sha','ledger')
        self.assertEqual(json.loads(json.dumps(r))['created_filetime'],'134000000000000001')
