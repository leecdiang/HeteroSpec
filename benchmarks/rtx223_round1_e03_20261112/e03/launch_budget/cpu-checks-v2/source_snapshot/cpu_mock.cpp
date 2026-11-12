#include "hs_launch_budget.hpp"
#include <atomic>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

extern int mock_tu_a(int n);
extern int mock_tu_b(int n);

int main(int argc, char ** argv) {
    if (argc != 2) return 2;
    std::string mode=argv[1];
    bool ok=true;
    uint64_t mock_submissions=0;
    int initial=0;
    if (mode=="failstop-unarmed") {
        hs_launch_budget_before_launch_v1("unarmed-before-mock-driver");
        std::cout << "UNSAFE_MOCK_DRIVER_EXECUTED\n";
    } else if (mode=="failstop-opaque") {
        hs_launch_budget_configure_v1(4,0,4,"CPU");
        hs_launch_budget_deny_opaque_v1("cudaGraphLaunch-before-mock-driver");
        std::cout << "UNSAFE_MOCK_DRIVER_EXECUTED\n";
    } else if (mode=="unarmed") {
        ok &= hs_launch_budget_try_v1("unarmed") == -1;
    } else if (mode=="invalid-limit") {
        ok &= hs_launch_budget_configure_v1(4097,0,4097,"CPU") == -5;
    } else if (mode=="boundary-4096") {
        initial=hs_launch_budget_configure_v1(4096,0,4096,"CPU"); ok &= initial==1;
        for (int i=0;i<4096;i++) ok &= hs_launch_budget_try_v1("boundary")==1;
        ok &= hs_launch_budget_try_v1("4097-refused")==-2;
        hs_launch_budget_snapshot_v1_t s{}; hs_launch_budget_snapshot_v1(&s);
        ok &= s.admitted_attempts==4096;
    } else if (mode=="multithread-4096") {
        initial=hs_launch_budget_configure_v1(4096,0,4096,"CPU"); ok &= initial==1;
        std::atomic<uint64_t> accepted{0}; std::vector<std::thread> workers;
        for (int t=0;t<8;t++) workers.emplace_back([&](){
            for (int j=0;j<1024;j++) if (hs_launch_budget_try_v1("thread")==1) accepted.fetch_add(1);
        });
        for (auto & t:workers) t.join();
        hs_launch_budget_snapshot_v1_t s{}; hs_launch_budget_snapshot_v1(&s);
        ok &= accepted.load()==4096 && s.admitted_attempts==4096;
    } else if (mode=="two-TUs-one-state") {
        initial=hs_launch_budget_configure_v1(10,0,10,"CPU"); ok &= initial==1;
        ok &= mock_tu_a(6)==6 && mock_tu_b(6)==4;
        hs_launch_budget_snapshot_v1_t s{}; hs_launch_budget_snapshot_v1(&s);
        ok &= s.admitted_attempts==10;
    } else if (mode=="inherited-reservation") {
        initial=hs_launch_budget_configure_v1(4096,4090,6,"CPU"); ok &= initial==1;
        for (int i=0;i<6;i++) ok &= hs_launch_budget_try_v1("reserved")==1;
        ok &= hs_launch_budget_try_v1("family-over-cap")==-2;
        hs_launch_budget_snapshot_v1_t s{}; hs_launch_budget_snapshot_v1(&s);
        ok &= s.inherited_charged+s.admitted_attempts==4096;
    } else if (mode=="failed-submission-no-refund") {
        initial=hs_launch_budget_configure_v1(4,0,4,"CPU"); ok &= initial==1;
        try { if(hs_launch_budget_try_v1("mock-failed-submit")==1) throw std::runtime_error("mock failure"); }
        catch (const std::exception &) {}
        ok &= hs_launch_budget_try_v1("next")==1;
        hs_launch_budget_snapshot_v1_t s{}; hs_launch_budget_snapshot_v1(&s);
        ok &= s.admitted_attempts==2;
    } else if (mode=="prelaunch-order") {
        initial=hs_launch_budget_configure_v1(2,0,2,"CPU"); ok &= initial==1;
        for (int i=0;i<3;i++) {
            if(hs_launch_budget_try_v1("before-mock-driver")==1) ++mock_submissions;
        }
        ok &= mock_submissions==2;
    } else if (mode=="reconfigure-denied") {
        initial=hs_launch_budget_configure_v1(4,0,4,"CPU"); ok &= initial==1;
        ok &= hs_launch_budget_try_v1("one")==1;
        ok &= hs_launch_budget_configure_v1(4096,0,4096,"new-fake-context")==-5;
        hs_launch_budget_snapshot_v1_t s{}; hs_launch_budget_snapshot_v1(&s);
        ok &= s.admitted_attempts==1;
        ok &= hs_launch_budget_try_v1("after-bad-reconfigure")==-7;
    } else if (mode=="reentry-denied") {
        initial=hs_launch_budget_configure_v1(4,0,4,"CPU"); ok &= initial==1;
        ok &= hs_launch_budget_test_reentry_v1()==-3;
        ok &= hs_launch_budget_try_v1("after-reentry")==-7;
    } else if (mode=="graph-replay-denied" || mode=="opaque-BLAS-denied" || mode=="opaque-CUB-denied") {
        initial=hs_launch_budget_configure_v1(4,0,4,"CPU"); ok &= initial==1;
        const char * name = mode=="graph-replay-denied" ? "cudaGraphLaunch" : mode=="opaque-BLAS-denied" ? "cublasGemmEx" : "cub::DeviceScan::InclusiveSum";
        for (int i=0;i<5;i++) {
            if(hs_launch_budget_deny_opaque_try_v1(name)==1) ++mock_submissions;
        }
        hs_launch_budget_snapshot_v1_t s{}; hs_launch_budget_snapshot_v1(&s);
        ok &= mock_submissions==0 && s.admitted_attempts==0 && s.rejected_attempts==5;
    } else if (mode=="zero-remaining") {
        initial=hs_launch_budget_configure_v1(4096,4096,0,"CPU"); ok &= initial==1;
        ok &= hs_launch_budget_try_v1("none")==-2;
    } else return 3;
    hs_launch_budget_snapshot_v1_t s{};
    ok &= hs_launch_budget_snapshot_v1(&s)==1;
    std::cout << "{\"scenario\":\"" << mode << "\",\"pass\":" << (ok ? "true":"false")
              << ",\"CPU_MOCK_ONLY\":true,\"actual_GPU_launches\":0,\"initial\":" << initial
              << ",\"admitted_mock_attempts\":" << s.admitted_attempts
              << ",\"rejected_mock_attempts\":" << s.rejected_attempts
              << ",\"terminal_code\":" << s.terminal_code
              << ",\"mock_submissions\":" << mock_submissions << "}\n";
    return ok?0:1;
}
