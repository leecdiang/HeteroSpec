"""Keep diagnostic state snapshots alive across fresh-context teardown."""
def once(s,a,b):
    if s.count(a)!=1:raise ValueError('fresh state lifetime anchor drift')
    return s.replace(a,b,1)

def fix(source):
    begin='    if(capture){\n        auto state_record=[&](Context* x,const char* role){'
    end='        state_record(target,"target");state_record(draft,"draft");\n    }'
    if source.count(begin)!=1 or source.count(end)!=1:raise ValueError('state writer anchor drift')
    start=source.index(begin);stop=source.index(end,start)+len(end);old=source[start:stop]
    # Capture native bytes while Context is live. Disk I/O remains after teardown
    # and outside the service clock; diagnostic serialization is also subtracted.
    capture='''    std::vector<uint8_t> target_snapshot,draft_snapshot;
    double state_capture_seconds=0;
    if(capture){
        const auto capture_start=Clock::now();
        auto snapshot=[&](Context* x,std::vector<uint8_t>& bytes){
            if(!x)return;
            const auto n=llama_state_seq_get_size(x->c,0);bytes.resize(n);
            need(llama_state_seq_get_data(x->c,bytes.data(),n,0)==n,"state serialization size");
        };
        snapshot(target,target_snapshot);snapshot(draft,draft_snapshot);
        state_capture_seconds=since(capture_start);
    }
'''
    writer='''    if(capture){
        auto state_record=[&](const std::vector<uint8_t>& bytes,const char* role){
            if(bytes.empty())return;
            auto file=dir/(std::string(role)+"_final.state");std::ofstream out(file,std::ios::binary);
            out.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());need(bool(out),"state write");out.close();
            r[std::string(role)+"_state"]={{"bytes",bytes.size()},{"sha256",hash_file(file)}};
        };
        state_record(target_snapshot,"target");state_record(draft_snapshot,"draft");
    }'''
    changed=once(source,old,writer)
    changed=once(changed,'    auto teardown=Clock::now();fresh.draft.reset();fresh.target.reset();hs_scope::active=false;',capture+'    auto teardown=Clock::now();fresh.draft.reset();fresh.target.reset();hs_scope::active=false;')
    changed=once(changed,'r["service_seconds"]=since(start);','r["service_seconds"]=since(start)-state_capture_seconds;')
    # The complete natural decoding/acceptance code through the metadata copy
    # preceding teardown must remain byte-identical.
    if source.split('    auto teardown=')[0]!=changed.split('    std::vector<uint8_t> target_snapshot')[0]:raise ValueError('natural request changed')
    after=changed.split('fresh.target.reset();',1)[1].split('int main(',1)[0]
    if 'target->' in after or 'draft->' in after or 'x->c' in after:raise ValueError('context read after teardown')
    return changed
