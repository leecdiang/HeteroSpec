import unittest
from diagnostic_costs import decompose_capture,reader


class CapturePartition(unittest.TestCase):
    def test_state_sync_partition_and_no_performance_admission(self):
        timeline={"state_capture_enabled":True,"clock":"steady_clock_ns","service":[0,100],"spans":[
            {"category":"verify","begin":0,"end":80},
            {"category":"state","begin":40,"end":80},
            {"category":"sync","begin":40,"end":50}]}
        result=decompose_capture(timeline,request_id="constructed",arm="A",source_sha256="a"*64,input_sha256="b"*64)
        self.assertEqual(result["exclusive_ns"],{"state":30,"sync":10,"unattributed":20,"verify":40})
        self.assertIs(result["performance_admitted"],False)
        self.assertEqual(result["endpoint_qualification"],"UNVERIFIED")

    def test_clean_record_cannot_use_capture_adapter(self):
        with self.assertRaises(reader.CostError):
            decompose_capture({"state_capture_enabled":False},request_id="x",arm="A",source_sha256="a"*64,input_sha256="b"*64)

    def test_crossing_state_intervals_refuse_partition(self):
        timeline={"state_capture_enabled":True,"clock":"steady_clock_ns","service":[0,100],"spans":[
            {"category":"verify","begin":0,"end":70},
            {"category":"state","begin":40,"end":80}]}
        with self.assertRaisesRegex(reader.CostError,"crossing"):
            decompose_capture(timeline,request_id="x",arm="A",source_sha256="a"*64,input_sha256="b"*64)


if __name__=="__main__":
    unittest.main()
