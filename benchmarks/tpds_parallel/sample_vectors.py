"""Ship the first row, the first new-extent row, and the last row of the 8B crossing."""
import io
import json
from zipfile import ZipFile,ZIP_DEFLATED,ZipInfo
from collect import E,ROOT,sha
def main():
    sample=ROOT/"probes/eight"
    rows={}
    def add(archive,name,data):
        item=ZipInfo(name,date_time=(2026,11,3,0,0,0))
        archive.writestr(item,data,compress_type=ZIP_DEFLATED,compresslevel=6)
    with ZipFile(E/"eight-crossing-vectors.zip","w") as archive:
        seen=set()
        for arm in ["oracle","S1","PQ-ext","QB-local","WB-cut","native"]:
            rows[arm]={}
            for r in [0,3,31]:
                p=sample/f"253-32-{arm}/row/{r}.f32";digest=sha(p)
                rows[arm][str(r)]=digest
                if digest not in seen:add(archive,f"{digest}.f32",p.read_bytes());seen.add(digest)
        add(archive,"rows.json",json.dumps(rows,indent=2).encode())
if __name__=="__main__":main()

