#pragma once
#include <cstdint>
#include "loop4_marker.h"
#include <limits>
#include <stdexcept>
#include <array>
#include <cstddef>
namespace hs_loop4 {
constexpr int32_t marker=HS_LOOP4_MARKER;
struct Tile {
    uint64_t begin,width,input_byte_offset,output_float_offset,input_group_blocks,output_group_floats;
};
inline uint64_t checked_mul(uint64_t a,uint64_t b){
    if(b && a>std::numeric_limits<uint64_t>::max()/b)throw std::overflow_error("loop4 offset overflow");
    return a*b;
}
// Offsets refer to the already-quantized activation, not original F32 bytes.
struct Plan {
    std::array<Tile,8> tiles{};
    size_t count=0;
    const Tile * begin() const {return tiles.data();}
    const Tile * end() const {return tiles.data()+count;}
};
inline Plan plan(uint64_t columns,uint64_t input_column_blocks,
                              uint64_t output_column_floats,uint64_t quant_block_bytes){
    if(columns<5 || columns>32 || !input_column_blocks || !output_column_floats || !quant_block_bytes)
        throw std::invalid_argument("loop4 scope: q5..32, positive strides");
    const auto in_span=checked_mul(columns,input_column_blocks);
    const auto out_span=checked_mul(columns,output_column_floats);
    if(in_span>uint64_t(std::numeric_limits<int>::max()) || out_span>uint64_t(std::numeric_limits<int>::max()))
        throw std::overflow_error("native MMVQ int stride overflow");
    checked_mul(in_span,quant_block_bytes);checked_mul(out_span,sizeof(float));
    Plan result;
    for(uint64_t begin=0;begin<columns;begin+=4){
        auto width=columns-begin<4 ? columns-begin : 4;
        result.tiles[result.count++]={begin,width,checked_mul(checked_mul(begin,input_column_blocks),quant_block_bytes),
            checked_mul(begin,output_column_floats),checked_mul(width,input_column_blocks),checked_mul(width,output_column_floats)};
    }
    return result;
}
} // namespace hs_loop4
