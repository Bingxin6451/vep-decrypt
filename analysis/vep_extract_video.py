#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(off):
    return struct.unpack('>I', data[off:off+4])[0]

# Extract video stream from mdat.
# mdat: size@1797893, type@1797897, data starts 1797901
mdat_data_start = 1797901
mdat_end = 1797893 + u32be(1797893)   # = 55068909
print('mdat data range:', mdat_data_start, '..', mdat_end)

# video stco: 10375 chunks
video_chunk_offsets = [u32be(871190 + i*4) for i in range(10375)]

# We don't know exact chunk sizes without stsz+stsc mapping, but video data is
# contiguous-ish in mdat interleaved with audio. For ffprobe test, just dump the
# whole mdat payload (video+audio interleaved won't parse as pure h264, but let's
# first check if the beginning is h264).
with open('/path/to/mdat_payload.bin', 'wb') as f:
    f.write(data[mdat_data_start:mdat_end])

print('wrote mdat_payload.bin, size', mdat_end - mdat_data_start)

# Also extract video-only by walking video chunks in order, using stsz sample sizes.
# stsz@580658: header 12 bytes, then 72625 u32 sample sizes (stsz uses '>' big endian)
stsz_off = 580658
samples = []
for i in range(72625):
    samples.append(u32be(stsz_off + 12 + i*4))
print('video total bytes:', sum(samples))

# stsc: chunks -> samples_per_chunk
# chunk 1: 8 spc ; chunk 2..10374: 7 spc ; chunk 10375: 6 spc
def spc(chunk_idx):  # chunk_idx 1-based
    if chunk_idx == 1:
        return 8
    if chunk_idx <= 10374:
        return 7
    return 6

# build sample->chunk mapping
vid_out = bytearray()
sample_idx = 0
for chunk_idx in range(1, 10376):
    n = spc(chunk_idx)
    for k in range(n):
        sz = samples[sample_idx]
        off = video_chunk_offsets[chunk_idx-1]
        # each chunk stores its samples contiguously; cumulative offset within chunk
        # we need per-chunk base + running offset
        sample_idx += 1

# Better: reconstruct contiguous video stream by walking chunks and accumulating
# offsets inside each chunk using sample sizes.
vid = bytearray()
si = 0
for ci in range(10375):
    n = spc(ci+1)
    chunk_base = video_chunk_offsets[ci]
    # sample data within chunk: need running offset; but chunks in mdat are
    # contiguous within a chunk only. Compute intra-chunk offsets by assuming
    # samples are laid out back-to-back starting at chunk_base.
    # We'll verify by checking h264 NAL structure.
    for k in range(n):
        sz = samples[si]
        vid += data[chunk_base:chunk_base+sz]
        chunk_base += sz
        si += 1

with open('/path/to/video_track.h264', 'wb') as f:
    f.write(vid)
print('video_track.h264 written, samples used', si, 'bytes', len(vid))
print('first 64 bytes:', vid[:64].hex(' '))
