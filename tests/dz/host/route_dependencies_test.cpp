#include "route_dependencies.h"
#include <cassert>
#include <iostream>
using namespace dz::crew;
int main() {
    RouteDependencies dependencies;dependencies.reset(1);
    assert(dependencies.add(3,4,100)&&dependencies.add(3,4,90)&&dependencies.count==1);
    assert(dependencies.add(5,2,200)&&dependencies.count==2&&dependencies.until==90);
    unsigned queries=0;
    auto expiry=[&](RouteDependency d){++queries;return d.group==3?100:200;};
    assert(dependencies.refresh(1,80,expiry,[]{return true;})==1&&queries==0);
    assert(dependencies.refresh(2,80,expiry,[]{return true;})==1&&queries==2); // Unrelated revision, same route.
    assert(dependencies.until==100);
    assert(dependencies.refresh(3,80,expiry,[]{return false;})==-1&&dependencies.revision==2);
    assert(dependencies.refresh(3,80,[](RouteDependency){return 0;},[]{return true;})==0&&dependencies.revision==2);
    assert(dependencies.refresh(2,100,expiry,[]{return true;})==0); // Exact spawn boundary.
    dependencies.trim([](RouteDependency d){return d.group==5;},[]{return true;});
    assert(dependencies.count==1&&dependencies.entries[0].group==5);
    assert(dependencies.refresh(4,100,expiry,[]{return true;})==1&&dependencies.until==200);
    for(int i=0;i<127;++i)assert(dependencies.add(10+i,0,200));
    assert(dependencies.count==128&&!dependencies.add(500,0,200));
    unsigned checks=0;dependencies.trim([](RouteDependency){return false;},[&]{return checks++<3;});
    assert(dependencies.count==125); // Unchecked tail survives a partial trim.
    dependencies.reset(5);assert(dependencies.refresh(6,2000,expiry,[]{return false;})==1&&dependencies.count==0);
    std::cout<<"Route dependency reuse, closure/expiry invalidation, bounded refresh and partial trimming passed\n";
}
