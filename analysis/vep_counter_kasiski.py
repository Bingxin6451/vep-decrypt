#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, hashlib
from Crypto.Cipher import AES

key = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')
target16 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee6')

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
hdr = data[0:16]

# Build a comprehensive list of 16-byte counter block candidates
blocks = []
# zeros with counter in various positions/endianness
for pos in [0, 4, 8, 12]:
    for val in [0, 1, 673, 18727, 81920]:
        for bo in ['be', 'le']:
            b = bytearray(16)
            b[pos:pos+4] = struct.pack('>I' if bo=='be' else '<I', val)
            blocks.append(('ctr_pos%d_%s_%d' % (pos, bo, val), bytes(b)))
# header-derived
blocks.append(('hdr16', hdr))
blocks.append(('hdr16_rev', hdr[::-1]))
blocks.append(('CRYP000', b'CRYP' + b'\x00'*12))
blocks.append(('vep000', b'vep.' + b'\x00'*12))
blocks.append(('md5_hdr', hashlib.md5(hdr).digest()))
blocks.append(('sha256_hdr16', hashlib.sha256(hdr).digest()[:16]))
# params combos
for a in [673, 18727, 81920, 158, 32, 190, 347]:
    blocks.append(('param_%d_be' % a, struct.pack('>I', a) + b'\x00'*12))
    blocks.append(('param_%d_le' % a, struct.pack('<I', a) + b'\x00'*12))

found = False
for name, blk in blocks:
    enc = AES.new(key, AES.MODE_ECB).encrypt(blk)
    if enc == target16:
        print('*** AES-ECB ENCRYPT MATCH:', name)
        found = True
    dec = AES.new(key, AES.MODE_ECB).decrypt(blk)
    if dec == target16:
        print('*** AES-ECB DECRYPT MATCH:', name)
        found = True

if not found:
    print('no match among', len(blocks), 'counter blocks')

# Also: try the tail 16-byte key as an SM4 key via gmssl if available
try:
    from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
    for name, blk in blocks[:20]:
        c = CryptSM4()
        c.set_key(key, SM4_ENCRYPT)
        e = c.crypt_ecb(blk)
        if e == target16:
            print('*** SM4-ECB ENCRYPT MATCH:', name)
            found = True
    print('sm4 ecb tested')
except ImportError:
    print('gmssl sm4 not available')

# Kasiski analysis on auth block
auth = data[55069173:55069520]
print('\n=== Kasiski on auth block ===')
def find_repeats(seq, minlen=4):
    reps = {}
    for L in range(minlen, 30):
        for i in range(len(seq)-L):
            pat = seq[i:i+L]
            for j in range(i+L, len(seq)-L+1):
                if seq[j:j+L] == pat:
                    reps.setdefault(pat.hex(), []).append((i, j, j-i))
    return reps

reps = find_repeats(auth, 5)
dists = []
for pat, occ in reps.items():
    for i, j, d in occ[:4]:
        dists.append(d)
from math import gcd
g = 0
for d in dists:
    g = gcd(g, d)
print('repeat distances:', sorted(set(dists)))
print('gcd of all distances:', g)
