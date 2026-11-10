#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

vsizes = [u32be(580674 + i*4) for i in range(72625)]
vcoffs = [u32be(871190 + i*4) for i in range(10375)]
def spc(ci):
    if ci == 1: return 8
    if ci <= 10374: return 7
    return 6

# locate break: find where NAL parse fails
pos = 0
while pos + 4 <= 29120220:
    l = struct.unpack('>I', bytes(bytearray()) or b'')  # placeholder
    break

# rebuild and locate sample boundaries
vid = bytearray()
si = 0
sample_abs = []  # (stream_offset, sample_index, size)
for ci in range(10375):
    n = spc(ci+1)
    base = vcoffs[ci] + 16
    for k in range(n):
        sz = vsizes[si]
        sample_abs.append((len(vid), si, sz))
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)

# walk NALs, find break
pos = 0
while pos + 4 <= len(vid):
    l = struct.unpack('>I', vid[pos:pos+4])[0]
    if l < 1 or l > 0x1000000 or pos + 4 + l > len(vid):
        print('BREAK at stream offset', pos)
        # find which sample this belongs to
        for so, si, sz in sample_abs:
            if so <= pos < so + sz:
                print('  in sample', si, 'sample offset', pos - so, 'of size', sz)
                break
        print('  bytes around:', vid[pos:pos+24].hex(' '))
        # also find containing chunk
        acc = 0
        for ci in range(10375):
            n = spc(ci+1)
            for k in range(n):
                if acc + vsizes[acc and 0 or 0]:
                    pass
                acc += 1
        break
    pos += 4 + l
else:
    print('no break, parsed fully to', pos)

# print sample sizes around the break for diagnosis
print('\nnearest sample_abs entries around break:')
for so, si, sz in sample_abs:
    if 10220000 < so < 10230000:
        print(f'  sample {si}: stream_off={so} size={sz}')
