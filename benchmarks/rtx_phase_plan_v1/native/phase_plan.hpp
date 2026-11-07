#pragma once
// Backend-neutral planning only. It does not establish GPU arithmetic equality.
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
namespace refplan {
struct Row {
    int64_t position, physical_extent;
    uint64_t arithmetic_class;
    bool requested_output;
    bool operator==(const Row& b) const {
        return position==b.position && physical_extent==b.physical_extent &&
               arithmetic_class==b.arithmetic_class && requested_output==b.requested_output;
    }
};
struct Group {size_t begin, count; int64_t extent; uint64_t arithmetic_class;};
inline void require(bool ok, const char* what) {if(!ok) throw std::invalid_argument(what);}
// Only for an independently bound dense, non-wrapping, contiguous cache profile.
// Native adapters should prefer observed scalar extents to this model.
inline std::vector<int64_t> dense_extents(int64_t head, size_t width,
                                        int64_t padding, int64_t capacity) {
    require(head>=0 && padding>0 && capacity>0 && head<=capacity,"invalid dense profile");
    require(width>0 && width<=static_cast<uint64_t>(capacity-head),"append exceeds capacity");
    std::vector<int64_t> result; result.reserve(width);
    for(size_t j=0;j<width;++j) {
        const int64_t n=head+static_cast<int64_t>(j)+1;
        const int64_t remainder=n%padding;
        const int64_t extra=remainder?padding-remainder:0;
        result.push_back(extra>capacity-n?capacity:n+extra);
    }
    return result;
}
// Full requirements, not token IDs or output contents, determine cuts.
inline std::vector<Group> plan(const std::vector<Row>& rows, size_t max_call) {
    require(!rows.empty() && max_call>0,"empty plan or zero width");
    for(size_t i=0;i<rows.size();++i) {
        const auto&r=rows[i];
        require(r.position>=0 && r.physical_extent>r.position,"invalid visible extent");
        if(i) require(rows[i-1].position<std::numeric_limits<int64_t>::max() &&
                      r.position==rows[i-1].position+1,"noncontiguous positions unsupported");
    }
    std::vector<Group> out;
    for(size_t i=0;i<rows.size();) {
        size_t end=i+1;
        while(end<rows.size() && end-i<max_call &&
              rows[end].physical_extent==rows[i].physical_extent &&
              rows[end].arithmetic_class==rows[i].arithmetic_class) ++end;
        out.push_back({i,end-i,rows[i].physical_extent,rows[i].arithmetic_class});i=end;
    }
    return out;
}
// Retains only rows already requested by the caller. No extra outputs/reserve.
// Copies raw bytes before the next native call overwrites the output storage.
class OutputRows {
    size_t bytes_per_row_;std::vector<std::vector<unsigned char>> rows_;
    std::vector<bool> requested_,present_;
public:
    OutputRows(const std::vector<Row>& rows,size_t bytes):bytes_per_row_(bytes),
        rows_(rows.size()),requested_(rows.size()),present_(rows.size(),false) {
        require(bytes>0,"zero vocabulary extent");
        for(size_t i=0;i<rows.size();++i) requested_[i]=rows[i].requested_output;
    }
    void put(size_t row,const void* bytes,size_t n) {
        require(row<rows_.size() && requested_[row] && !present_[row],"unrequested/duplicate row");
        require(bytes && n==bytes_per_row_,"wrong output byte count");
        const auto*p=static_cast<const unsigned char*>(bytes);
        rows_[row].assign(p,p+n);present_[row]=true;
    }
    const std::vector<unsigned char>& get(size_t row) const {
        require(row<rows_.size() && requested_[row] && present_[row],"missing output row");
        return rows_[row];
    }
    bool complete() const {
        for(size_t i=0;i<requested_.size();++i) if(requested_[i]&&!present_[i]) return false;
        return true;
    }
};
// Equality is structural. A hash alone must never admit graph reuse.
struct Identity {
    std::string deployment,phase,lowering;
    size_t max_call;std::vector<Row> rows;
    bool operator==(const Identity&b)const {
        return deployment==b.deployment && phase==b.phase && lowering==b.lowering &&
               max_call==b.max_call && rows==b.rows;
    }
};
// Accounting fields are measured by the host adapter, not guessed by this helper.
struct OnlineWork {
    uint64_t exports=0,imports=0,context_creates=0,reference_replays=0;
    bool state_stationary()const {
        return exports==0 && imports==0 && context_creates==0 && reference_replays==0;
    }
};
} // namespace refplan
