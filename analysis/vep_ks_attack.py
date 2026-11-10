#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct
from Crypto.Cipher import AES, ARC4, ChaCha20

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

# encrypted region: [16 : 16+81920]
enc = data[16:16+81920]
P = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')

# Known plaintext: ftyp (24 bytes)
ftyp = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')
ks = bytes(a ^ b for a, b in zip(enc[:24], ftyp))
print('keystream[0:24] =', ks.hex())

# test target: does keystream match RC4(P) ?
rc4 = ARC4.new(P)
print('RC4(P) first 24   =', rc4.encrypt(bytes(24)).hex())

# ChaCha20 with nonce = 673, 18727 in various layouts
for label, key, nonce in [
    ('ChaCha(P, nonce=673_le)', P, struct.pack('<I', 673) + bytes(8)),
    ('ChaCha(P, nonce=673_be)', P, struct.pack('>I', 673) + bytes(8)),
    ('ChaCha(P, nonce=18727_le)', P, struct.pack('<I', 18727) + bytes(8)),
    ('ChaCha(P, nonce=18727_be)', P, struct.pack('>I', 18727) + bytes(8)),
    ('ChaCha(P, nonce=673_18727)', P, struct.pack('<II', 673, 18727)),
]:
    try:
        c = ChaCha20.new(key=key, nonce=nonce)
        print(f'{label}: {c.encrypt(bytes(24)).hex()}')
    except Exception as e:
        print(f'{label}: ERR {e}')

# AES-CTR with nonce/counter from 673/18727
from Crypto.Util import Counter
def aes_ctr(key, nonce_bytes, prefix=8):
    ctr = Counter.new(128, initial_value=int.from_bytes(nonce_bytes, 'big'))
    return AES.new(key, AES.MODE_CTR, counter=ctr).encrypt(bytes(24))

for label, nonce_bytes in [
    ('AES-CTR(P, nonce=673_le+8)', struct.pack('<I', 673) + bytes(8)),
    ('AES-CTR(P, nonce=18727_le+8)', struct.pack('<I', 18727) + bytes(8)),
    ('AES-CTR(P, nonce=673_18727)', struct.pack('<II', 673, 18727)),
    ('AES-CTR(P, nonce=8+673_le)', bytes(8) + struct.pack('<I', 673)),
    ('AES-CTR(P, nonce=4+673_le+4)', bytes(4) + struct.pack('<I', 673) + bytes(4)),
    ('AES-CTR(P, nonce=673_be+8)', struct.pack('>I', 673) + bytes(8)),
]:
    try:
        print(f'{label}: {aes_ctr(P, nonce_bytes).hex()}')
    except Exception as e:
        print(f'{label}: ERR {e}')

# Compare with keystream
print()
print('TARGET keystream  =', ks.hex())
print('TARGET == RC4(P)?', ks[:24] == ARC4.new(P).encrypt(bytes(24))[:24])
