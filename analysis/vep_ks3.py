#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# Plaintext of mvhd time fields: try timescale=1000, duration=4803000
for ts, dur in [(1000, 4803000), (90000, 432270000), (1000, 4803), (15360, 73774080)]:
    pt = struct.pack('>I', ts) + struct.pack('>I', dur)
    ct = enc[52:60]
    k = bytes(a ^ b for a, b in zip(ct, pt))
    print(f'ts={ts} dur={dur}: keystream[52:60] = {k.hex()}')

# dump plaintext atom structure after enc region (file offset 81920)
def atom_headers(start, end):
    p = start
    out = []
    while p + 8 <= end:
        sz = struct.unpack('>I', data[p:p+4])[0]
        typ = data[p+4:p+8]
        if typ in (b'stts', b'stss', b'stsz', b'stco', b'stsc', b'stsd', b'avc1', b'mp4a', b'mdia', b'minf', b'stbl', b'dinf', b'edts', b'udta', b'mvhd', b'trak', b'moov', b'mdat', b'tkhd', b'mdhd', b'hdlr', b'vmhd', b'smhd', b'dref', b'esds'):
            out.append((p, sz, typ.decode()))
        if sz == 0: break
        p += sz
    return out

print('\natom structure from 81920 (first 40000 bytes):')
for a in atom_headers(81920, 81920+40000):
    print(f'  file {a[0]} size {a[1]} type {a[2]}')
