#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, hashlib
from Crypto.Cipher import AES, ARC4, ChaCha20

TARGET = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')
P = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')

candidates = []
# direct keys
candidates.append(('P', P))
candidates.append(('MD5(P)', hashlib.md5(P).digest()))
candidates.append(('SHA1(P)[:16]', hashlib.sha1(P).digest()[:16]))
candidates.append(('SHA256(P)[:16]', hashlib.sha256(P).digest()[:16]))
# P combined with 673 / 18727
for label, extra in [
    ('673_le', struct.pack('<I', 673)), ('673_be', struct.pack('>I', 673)),
    ('18727_le', struct.pack('<I', 18727)), ('18727_be', struct.pack('>I', 18727)),
    ('673_18727_le', struct.pack('<II', 673, 18727)),
]:
    candidates.append((f'MD5(P+{label})', hashlib.md5(P + extra).digest()))
    candidates.append((f'SHA256(P+{label})[:16]', hashlib.sha256(P + extra).digest()[:16]))
    candidates.append((f'MD5({label}+P)', hashlib.md5(extra + P).digest()))
# P repeated / padded to 32 bytes
candidates.append(('P*2', P*2))
candidates.append(('P+8zero', P + bytes(8)))
candidates.append(('8zero+P', bytes(8) + P))
candidates.append(('SHA256(P)', hashlib.sha256(P).digest()))

print('== RC4 tests ==')
for name, key in candidates:
    if len(key) < 5:
        continue
    out = ARC4.new(key).encrypt(bytes(24))
    if out == TARGET:
        print(f'  RC4({name}) MATCH!')
    elif out[:2] == TARGET[:2]:
        print(f'  RC4({name}) first2 match: {out.hex()}')

print('== AES-CTR tests (nonce=0, counter from 0) ==')
from Crypto.Util import Counter
for name, key in candidates:
    if len(key) != 16: continue
    for ctr_init in [0, 1]:
        ctr = Counter.new(128, initial_value=ctr_init)
        out = AES.new(key, AES.MODE_CTR, counter=ctr).encrypt(bytes(24))
        if out == TARGET:
            print(f'  AES-CTR({name}, ctr0={ctr_init}) MATCH!')
        elif out[:2] == TARGET[:2]:
            print(f'  AES-CTR({name}, ctr0={ctr_init}) first2: {out.hex()}')

print('== AES-OFB/CFB (IV=0) ==')
for name, key in candidates:
    if len(key) != 16: continue
    for mode in [AES.MODE_OFB, AES.MODE_CFB]:
        out = AES.new(key, mode, iv=bytes(16)).encrypt(bytes(24))
        if out == TARGET:
            print(f'  AES-{mode}({name}) MATCH!')

print('== ChaCha20 (32-byte keys) ==')
for name, key in candidates:
    if len(key) != 32: continue
    for nlabel, nonce in [('0', bytes(8)), ('673_le', struct.pack('<I',673)+bytes(4)), ('18727_le', struct.pack('<I',18727)+bytes(4))]:
        out = ChaCha20.new(key=key, nonce=nonce).encrypt(bytes(24))
        if out == TARGET:
            print(f'  ChaCha20({name}, nonce={nlabel}) MATCH!')

print('done')
