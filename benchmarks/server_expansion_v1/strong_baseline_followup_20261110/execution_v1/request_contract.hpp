#pragma once
#include <cstddef>
// Match the unchanged pristine R's admitted M envelope. No draft transient rows.
inline bool hs_m_input_valid(std::size_t prompt,int cap,int context){
    return prompt>0&&cap>=1&&cap<=128&&context>0&&prompt<=std::size_t(context)&&
           std::size_t(cap)<=std::size_t(context)-prompt;
}
