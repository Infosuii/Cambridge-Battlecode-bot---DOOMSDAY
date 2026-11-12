#include "economic_cycle.h"
#include <cassert>
#include <iostream>
int main() {
    using namespace economic_cycle;
    assert(!plan_active(149,150,500));
    assert(plan_active(150,150,500));
    assert(plan_active(499,150,500));
    assert(!plan_active(500,150,500));
    assert(plan_active(800,150,0));
    assert(!plan_active(800,-1,500));
    assert(delivery_cost(20,0,100,30)==20);
    assert(delivery_cost(20,20,0,-1)==20);
    assert(delivery_cost(20,20,0,30)==52);
    assert(delivery_cost(20,20,0,5)<delivery_cost(20,20,0,30));
    assert(delivery_cost(20,20,100,30)<delivery_cost(20,20,0,30));
    // Equal collection yields: rank the nearer bank higher.
    assert(20/delivery_cost(20,20,0,5)>20/delivery_cost(20,20,0,30));
    std::cout << "12 economic-cycle / plan-boundary checks passed\n";
}
