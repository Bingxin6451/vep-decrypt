#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# Build full mvhd plaintext (version 0), creation/modification ~ Aug 2026
def build_mvhd(ctime, mtime, ts=1000, dur=4803000):
    pt = bytearray()
    pt += struct.pack('>I', 108) + b'mvhd' + bytes(4)
    pt += struct.pack('>I', ctime) + struct.pack('>I', mtime)
    pt += struct.pack('>I', ts) + struct.pack('>I', dur)
    pt += struct.pack('>I', 0x00010000)  # rate
    pt += bytes.fromhex('0100') + bytes(2) + bytes(8)  # volume + reserved
    # matrix
    pt += struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x40000000)
    pt += bytes(24)  # pre_defined
    pt += struct.pack('>I', 2)  # next_track_ID
    return bytes(pt)

# keystream [0:32] already known (ftyp + moov)
ks = bytearray()
ks += bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')  # 0:24
ks += bytes.fromhex('c7eb92323d300c7c')  # 24:32 (moov size+type)
# mvhd at enc offset 32
mvhd_pt = build_mvhd(0x6A7A0000, 0x6A7A0000)
mvhd_ct = enc[32:32+108]
ks += bytes(a ^ b for a, b in zip(mvhd_ct, mvhd_pt))
ks = bytes(ks)
print('keystream [0:140]:')
for i in range(0, 140, 16):
    print(f'  {i:4d}: {ks[i:i+16].hex()}')

# autocorrelation search for period
def autocorr(seq, period):
    n = len(seq) - period
    if n <= 0: return None
    matches = sum(1 for i in range(n) if seq[i] == seq[i+period])
    return matches / n

print('\nautocorrelation (byte equality rate) for candidate periods:')
for p in [8, 16, 24, 25, 32, 40, 48, 50, 64, 75, 80, 100, 128]:
    r = autocorr(ks, p)
    print(f'  period {p:3d}: {r:.3f}')
