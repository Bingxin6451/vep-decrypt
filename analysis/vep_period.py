#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# Known plaintext -> recovered XOR key positions (certain ones only)
key = {}
ftyp24 = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')
def setk(pos, pt):
    for i, b in enumerate(pt):
        key[pos+i] = enc[pos+i] ^ b

setk(0, ftyp24)
setk(28, b'moov')
setk(32, struct.pack('>I', 0x6c))
setk(36, b'mvhd')
setk(40, b'\x00'*4)
setk(60, struct.pack('>I', 0x00010000))
setk(64, b'\x01\x00\x00\x00')
setk(68, b'\x00'*4)
setk(72, struct.pack('>I', 0x00010000))
setk(104, struct.pack('>I', 0x40000000))
setk(108, b'\x00'*24)

positions = sorted(key.keys())
print('known positions count:', len(positions), 'max', max(positions))

# Test period L: key[i] == key[i mod L] must hold for all known i
# Only meaningful for L <= max_pos where at least some i >= L
found_periods = []
for L in range(1, 140):
    ok = True
    checks = 0
    for i in positions:
        r = i % L
        if r != i and r in key:
            checks += 1
            if key[i] != key[r]:
                ok = False
                break
    if ok and checks >= 8:
        found_periods.append((L, checks))

print('candidate periods (L, checks):', found_periods[:20])

# Also test if key is NOT periodic: print key values for visual inspection
print('\nkey[0:44]:', bytes(key[i] for i in range(44)).hex())
