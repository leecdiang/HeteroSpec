#!/usr/bin/env python3
"""State-machine checks needed before wiring the M4 backend."""

import unittest

from runtime_policy import Guard


class GuardTests(unittest.TestCase):
    def test_early_continue_then_late_fallback_and_no_switch_back(self):
        guard = Guard(2, 0.05, 100)
        self.assertIsNone(guard.observe_round(2, 120))
        self.assertEqual(guard.observe_round(4, 320).action, "CONTINUE")
        self.assertEqual(guard.observe_round(5, 600).action, "FALLBACK")
        self.assertEqual(guard.state, "TARGET_ONLY")
        with self.assertRaises(RuntimeError):
            guard.observe_round(6, 610)

    def test_immediate_fallback_at_first_decision(self):
        guard = Guard(2, 0.0, 100)
        guard.observe_round(1, 80)
        self.assertEqual(guard.observe_round(2, 250).action, "FALLBACK")

    def test_zero_committed_progress_is_safe(self):
        guard = Guard(2, 0.0, 100)
        guard.observe_round(0, 10)
        decision = guard.observe_round(0, 20)
        self.assertIsNone(decision.realized_ns_per_token)
        self.assertEqual(decision.action, "FALLBACK")

    def test_exact_threshold_continues(self):
        guard = Guard(1, 0.1, 100)
        self.assertEqual(guard.observe_round(2, 180).action, "CONTINUE")


if __name__ == "__main__":
    unittest.main()
