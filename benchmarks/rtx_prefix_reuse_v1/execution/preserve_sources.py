from host import *
def main():
    s=(HERE/'worker_service.cpp').read_text()
    s6=s.replace('if(!u.contains("state")&&head>0)','if(!u.contains("state"))').replace('auto t=Clock::now();llama_memory_clear(llama_get_memory(c),true);hs_scope::active=false;hsc::begin("baseline",32);','llama_memory_clear(llama_get_memory(c),true);hs_scope::active=false;hsc::begin("baseline",32);auto t=Clock::now();')
    s5=s6.replace('auto service_start=t;std::vector<uint8_t>state;','std::vector<uint8_t>state;').replace('if(!u.contains("state"))service_start=Clock::now();','').replace('t=service_start;llama_memory_clear','t=Clock::now();llama_memory_clear')
    s4=s5.replace('double producer=seconds(t);','double producer=seconds(t);llama_memory_clear(llama_get_memory(c),true);').replace('t=Clock::now();llama_memory_clear(llama_get_memory(c),true);std::vector<int> request_key','t=Clock::now();std::vector<int> request_key')
    s3=s4.replace('arm=="WB-rechunk"||arm=="AUTO","arm"','arm=="WB-rechunk","arm"').replace('if(arm=="AUTO"){arm=u.at("policy").at(u.at("selection_bin").get<std::string>());check(arm=="QB"||arm=="WB-cut"||arm=="WB-rechunk","frozen policy arm");}','')
    for n,body in [(3,s3),(4,s4),(5,s5),(6,s6)]:
        expected=read(ROOT/f'candidate{n:02}/binding.json')['source'];b=body.replace(chr(10),chr(13)+chr(10)).encode();assert hashlib.sha256(b).hexdigest()==expected,(n,expected,hashlib.sha256(b).hexdigest())
        (ROOT/f'candidate{n:02}/compiled-source.cpp').write_bytes(b)
    for label in ('candidate01','candidate02','oracle02'):
        body=(HERE/'worker.cpp').read_bytes()
        if sha(HERE/'worker.cpp')==read(ROOT/label/'binding.json')['source']:(ROOT/label/'compiled-source.cpp').write_bytes(body)
    original=(HERE/'worker.cpp').read_text();a=original.index('static void raw(');b=original.index('int main(int argc',a)
    first=original[:a]+original[b:]
    first=first.replace('    if(mode=="requests"){for(auto&u:j.at("units"))request(m.get(),ctx.get(),u,out);return 0;}\n    throw std::runtime_error("unsupported mode");','    throw std::runtime_error("mode not yet implemented");')
    expected=read(ROOT/'candidate01/binding.json')['source'];assert hashlib.sha256(first.encode()).hexdigest()==expected
    (ROOT/'candidate01/compiled-source.cpp').write_bytes(first.encode())
    print('epochs03-06 recovered and authenticated against original build hashes')
if __name__=='__main__':main()
