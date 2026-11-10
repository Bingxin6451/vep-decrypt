#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o): return struct.unpack('>I', data[o:o+4])[0]
def u16be(o): return struct.unpack('>H', data[o:o+2])[0]

# esds @913099 (type), atom 913095 (size)
esds_size = u32be(913095)
print('esds size:', esds_size)
esds_data = data[913099+4: 913095+esds_size]
print('esds content:', esds_data.hex())

# find audioSpecificConfig (0x05 tag = DecoderSpecificInfo)
i = 0
asc = None
while i < len(esds_data):
    tag = esds_data[i]
    if tag == 0x05:  # DecoderSpecificInfo
        ln = 0
        j = i+1
        while True:
            b = esds_data[j]; ln = (ln << 7) | (b & 0x7f); j += 1
            if not (b & 0x80): break
        asc = esds_data[j:j+ln]
        print('AudioSpecificConfig:', asc.hex())
        break
    i += 1

# parse AudioSpecificConfig
if asc:
    aot = (asc[0] >> 3) & 0x1f
    freq_idx = ((asc[0] & 0x7) << 1) | (asc[1] >> 7)
    chan = (asc[1] >> 3) & 0xf
    freqs = [96000,88200,64000,48000,44100,32000,24000,22050,16000,12000,11025,8000,7350]
    print(f'AOT={aot} freq_idx={freq_idx} freq={freqs[freq_idx] if freq_idx<13 else "?"} channels={chan}')

# stsc @913165
stsc_size = u32be(913161)
n = u32be(913169)
entries = []
for k in range(n):
    fc = u32be(913173 + 12*k)
    spc = u32be(913177 + 12*k)
    sd = u32be(913181 + 12*k)
    entries.append((fc, spc, sd))
print('stsc entries:', entries[:5], '... total', n)

# stsz @928925 (type), count at 928937, entries from 928941
acount = u32be(928937)
print('audio sample count:', acount)

# stco @1756381 (type), count at 1756389, offsets from 1756393
ccount = u32be(1756389)
print('audio chunk count:', ccount)
print('first 3 chunk offsets:', [u32be(1756393+4*k) for k in range(3)])
