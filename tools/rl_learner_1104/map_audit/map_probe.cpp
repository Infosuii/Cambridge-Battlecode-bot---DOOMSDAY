#include <cambc.h>
#include <cstdio>
int main() {
  namespace bc = cambc;
  std::printf("JDMAP %d %d %d\n", bc::map::width(), bc::map::height(), int(bc::map::symmetry()));
  std::printf("JDTILES ");
  for (int y=0;y<bc::map::height();++y) for(int x=0;x<bc::map::width();++x) {
    bc::vec2 p{x,y};
    int v=bc::map::walls().is_set(p) | (bc::map::holes().is_set(p)<<1) |
      (bc::map::bushes().is_set(p)<<2) | (bc::map::altars().is_set(p)<<3) |
      (bc::map::spawn_region(bc::team::ally).is_set(p)<<4) |
      (bc::map::spawn_region(bc::team::enemy).is_set(p)<<5);
    std::printf("%02x",v);
  }
  std::printf("\n");
  for(const auto& g:bc::map::camp_groups()) {
    std::printf("JDGROUP %u %u %d",g.gold_value(),g.gem_value(),g.max_respawn_timer());
    for(const auto& c:g.camps()) {auto p=c.spawn_position(); std::printf(" %d,%d,%d",p.x,p.y,int(c.kind()));}
    std::printf("\n");
  }
  std::fflush(stdout);
  bc::resign();
  bc::end_turn();
}
