#include "hs_launch_budget.hpp"
int mock_tu_b(int n) {
    int accepted=0;
    for (int i=0;i<n;i++) if (hs_launch_budget_try_v1("TU-B")==1) accepted++;
    return accepted;
}
