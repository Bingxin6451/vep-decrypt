#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, hashlib
from Crypto.Cipher import AES

K16 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee6')
P = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')
FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
hdr = data[0:16]

# AES-256 candidates
keys256 = {
    'P+P': P + P,
    'P+hdr': P + hdr,
    'hdr+P': hdr + P,
    'P+md5(P)': P + hashlib.md5(P).digest(),
    'md5(P)+P': hashlib.md5(P).digest() + P,
}
found = False
for name, k in keys256.items():
    for init in [0, 1, 673, 18727, 81920]:
        for le in [False, True]:
            from Crypto.Util import Counter
            try:
                ctr = Counter.new(128, initial_value=init, prefix=b'\x00'*8, little_endian=le)
                c = AES.new(k, AES.MODE_CTR, counter=ctr)
                if c.encrypt(bytes(16)) == K16:
                    print('*** AES256-CTR MATCH', name, init, le)
                    found = True
            except Exception:
                pass

# hash-chain: K[i*16:(i+1)*16] = MD5(P || counter) or SHA256(P||counter)[:16]
for hname in ['md5', 'sha1', 'sha256']:
    h = getattr(hashlib, hname)
    for ctr_fmt in ['le', 'be', 'ascii']:
        for start in [0, 1]:
            block = bytearray()
            ok = True
            for i in range(start, start+1):
                if ctr_fmt == 'le':
                    ctr = struct.pack('<I', i)
                elif ctr_fmt == 'be':
                    ctr = struct.pack('>I', i)
                else:
                    ctr = str(i).encode()
                d = h(P + ctr).digest()
                block += d
            if block[:16] == K16:
                print('*** HASH CHAIN MATCH', hname, ctr_fmt, start)
                found = True

# K = HMAC(P, counter)
import hmac
for start in [0, 1, 673, 18727]:
    for ctr_fmt in ['le', 'be']:
        ctr = struct.pack('<I' if ctr_fmt=='le' else '>I', start)
        d = hmac.new(P, ctr, hashlib.sha256).digest()
        if d[:16] == K16:
            print('*** HMAC MATCH', start, ctr_fmt)
            found = True

# ChaCha20-like via AES? Try Salsa20 unavailable. Try AES-CTR with nonce = hdr[:8]
try:
    from Crypto.Cipher import ChaCha20
    for key in [P, P+b'\x00'*16, hashlib.sha256(P).digest()]:
        for nonce in [b'\x00'*8, b'\x00'*12, hdr[:8]]:
            try:
                c = ChaCha20.new(key=key, nonce=nonce[:8] if len(nonce)>=8 else nonce+b'\x00'*8)
                if c.encrypt(bytes(16)) == K16:
                    print('*** ChaCha20 MATCH')
                    found = True
            except Exception:
                pass
except ImportError:
    print('ChaCha20 not available')

if not found:
    print('no match (AES256, hash-chain, HMAC, ChaCha20)')
print('K16 =', K16.hex())
