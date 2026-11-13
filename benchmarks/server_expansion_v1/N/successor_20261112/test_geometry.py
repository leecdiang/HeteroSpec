"""Meaningful CPU fixtures for ordered work, bounds and denominator retention."""
import unittest

from geometry import schedule


def widths(calls):return [x['width']for x in calls]


class Geometry(unittest.TestCase):
    def test_unequal_rechunk_counterexample(self):
        r=schedule(205,84)
        self.assertEqual(widths(r['whole_fixed']['calls']),[32,19,13,20])
        self.assertEqual(widths(r['whole_rechunk']['calls']),[32,19,32,1])
        self.assertEqual(widths(r['local_outer']['calls']),[32,32,20])
        self.assertEqual(widths(r['local_inner']['calls']),[32,19,13,20])
        self.assertFalse(r['comparisons']['whole_fixed_vs_rechunk_identical_ordered_partition'])
        self.assertEqual(r['comparisons']['rechunk_extra_graph_calls_over_local_projection'],1)
        self.assertEqual(r['whole_rechunk']['predicted_padded_attention_work'],51*256+33*512)

    def test_every_small_dense_position_against_independent_token_sum(self):
        for padding in (8,16,32):
            for q in (1,2,4,8):
                for head in range(2*padding):
                    for append in (0,1,3,7,8,15,17,33):
                        with self.subTest(padding=padding,q=q,head=head,append=append):
                            r=schedule(head,append,q,padding,capacity=128)
                            expected=sum(((head+i)//padding+1)*padding for i in range(append))
                            for strategy in ('whole_fixed','whole_rechunk','local_inner'):
                                calls=r[strategy]['calls']
                                self.assertEqual(sum(x['width']for x in calls),append)
                                positions=[p for x in calls for p in range(x['position'],x['position']+x['width'])]
                                self.assertEqual(positions,list(range(head,head+append)))
                                self.assertEqual(r[strategy]['predicted_padded_attention_work'],expected)
                                for x in calls:
                                    self.assertEqual(x['position']//padding,(x['position']+x['width']-1)//padding)
                            self.assertLessEqual(r['whole_rechunk']['call_count'],(append+q-1)//q+1)
                            self.assertEqual(r['local_outer']['projection_call_count'],(append+q-1)//q)

    def test_initial_prefill_coalesces_when_q_divides_padding(self):
        for append in (1,31,32,255,256,257,1024,4096):
            r=schedule(0,append)
            self.assertTrue(r['comparisons']['whole_rechunk_vs_local_outer_identical_ordered_partition'])
            self.assertTrue(r['comparisons']['whole_fixed_vs_rechunk_identical_ordered_partition'])

    def test_exact_boundary_tail_and_empty_append(self):
        r=schedule(255,2)
        self.assertEqual(widths(r['whole_rechunk']['calls']),[1,1])
        self.assertEqual([x['predicted_attention_extent']for x in r['local_inner']['calls']],[256,512])
        self.assertEqual(r['local_outer']['split_outer_calls'],1)
        self.assertEqual(widths(schedule(256,33)['whole_rechunk']['calls']),[32,1])
        z=schedule(4096,0)
        self.assertEqual(z['whole_rechunk']['call_count'],0)
        self.assertEqual(z['whole_rechunk']['predicted_padded_attention_work'],0)

    def test_no_general_divisibility_claim(self):
        r=schedule(3,35,q=3,padding=8,capacity=64)
        self.assertFalse(r['whole_rechunk']['divisible_padding_bound_applicable'])
        self.assertIsNone(r['whole_rechunk']['divisible_padding_call_bound'])
        self.assertEqual(r['whole_rechunk']['token_rows'],35)

    def test_capacity_reject_is_retained_and_not_zero_work(self):
        r=schedule(4095,2)
        self.assertEqual(r['status'],'UNSUPPORTED_CAPACITY')
        self.assertFalse(r['capacity_admitted'])
        self.assertTrue(r['not_dropped_from_denominator'])
        for key in ('whole_fixed','whole_rechunk','local_outer','local_inner','comparisons'):
            self.assertIsNone(r[key])
        self.assertEqual(schedule(4095,1)['whole_rechunk']['call_count'],1)

    def test_strict_geometry_and_capacity_metadata(self):
        for args in [dict(head=True,append=1),dict(head=0,append=-1),dict(head=0,append=1,q=0),
                     dict(head=0,append=1,padding=0),dict(head=0,append=1,capacity=True),
                     dict(head=0,append=1,capacity=4095),dict(head=0.0,append=1)]:
            with self.subTest(args=args),self.assertRaises(ValueError):schedule(**args)

    def test_prediction_not_observation_or_speed(self):
        r=schedule(205,84)
        self.assertFalse(r['head_observed'])
        self.assertIsNone(r['native_head'])
        self.assertEqual(r['native_head_status'],'NOT_OBSERVED_ZERO_FORWARD')
        self.assertTrue(r['not_performance_or_numerical_evidence'])
        self.assertEqual(r['profile_status'],'PROSPECTIVE_NOT_NATIVE_QUALIFIED')


if __name__=='__main__':unittest.main()
