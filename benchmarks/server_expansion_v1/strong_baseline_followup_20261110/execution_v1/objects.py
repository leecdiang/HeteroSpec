"""Identify every ar member occurrence, including legitimate repeated basenames."""
import hashlib
from pathlib import Path
from support import need


def archive_members(path):
    data=Path(path).read_bytes();need(data[:8]==b'!<arch>\n','Unsupported/thin archive')
    at=8;table=b'';result=[]
    while at<len(data):
        h=data[at:at+60];need(len(h)==60 and h[58:60]==b'`\n','Invalid ar header')
        size=int(h[48:58]);body=data[at+60:at+60+size]
        need(len(body)==size,'Truncated ar member');name=h[:16].decode('ascii').strip()
        if name=='//':table=body
        elif name not in ('/','/SYM64/'):
            if name.startswith('#1/'):
                n=int(name[3:]);need(0<n<=len(body),'BSD member filename')
                name=body[:n].rstrip(b'\0').decode('utf-8');body=body[n:]
            elif name.startswith('/'):
                offset=int(name[1:]);need(0<=offset<len(table),'GNU name offset')
                end=table.find(b'/\n',offset);need(end>=offset,'GNU member name termination')
                name=table[offset:end].decode('utf-8')
            else:name=name.removesuffix('/')
            result.append(dict(ordinal=len(result),member=name,bytes=len(body),
                               sha256=hashlib.sha256(body).hexdigest()))
        at+=60+size+(size%2)
    need(at==len(data),'Archive trailing/truncated padding')
    return result
