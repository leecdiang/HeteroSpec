"""Actual saved-state fixture: open writer, closed complete, and failed partial."""
from smol_state import *
from smol_stream import StateStream,complete_closed

def test():
 folder=SROOT/'stream-check01';folder.mkdir();states=folder/'0.json.states';states.mkdir()
 raw=load(SROOT/'observer-R-0-capture.json.states/0.bin');path=states/'0.bin'
 stream=StateStream(folder,pack)
 with path.open('wb') as f:
  f.write(raw[:len(raw)//2]);f.flush();time.sleep(.2);assert not complete_closed(path) and stream.count==0
  f.write(raw[len(raw)//2:]);f.flush();time.sleep(.2);assert not complete_closed(path) and stream.count==0
 deadline=time.monotonic()+20
 while path.exists() and time.monotonic()<deadline:time.sleep(.05)
 partial=states/'1.bin';partial.write_bytes(raw[:len(raw)//2]);time.sleep(.2)
 assert not complete_closed(partial)
 stream.finish();assert not path.exists() and stream.count==1 and partial.exists()
 assert load(path)==raw
 write(folder/'PROOF.json',dict(status='ACTUAL_PAYLOAD_STREAM_STORAGE_PASS',source_raw_sha256=hashlib.sha256(raw).hexdigest(),source_bytes=len(raw),open_writers_never_packed=True,complete_closed_payload_reconstructs_bit_exact=True,failed_partial_raw_unchanged=partial.read_bytes()==raw[:len(raw)//2],models_run=0))

if __name__=='__main__':test()
