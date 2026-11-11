"""CPU regressions for correct-hash but semantically wrong execution declarations."""
import copy,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'p1'))
from protocol import read_json,file_sha,digest
from contract_audit import evaluate
class CadenceContract(unittest.TestCase):
 def test_actual_approved_F0_hash_does_not_certify_sampling(self):
  f0=read_json(ROOT/'p0/F0_EXECUTION.json');self.assertEqual(file_sha(ROOT/'p0/F0_EXECUTION.json'),digest(f0));self.assertEqual(digest(f0),read_json(ROOT/'p1/AUTHOR_APPROVAL.json')['F0_sha256']);report=read_json(ROOT/'p1/EXECUTION_CONTRACT_AUDIT.json');result=evaluate(f0,report['receipts']);self.assertEqual(result['status'],'VIOLATION_REQUIRES_STOP');self.assertEqual(len(result['violations']),8);self.assertTrue(all(x['actual_requested_period_ms'] is None for x in result['violations']))
 def test_native_checkpoint_receipt_cannot_be_filled_as100ms(self):
  f0=read_json(ROOT/'p0/F0_EXECUTION.json');row=copy.deepcopy(read_json(ROOT/'p1/EXECUTION_CONTRACT_AUDIT.json')['receipts'][0]);self.assertEqual(row['arm'],'R');self.assertGreater(row['max_observed_gap_ms'],100);self.assertEqual(evaluate(f0,[row])['status'],'VIOLATION_REQUIRES_STOP');row['requested_period_ms']=100;self.assertNotEqual(row,read_json(ROOT/'p1/EXECUTION_CONTRACT_AUDIT.json')['receipts'][0])
if __name__=='__main__':unittest.main(verbosity=2)
