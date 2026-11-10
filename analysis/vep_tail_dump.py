#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
N = len(data)
print('N =', N, '= 0x%x' % N)

# dump last 1200 bytes with offsets
start = N - 1200
for off in range(start, N, 32):
    seg = data[off:off+32]
    ascii_ = ''.join(chr(b) if 32 <= b < 127 else '.' for b in seg)
    print(f'0x{off:08x} ({off}): {seg.hex(" ")}  {ascii_}')
