#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, hashlib, itertools

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]
ftyp = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')
P = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')

# candidate keys for cyclic XOR
candidates = []
# single params
for v in [673, 18727, 81920, 158, 32, 190, 347]:
    candidates.append(('u32le_%d' % v, struct.pack('<I', v)))
    candidates.append(('u32be_%d' % v, struct.pack('>I', v)))
# param pairs / triples
candidates.append(('673+18727_le', struct.pack('<II', 673, 18727)))
candidates.append(('18727+673_le', struct.pack('<II', 18727, 673)))
candidates.append(('3params_le', struct.pack('<III', 81920, 673, 18727)))
# header-derived
candidates.append(('CRYP', b'CRYP'))
candidates.append(('vep.', b'vep.'))
candidates.append(('hdr16', data[0:16]))
# P and transforms
candidates.append(('P', P))
candidates.append(('P_rev', P[::-1]))
candidates.append(('P_md5', hashlib.md5(P).digest()))
candidates.append(('P_sha1_16', hashlib.sha1(P).digest()[:16]))
candidates.append(('P_sha256_16', hashlib.sha256(P).digest()[:16]))
candidates.append(('P_b64_1', b'tkEDoksW0UPyQWR8O4ynPg=='))
candidates.append(('P_b64_2', b'dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09'))
# XOR combinations of P with params
for v in [673, 18727, 81920]:
    candidates.append(('P_xor_u32le_%d' % v, bytes(a ^ b for a, b in zip(P, struct.pack('<I', v) * 4))))
# hex strings of params
candidates.append(('str673', b'673'))
candidates.append(('str18727', b'18727'))

for name, key in candidates:
    if len(key) == 0:
        continue
    dec = bytes(enc[i] ^ key[i % len(key)] for i in range(24))
    if dec == ftyp:
        print('*** CYCLIC XOR MATCH:', name, 'keylen', len(key))
        break
else:
    print('no cyclic XOR match among', len(candidates), 'candidates')

# Also: is K a repeating pattern with period 673/18727? Test via known K positions only.
# We only know K[0:24], K[28:32], K[32:36]... too sparse. Skip.

# Print what XOR with "P" gives for first 24 bytes (reference)
print('enc ^ P[:24]:', bytes(enc[i] ^ P[i % 16] for i in range(24)).hex())
