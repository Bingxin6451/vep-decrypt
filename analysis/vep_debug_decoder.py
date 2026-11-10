#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct
from decode_vep import VepDecoder, u32

d = VepDecoder('sample.vep')
d.parse_trak()
print('video:', d.video)
print('audio:', d.audio)
vsz_off, vco_off, vcc = d.video
vcount = u32(d.data, vsz_off + 12)
print('video sample count:', vcount, 'chunk count:', vcc)
vstsc_off = d._find_stsc(vsz_off)
print('video stsc offset:', vstsc_off)
vstsc = d._parse_stsc(vstsc_off)
print('video stsc entries:', vstsc[:5], '...', vstsc[-3:])

# check enc_chunks identification
vchunks = [u32(d.data, vco_off + 12 + 4*i) + 16 for i in range(vcc)]
enc = []
for ci in range(vcc):
    off = vchunks[ci]
    L = u32(d.data, off)
    if not (0 < L < 0x1000000):
        enc.append(ci+1)
print('enc chunks count:', len(enc))
print('enc chunks:', enc)

# verify samples per chunk mapping total
total = 0
for ci in range(vcc):
    total += d._samples_per_chunk(vstsc, ci+1)
print('total samples from stsc:', total, 'vs vcount', vcount)
