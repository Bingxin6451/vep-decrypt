#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, sys

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
N = len(data)

ATOMS = [b'ftyp', b'moov', b'mvhd', b'trak', b'tkhd', b'mdia', b'mdhd', b'hdlr',
         b'minf', b'vmhd', b'smhd', b'dinf', b'dref', b'url ', b'stbl', b'stsd',
         b'stts', b'stsc', b'stsz', b'stco', b'co64', b'stss', b'ctts', b'sgpd',
         b'sbgp', b'udta', b'meta', b'mdat', b'moof', b'free', b'skip', b'wide',
         b'avcC', b'avc1', b'mp4a', b'esds', b'hvc1', b'hvcC', b'elst', b'edts',
         b'name', b'art ', b'cprt', b'ilst', b'data', b'iods', b'pdin', b'mvex',
         b'trex', b'mehd', b'sidx', b'emsg', b'uuid', b'rap ', b'bits']

# find all occurrences of atom types, check size field (4 bytes before) plausibility
print('=== ATOM MAP (plausible atoms with valid size) ===')
found = {}
for t in ATOMS:
    idxs = []
    i = 0
    while True:
        j = data.find(t, i)
        if j < 0:
            break
        idxs.append(j)
        i = j + 1
    for j in idxs:
        if j >= 4:
            size = struct.unpack('>I', data[j-4:j])[0]
            # plausible: size in [8, 60_000_000] and aligned-ish
            if 8 <= size <= 60_000_000:
                key = t.decode('latin1')
                found.setdefault(key, []).append((j, size))

for k in sorted(found):
    lst = found[k]
    print(f'{k:6s} {len(lst):3d} : ' + ' '.join(f'@{o}(sz={s})' for o, s in lst[:12]))
