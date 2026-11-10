#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
N = len(data)

def u32be(off):
    return struct.unpack('>I', data[off:off+4])[0]

def read_stco(atom_data_off, count_off):
    n = u32be(count_off)
    offs = []
    base = atom_data_off + 8
    for i in range(n):
        offs.append(u32be(base + i*4))
    return offs

# video stco @871174: size@871174, type@871178, ver@871182, count@871186
print('=== VIDEO stco ===')
vsize = u32be(871174)
vcount = u32be(871186)
print('size', vsize, 'count', vcount)
voffs = [u32be(871190 + i*4) for i in range(vcount)]
print('min', min(voffs), 'max', max(voffs))
print('first 15:', voffs[:15])
print('last 5:', voffs[-5:])

# audio stco @1756381: size@1756381, type@1756385, ver@1756389, count@1756393
print('\n=== AUDIO stco ===')
asize = u32be(1756381)
acount = u32be(1756393)
print('size', asize, 'count', acount)
aoffs = [u32be(1756397 + i*4) for i in range(acount)]
print('min', min(aoffs), 'max', max(aoffs))
print('first 15:', aoffs[:15])
print('last 5:', aoffs[-5:])

# check: are video offsets pointing inside mdat (1797893..55068909)?
print('\n=== VIDEO offsets vs mdat range [1797893, 55068909] ===')
inmdat = sum(1 for o in voffs if 1797893 <= o < 55068909)
print('video chunks inside mdat:', inmdat, '/', len(voffs))
outside = [o for o in voffs if not (1797893 <= o < 55068909)]
print('video chunks OUTSIDE mdat:', len(outside), 'examples:', outside[:10])

print('\n=== AUDIO offsets vs mdat range ===')
ainmdat = sum(1 for o in aoffs if 1797893 <= o < 55068909)
print('audio chunks inside mdat:', ainmdat, '/', len(aoffs))
aoutside = [o for o in aoffs if not (1797893 <= o < 55068909)]
print('audio chunks OUTSIDE mdat:', len(aoutside), 'examples:', aoutside[:10])
