import unittest
from unittest.mock import patch
from datetime import datetime, timezone
import diagnostic as d
import common as c

class DiagnosticTests(unittest.TestCase):
    def test_exact_registered_schedule(self):
        rows=d.slots()
        self.assertEqual(len({r['slot_id'] for r in rows}),54)
        self.assertEqual({r['lifecycle'] for r in rows},{'fresh'})
        self.assertEqual({r['producer'] for r in rows},{'NATIVE','P1','P4_NATIVE'})
        self.assertTrue(all(r['diagnostic_only'] for r in rows))

    def test_complete_unexamined_vector_rows(self):
        raw={'endpoint':{'ids':[1,2]},'cycles':[{'cycle':0,'proposals':[3,4,5],'decisions':[2,6,7,8]}]}
        expected=d.expected_vectors(raw,{'draft_enabled':True})
        self.assertEqual(len(expected),8)
        self.assertEqual(expected['target/verify-0-3.f32'],8)
        self.assertEqual(expected['draft/proposal-0-2.f32'],5)

    def test_metadata_alias_requires_exact_operand_and_layer(self):
        q={'name':'jsa_llama_query_batch-3','ne':[128,1,32,4],'nb':[4,16384,512,16384]}
        g={'name':'kq-3','op':'MUL_MAT','sources':[{},q]}
        self.assertEqual(d.geometry({'geometry':[g]},{'scope':'QB'}),[q])
        self.assertEqual(d.geometry({'geometry':[g]},{'scope':'PQ'}),[])
        for bad in ({**g,'op':'ADD'},{**g,'name':'kq-4'},{**g,'sources':[q,{}]}):
            self.assertEqual(d.geometry({'geometry':[bad]},{'scope':'QB'}),[])

    def test_formal_date_has_priority(self):
        with patch.object(c.host,'validate_freeze',return_value={'calendar_dates':['2026-10-30','2026-10-31','2026-11-01']}),patch.object(c.s,'read',return_value=[]),patch.object(c,'now',return_value=datetime(2026,10,30,16,tzinfo=timezone.utc)),patch.object(c.s,'lines',return_value=[{'date_slot':0,'unit_id':'formal/d0/s0/Qwen'}]):
            with self.assertRaisesRegex(ValueError,'formal collection has priority'):
                c.idle_window(600)

    def test_deadline_excludes_next_formal_window(self):
        completed=[{'unit_id':'done','status':'COMPLETE','cleanup_verified':True}]
        with patch.object(c.host,'validate_freeze',return_value={'calendar_dates':['2026-10-30','2026-10-31','2026-11-01']}),patch.object(c.s,'read',return_value=completed),patch.object(c,'now',return_value=datetime(2026,10,30,15,50,tzinfo=timezone.utc)),patch.object(c.s,'lines',return_value=[]):
            with self.assertRaisesRegex(ValueError,'insufficient gap'):
                c.idle_window(600)

if __name__=='__main__':unittest.main()
