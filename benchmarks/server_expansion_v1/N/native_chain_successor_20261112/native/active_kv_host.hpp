#pragma once
// Pure host byte/layout helpers only: no llama, tensor, model or backend API.
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
namespace hs::n1chain::hostkv {
inline void require(bool x,const char *s){if(!x)throw std::runtime_error(s);}
inline std::size_t product(std::size_t a,std::size_t b){require(!b||a<=std::numeric_limits<std::size_t>::max()/b,"KV byte product overflow");return a*b;}
struct Layout{std::uint32_t capacity,heads,dimension;bool transposed;};
inline void validate_map(const std::vector<std::uint32_t>&physical_by_position,std::uint32_t capacity){std::vector<bool> seen(capacity,false);for(auto p:physical_by_position){require(p<capacity,"physical cell outside cache");require(!seen[p],"duplicate physical cell");seen[p]=true;}}
inline std::vector<std::uint8_t> canonical_f16(const std::vector<std::uint8_t>&storage,const Layout&l,const std::vector<std::uint32_t>&physical_by_position){
 require(l.capacity&&l.heads&&l.dimension,"empty physical KV layout");validate_map(physical_by_position,l.capacity);const auto width=product(l.heads,l.dimension);require(storage.size()==product(product(l.capacity,width),2),"physical F16 storage byte count");const auto head=physical_by_position.size();std::vector<std::uint8_t> out(product(product(head,width),2));
 for(std::size_t h=0;h<l.heads;++h)for(std::size_t p=0;p<head;++p)for(std::size_t d=0;d<l.dimension;++d){const auto j=h*l.dimension+d;const auto cell=physical_by_position[p];const auto source=(l.transposed?j*l.capacity+cell:cell*width+j)*2;const std::uint16_t bits=std::uint16_t(storage[source])|(std::uint16_t(storage[source+1])<<8);require((bits&0x7c00)!=0x7c00,"nonfinite active F16 value");const auto target=((h*head+p)*l.dimension+d)*2;out[target]=storage[source];out[target+1]=storage[source+1];}
 return out;
}
struct Range{std::uint32_t first,last;};
inline std::vector<Range> ranges_from_physical(const std::vector<std::uint32_t>&sorted){std::vector<Range> ranges;for(auto p:sorted){if(!ranges.empty()){require(p>=ranges.back().last,"physical cells not strictly sorted");if(p==ranges.back().last){++ranges.back().last;continue;}}ranges.push_back({p,p+1});}return ranges;}
struct Cursor{const std::vector<std::uint8_t>&bytes;std::size_t offset=0;
 std::uint32_t u32(){require(offset<=bytes.size()&&bytes.size()-offset>=4,"truncated KV scalar metadata");std::uint32_t v=0;for(int k=0;k<4;++k)v|=std::uint32_t(bytes[offset++])<<(8*k);return v;}
 std::uint64_t u64(){const auto lo=u32(),hi=u32();return std::uint64_t(lo)|(std::uint64_t(hi)<<32);}
 std::int32_t i32(){return static_cast<std::int32_t>(u32());}
};
inline void validate_state_header(Cursor&c,const std::vector<std::int32_t>&positions_in_physical_order,std::uint32_t layers){require(c.u32()==1,"unsupported KV stream count");require(c.u32()==positions_in_physical_order.size(),"native active cell count mismatch");for(auto p:positions_in_physical_order){require(c.i32()==p,"native cell position mapping mismatch");require(c.u32()==1,"unsupported shared KV cell");require(c.i32()==0,"unexpected KV sequence");}if(!positions_in_physical_order.empty()){require(c.u32()==1,"FLASH_DISABLED profile requires serialized transposed V");require(c.u32()==layers,"native KV layer count mismatch");}}
}
