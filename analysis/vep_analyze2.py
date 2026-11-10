#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
N = len(data)

def u32(off):
    return struct.unpack('<I', data[off:off+4])[0]

# 1) index table region: 81936 .. 579362 (start of stss size field)
region_start = 81936
region_end = 579362
print('index region: 0x%x .. 0x%x, len=%d' % (region_start, region_end, region_end-region_start))

# dump first 256 bytes raw
print('--- first 256 bytes raw ---')
print(data[region_start:region_start+256].hex(' '))

# 2) analyze video stbl atoms precisely
print('\n--- video stbl atoms (recheck sizes at atom start) ---')
# stss: size field at 579362
for name, szoff in [('stss', 579362), ('stsc', 580602), ('stsz', 580654), ('stco', 871174)]:
    size = struct.unpack('>I', data[szoff:szoff+4])[0]
    typ = data[szoff+4:szoff+8]
    print('%s @%d size=%d end=%d' % (name, szoff, size, szoff+size))
    # header byte (full box version+flags)
    print('   ver/flags:', data[szoff+8:szoff+12].hex(' '))

# stsc contents (full dump, it's only 52 bytes)
print('\n--- stsc full hex ---')
print(data[580602:580654].hex(' '))
print('--- stsc parsed as (first_chunk, samples_per_chunk, sdi) ---')
off = 580606
v = data[off+4]
n = struct.unpack('>I', data[off+4+4:off+4+8])[0]
print('ver', v, 'entries', n)
for k in range(n):
    e = struct.unpack('>III', data[off+8+k*12: off+8+k*12+12])
    print('  entry', k, e)
# try alternate parse: maybe it's stsd-like or the '52' size includes padding
