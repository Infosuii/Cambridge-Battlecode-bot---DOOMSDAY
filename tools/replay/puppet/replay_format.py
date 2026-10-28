"""Read engine2 accepted input records; validate byte boundaries against the native ledger.

Map bytes must match a supplied official map exactly. Unknown variants fail closed.
Schema inferred by generating accepted commands with pinned official engine APIs;
it must also pass an independent official replay / reserialization check.
"""
import struct


def parse(replay: bytes, map_bytes: bytes):
    if replay[:8] != b'a62per\0\0' or replay[14:14 + len(map_bytes)] != map_bytes:
        raise ValueError('Engine2 replay / exact embedded-map prefix mismatch')
    offset = 14 + len(map_bytes)
    count, = struct.unpack_from('<I', replay, offset)
    offset += 4
    rows = []
    for index in range(count):
        start = offset
        tag = replay[offset]
        offset += 1
        args = []
        action = None
        if tag == 0:
            action = replay[offset]
            offset += 1
            # Entities use a one-byte kind and a uint32 handle; positions are int32.
            layouts = {0: 'i', 1: 'ii', 2: 'BII', 3: 'IBIii', 4: '', 5: 'ii',
                       6: 'II', 7: '', 8: 'II', 9: 'Bii', 10: 'ii', 11: 'I'}
            if action not in layouts:
                raise ValueError(f'Unknown action{action} at input{index + 1},offset{offset}')
            layout = '<' + layouts[action]
            args = list(struct.unpack_from(layout, replay, offset))
            offset += struct.calcsize(layout)
        elif tag == 3:
            args = [replay[offset]]
            offset += 1
        elif tag == 4:
            has_pick = replay[offset]
            offset += 1
            if has_pick not in (0, 1):
                raise ValueError('Invalid draft option')
            pick = None
            if has_pick:
                pick, = struct.unpack_from('<i', replay, offset)
                offset += 4
            reason = replay[offset]
            offset += 1
            args = [has_pick, pick, reason]
        elif tag == 1:
            # Resign is confirmed separately before using a record containing it.
            raise ValueError(f'Unknown outer1 at input{index+1},offset{start}; prior{rows[-1]}; bytes{replay[start:start+30].hex()}')
        else:
            raise ValueError(f'Unknown input tag{tag} at input{index + 1},offset{start}')
        rows.append({'input': index + 1, 'tag': tag, 'action': action, 'args': args,
                     'start_offset': start, 'end_offset': offset})
    if offset != len(replay):
        raise ValueError(f'Input decoder ends at{offset}, replay has{len(replay)} bytes')
    return rows
