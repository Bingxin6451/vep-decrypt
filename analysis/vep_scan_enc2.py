#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct
from decode_vep import VepDecoder, u32

d = VepDecoder('sample.vep')
d.parse_trak()
vsz_off, vco_off, vcc = d.video
vcount = u32(d.data, vsz_off + 12)
vsizes = [u32(d.data, vsz_off + 16 + 4*i) for i in range(vcount)]
vchunks = [u32(d.data, vco_off + 12 + 4*i) + 16 for i in range(vcc)]
vstsc = d._parse_stsc(d._find_stsc(vsz_off))

# walk all samples, check each sample's first NAL length prefix
bad_samples = []
si = 0
for ci in range(vcc):
    ns = d._samples_per_chunk(vstsc, ci+1)
    base = vchunks[ci]
    for k in range(ns):
        if si >= vcount: break
        sz = vsizes[si]
        if base + 4 <= d.n:
            L = u32(d.data, base)
            # valid NAL length prefix?
            if not (0 < L < 0x1000000 and L + 4 <= sz):
                bad_samples.append((si, ci+1, L))
        base += sz
        si += 1

print('total samples:', si)
print('bad (encrypted) samples:', len(bad_samples))
# group by chunk
from collections import defaultdict
by_chunk = defaultdict(list)
for si, ci, L in bad_samples:
    by_chunk[ci].append(si)
print('encrypted chunks:', sorted(by_chunk.keys()))
# print ranges
ranges = []
keys = sorted(by_chunk.keys())
start = keys[0]; prev = keys[0]
for k in keys[1:]:
    if k == prev + 1:
        prev = k
    else:
        ranges.append((start, prev))
        start = prev = k
ranges.append((start, prev))
print('encrypted chunk ranges:', ranges)
