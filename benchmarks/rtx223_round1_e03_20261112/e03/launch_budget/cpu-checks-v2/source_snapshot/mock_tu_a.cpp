#include "hs_launch_budget.hpp"
int mock_tu_a(int n) {
    int accepted=0;
    for (int i=0;i<n;i++) if (hs_launch_budget_try_v1("TU-A")==1) accepted++;
    return accepted;
}
