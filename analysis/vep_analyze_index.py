#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
N = len(data)

# Analyze the "index table" region from 81936 (0x14010) onward.
# Records look like 16 bytes: (u32, 1, u32, 1)
start = 81936
end_guess = 912783  # where trak starts
print('=== index table region', hex(start), '->', hex(end_guess), 'len', end_guess-start)
i = start
count = 0
first = []
while i + 16 <= end_guess:
    a, b, c, d = struct.unpack('<IIII', data[i:i+16])
    if b == 1 and d == 1 and a < 0x100000 and c < 0x100000:
        count += 1
        if len(first) < 20:
            first.append((i-start, a, b, c, d))
        i += 16
    else:
        # maybe 8-byte or other alignment; stop
        break
print('matched 16B records:', count, 'consumed until', hex(start + count*16))
for r in first:
    print('  +0x%06x  a=%d b=%d c=%d d=%d' % r)

# dump raw hex right after the matched records
after = start + count*16
print('=== raw after matched records at', hex(after))
print(data[after:after+128].hex(' '))
print(''.join(chr(x) if 32 <= x < 127 else '.' for x in data[after:after+128]))
