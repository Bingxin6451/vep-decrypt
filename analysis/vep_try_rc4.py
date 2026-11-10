#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib

key_known = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')

def rc4(key):
    S = list(range(256))
    j = 0
    klen = len(key)
    for i in range(256):
        j = (j + S[i] + key[i % klen]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for _ in range(64):
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(S[(S[i] + S[j]) % 256])
    return bytes(out)

candidates = [
    b'dahuangfeng', b'dhf', b'DHF', b'HBPlayer', b'hbplayer', b'vep', b'CRYP',
    b'dhf123456', b'123456', b'12345678', b'888888', b'666666',
    b'2024', b'2025', b'2026',
    '大黄蜂'.encode('utf-8'), '大黄蜂'.encode('gbk'),
    b'dahuangfeng2024', b'dhf2024', b'dhf2025',
]

# also derived keys via hash
extra = []
for s in [b'dahuangfeng', b'HBPlayer', b'CRYP', '大黄蜂'.encode('utf-8'), b'vep']:
    extra.append(hashlib.md5(s).digest())
    extra.append(hashlib.sha1(s).digest()[:16])
    extra.append(hashlib.sha256(s).digest()[:16])
candidates += extra

for k in candidates:
    stream = rc4(k)
    if stream[:len(key_known)] == key_known:
        print('*** RC4 MATCH key=', k, '***')
        break
else:
    print('no RC4 match among', len(candidates), 'candidates')

# Also test: maybe key stream is XOR of two PRNGs, or AES. Print first bytes of
# rc4 with a few keys for reference
for k in [b'dahuangfeng', '大黄蜂'.encode('utf-8'), b'123456']:
    print('rc4(', k, ')[:24] =', rc4(k)[:24].hex())
print('target                  =', key_known.hex())
