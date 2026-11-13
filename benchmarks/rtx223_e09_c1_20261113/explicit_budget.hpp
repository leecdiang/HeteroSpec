#pragma once
#include <cstdint>
#include <stdexcept>
struct ApplicationBudget {
    uint32_t used=0,limit=0;
    bool configured=false;
    void configure(uint32_t n) {
        if(configured||n==0||n>355)throw std::runtime_error("invalid or repeated explicit budget configuration");
        configured=true;limit=n;
    }
    void reserve(uint32_t n) {
        if(!configured||n==0||used>limit||n>limit-used)throw std::runtime_error("explicit budget refused before dispatch");
        used+=n;
    }
};
