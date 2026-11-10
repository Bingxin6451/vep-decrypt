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
    pos = 0; nals = 0
    while pos + 4 <= len(sample):
        L = struct.unpack('>I', sample[pos:pos+4])[0]
        if not (0 < L < 0x1000000) or pos + 4 + L > len(sample):
            return False, nals
        nals += 1
        pos += 4 + L
    return (pos == len(sample)), nals

# sample index offsets for the 26 chunks
target_chunks = set(range(3826, 3832)) | set(range(7907, 7927))
si = 0
for ci in range(vcc):
    ns = d._samples_per_chunk(vstsc, ci+1)
    base = vchunks[ci]
    statuses = []
    for k in range(ns):
        if si >= vcount: break
        sz = vsizes[si]
        smp = d.data[base:base+sz] if base+sz <= d.n else b''
        ok, nals = sample_ok(smp)
        statuses.append(('OK' if ok else 'ENC', nals))
        base += sz
        si += 1
    if ci+1 in target_chunks:
        print(f'chunk {ci+1}: {statuses}')
