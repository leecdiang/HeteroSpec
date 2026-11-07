"""General pre-freeze service-accounting correction, retaining epoch02 source."""
from host import *
def main():
    s=(HERE/'worker.cpp').read_text()
    s=s.replace('t=Clock::now();check(llama_state_seq_set_data(c,state.data(),state.size(),0)==state.size(),"restore");', '''std::map<std::vector<int>,std::vector<uint8_t>> cache;
    std::vector<int> key(ids.begin(),ids.begin()+head);cache.emplace(key,state);
    t=Clock::now();std::vector<int> request_key(ids.begin(),ids.begin()+head);
    auto entry=cache.find(request_key);check(entry!=cache.end(),"prefix lookup");
    const auto & selected_state=entry->second;
    check(llama_state_seq_set_data(c,selected_state.data(),selected_state.size(),0)==selected_state.size(),"restore");''')
    s=s.replace('llama_synchronize(c);double service=seconds(t);', 'llama_synchronize(c);auto committed_output=output;int committed_position=llama_memory_seq_pos_max(llama_get_memory(c),0);double service=seconds(t);')
    s=s.replace('auto final=snapshot(c);if(capture)raw(dir/"final.bin",final.data(),final.size());','if(capture){auto final=snapshot(c);raw(dir/"final.bin",final.data(),final.size());}check(state==selected_state,"retained prefix mutation");')
    s=s.replace('{"output",output}', '{"output",committed_output}')
    s=s.replace('{"final_position",llama_memory_seq_pos_max(llama_get_memory(c),0)}','{"final_position",committed_position}')
    s=s.replace('#undef main','#undef main\n#include <map>')
    s=s.replace('double producer=seconds(t);llama_memory_clear(llama_get_memory(c),true);','double producer=seconds(t);')
    s=s.replace('t=Clock::now();std::vector<int> request_key','t=Clock::now();llama_memory_clear(llama_get_memory(c),true);std::vector<int> request_key')
    # File-backed replay materializes the host snapshot on every actual request.
    # Charge that I/O and the index construction, not just GPU state import.
    s=s.replace('std::vector<uint8_t>state;', 'auto service_start=t;std::vector<uint8_t>state;')
    s=s.replace('double producer=seconds(t);', 'double producer=seconds(t);if(!u.contains("state")&&head>0)service_start=Clock::now();')
    s=s.replace('llama_memory_clear(llama_get_memory(c),true);hs_scope::active=false;hsc::begin("baseline",32);auto t=Clock::now();','auto t=Clock::now();llama_memory_clear(llama_get_memory(c),true);hs_scope::active=false;hsc::begin("baseline",32);')
    s=s.replace('t=Clock::now();llama_memory_clear(llama_get_memory(c),true);std::vector<int> request_key', 't=service_start;llama_memory_clear(llama_get_memory(c),true);std::vector<int> request_key')
    s=s.replace('arm=="WB-rechunk","arm"','arm=="WB-rechunk"||arm=="AUTO","arm"')
    s=s.replace('double import_s=seconds(t);json calls=json::array();','double import_s=seconds(t);if(arm=="AUTO"){arm=u.at("policy").at(u.at("selection_bin").get<std::string>());check(arm=="QB"||arm=="WB-cut"||arm=="WB-rechunk","frozen policy arm");}json calls=json::array();')
    (HERE/'worker_service.cpp').write_text(s)
    build('candidate07',source='worker_service.cpp')
if __name__=='__main__':main()
