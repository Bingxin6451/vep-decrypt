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

def sample_ok(sample):
    """Check if sample is a valid AVCC NAL sequence (plaintext)."""
    pos = 0
    nals = 0
    while pos + 4 <= len(sample):
        L = struct.unpack('>I', sample[pos:pos+4])[0]
        if not (0 < L < 0x1000000) or pos + 4 + L > len(sample):
            return False, nals
        # check NAL header byte is sane
        nals += 1
        pos += 4 + L
    return (pos == len(sample)), nals

# walk all samples, classify
enc_samples = []
si = 0
for ci in range(vcc):
    ns = d._samples_per_chunk(vstsc, ci+1)
    base = vchunks[ci]
    for k in range(ns):
        if si >= vcount: break
        sz = vsizes[si]
        smp = d.data[base:base+sz] if base+sz <= d.n else b''
        ok, nals = sample_ok(smp)
        if not ok:
            enc_samples.append((si, ci+1))
        base += sz
        si += 1

print('encrypted samples:', len(enc_samples))
from collections import defaultdict
by_chunk = defaultdict(list)
for si, ci in enc_samples:
    by_chunk[ci].append(si)
keys = sorted(by_chunk.keys())
ranges = []
start = prev = keys[0]
for k in keys[1:]:
    if k == prev+1:
        prev = k
    else:
        ranges.append((start, prev)); start = prev = k
ranges.append((start, prev))
print('encrypted chunk ranges:', ranges)
print('total encrypted chunks:', len(keys))
