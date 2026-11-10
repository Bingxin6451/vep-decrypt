#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, hashlib
from Crypto.Cipher import AES

target16 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee6')

def aes_ctr_stream(key, nonce_bytes, nblocks):
    # build counter blocks and encrypt
    out = bytearray()
    for i in range(nblocks):
        ctr = nonce_bytes + struct.pack('>I', i)
        if len(ctr) != 16:
            ctr = (nonce_bytes + struct.pack('>I', i))[:16]
        enc = AES.new(key, AES.MODE_ECB).encrypt(ctr)
        out += enc
    return bytes(out)

keys = []
for s in [b'dahuangfeng', b'HBPlayer', b'CRYP', '大黄蜂'.encode('utf-8'), b'vep', b'dhf', b'huangfeng']:
    keys.append((f'md5({s})', hashlib.md5(s).digest()))
    keys.append((f'sha256({s})[:16]', hashlib.sha256(s).digest()[:16]))
keys += [
    ('zeros', b'\x00'*16),
    ('ones', b'\xff'*16),
    ('1234567890abcdef', b'1234567890abcdef'),
    ('0123456789abcdef', b'0123456789abcdef'),
]

nonces = [
    ('zero', b'\x00'*8),
    ('zero12', b'\x00'*12),
    ('zero4', b'\x00'*4),
    ('header4', b'CRYP'),
    ('param673', struct.pack('>I', 673) + b'\x00'*12),
    ('param18727', struct.pack('>I', 18727) + b'\x00'*12),
    ('param81920', struct.pack('>I', 81920) + b'\x00'*12),
]

found = False
for kname, key in keys:
    for nname, nonce in nonces:
        # try counter width = remaining bytes
        for nonce_len in [8, 12]:
            n = nonce[:nonce_len]
            nblocks = 1
            # build counter: nonce (nonce_len) + counter (16-nonce_len)
            ctr = n + b'\x00'*(16-nonce_len)
            try:
                stream = AES.new(key, AES.MODE_ECB).encrypt(ctr)
            except Exception:
                continue
            if stream[:16] == target16:
                print('*** AES MATCH key=', kname, 'nonce=', nname, 'nonce_len', nonce_len)
                found = True

if not found:
    print('no AES-CTR match')
print('target16:', target16.hex())
