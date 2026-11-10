#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# Build a known-plaintext map for the header (assuming ftyp + moov with mvhd v0 + video trak)
pt = {}
def setpt(pos, b):
    for i, x in enumerate(b):
        pt[pos+i] = x

setpt(0, bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32'))
# moov: size unknown at 24, but "moov" at 28
setpt(28, b'moov')
setpt(32, struct.pack('>I', 0x6c))   # mvhd size 108
setpt(36, b'mvhd')
setpt(40, b'\x00'*4)                  # version+flags
setpt(44, b'\x00'*8)                  # creation+modification (assume 0)
# timescale@52, duration@56 unknown
setpt(60, struct.pack('>I', 0x00010000))  # rate
setpt(64, b'\x01\x00\x00\x00')        # volume
setpt(68, b'\x00'*4)                  # reserved
setpt(72, struct.pack('>I', 0x00010000))  # matrix a
setpt(88, struct.pack('>I', 0x00010000))  # matrix b
setpt(104, struct.pack('>I', 0x40000000)) # matrix u
setpt(108, b'\x00'*24)                # pre_defined
setpt(132, struct.pack('>I', 2))      # next_track_ID (2 tracks)

# K = enc ^ pt
K = {}
for pos, p in pt.items():
    K[pos] = enc[pos] ^ p

positions = sorted(K.keys())
print('known K positions:', len(positions), 'range', positions[0], '..', positions[-1])
for i in range(0, 140, 16):
    row = ' '.join(f'{K.get(j, 0):02x}' if j in K else '..' for j in range(i, min(i+16, 140)))
    print(f'K[{i:3d}] {row}')

# Period test on known positions
print('\n=== period search (using known positions) ===')
for L in range(1, 140):
    ok = True
    checks = 0
    for i in positions:
        r = i % L
        if r != i and r in K:
            checks += 1
            if K[i] != K[r]:
                ok = False
                break
    if ok and checks >= 10:
        print('candidate period', L, 'checks', checks)

# Check: even/odd position structure
print('\nK even positions:', ' '.join(f'{K.get(i, 0):02x}' if i in K else '..' for i in range(0, 40, 2)))
print('K odd positions :', ' '.join(f'{K.get(i, 0):02x}' if i in K else '..' for i in range(1, 40, 2)))
