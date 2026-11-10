#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess
from vep_build_sps import build_sps

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

# encrypted chunks to skip
enc_chunks = set(range(3826, 3832)) | set(range(7908, 7927))

# Build AVCC video stream (SPS + PPS + plaintext samples, skipping encrypted chunks)
sps = build_sps(1920, 1080)
pps = bytes.fromhex('68ebe72c8b')

avcc = bytearray()
for nal in [sps, pps]:
    avcc += struct.pack('>I', len(nal)) + nal

si = 0
skipped = 0
for ci in range(1, 10376):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    if ci in enc_chunks:
        si += n
        skipped += n
        continue
    for k in range(n):
        sz = vsizes[si]
        avcc += data[base:base+sz]
        base += sz
        si += 1

print('video samples kept:', si - skipped, 'skipped(encrypted):', skipped)

# Convert AVCC to Annex B
annexb = bytearray()
pos = 0
while pos + 4 <= len(avcc):
    L = struct.unpack('>I', avcc[pos:pos+4])[0]
    if not (0 < L < 0x1000000) or pos + 4 + L > len(avcc):
        break
    annexb += b'\x00\x00\x00\x01' + avcc[pos+4:pos+4+L]
    pos += 4 + L
print('annexb bytes:', len(annexb))

open('/tmp/full_video.h264', 'wb').write(annexb)

# ffmpeg: h264 -> mp4 (video only first)
r = subprocess.run(['ffmpeg', '-v', 'error', '-fflags', '+genpts', '-i', '/tmp/full_video.h264',
                    '-c:v', 'copy', '-f', 'mp4', '-y', '/tmp/rebuilt.mp4'],
                   capture_output=True, timeout=300)
print('ffmpeg exit:', r.returncode)
err = r.stderr.decode(errors='replace')
print('ffmpeg err (first 500):', err[:500])
