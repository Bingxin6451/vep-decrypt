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

# rebuild video stream, record sample boundaries
vid = bytearray()
sample_bounds = []  # (stream_offset, sample_index, size)
si = 0
for ci in range(10375):
    n = spc(ci+1)
    base = vcoffs[ci] + 16
    for k in range(n):
        sz = vsizes[si]
        sample_bounds.append((len(vid), si, sz))
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)
print('video stream built:', len(vid), 'samples', si)

# walk NALs, find first break
pos = 0
count = 0
while pos + 4 <= len(vid):
    l = struct.unpack('>I', vid[pos:pos+4])[0]
    if not (0 < l < 0x1000000) or pos + 4 + l > len(vid):
        print('BREAK at stream offset', pos, 'after', count, 'NALs')
        for so, sIdx, sz in sample_bounds:
            if so <= pos < so + sz:
                print('  inside sample', sIdx, 'sample_off', pos - so, 'sample_size', sz)
                # which chunk?
                break
        print('  raw bytes at break:', vid[pos:pos+32].hex(' '))
        print('  prev 16 bytes:', vid[max(0,pos-16):pos].hex(' '))
        break
    pos += 4 + l
    count += 1
else:
    print('FULL PARSE OK,', count, 'NALs, end pos', pos)

# Also: verify every sample boundary is a valid NAL start (length-prefixed)
print('\n=== check each sample boundary is valid NAL start ===')
bad_samples = 0
for so, sIdx, sz in sample_bounds:
    if so + 4 > len(vid):
        bad_samples += 1
        continue
    l = struct.unpack('>I', vid[so:so+4])[0]
    if not (0 < l < 0x1000000) or so + 4 + l > len(vid):
        bad_samples += 1
        if bad_samples <= 10:
            print(f'  BAD sample {sIdx} @{so} size={sz} lenfield={l}')
print('bad sample boundaries:', bad_samples, '/', len(sample_bounds))
