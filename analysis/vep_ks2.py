#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]  # encrypted region

# Verify plaintext boundary
print('enc region end [81920-16:] file offset 81920:', data[81920:81940].hex())
print('file offset 81920 as chars:', data[81920:81940])

# Check mdat location
print('file 1797897:', data[1797897:1797905].hex())

# Known plaintext map: encrypt_offset -> bytes
known = {}
# ftyp
known[0] = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')
# moov: size (guess 1797857 = 0x1B6F61) + 'moov'
known[24] = struct.pack('>I', 1797857) + b'moov'
# mvhd: size 108 + 'mvhd' + version_flags(0)
known[32] = struct.pack('>I', 108) + b'mvhd' + bytes(4)
# creation/modification times (unknown, skip), timescale/duration unknown
# rate @ 60: 0x00010000, volume 0x0100, reserved
known[60] = struct.pack('>I', 0x00010000) + bytes.fromhex('01000000000000000000')
# matrix @76 (36 bytes): fixed identity + pre_defined 24 zero
matrix = struct.pack('>I', 0x00010000) + bytes(4) + bytes(4) + bytes(4) + struct.pack('>I', 0x00010000) + bytes(4) + bytes(4) + bytes(4) + struct.pack('>I', 0x40000000)
known[76] = matrix + bytes(24)  # + pre_defined

# Recover keystream where known
ks = bytearray()
for off, pt in sorted(known.items()):
    ct = enc[off:off+len(pt)]
    k = bytes(a ^ b for a, b in zip(ct, pt))
    print(f'offset {off:4d}: keystream = {k.hex()}')

# Also try: is 673/18727 file offsets inside encrypted region?
for off in [673, 18727, 673+16, 18727+16]:
    if off < len(data):
        print(f'file[{off}:{off+16}] = {data[off:off+16].hex()}')
