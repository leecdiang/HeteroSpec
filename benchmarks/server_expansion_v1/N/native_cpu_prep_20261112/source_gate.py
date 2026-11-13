"""Read-only source identity gate. This program cannot authorize native work."""
import hashlib, json, sys
from pathlib import Path
FROZEN = {
 'reference_frontend': '111401574d53c534e3a39cac75785ae5ae5fa9a61b44fc7ada989a96305f4723',
 'reference_llama_header': '3d1b18eda626c1b9ecf5bda0798e65b974a8f70f30d56726610633a980cb4160',
 'producer_common_chat': 'abab0d03a111bd198693a518c7cdd07a33326a6a6685cc182a88d4fdae5f61dc',
 'strong_worker': '429ca63224bffdc62fff65cc0c4b4199ea0ae9677fa3b087d1bbbe1d01b12938',
 'strong_resident_context': '02b361035da2baa586e7c2192ca05a87036ef4336a478f954ee1a006fa6b8647',
}
def inspect(paths):
 out={}
 for role, expected in FROZEN.items():
  path=paths.get(role)
  if not path or not Path(path).is_file(): out[role]={'status':'MISSING','expected_sha256':expected};continue
  h=hashlib.sha256()
  with open(path,'rb') as f:
   for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
  actual=h.hexdigest()
  out[role]={'status':'MATCH' if actual==expected else 'IDENTITY_CONFLICT','expected_sha256':expected,'actual_sha256':actual}
 return {'sources':out,'gpu_admission':'DENIED','native_reference_qualified':False,
 'scope':'source identity only, never proof of arithmetic, native linkage, state writer, resources or execution permission'}
if __name__=='__main__':
 print(json.dumps(inspect(json.loads(Path(sys.argv[1]).read_text())),indent=2))
