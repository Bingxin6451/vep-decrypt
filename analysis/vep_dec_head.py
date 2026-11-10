#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# Recover keystream [0:140] (same as vep_ks4)
ks = bytearray()
ks += bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')
ks += bytes.fromhex('c7eb92323d300c7c')
def build_mvhd(ctime, mtime, ts=1000, dur=4803000):
    pt = bytearray()
    pt += struct.pack('>I', 108) + b'mvhd' + bytes(4)
    pt += struct.pack('>I', ctime) + struct.pack('>I', mtime)
    pt += struct.pack('>I', ts) + struct.pack('>I', dur)
    pt += struct.pack('>I', 0x00010000)
    pt += bytes.fromhex('0100') + bytes(2) + bytes(8)
    pt += struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x40000000)
    pt += bytes(24) + struct.pack('>I', 2)
    return bytes(pt)
mvhd_pt = build_mvhd(0x6A7A0000, 0x6A7A0000)
ks += bytes(a ^ b for a, b in zip(enc[32:32+108], mvhd_pt))
ks = bytes(ks)

# decrypt first 200 bytes of enc region and show structure
dec = bytes(a ^ b for a, b in zip(enc[:200], ks))
print('decrypted moov head:')
for i in range(0, 200, 16):
    print(f'  {i:4d}: {dec[i:i+16].hex()}  {dec[i:i+16]!r}')

# parse atoms
def atoms(buf, base=0):
    p = 0
    out = []
    while p + 8 <= len(buf):
        sz = struct.unpack('>I', buf[p:p+4])[0]
        typ = buf[p+4:p+8]
        if sz < 8 or sz > 0x1000000: break
        out.append((base+p, sz, typ))
        p += sz
    return out
print('\natoms:', [(a, s, t) for a, s, t in atoms(dec)])
