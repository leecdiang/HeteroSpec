"""Retain calendar spans including outer CPU checks, archives and repair gaps."""
from native_adapter import ROOT,RUNS,put
from pathlib import Path
import sqlite3,datetime

def main():
    db=sqlite3.connect(ROOT/'ledger.sqlite');starts=dict(db.execute('select id,started from attempts'));db.close();rows=[]
    definitions=[
        ('D development and priming','bridge-old-r-01',max(RUNS.glob('priming-v3-*/exit.json'),key=lambda p:p.stat().st_mtime)),
        ('D frozen confirmation including independent references','D-main-original-0',RUNS/'D-main-s0-pair4/exit.json'),
        ('D actual-head causal diagnosis','D-boundary-diagnostic-v1',RUNS/'D-boundary-diagnostic-v1/exit.json'),
        ('O operator engineering and final full-runtime bridge','O-replay-v3-8B-original-clean',ROOT/'O-RUNTIME-BRIDGE.json'),
        ('O whole-model boundary qualification including loading failure','O-prefix-v4-8B',ROOT/'O-BOUNDARY-QUALIFICATION.json'),
        ('O natural-service qualification including CPU comparison, lossless archive, priming and storage repair','O-old-root0',ROOT/'O-SERVICE-QUALIFICATION.json'),
        ('O frozen confirmation including independent references, all warmups, post-service state checks and analysis','O-main-original-0',ROOT/'O-MAIN-ANALYSIS.json')]
    for name,start_id,end in definitions:
        begin=starts[start_id];finish=end.stat().st_mtime;assert finish>=begin
        rows.append(dict(stage=name,first_reserved_attempt=start_id,start_unix=begin,end_unix=finish,end_evidence=str(end),elapsed_calendar_s=finish-begin,start_utc=datetime.datetime.fromtimestamp(begin,datetime.timezone.utc).isoformat(),end_utc=datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat()))
    put(ROOT/'ELAPSED_STAGE_SPANS.json',dict(stages=rows,scope='Calendar spans derived from durable attempt start timestamps and final receipt filesystem timestamps on the original host. Include intervening CPU comparison, archival, engineering and agent pauses. Not active GPU time; overlapping spans must not be summed. Native process wall and service components are nested and remain separately recorded. No unmeasured gap is silently set to zero.'))

if __name__=='__main__':main()
