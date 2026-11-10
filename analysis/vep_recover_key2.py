#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# Known plaintext map (offset -> value), assuming ftyp24 + moov + mvhd (ver 0)
# plaintext layout:
# 0:24 ftyp
# 24:28 moov size (unknown)
# 28:32 'moov'
# 32:36 mvhd size 0x6c
# 36:40 'mvhd'
# 40:44 version+flags 0
# 44:48 creation_time (assume 0)
# 48:52 modification_time (assume 0)
# 52:56 timescale (unknown, guess 1000)
# 56:60 duration (unknown)
# 60:64 rate 0x00010000
# 64:68 volume 0x01000000
# 68:72 reserved 0
# 72:108 matrix (mostly 0, with 0x00010000 at [72:76] and [88:92], 0x40000000 at [104:108])
# 108:132 pre_defined 0 (24 bytes)

ftyp24 = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')

key = bytearray(200)

def set_key(pos, pt_bytes):
    for i, b in enumerate(pt_bytes):
        key[pos+i] = enc[pos+i] ^ b

set_key(0, ftyp24)
set_key(28, b'moov')
set_key(32, struct.pack('>I', 0x6c))
set_key(36, b'mvhd')
set_key(40, b'\x00'*4)
set_key(44, b'\x00'*8)  # creation + modification
set_key(60, struct.pack('>I', 0x00010000))  # rate
set_key(64, b'\x01\x00\x00\x00')  # volume
set_key(68, b'\x00'*4)  # reserved
# matrix
set_key(72, struct.pack('>I', 0x00010000))
set_key(88, struct.pack('>I', 0x00010000))
set_key(104, struct.pack('>I', 0x40000000))
set_key(108, b'\x00'*24)  # pre_defined

# print recovered key bytes
print('recovered key (positions 0-131):')
for i in range(0, 132, 16):
    row = ' '.join(f'{key[j]:02x}' if key[j] else '..' for j in range(i, min(i+16, 132)))
    print(f'  [{i:3d}] {row}')

# Check u32 structure of the key stream (little-endian)
print('\nkey as LE u32 (only fully-known runs):')
print('key[0:24]:', bytes(key[0:24]).hex())
print('key[28:52]:', bytes(key[28:52]).hex())
print('key[60:76]:', bytes(key[60:76]).hex())
print('key[88:92]:', bytes(key[88:92]).hex())
print('key[104:132]:', bytes(key[104:132]).hex())

# Test: is the key stream = repeated fixed pattern with period 673 or 18727?
# compare key[0:24] with key at later positions via known overlaps
# We have key[0:24] and key[28:52]. If period P, key[28:52] == key[28%P : 28%P+24]
# Try to find P such that key[i] == key[i+P] for known positions
known = {i: key[i] for i in range(200) if i not in (24,25,26,27, 52,53,54,55, 56,57,58,59)}
print('\nknown key positions:', sorted(known.keys()))

# brute force period check
for P in range(1, 132):
    ok = True
    cnt = 0
    for i in known:
        if i + P in known and key[i] != key[i+P]:
            ok = False
            break
        if i + P in known:
            cnt += 1
    if ok and cnt >= 5:
        print(f'possible period {P} with {cnt} consistent checks')
