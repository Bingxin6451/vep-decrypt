#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

vsizes = [u32be(580674 + i*4) for i in range(72625)]
vcoffs = [u32be(871190 + i*4) for i in range(10375)]
# audio stco: atom@1756377, entries@1756393
acount = u32be(1756389)
acoffs = [u32be(1756393 + i*4) for i in range(acount)]
def spc(ci):
    if ci == 1: return 8
    if ci <= 10374: return 7
    return 6

# sample 26776 -> chunk 3826 (1-based). Investigate chunks 3820..3830
for ci in range(3820, 3831):
    voff = vcoffs[ci-1]
    aoff = acoffs[ci-1]
    # video chunk ci sample count
    n = spc(ci)
    # video chunk ci total size
    start_si = 8 + (ci-2)*7 if ci >= 2 else 0
    total = sum(vsizes[start_si:start_si+n])
    print(f'chunk {ci}: video_stco={voff} (+16={voff+16}) vsize={total} vend={voff+16+total} | audio_stco={aoff} (+16={aoff+16})')

# detailed: chunk 3825 last samples and chunk 3826 boundary
print('\n=== chunk 3825 vs 3826 boundary detail ===')
ci = 3825
voff = vcoffs[ci-1]
start_si = 8 + (ci-2)*7
n = spc(ci)
base = voff + 16
cum = base
for k in range(n):
    sz = vsizes[start_si+k]
    cum += sz
print('chunk 3825: stco', voff, 'data start', base, '7 samples end at', cum)
print('chunk 3826: stco', vcoffs[3825], '+16 =', vcoffs[3825]+16)
print('gap between chunk3825 end and chunk3826(+16) start:', vcoffs[3825]+16 - cum)
print('audio chunk 3825 stco', acoffs[3824], 'audio chunk 3826 stco', acoffs[3825])
# what's in the gap?
gap = vcoffs[3825] + 16 - cum
if gap > 0:
    print('gap bytes:', data[cum:cum+min(gap,48)].hex(' '))
# check chunk 3826 data at +16
print('chunk3826 @+16 bytes:', data[vcoffs[3825]+16:vcoffs[3825]+16+32].hex(' '))
# check chunk 3826 raw stco (no +16)
print('chunk3826 @stco bytes:', data[vcoffs[3825]:vcoffs[3825]+32].hex(' '))
