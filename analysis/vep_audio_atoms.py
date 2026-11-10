#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o): return struct.unpack('>I', data[o:o+4])[0]

# Scan moov region for all atoms, list audio-related
p = 40
end = 1797897
atoms = []
while p + 8 <= end:
    sz = u32be(p)
    typ = data[p+4:p+8]
    if sz < 8 or sz > 0x10000000 or p + sz > end + 8:
        break
    atoms.append((p, sz, typ))
    p += sz
    if p > 1200000:  # enough to cover audio trak
        break

# print audio track atoms
print('atoms after video stco (from 912694):')
for a, s, t in atoms:
    if a > 870000:
        print(f'  file {a} size {s} type {t.decode(errors="replace")}')
