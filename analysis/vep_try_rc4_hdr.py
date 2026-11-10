#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
header = data[0:16]
target24 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')

def rc4(key, n=64):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for _ in range(n):
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(S[(S[i] + S[j]) % 256])
    return bytes(out)

candidates = [
    ('header16', header),
    ('CRYP', b'CRYP'),
    ('header8', header[:8]),
    ('hdr_params_le', struct.pack('<III', 81920, 673, 18727)),
    ('params_le_81920', struct.pack('<I', 81920)),
    ('params_le_673', struct.pack('<I', 673)),
    ('params_le_18727', struct.pack('<I', 18727)),
    ('param_bytes', bytes([0x00,0x40,0x01,0x00,0xa1,0x02,0x00,0x00,0x27,0x49,0x00,0x00])),
    ('param12', header[4:16]),
]
for name, k in candidates:
    if len(k) == 0:
        continue
    s = rc4(k)
    if s[:24] == target24:
        print('*** RC4 MATCH', name)
    else:
        print(f'rc4({name})[:8] = {s[:8].hex()}')

print('target[:8] =', target24[:8].hex())
