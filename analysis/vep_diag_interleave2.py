#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

# audio stsc: size@913161, type@913165, ver@913169, count@913173, entries@913177
a_stsc_count = u32be(913173)
a_stsc = []
for i in range(a_stsc_count):
    fc = u32be(913177 + i*12)
    spc = u32be(913181 + i*12)
    sdi = u32be(913185 + i*12)
    a_stsc.append((fc, spc, sdi))
print('audio stsc count:', a_stsc_count, 'first 5:', a_stsc[:5], 'last 3:', a_stsc[-3:])

# audio stsz entries @928941, count 206859
a_sizes = [u32be(928941 + i*4) for i in range(206859)]
# audio stco entries @1756393
a_coffs = [u32be(1756393 + i*4) for i in range(10375)]

def a_spc(chunk_idx):
    r = None
    for fc, spc, sdi in a_stsc:
        if chunk_idx >= fc:
            r = spc
        else:
            break
    return r

total_a = sum(a_spc(ci) for ci in range(1, 10376))
print('total audio samples from stsc:', total_a)

# verify interleaving at chunks 3824..3828
vcoffs = [u32be(871190 + i*4) for i in range(10375)]
def spc(ci):
    if ci == 1: return 8
    if ci <= 10374: return 7
    return 6

a_si = 0
for ci in range(1, 3830):
    n = a_spc(ci)
    if ci >= 3824:
        # video chunk ci
        v_start = vcoffs[ci-1] + 16
        # audio chunk ci
        a_start = a_coffs[ci-1] + 16
        a_n = a_spc(ci)
        a_tot = sum(a_sizes[a_si:a_si+a_n])
        print(f'chunk {ci}: video+16={v_start} | audio+16={a_start} audio_size={a_tot} audio_end={a_start+a_tot}')
    a_si += n
