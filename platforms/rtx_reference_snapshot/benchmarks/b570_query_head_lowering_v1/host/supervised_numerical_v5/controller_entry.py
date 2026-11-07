"""Owned/gated entry for the single production controller; no GPU before gate."""
import sys
sys.dont_write_bytecode=True
gate=sys.stdin.buffer.readline()
if gate not in (b'LAUNCH_GO\r\n',b'LAUNCH_GO\n'):
    raise SystemExit('owned launcher gate required')
import execute
execute.main()
