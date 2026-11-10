"""Actual free VRAM must govern admission, including driver reserved memory."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from host import resource


class Resource(unittest.TestCase):
    def test_reserved_memory_is_not_free(self):
        with tempfile.TemporaryDirectory()as directory:
            config=dict(gpu_uuid='SYNTHETIC_GPU',gpu_reserve_bytes=1024**3,ram_reserve_bytes=1,
                output_root=directory,disk_required_free_bytes=1,max_idle_gpu_memory_bytes=32*1024**3)
            class Reply:
                def __init__(self,text):self.stdout=text
            def query(argv,**kw):
                if any(x.startswith('--query-gpu=')for x in argv):
                    # total-used=2048MiB, actual free=512MiB: must reject.
                    return Reply('SYNTHETIC_GPU,24564,22516,0,40,1000,100,512\n')
                return Reply('')
            with patch('host.subprocess.run',side_effect=query):
                with self.assertRaisesRegex(ValueError,'Actual NVML free-memory'):resource(config)


if __name__=='__main__':unittest.main()
