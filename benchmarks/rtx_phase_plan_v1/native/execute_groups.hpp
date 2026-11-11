#pragma once
#include "phase_plan.hpp"
namespace refplan {
// The native adapter provides:
//   preflight(rows, groups) -- all validation before the first mutating decode
//   decode(group, original_rows) -- same context, exact positions/output masks
//   output(original_row, group) -- returns copied bytes for an already requested row
//   poison() -- prevent this context from re-entering service after any failure
// No automatic fallback after mutation. No sampling, KV export or state restore.
template<class Backend>
OutputRows execute_groups(Backend& backend,const std::vector<Row>& rows,
                          size_t max_call,size_t bytes_per_row) {
    auto groups=plan(rows,max_call);
    backend.preflight(rows,groups);
    OutputRows outputs(rows,bytes_per_row);
    try {
        for(const auto& g:groups) {
            backend.decode(g,rows);
            for(size_t i=g.begin;i<g.begin+g.count;++i) if(rows[i].requested_output) {
                auto bytes=backend.output(i,g);
                outputs.put(i,bytes.data(),bytes.size());
            }
        }
        require(outputs.complete(),"incomplete output map");
    } catch(...) {backend.poison();throw;}
    return outputs;
}
} // namespace refplan
