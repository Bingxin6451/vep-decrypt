#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random, struct

# recovered key bytes (certain ones from ftyp)
key_known = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')

def test_seed(seed_val, label):
    r = random.Random(seed_val)
    # generate bytes: use getrandbits(32) little-endian like many C implementations
    gen = bytearray()
    for _ in range(8):
        gen += struct.pack('<I', r.getrandbits(32))
    gen = bytes(gen)
    if gen[:len(key_known)] == key_known:
        print(f'*** MATCH seed={label} ***')
        return True
    # also try big-endian
    return False

# also test: random bytes via randbytes (Python 3.9+)
def test_seed_randbytes(seed_val, label):
    r = random.Random(seed_val)
    gen = r.randbytes(64)
    if gen[:len(key_known)] == key_known:
        print(f'*** MATCH randbytes seed={label} ***')
        return True
    return False

candidates = [0, 1, 673, 18727, 81920, 0x14000, 0x2a1, 0x4927, 16, 55069524, 2024, 2025, 2026]
for c in candidates:
    if test_seed(c, c):
        break
    if test_seed_randbytes(c, c):
        break
else:
    # try combined
    for a in [673, 18727, 81920]:
        for b in [673, 18727, 81920]:
            for comb in [a+b, a*b, a^b, (a<<16)|b, (b<<16)|a]:
                if test_seed(comb, f'comb({a},{b})'):
                    break

print('key_known:', key_known.hex())
# print what MT19937 with seed 673 would give, for comparison
r = random.Random(673)
g = bytearray()
for _ in range(6):
    g += struct.pack('<I', r.getrandbits(32))
print('MT19937 seed 673 (LE u32):', g.hex())
