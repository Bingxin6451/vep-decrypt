#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

# audio stsz: size@928921, type@928925, ver@928929, sample_size@928933, count@928937, entries@928941
a_sample_size = u32be(928933)
a_count = u32be(928937)
print('audio stsz: sample_size', a_sample_size, 'count', a_count)
a_sizes = [u32be(928941 + i*4) for i in range(a_count)]
print('audio total bytes:', sum(a_sizes), 'first 6:', a_sizes[:6])

# audio stsc: size@913157, type@913161, ver@913165, count@913169, entries@913173
# walk said stsc @913161 size=15760 entry_count=1312
a_stsc_count = u32be(913169)
print('audio stsc entries:', a_stsc_count)
a_stsc = []
for i in range(a_stsc_count):
    fc = u32be(913173 + i*12)
    spc = u32be(913177 + i*12)
    sdi = u32be(913181 + i*12)
    a_stsc.append((fc, spc, sdi))
print('audio stsc first 5:', a_stsc[:5])
print('audio stsc last 3:', a_stsc[-3:])

# audio stco: size@1756377, type@1756381, ver@1756385, count@1756389, entries@1756393
a_chunk_count = u32be(1756389)
a_coffs = [u32be(1756393 + i*4) for i in range(a_chunk_count)]
print('audio chunk count:', a_chunk_count, 'first 3:', a_coffs[:3], 'last 3:', a_coffs[-3:])

# build per-chunk sample counts for audio from stsc
def a_spc(chunk_idx):  # 1-based
    # stsc: (first_chunk, samples_per_chunk, sdi)
    result = None
    for fc, spc, sdi in a_stsc:
        if chunk_idx >= fc:
            result = spc
        else:
            break
    return result

# verify total audio samples
total_a = 0
for ci in range(1, a_chunk_count+1):
    total_a += a_spc(ci)
print('total audio samples from stsc:', total_a, '(expected ~206859)')

# Now check interleaving around chunk 3825/3826
# video chunk 3825: stco 20969184, +16 start 20969200, 7 samples, end 20969904
# audio chunk 3825 should start at 20969904 and end at video chunk 3826 (+16) = 20972256
vid3825_start = u32be(871190 + 3824*4) + 16
# compute audio chunk 3825 size
a_si = 0
for ci in range(1, 3826):
    a_si += a_spc(ci)
a_chunk3825_n = a_spc(3825)
a_chunk3825_sizes = a_sizes[a_si:a_si+a_chunk3825_n]
a_chunk3825_total = sum(a_chunk3825_sizes)
print('\naudio chunk 3825: n_samples', a_chunk3825_n, 'total size', a_chunk3825_total)
print('audio chunk 3825 stco', a_coffs[3824], '+16 =', a_coffs[3824]+16)
print('audio chunk 3825 expected end:', a_coffs[3824]+16+a_chunk3825_total)
print('video chunk 3826 +16 start:', u32be(871190 + 3825*4)+16)
