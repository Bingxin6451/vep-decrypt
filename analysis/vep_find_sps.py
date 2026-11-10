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

# rebuild plaintext video stream (chunks 1..3825 only, skipping encrypted 3826..3831)
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
vid = bytes(vid)
print('plaintext video stream:', len(vid), 'bytes, samples', si)

# search for SPS NAL: length-prefixed 0x67, or annexb 00000001 67
import re
# AVCC style: 4-byte len then 0x67
sps_avcc = []
for m in re.finditer(b'\x00\x00\x00\x00\x67', vid):
    pos = m.start()
    L = struct.unpack('>I', vid[pos:pos+4])[0]
    if 4 <= L <= 200:
        sps_avcc.append((pos, L))
print('AVCC SPS candidates (len 4..200):', len(sps_avcc), sps_avcc[:10])

# Annex B style: 00000001 67
sps_annexb = [m.start() for m in re.finditer(b'\x00\x00\x00\x01\x67', vid)]
print('AnnexB SPS candidates:', len(sps_annexb), sps_annexb[:10])

# search 0x67 0x64 (SPS header profile high) with length prefix
sps_hdr = []
for m in re.finditer(b'\x67\x64', vid):
    pos = m.start()
    if pos >= 4:
        L = struct.unpack('>I', vid[pos-4:pos])[0]
        if 4 <= L <= 200:
            sps_hdr.append((pos, L))
print('0x67 0x64 with valid len prefix:', len(sps_hdr), sps_hdr[:10])

# Also scan PPS: find first PPS to check if SPS is nearby
pps = []
for m in re.finditer(b'\x68', vid):
    pos = m.start()
    if pos >= 4:
        L = struct.unpack('>I', vid[pos-4:pos])[0]
        if 2 <= L <= 100 and (vid[pos] & 0x1f) == 8:
            pps.append((pos, L))
print('PPS candidates:', len(pps), pps[:5])

# first 50 NAL types around first PPS
first_pps = pps[0][0] if pps else None
if first_pps:
    print('\nNALs around first PPS @', first_pps, ':')
    pos = max(0, first_pps - 200)
    count = 0
    while pos + 4 <= len(vid) and count < 20:
        L = struct.unpack('>I', vid[pos:pos+4])[0]
        if not (0 < L < 0x1000000):
            break
        t = vid[pos+4] & 0x1f
        print(f'  @{pos} len={L} naltype={t}')
        pos += 4 + L
        count += 1
