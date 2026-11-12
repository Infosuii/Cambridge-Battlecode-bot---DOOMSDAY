// Per-champion state. A cancelled channel must not immediately re-enter its start path.
#pragma once
struct ChannelRetry {
    enum Kind { none, recall, submit };
    Kind kind = none;
    int round = -1, x = -1, y = -1, altar_x = -1, altar_y = -1;

    void cancelled(Kind k, int r, int px, int py, int ax = -1, int ay = -1) {
        kind = k; round = r; x = px; y = py; altar_x = ax; altar_y = ay;
    }
    bool matches(Kind k, int px, int py, int ax = -1, int ay = -1) const {
        return kind == k && x == px && y == py && (k != submit || (altar_x == ax && altar_y == ay));
    }
    bool allows(Kind k, int r, int px, int py, int ax, int ay, bool unsafe) const {
        return !matches(k, px, py, ax, ay) || (r > round && !unsafe);
    }
};
