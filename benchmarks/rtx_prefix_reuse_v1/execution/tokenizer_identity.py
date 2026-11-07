from calibrate import *
def main():
    peer=read(ROOT/'B570_TOKENIZER_AND_CENSUS.json');base=Path('E:/rtx170/candidate01/source/src');result={}
    for role,name in [('tokenizer','llama-vocab.cpp'),('renderer','llama-chat.cpp')]:
        p=base/name;b=p.read_bytes();h=hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest();assert h==peer[role+'_source'];result[role]=dict(raw_sha256=sha(p),normalized_LF_sha256=h,peer_source_sha256=peer[role+'_source'],only_line_ending_difference=True)
    model=sha(MODEL);assert model==read(ROOT/'B570_HOST_ADMISSION.json')['model']['sha256']
    identity=dict(model_sha256=model,native_source_commit='0cae43063cf15170e91a2ff4d034da0ecef4a1b2',add_special=True,parse_special=True,renderer=peer['tokenizer']['renderer'])
    assert study.digest(identity)==peer['tokenizer_sha256']
    put(ROOT/'TOKENIZER_IDENTITY_MATCH.json',dict(native_identity=identity,tokenizer_sha256=study.digest(identity),source_files=result,template_sha256=hashlib.sha256(read(ROOT/'tokenize01/template.json')['template'].encode()).hexdigest(),selected_cached_and_request_token_arrays_matched=44))
    print('native tokenizer identity matches peer',study.digest(identity))
if __name__=='__main__':main()
