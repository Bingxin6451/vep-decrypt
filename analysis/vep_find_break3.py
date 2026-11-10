#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct
from decode_vep import VepDecoder, u32

d = VepDecoder('sample.vep')
d.parse_trak()
d.decode('x.mp4')
v = d.vid
print('vid len:', len(v))

# walk NALs, find break point
pos = 0
cnt = 0
breaks = []
while pos + 4 <= len(v):
    L = u32(v, pos)
    if not (0 < L < 0x1000000) or pos+4+L > len(v):
        breaks.append((pos, L, len(v) - pos))
        break
    cnt += 1
    pos += 4 + L
print('NAL count before break:', cnt)
print('break at pos', breaks if breaks else 'none', 'remaining:', len(v) - pos if pos < len(v) else 0)

# what's at the break
if breaks:
    bp = breaks[0][0]
    print('bytes at break:', v[bp:bp+32].hex())
    print('bytes at break repr:', repr(v[bp:bp+32]))
