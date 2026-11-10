#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

# video stsz entries start at 580674 (size@580654, type@580658, ver+flags@580662,
# sample_size@580666, count@580670, entries@580674)
VIDEO_SAMPLE_COUNT = 72625
vsizes = [u32be(580674 + i*4) for i in range(VIDEO_SAMPLE_COUNT)]
print('video sample sizes (first 8):', vsizes[:8], 'total bytes', sum(vsizes))

# video stco entries @871190, 10375 chunks
VIDEO_CHUNK_COUNT = 10375
vcoffs = [u32be(871190 + i*4) for i in range(VIDEO_CHUNK_COUNT)]

# stsc: chunk1=8 spc, chunk2..10374=7 spc, chunk10375=6 spc
def spc(ci):  # 1-based chunk index
    if ci == 1: return 8
    if ci <= 10374: return 7
    return 6

# verify +16 rule by checking NAL structure at each chunk boundary
print('\n--- verify +16 rule (chunk base data should start with 00 00 xx xx length) ---')
bad = 0
for ci in range(0, min(8, VIDEO_CHUNK_COUNT)):
    base = vcoffs[ci] + 16
    prefix = data[base:base+4]
    nallen = u32be(base) if False else struct.unpack('>I', prefix)[0]
    ok = (nallen < 0x100000)
    print(f'chunk {ci+1}: stco={vcoffs[ci]} -> +16={base}, first4={prefix.hex(" ")} nallen={nallen} {"OK" if ok else "BAD"}')
    if not ok:
        bad += 1

# extract full video stream with +16 correction
vid = bytearray()
si = 0
for ci in range(VIDEO_CHUNK_COUNT):
    n = spc(ci+1)
    base = vcoffs[ci] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
print('\nvideo samples consumed', si, 'of', VIDEO_SAMPLE_COUNT, 'bytes', len(vid))
print('first 48 bytes:', bytes(vid[:48]).hex(' '))

with open('/path/to/video_track.h264', 'wb') as f:
    f.write(vid)
print('wrote video_track.h264')
