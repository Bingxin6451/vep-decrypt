#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, hashlib

K = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')
P = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')

def rc4(key, n, drop=0):
    S = list(range(256)); j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for _ in range(n + drop):
        i = (i+1) % 256; j = (j+S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(S[(S[i]+S[j]) % 256])
    return bytes(out[drop:])

# RC4 with various drop counts
for drop in [0, 256, 768, 1024, 3072]:
    s = rc4(P, 24, drop)
    if s == K:
        print('*** RC4(P) drop', drop, 'MATCH')

# RC4 with P + salt
for salt in [b'CRYP', b'vep', b'\x00', struct.pack('<I', 673), struct.pack('<I', 18727),
             struct.pack('<I', 81920), struct.pack('<I', 158), struct.pack('<I', 347)]:
    for combo in [P + salt, salt + P]:
        s = rc4(combo, 24, 0)
        if s == K:
            print('*** RC4(P+salt)', salt, 'MATCH')
        s = rc4(combo, 24, 256)
        if s == K:
            print('*** RC4(P+salt)', salt, 'drop256 MATCH')

# MD5/SHA of P as RC4 key
for hname in ['md5', 'sha1', 'sha256']:
    h = getattr(hashlib, hname)(P).digest()
    for drop in [0, 256]:
        if rc4(h[:16], 24, drop) == K:
            print('*** RC4('+hname+'(P)) drop', drop, 'MATCH')
        if rc4(h, 24, drop) == K:
            print('*** RC4('+hname+'(P) full) drop', drop, 'MATCH')

# Is K itself RC4 output for some key = P reversed etc?
for name, pk in [('P_rev', P[::-1]), ('P_rot', P[8:]+P[:8])]:
    for drop in [0, 256]:
        if rc4(pk, 24, drop) == K:
            print('*** RC4('+name+') drop', drop, 'MATCH')

# XOR difference K^P_cycle as reference
D = bytes(K[i] ^ P[i % 16] for i in range(24))
print('K^P_cycle =', D.hex())
print('md5(P) =', hashlib.md5(P).hexdigest())
print('sha256(P)[:24] =', hashlib.sha256(P).digest()[:24].hex())
print('K =', K.hex())
