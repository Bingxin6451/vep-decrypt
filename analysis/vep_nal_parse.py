#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

# rebuild video stream (same as extract_video2)
vsizes = [u32be(580674 + i*4) for i in range(72625)]
vcoffs = [u32be(871190 + i*4) for i in range(10375)]
def spc(ci):
    if ci == 1: return 8
    if ci <= 10374: return 7
    return 6
vid = bytearray()
si = 0
for ci in range(10375):
    n = spc(ci+1)
    base = vcoffs[ci] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)

# parse NAL units in first sample (47221 bytes)
nal_types = {}
i = 0
pos = 0
first_nals = []
while pos + 4 <= len(vid):
    l = struct.unpack('>I', vid[pos:pos+4])[0]
    if l < 1 or l > 0x1000000 or pos+4+l > len(vid):
        break
    nalu = vid[pos+4:pos+4+l]
    nal_type = nalu[0] & 0x1F
    nal_types[nal_type] = nal_types.get(nal_type, 0) + 1
    if len(first_nals) < 12:
        first_nals.append((pos, l, nal_type))
    pos += 4 + l
    i += 1
    if i > 200000:
        break

print('total NALs parsed:', i, 'stream bytes', len(vid), 'last pos', pos)
print('NAL type distribution:')
for t in sorted(nal_types):
    print(f'  type {t:2d}: {nal_types[t]}')
print('\nfirst 12 NALs (pos, len, type):')
for p, l, t in first_nals:
    print(f'  @{p} len={l} type={t}')

# find SPS (type 7) and PPS (type 8)
sps_pos = pps_pos = None
pos = 0
while pos + 4 <= len(vid):
    l = struct.unpack('>I', vid[pos:pos+4])[0]
    if l < 1 or l > 0x1000000 or pos+4+l > len(vid):
        break
    t = vid[pos+4] & 0x1F
    if t == 7 and sps_pos is None:
        sps_pos = pos
    if t == 8 and pps_pos is None:
        pps_pos = pos
    pos += 4 + l
    if sps_pos is not None and pps_pos is not None:
        break

print('\nSPS NAL @', sps_pos, 'PPS NAL @', pps_pos)
if sps_pos is not None:
    l = struct.unpack('>I', vid[sps_pos:sps_pos+4])[0]
    sps = vid[sps_pos+4:sps_pos+4+l]
    print('SPS bytes:', sps.hex(' '))
    print('SPS hex (for avcC):', sps.hex())
if pps_pos is not None:
    l = struct.unpack('>I', vid[pps_pos:pps_pos+4])[0]
    pps = vid[pps_pos+4:pps_pos+4+l]
    print('PPS hex:', pps.hex())
