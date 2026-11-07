"""Bounded reads of top-level fields from native dump(2) JSON receipts.

Large saved geometry remains intact. Never materialize it to read model/module
metadata; this runs outside native service and changes no candidate execution.
"""
import json,mmap
from pathlib import Path

def fields(path,keys):
    result={}
    with Path(path).open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as data:
        for key in keys:
            marker=b'\n  '+json.dumps(key).encode()+b': '
            start=data.find(marker)
            if start<0:continue
            assert data.find(marker,start+1)<0,'duplicate top-level metadata field'
            start+=len(marker);width=4096
            while True:
                try:result[key]=json.JSONDecoder().raw_decode(data[start:start+width].decode('utf8'))[0];break
                except (json.JSONDecodeError,UnicodeDecodeError):
                    assert start+width<len(data),'invalid native top-level field'
                    width*=2;assert width<=64*1024**2,'unexpectedly large metadata field'
    return result
