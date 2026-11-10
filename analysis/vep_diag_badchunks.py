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

# read stss properly: atom@579366, ver@579370, count@579374, entries@579378
stss_count = u32be(579374)
stss_entries = [u32be(579378 + i*4) for i in range(stss_count)]
print('stss count', stss_count, 'first 10', stss_entries[:10], 'last 5', stss_entries[-5:])
keyset = set(stss_entries)
print('keyframe samples near 26776:', [k for k in stss_entries if 26600 <= k <= 27000])

# For each chunk, check if first sample NAL lenfield is valid; collect bad chunk ranges
def first_sample_offset(ci):
    start_si = 8 + (ci-2)*7 if ci >= 2 else 0
    return start_si

bad_chunks = []
si = 0
for ci in range(1, 10376):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    # check first sample of chunk
    l = u32be(base)
    ok = (0 < l < 0x100000) and (base + 4 + l <= len(data))
    if not ok:
        bad_chunks.append(ci)
    si += n

# collapse bad chunks into ranges
ranges = []
if bad_chunks:
    s = p = bad_chunks[0]
    for c in bad_chunks[1:]:
        if c == p + 1:
            p = c
        else:
            ranges.append((s, p))
            s = p = c
    ranges.append((s, p))
print('\nbad chunks:', len(bad_chunks), 'ranges:', ranges)

# For each bad chunk range, check if it contains a keyframe (sample in stss)
for s, p in ranges:
    # samples covered by chunks s..p
    first_si = first_sample_offset(s)
    last_si = first_sample_offset(p) + spc(p) - 1
    kfs = [k for k in stss_entries if first_si <= k <= last_si]
    print(f'  chunks {s}..{p} samples {first_si}..{last_si} keyframes_inside={len(kfs)} {kfs[:5]}')

# Also: check the big sample 26779 (size 64532) - is it a keyframe?
print('\nsample 26779 in stss?', 26779 in keyset, ' sample 26776?', 26776 in keyset)
