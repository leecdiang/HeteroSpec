"""Zero-GPU source endpoint regression; artificial bytes are not observations."""
import unittest
from build_service import patch_worker


class Clock(unittest.TestCase):
    def test_complete_reset_and_final_fence_are_inside_endpoint(self):
        source='''static double since(Clock::time_point t){}
Pair fresh;Context*target=nullptr,*draft=nullptr;
target->reset(capture,dir/"target");
execute_all_model_work();
llama_synchronize(target->c);if(draft)llama_synchronize(draft->c);
    r["ids"]=ids;serialize_receipt();'''
        patched=patch_worker(source)
        self.assertLess(patched.index('sb3_start=sb3_ns()'),patched.index('target->reset('))
        self.assertLess(patched.index('target->reset('),patched.index('sb3_reset_end=sb3_ns()'))
        self.assertLess(patched.index('llama_synchronize(target->c)'),patched.index('const int64_t sb3_end=sb3_ns()'))
        self.assertLess(patched.index('const int64_t sb3_end=sb3_ns()'),patched.index('serialize_receipt()'))
        self.assertIn('CLOCK_MONOTONIC',patched)
        self.assertIn('empty active state after complete reset',patched)

    def test_changed_or_duplicated_anchor_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'unique source anchor'):patch_worker('different source')


if __name__=='__main__':unittest.main()
