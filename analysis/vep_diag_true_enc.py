#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, math
from collections import Counter

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

stss_entries = [u32be(579378 + i*4) for i in range(306)]  # 1-based sample numbers

# check chunk 97 (high-entropy but "valid length"?) vs chunk 3826 (bad)
def chunk_info(ci):
    base = vcoffs[ci-1] + 16
    n = spc(ci)
    start_si = 8 + (ci-2)*7 if ci >= 2 else 0
    sizes = vsizes[start_si:start_si+n]
    # check each sample's NAL structure
    results = []
    pos = base
    for k, sz in enumerate(sizes):
        l = u32be(pos) if pos+4 <= len(data) else 0
        ok = (0 < l < 0x100000) and (pos + 4 + l <= base + sum(sizes))
        # check nal header byte
        nal_hdr = data[pos+4] if pos+4 < len(data) else 0
        nal_type = nal_hdr & 0x1f
        results.append((k, sz, l, nal_type, ok))
        pos += sz
    return results

for ci in [97, 3826, 3825]:
    print(f'=== chunk {ci} ===')
    for k, sz, l, nt, ok in chunk_info(ci):
        kf = 'KF' if (start_si := (8+(ci-2)*7 if ci>=2 else 0)) is not None and (start_si+k+1) in stss_entries else '  '
        print(f'  sample {start_si+k}: size={sz} lenfield={l} naltype={nt} valid={ok} {kf}')

# determine: how many chunks have INVALID nal structure (truly encrypted)
def first_len_valid(ci):
    base = vcoffs[ci-1] + 16
    l = u32be(base)
    n = spc(ci)
    start_si = 8 + (ci-2)*7 if ci >= 2 else 0
    total = sum(vsizes[start_si:start_si+n])
    return (0 < l < 0x100000) and (base + 4 + l <= base + total)

enc_chunks = [ci for ci in range(1, 10376) if not first_len_valid(ci)]
print('\ntruly encrypted chunks (invalid first-sample lenfield):', len(enc_chunks))
ranges = []
if enc_chunks:
    s = p = enc_chunks[0]
    for c in enc_chunks[1:]:
        if c == p+1:
            p = c
        else:
            ranges.append((s,p)); s=p=c
    ranges.append((s,p))
print('ranges:', ranges)
for s, p in ranges:
    first_si = 8 + (s-2)*7 if s >= 2 else 0
    kfs = [k for k in stss_entries if first_si+1 <= k <= first_si+1+(p-s+1)*7]
    print(f'  chunks {s}..{p}: 1-based samples {first_si+1}..{first_si+(p-s+1)*7} keyframes={kfs}')
