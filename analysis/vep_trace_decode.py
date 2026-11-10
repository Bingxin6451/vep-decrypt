#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess

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

vid = bytearray()
si = 0
for ci in range(1, 200):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)

# Use the 1920x1080 SPS from before + PPS, build annexb with ONLY first few samples
sps = bytes.fromhex('6742c028dc0780227e5c0440000003004000000c83c60ce0')
pps = bytes.fromhex('68ebe72c8b')

# build annexb of first 5 samples (SEI+IDR+3 P frames)
avcc = bytearray()
pos = 0
count = 0
# first sample = SEI + IDR; skip SEI, keep IDR only for clean test
# Actually include everything: SPS+PPS then original samples
for nal in [sps, pps]:
    avcc += struct.pack('>I', len(nal)) + nal
avcc += vid[:200000]  # first ~200KB
annexb = bytearray()
pos = 0
while pos + 4 <= len(avcc):
    L = struct.unpack('>I', avcc[pos:pos+4])[0]
    if not (0 < L < 0x1000000) or pos+4+L > len(avcc):
        break
    annexb += b'\x00\x00\x00\x01' + avcc[pos+4:pos+4+L]
    pos += 4+L

fn = '/tmp/trace_test.h264'
open(fn, 'wb').write(annexb)

# ffmpeg trace decode, capture slice header parsing
cmd = ['ffmpeg', '-v', 'trace', '-i', fn, '-frames:v', '1', '-f', 'null', '-']
r = subprocess.run(cmd, capture_output=True, timeout=60)
err = r.stderr.decode(errors='replace')
# print lines about slice header / SPS / PPS / weight / frame_num / poc
lines = err.split('\n')
for ln in lines:
    if any(k in ln for k in ['SPS', 'PPS', 'slice', 'frame_num', 'poc', 'weight', 'ref', 'mb', 'first_mb', 'pps_id', 'sps_id', 'log2', 'pic_order', 'level', 'profile', 'out of range', 'illegal', 'invalid']):
        print(ln[:200])
