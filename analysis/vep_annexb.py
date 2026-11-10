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

# rebuild video stream (plaintext chunks only up to first encrypted chunk 3826)
vid = bytearray()
si = 0
for ci in range(1, 3826):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
print('plaintext video prefix (chunks 1..3825):', len(vid), 'bytes, samples', si)

# convert AVCC to Annex B
annexb = bytearray()
pos = 0
while pos + 4 <= len(vid):
    l = struct.unpack('>I', vid[pos:pos+4])[0]
    if not (0 < l < 0x1000000) or pos + 4 + l > len(vid):
        break
    annexb += b'\x00\x00\x00\x01'
    annexb += vid[pos+4:pos+4+l]
    pos += 4 + l
print('annexb bytes:', len(annexb), 'nal end pos', pos)

with open('/path/to/video_prefix.h264', 'wb') as f:
    f.write(annexb)
print('wrote video_prefix.h264')
