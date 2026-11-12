#include "C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-round1-resume-20261112-e02/request/timeline.hpp"
int value(){hs_request_timeline::Recorder r;{hs_request_timeline::Span s(&r,"test");}r.finish();return r.spans.size();}
