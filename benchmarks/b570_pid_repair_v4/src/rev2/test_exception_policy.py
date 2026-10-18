import unittest
from exception_policy import ExceptionPolicy,CONTINUE,NOT_HANDLED,BREAKPOINT
class Tests(unittest.TestCase):
    def test_loader_once(self):
        p=ExceptionPolicy();p.created((7,'1'));self.assertEqual(p.decide((7,'1'),BREAKPOINT,1),CONTINUE);self.assertEqual(p.decide((7,'1'),BREAKPOINT,1),NOT_HANDLED)
    def test_second_chance_never_swallowed(self):
        p=ExceptionPolicy();p.created((7,'1'));self.assertEqual(p.decide((7,'1'),BREAKPOINT,0),NOT_HANDLED)
    def test_single_step_never_swallowed(self):
        p=ExceptionPolicy();p.created((7,'1'));self.assertEqual(p.decide((7,'1'),0x80000004,1),NOT_HANDLED)
    def test_unknown_never_swallowed(self):self.assertEqual(ExceptionPolicy().decide(None,BREAKPOINT,1),NOT_HANDLED)
    def test_reused_pid_new_loader(self):
        p=ExceptionPolicy()
        for created in ['1','2']:
            p.created((7,created));self.assertEqual(p.decide((7,created),BREAKPOINT,1),CONTINUE)
    def test_access_violation_passed(self):
        p=ExceptionPolicy();p.created((7,'1'));self.assertEqual(p.decide((7,'1'),0xc0000005,1),NOT_HANDLED)
if __name__=='__main__':unittest.main()
