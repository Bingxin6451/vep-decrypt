#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from Crypto.Cipher import AES

P = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')
ks = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7ec7eb92323d300c7c33bb83fae438dd90c2c804c3c0bc7fe6')

cipher = AES.new(P, AES.MODE_ECB)
for i in range(0, 48, 16):
    block = ks[i:i+16]
    pt = cipher.decrypt(block)
    print(f'counter block {i//16}: AES_dec(P, ks[{i}:{i+16}]) = {pt.hex()}')

# Also check: is keystream = AES_enc(P, counter) with counter=0,1,2...?
print('\nAES_enc(P, counter) for counter=0,1,2:')
for c in range(3):
    ctr = c.to_bytes(16, 'big')
    print(f'  ctr={c}: {cipher.encrypt(ctr).hex()}')
print('target ks[0:16] =', ks[0:16].hex())
