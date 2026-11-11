"""Diagnostic-only Vulkan dispatch observation; no arithmetic or routing edits."""
from pathlib import Path
import argparse,hashlib

def apply(source):
    p=Path(source)/'ggml/src/ggml-vulkan/ggml-vulkan.cpp';s=p.read_text()
    marker='    subctx->s->buffer->buf.dispatch(wg0, wg1, wg2);'
    assert s.count(marker)==1
    observer=r'''
    // Diagnostic binary only: the dispatch immediately below remains unchanged.
    std::cerr << "HS_DISPATCH pipeline=" << pipeline->name
              << " wg=" << wg0 << "," << wg1 << "," << wg2 << " buffers=";
    for (const auto & b : descriptor_buffer_infos) {
        std::cerr << b.offset << ":" << b.range << ";";
    }
    std::cerr << " pc=";
    const auto * hs_pc = reinterpret_cast<const unsigned char *>(push_constant_data(push_constants));
    const char * hs_hex = "0123456789abcdef";
    for (size_t i = 0; i < push_constant_size(push_constants); ++i) {
        std::cerr << hs_hex[hs_pc[i] >> 4] << hs_hex[hs_pc[i] & 15];
    }
    std::cerr << "\n";
'''
    s=s.replace(marker,observer+'\n'+marker);p.write_text(s)
    print(hashlib.sha256(p.read_bytes()).hexdigest())

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--source',required=True);apply(a.parse_args().source)
