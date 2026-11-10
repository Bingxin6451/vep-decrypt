#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o): return struct.unpack('>I', data[o:o+4])[0]

# audio stsc: atom 913161(size) 913165(type) 913169(verflags) 913173(count) 913177(entries)
n = u32be(913173)
stsc = []
for k in range(n):
    fc = u32be(913177 + 12*k)
    spc = u32be(913181 + 12*k)
    sd = u32be(913185 + 12*k)
    stsc.append((fc, spc, sd))
print('stsc entries:', stsc[:6])

# audio stsz: entries from 928941 (type 928925 + 16)
acount = u32be(928937)
asizes = [u32be(928941 + 4*i) for i in range(acount)]

# audio stco: offsets from 1756393 (type 1756381 + 12)
ccount = u32be(1756389)
acoffs = [u32be(1756393 + 4*i) + 16 for i in range(ccount)]

# build chunk -> samples mapping from stsc
def chunk_samples(stsc, nchunks):
    mapping = []
    for ci in range(1, nchunks+1):
        # find stsc entry
        spc = 1; sd = 1
        for j, (fc, s, d) in enumerate(stsc):
            if ci < fc:
                break
            spc, sd = s, d
        mapping.append(spc)
    return mapping

csm = chunk_samples(stsc, ccount)
print('total samples from mapping:', sum(csm), 'vs acount', acount)

# extract audio, build ADTS frames
adts = bytearray()
si = 0
for ci in range(ccount):
    spc = csm[ci]
    base = acoffs[ci]
    for k in range(spc):
        if si >= acount: break
        sz = asizes[si]
        raw = data[base:base+sz]
        base += sz
        # ADTS header: 7 bytes for AAC-LC 44100 2ch
        # profile=1 (AAC LC), sf_index=4 (44100), channel=2
        frame_len = sz + 7
        hdr = bytearray()
        hdr.append(0xFF)
        hdr.append(0xF1)  # MPEG-4, layer 0, no CRC
        hdr.append(((1 << 6) | (4 << 2) | (2 >> 2)) & 0xFF)  # profile<<6 | sf_idx<<2 | chan>>2
        hdr.append(((2 & 0x3) << 6) | ((frame_len >> 11) & 0x3))
        hdr.append((frame_len >> 3) & 0xFF)
        hdr.append(((frame_len & 0x7) << 5) | 0x1F)
        hdr.append(0xFC)
        adts += hdr + raw
        si += 1

open('/tmp/audio.aac', 'wb').write(adts)
print('audio ADTS size:', len(adts), 'samples written:', si)
