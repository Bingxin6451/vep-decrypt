#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# Test hypothesis: plaintext[673:] is stts atom (size 18727 = 0x4927, type "stts")
# If true, key[673:681] = enc XOR (00 00 49 27 "stts")
# Then plaintext[681:689] = version+flags(4) + entry_count(4)
# stts entry_count must divide total samples 72625 into entries.
# Recover key via stts structure, then TEST if the recovered key stream is CONSISTENT
# with the key recovered from ftyp/moov by checking for a common PRNG/period.

# Build full known plaintext hypothesis:
pt = bytearray(81920)
pt[0:24] = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')
# moov at 24
pt[28:32] = b'moov'
pt[32:36] = struct.pack('>I', 0x6c)  # mvhd size
pt[36:40] = b'mvhd'
pt[40:44] = b'\x00'*4  # version+flags
# leave creation/modification/timescale/duration unknown (44:60)
pt[60:64] = struct.pack('>I', 0x00010000)  # rate
pt[64:68] = b'\x01\x00\x00\x00'  # volume
pt[68:72] = b'\x00'*4
pt[72:76] = struct.pack('>I', 0x00010000)  # matrix a
pt[104:108] = struct.pack('>I', 0x40000000)  # matrix u
pt[108:132] = b'\x00'*24
# stts at 673 (hypothesis)
pt[673:677] = struct.pack('>I', 18727)  # stts size
pt[677:681] = b'stts'
pt[681:685] = b'\x00'*4  # version+flags
# entry_count unknown, but stts total = 18727 => entries region = 18727-16 = 18711 bytes
# => 18711/8 = 2338.875, NOT integer! So entry_count*8 must = 18711 -> impossible.
print('CHECK: 18727-16 =', 18727-16, '/8 =', (18727-16)/8)
print('-> NOT divisible by 8! stts size 18727 is IMPOSSIBLE for a valid stts.')
print('So the 18727=stts-length hypothesis is WRONG, or stts size != 18727.')

# stts sizes must satisfy: size = 16 + 8*N. So size in {16+8k}. 18727 = 16+8*2340 = 18736? no.
# 18736 = 16 + 8*2340. 18727 != 18736.
# Therefore 18727 cannot be a stts atom size. Alternative: 18727 = entry_count? 18727 entries?
# 18727*8+16 = 149832 bytes > 81920. No.
print('\n18727 cannot be stts size. Reconsider meanings of 673 and 18727.')
print('673 =? 18727 =?')
print('673*8+16 =', 673*8+16, '-> if 673 were stts entry_count, size =', 673*8+16)
print('18727 could be: 72625*? no; 18727 = total encrypted video chunk bytes? let me check')

# compute total bytes of the 25 encrypted video chunks
def u32be(o): return struct.unpack('>I', data[o:o+4])[0]
vsizes = [u32be(580674+i*4) for i in range(72625)]
def spc(ci):
    if ci == 1: return 8
    if ci <= 10374: return 7
    return 6
enc_chunks = list(range(3826, 3832)) + list(range(7908, 7927))
tot = 0
for ci in enc_chunks:
    start_si = 8 + (ci-2)*7 if ci >= 2 else 0
    n = spc(ci)
    tot += sum(vsizes[start_si:start_si+n])
print('total encrypted video bytes (25 chunks):', tot)
print('81920 +', tot, '=', 81920+tot)
