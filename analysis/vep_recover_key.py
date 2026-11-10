#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

enc = data[16:16+81920]

# Known plaintext structure hypothesis:
# [0:24] ftyp (24 bytes)
ftyp24 = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')
# [24:28] moov size (unknown low 2 bytes)
# [28:32] "moov"
# [32:36] mvhd size 0x6c
# [36:40] "mvhd"
# [40:44] version+flags 0
# [44:48] creation_time 0
# [48:52] modification_time 0
# [52:56] timescale (unknown)

# Recover key for positions where plaintext is fully known
key = bytearray(64)
for i, b in enumerate(ftyp24):
    key[i] = enc[i] ^ b
key[28] = enc[28] ^ 0x6d
key[29] = enc[29] ^ 0x6f
key[30] = enc[30] ^ 0x6f
key[31] = enc[31] ^ 0x76
key[32] = enc[32] ^ 0x00
key[33] = enc[33] ^ 0x00
key[34] = enc[34] ^ 0x00
key[35] = enc[35] ^ 0x6c
key[36] = enc[36] ^ 0x6d
key[37] = enc[37] ^ 0x76
key[38] = enc[38] ^ 0x68
key[39] = enc[39] ^ 0x64
key[40] = enc[40] ^ 0x00
key[41] = enc[41] ^ 0x00
key[42] = enc[42] ^ 0x00
key[43] = enc[43] ^ 0x00
# creation/modification often 0
key[44] = enc[44] ^ 0x00
key[45] = enc[45] ^ 0x00
key[46] = enc[46] ^ 0x00
key[47] = enc[47] ^ 0x00
key[48] = enc[48] ^ 0x00
key[49] = enc[49] ^ 0x00
key[50] = enc[50] ^ 0x00
key[51] = enc[51] ^ 0x00

print('recovered key[0:52]:')
print(bytes(key[:52]).hex(' '))
print('as groups of 8:')
for i in range(0, 52, 8):
    print(f'  key[{i}:{i+8}] = {bytes(key[i:i+8]).hex(" ")}')

# Check if key shows periodicity. Try to find period by looking for repeated
# patterns in the recovered key bytes.
k = bytes(key[:52])
for period in range(8, 27):
    matches = sum(1 for i in range(52 - period) if k[i] == k[i+period])
    if matches >= 4:
        print(f'candidate period {period}: {matches} matches')

# Also try: is key a repeating pattern of some base key? Check common periods.
# Print key as if it's derived from a PRNG - check consecutive XOR diffs
print('\nkey[0:16]:', bytes(key[:16]).hex(' '))
print('key[16:32]:', bytes(key[16:32]).hex(' '))
print('key[32:48]:', bytes(key[32:48]).hex(' '))
