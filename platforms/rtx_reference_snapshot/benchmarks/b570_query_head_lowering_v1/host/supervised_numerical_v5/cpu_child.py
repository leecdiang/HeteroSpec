"""Explicit CPU-only fault-injection child, never a native/GPU evidence source."""
import json
import pathlib
import sys
import time
from legacy import load,modules

cfg=load(sys.argv[1]);folder=pathlib.Path(sys.argv[1]).parent
def emit(event,**fields):
    with (folder/'raw.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(dict(event=event,origin='CPU_TEST_NOT_GPU',**fields))+'\n');f.flush()
emit('CPU_START',modules=modules())
if cfg.get('exit_early'):raise SystemExit(7)
emit('AWAIT_RUNTIME_GATE',modules=[])
if cfg.get('exit_before_GO'):raise SystemExit(0)
if cfg.get('exit_before_GO_when'):
    while not pathlib.Path(cfg['exit_before_GO_when']).exists():time.sleep(.005)
    emit('CLOSE',modules=modules());raise SystemExit(0)
gate=sys.stdin.readline().strip()
if gate!='GO':raise SystemExit(8)
(folder/'EXECUTED').write_text('Only written after actual GO')
emit('CPU_EXECUTION')
release=pathlib.Path(cfg['release'])
while not release.exists():time.sleep(.005)
if cfg.get('exit_code'):raise SystemExit(cfg['exit_code'])
if not cfg.get('missing_output'):(folder/'output.bin').write_bytes(b'x' if cfg.get('truncated') else b'CPU-ONLY-EXPECTED-OUTPUT')
emit('CLOSE',modules=modules())
