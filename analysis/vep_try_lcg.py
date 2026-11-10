#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

# Known key stream bytes (from ftyp + moov/mvhd known structures)
target = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')

def glibc_rand(seed, n):
    # x_{n+1} = (1103515245 * x + 12345) & 0x7fffffff
    x = seed & 0x7fffffff
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) & 0x7fffffff
        out.append((x >> 16) & 0x7fff)  # glibc rand returns 15 bits
    return out

def msvc_rand(seed, n):
    x = seed & 0xffffffff
    out = []
    for _ in range(n):
        x = (214013 * x + 2531011) & 0xffffffff
        out.append((x >> 16) & 0x7fff)
    return out

def test_stream(name, values, mode):
    # mode: 'lo' low byte, 'hi' high byte, 'le' u32 little-endian, 'be' u32 big-endian
    b = bytearray()
    for v in values:
        if mode == 'lo':
            b.append(v & 0xff)
        elif mode == 'hi':
            b.append((v >> 8) & 0xff)
        elif mode == 'le':
            b += struct.pack('<I', v & 0xffffffff)
        elif mode == 'be':
            b += struct.pack('>I', v & 0xffffffff)
    return bytes(b)

seeds = [673, 18727, 81920, 0x14000, 0x2a1, 0x4927]
for seed in seeds:
    for mode in ['lo', 'hi', 'le', 'be']:
        g = glibc_rand(seed, 24)
        s = test_stream('g', g, mode)
        if s[:24] == target:
            print('*** MATCH glibc seed', seed, 'mode', mode)
        m = msvc_rand(seed, 24)
        s2 = test_stream('m', m, mode)
        if s2[:24] == target:
            print('*** MATCH msvc seed', seed, 'mode', mode)

# also try: simple LCG x = (a*x+c) mod 2^32 with various a,c, taking low byte
# and try seed from header ints combined
print('target:', target.hex())
g = glibc_rand(673, 8)
print('glibc 673 hi bytes:', bytes([v & 0xff for v in g]).hex())
