import unittest,ctypes
from process_registry import Registry

class API:
    def __init__(self):self.rows={};self.disposed=[]
    def add(self,h,created,code=0):self.rows[h]=dict(created_filetime=str(created),exit_filetime=str(created+10000000),code=code)
    def retain(self,h):return h
    def identity(self,h):return dict(created_filetime=self.rows[h]['created_filetime'])
    def os_times(self,h):return {k:v for k,v in self.rows[h].items() if k!='code'}
    def wait_handle(self,h,ms):return 0
    def exit_code(self,h):return self.rows[h]['code']
    def close(self,h):self.disposed.append(h);return True
    def checked(self,x,msg):
        if not x:raise ValueError(msg)
class Journal:
    def __init__(self):self.rows=[]
    def emit(self,event,**kw):self.rows.append(dict(event=event,**kw))
class Tests(unittest.TestCase):
    def setUp(self):self.a=API();self.j=Journal();self.r=Registry(self.a,self.j)
    def create(self,h,pid=7,created=None):
        self.a.add(h,created or h*100000000);return self.r.create(pid,h)
    def end(self,pid=7):self.r.complete_exit(self.r.exit_observed(pid,0),0)
    def test_reuse_after_close(self):
        x=self.create(1);self.end();y=self.create(2);self.end()
        self.assertNotEqual(x,y);self.assertEqual(len(self.r.closed),2);self.assertTrue(self.r.complete())
    def test_cleanup_reuse(self):
        self.create(1);self.r.finish_signalled();self.create(2);self.r.finish_signalled()
        self.assertEqual(len(self.r.closed),2);self.assertTrue(self.r.complete())
    def test_active_collision_evidence(self):
        self.create(1)
        with self.assertRaisesRegex(ValueError,'DUPLICATE_ACTIVE'):self.create(2)
        raw=self.j.rows[-1];self.assertEqual(raw['created_filetime'],'200000000');self.assertEqual(raw['active_identity'],[7,'100000000'])
        self.r.finish_signalled();self.assertFalse(self.r.complete());self.assertFalse(self.r.orphans)
    def test_replayed_identity(self):
        self.create(1);self.end()
        with self.assertRaisesRegex(ValueError,'DUPLICATE_PROCESS'):self.create(2,created=100000000)
        self.r.finish_signalled();self.assertFalse(self.r.complete())
    def test_unknown_exit(self):
        self.create(1);self.end()
        with self.assertRaisesRegex(ValueError,'UNMATCHED_EXIT'):self.r.exit_observed(7,0)
        self.assertIsNone(self.j.rows[-1]['created_filetime']);self.assertFalse(self.r.complete())
    def test_creation_mismatch(self):
        k=self.create(1);self.a.rows[1]['created_filetime']='3'
        with self.assertRaisesRegex(ValueError,'EXIT_IDENTITY'):self.r.complete_exit(k,0)
        self.assertFalse(self.r.complete())
    def test_exit_code_mismatch(self):
        k=self.create(1)
        with self.assertRaisesRegex(ValueError,'EXIT_CODE'):self.r.complete_exit(k,1)
        self.assertFalse(self.r.complete())
    def test_root_pid_reused_is_descendant(self):
        self.r.root_key=(7,'100000000');self.create(1);self.end();self.create(2);self.end()
        self.assertEqual([x['role'] for x in self.j.rows if x['event']=='PROCESS_CREATE'],['root','descendant'])
    def test_image_closed_on_rejection(self):
        self.create(1);self.a.add(2,200000000)
        with self.assertRaises(ValueError):self.r.create(7,2,999)
        self.assertIn(999,self.a.disposed)
    def test_raw_pid_before_identity_failure(self):
        with self.assertRaises(KeyError):self.r.create(7,99)
        self.assertEqual(self.j.rows[0],dict(event='PROCESS_CREATE_RECEIVED',pid=7));self.assertFalse(self.r.complete())
    def test_600_reused_identities(self):
        for h in range(1,601):self.create(h,pid=1+h%3);self.end(pid=1+h%3)
        self.assertEqual(len(self.r.closed),600);self.assertEqual(sum(x['lifetime_seconds'] for x in self.r.closed.values()),600);self.assertTrue(self.r.complete())
    def test_actual_ctypes_handle(self):
        self.a.add(1,100000000)
        original_identity=self.a.identity;original_times=self.a.os_times;original_code=self.a.exit_code
        self.a.retain=lambda h:ctypes.c_void_p(h)
        self.a.identity=lambda h:original_identity(h.value)
        self.a.os_times=lambda h:original_times(h.value)
        self.a.exit_code=lambda h:original_code(h.value)
        self.r.create(7,1);self.end();self.assertTrue(self.r.complete())
    def test_rejected_ctypes_handle_cleanup(self):
        self.a.add(1,100000000);self.a.add(2,200000000)
        original_identity=self.a.identity;original_times=self.a.os_times;original_code=self.a.exit_code
        self.a.retain=lambda h:ctypes.c_void_p(h)
        self.a.identity=lambda h:original_identity(h.value)
        self.a.os_times=lambda h:original_times(h.value)
        self.a.exit_code=lambda h:original_code(h.value)
        self.r.create(7,1)
        with self.assertRaisesRegex(ValueError,'DUPLICATE_ACTIVE'):self.r.create(7,2)
        self.r.finish_signalled();self.assertFalse(self.r.orphans);self.assertFalse(self.r.complete())
    def test_disposal_not_exit(self):
        self.create(1);self.r.release_remaining();self.assertFalse(self.r.complete());self.assertFalse(self.r.closed)
if __name__=='__main__':unittest.main()
