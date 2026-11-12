"""Canonical team-perspective transforms (agent C); mirror of the inline helpers in bot/src/nn_obs.h.

Map symmetry values follow cambc::symmetry: 0 horizontal (x reversed), 1 vertical (y reversed), 2 rotational180.

* position  T(x, y):  horizontal (W-1-x, y); vertical (x, H-1-y); rotational180 (W-1-x, H-1-y)  (an involution)
* vector    L(dx, dy): horizontal (-dx, dy); vertical (dx, -dy); rotational180 (-dx, -dy)  (linear part of T)
* heading   8 compass directions in common.h kDirs order (0 N=+y, 1 NE, 2 E, 3 SE, 4 S, 5 SW, 6 W, 7 NW)
* canonical frame: flip (apply T) when our spawn centre lies in the high half along the symmetry axis
  (observation.json coordinate_frame.rule); then team A and team B see equivalent states on symmetric maps.
"""
from __future__ import annotations

from dataclasses import dataclass

HORIZONTAL, VERTICAL, ROTATIONAL180 = 0, 1, 2
DIRS = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]  # common.h kDirs


@dataclass(frozen=True)
class Frame:
    w: int
    h: int
    sym: int
    flip: bool
    fx: bool
    fy: bool

    def canon_x(self, x: int) -> int:
        return self.w - 1 - x if self.fx else x

    def canon_y(self, y: int) -> int:
        return self.h - 1 - y if self.fy else y

    def canon_pos(self, p: tuple[int, int]) -> tuple[int, int]:
        return self.canon_x(p[0]), self.canon_y(p[1])

    def canon_dx(self, dx: int) -> int:
        return -dx if self.fx else dx

    def canon_dy(self, dy: int) -> int:
        return -dy if self.fy else dy

    def canon_vec(self, v: tuple[int, int]) -> tuple[int, int]:
        return self.canon_dx(v[0]), self.canon_dy(v[1])

    def canon_dir(self, d: int) -> int:
        d &= 7
        if self.fx:
            d = (8 - d) & 7
        if self.fy:
            d = (12 - d) & 7
        return d

    # The frame is its own inverse (T and L are involutions), so these also map canonical -> world.
    world_pos = canon_pos
    world_vec = canon_vec
    world_dir = canon_dir


def make_frame(w: int, h: int, sym: int, s2x: int, s2y: int, abs_team: int) -> Frame:
    """s2x/s2y = twice our spawn centre (x0 + x1 of the inclusive spawn bounding box)."""
    team_b = abs_team == 1
    if sym == HORIZONTAL:
        flip = (s2x > w - 1) if s2x != w - 1 else team_b
    elif sym == VERTICAL:
        flip = (s2y > h - 1) if s2y != h - 1 else team_b
    elif sym == ROTATIONAL180:
        flip = (s2x > w - 1) if s2x != w - 1 else ((s2y > h - 1) if s2y != h - 1 else team_b)
    else:
        flip = False
    fx = flip and sym in (HORIZONTAL, ROTATIONAL180)
    fy = flip and sym in (VERTICAL, ROTATIONAL180)
    return Frame(w, h, sym, flip, fx, fy)


def reflect_pos(sym: int, w: int, h: int, p: tuple[int, int]) -> tuple[int, int]:
    """The SDK map symmetry T applied to a tile (cambc::map::reflect_horizontal/reflect_vertical/rotate_180)."""
    x, y = p
    if sym == HORIZONTAL:
        return w - 1 - x, y
    if sym == VERTICAL:
        return x, h - 1 - y
    if sym == ROTATIONAL180:
        return w - 1 - x, h - 1 - y
    raise ValueError(f'unknown symmetry {sym}')


def reflect_vec(sym: int, v: tuple[int, int]) -> tuple[int, int]:
    """Linear part L of T (vec2::reflect_horizontal / reflect_vertical / rotate_180)."""
    dx, dy = v
    if sym == HORIZONTAL:
        return -dx, dy
    if sym == VERTICAL:
        return dx, -dy
    if sym == ROTATIONAL180:
        return -dx, -dy
    raise ValueError(f'unknown symmetry {sym}')


def reflect_dir(sym: int, d: int) -> int:
    """T on a compass direction index (kDirs order)."""
    return DIRS.index(reflect_vec(sym, DIRS[d & 7]))


def reflect_ability_target(sym: int, w: int, h: int, target: tuple[int, int] | None, relative: bool) -> tuple[int, int] | None:
    """Ability destinations: ground/dash tiles are positions (T); direction-style targets are vectors (L)."""
    if target is None:
        return None
    return reflect_vec(sym, target) if relative else reflect_pos(sym, w, h, target)


def sector_of(dx: int, dy: int, radius: int = 16) -> int:
    """Belief sector (observation.json belief): 0..7 compass octant of a canonical displacement within Chebyshev
    `radius` (0 = N, clockwise, octant boundaries at +-22.5 degrees), 8 = farther. (0, 0) counts as sector 0."""
    if max(abs(dx), abs(dy)) > radius:
        return 8
    if dx == 0 and dy == 0:
        return 0
    import math
    ang = math.degrees(math.atan2(dx, dy)) % 360.0  # 0 = +y (north), clockwise towards +x (east)
    return int(((ang + 22.5) % 360.0) // 45.0)


def mirror_raw(raw: dict) -> dict:
    """The same game state seen by the other team on a symmetric map: every absolute tile goes through the map
    symmetry T, the spawn boxes follow, and the absolute team flips. Used to test team-A/B equivalence."""
    import copy
    r = copy.deepcopy(raw)
    sym, w, h = r['symmetry'], r['width'], r['height']

    def tp(xk, yk, d=r):
        d[xk], d[yk] = reflect_pos(sym, w, h, (d[xk], d[yk]))

    tp('pos_x', 'pos_y')
    tp('sight_x', 'sight_y')
    tp('distress_x', 'distress_y')
    for side in ('own_spawn', 'enemy_spawn'):
        a = reflect_pos(sym, w, h, (r[f'{side}_x0'], r[f'{side}_y0']))
        b = reflect_pos(sym, w, h, (r[f'{side}_x1'], r[f'{side}_y1']))
        r[f'{side}_x0'], r[f'{side}_x1'] = min(a[0], b[0]), max(a[0], b[0])
        r[f'{side}_y0'], r[f'{side}_y1'] = min(a[1], b[1]), max(a[1], b[1])
    for o in r['obj']:
        tp('anchor_x', 'anchor_y', o)
    for a in r['ally']:
        tp('x', 'y', a)
    for e in r['enemy']:
        tp('x', 'y', e)
    r['abs_team'] = 1 - r['abs_team'] if r['abs_team'] in (0, 1) else r['abs_team']
    return r
