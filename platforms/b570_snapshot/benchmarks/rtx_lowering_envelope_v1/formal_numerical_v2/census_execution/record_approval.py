"""CPU/transport-only receipt of the actual census-only human message."""
import datetime, hashlib, json, subprocess, urllib.request
from pathlib import Path

D = Path(__file__).resolve().parent
V = D.parent
def sha(data): return hashlib.sha256(data).hexdigest()
def save(name, value):
    with (D / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=V).decode().strip()
assert head == '05912d0b10191b861af5cdb85333f1d963dba294'
assert not Path('D:/hs113-formal-numerical-v2').exists()
assert not (V/'execution_ledger').exists()
f0 = (V/'F0.json').read_bytes()
assert sha(f0) == '73ef7106240be73ab914e4c6a36064a0d1fd6d41ce5d9c38bf65f38e8331f080'
assert (V/'REMOTE_F0_BYTES.json').read_bytes() == f0
token = subprocess.check_output(['gh','auth','token']).decode().strip()
url = 'https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/F0.json?ref='+head
req = urllib.request.Request(url, headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-census-preflight'})
with urllib.request.urlopen(req,timeout=45) as r:
    assert r.status == 200; remote = r.read()
assert remote == f0
save('REMOTE_PREFLIGHT.json', dict(commit=head, F0_sha256=sha(remote),bytes=len(remote),authenticated_remote_bytes=True, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),GPU_calls=0))
message = (D/'AUTHOR_MESSAGE.txt').read_text(encoding='utf-8').removesuffix('\n')
save('AUTHOR_APPROVAL.json', dict(stage='FORMAL_V2_CENSUS_ONLY',run_id='pr113-formal-numerical-v2',F0_sha256=sha(f0),author_message=message,author_message_sha256=sha(message.encode('utf-8')),reviewed_commit=head,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),time_semantics='Actual receipt recording time; no claim of earlier approval.',numerical_authorization='NOT_GRANTED'))
print('Recorded census-only approval; authenticated reviewed remote F0 equals frozen local bytes. No GPU activity.')
