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

# check entropy of video data for a few chunks: normal (3825), bad (3826), and bad2 (7908)
def chunk_entropy(ci):
    base = vcoffs[ci-1] + 16
    n = spc(ci)
    start_si = 8 + (ci-2)*7 if ci >= 2 else 0
    total = sum(vsizes[start_si:start_si+n])
    seg = data[base:base+total]
    return entropy(seg), total

for ci in [3824, 3825, 3826, 3827, 3828, 3830, 3831, 3832, 7907, 7908, 7909, 7926, 7927]:
    e, tot = chunk_entropy(ci)
    print(f'chunk {ci}: entropy={e:.3f} bytes={tot}')

# sample sizes of bad chunk 3826 (samples 26776..26782)
print('\nchunk 3826 sample sizes:', [vsizes[26776+k] for k in range(7)])
print('chunk 7908 sample sizes:', [vsizes[8+(7908-2)*7+k] for k in range(7)])

# check if bad chunk data resembles the header encrypted region (both high entropy streams)
# try XOR of bad chunk data with known plaintext h264? First, look at first 32 bytes of a bad chunk vs normal
print('\nnormal chunk 3825 first 32:', data[vcoffs[3824]+16:vcoffs[3824]+16+32].hex(' '))
print('bad chunk 3826 first 32:', data[vcoffs[3825]+16:vcoffs[3825]+16+32].hex(' '))
print('bad chunk 7908 first 32:', data[vcoffs[7907]+16:vcoffs[7907]+16+32].hex(' '))
