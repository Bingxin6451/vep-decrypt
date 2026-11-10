#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, math
from collections import Counter

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

def entropy(b):
    if not b:
        return 0
    c = Counter(b)
    n = len(b)
    return -sum((v/n)*math.log2(v/n) for v in c.values())

vsizes = [u32be(580674 + i*4) for i in range(72625)]
vcoffs = [u32be(871190 + i*4) for i in range(10375)]
def spc(ci):
    if ci == 1: return 8
    if ci <= 10374: return 7
    return 6

# scan all video chunks entropy (sample a small window of each chunk for speed)
enc_chunks = []
si = 0
for ci in range(1, 10376):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    start_si = si
    total = sum(vsizes[si:si+n])
    # sample first min(total, 512) bytes
    seg = data[base:base+min(total, 512)]
    e = entropy(seg)
    if e > 7.0:
        enc_chunks.append((ci, e, total, start_si))
    si += n

print('encrypted-looking video chunks (>7.0 entropy):', len(enc_chunks))
ranges = []
for ci, e, tot, ssi in enc_chunks:
    ranges.append((ci, e, tot))
# collapse
if ranges:
    s = p = ranges[0][0]
    for ci, e, tot in ranges[1:]:
        if ci == p + 1:
            p = ci
        else:
            print(f'  chunks {s}..{p} (samples {s and (8+(s-2)*7)}..{8+(p-1)*7-1+spc(p)})')
            s = p = ci
    print(f'  chunks {s}..{p}')

# print all ranges with sample indices
print('\ndetail:')
for ci, e, tot, ssi in enc_chunks:
    if ci < 40 or ci > 10340:
        print(f'  chunk {ci}: entropy={e:.3f} size={tot} sample_start={ssi}')
