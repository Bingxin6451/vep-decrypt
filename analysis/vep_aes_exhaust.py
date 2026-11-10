#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, hashlib
from Crypto.Cipher import AES
from Crypto.Util import Counter

K16 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee6')
P = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')
b64s = b'tkEDoksW0UPyQWR8O4ynPg=='
b64outer = b'dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09'

# key candidates
keys = {}
keys['P'] = P
keys['md5(P)'] = hashlib.md5(P).digest()
keys['sha1(P)16'] = hashlib.sha1(P).digest()[:16]
keys['sha256(P)16'] = hashlib.sha256(P).digest()[:16]
keys['md5(b64s)'] = hashlib.md5(b64s).digest()
keys['md5(b64outer)'] = hashlib.md5(b64outer).digest()
keys['sha256(b64s)16'] = hashlib.sha256(b64s).digest()[:16]
keys['P^md5(P)'] = bytes(a^b for a,b in zip(P, hashlib.md5(P).digest()))
keys['P+zeros16'] = P
keys['zeros'] = b'\x00'*16
keys['CRYP000'] = b'CRYP' + b'\x00'*12
keys['md5(vep.)'] = hashlib.md5(b'vep.').digest()

found = False
for kname, key in keys.items():
    if len(key) != 16:
        continue
    # exhaustive CTR layouts
    for prefix_len in range(0, 17, 4):
        for init in [0, 1, 673, 18727, 81920]:
            for le in [False, True]:
                try:
                    ctr = Counter.new(128, initial_value=init, prefix=b'\x00'*prefix_len, little_endian=le)
                    c = AES.new(key, AES.MODE_CTR, counter=ctr)
                    if c.encrypt(bytes(16)) == K16:
                        print('*** CTR MATCH', kname, 'prefix', prefix_len, 'init', init, 'le', le)
                        found = True
                except Exception:
                    pass
    # CFB/OFB with various IVs
    for iv in [b'\x00'*16, b'\x00'*8+b'\x01'*8, struct.pack('<I',673)+b'\x00'*12, struct.pack('<I',18727)+b'\x00'*12]:
        for mode in [AES.MODE_CFB, AES.MODE_OFB]:
            try:
                c = AES.new(key, mode, iv, segment_size=128)
                if c.encrypt(bytes(16)) == K16:
                    print('*** CFB/OFB MATCH', kname, mode, 'iv', iv.hex())
                    found = True
            except Exception:
                pass

if not found:
    print('no match. tested', len(keys), 'keys x full CTR/CFB/OFB layouts')
print('K16 =', K16.hex())
