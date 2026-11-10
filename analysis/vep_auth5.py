#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, base64

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[len(data)-541:]
auth = tail[190:190+347]

# key derived from tail unit (ciphertext ^ plaintext of repeating unit)
key = bytes.fromhex('4001281000071108040042404202071a10040a501041194168')
print('key len:', len(key), key.hex())

pt = bytes(a ^ key[i % 25] for i, a in enumerate(auth))
print('decrypted auth:')
print(repr(pt))
print()
print('printable:', sum(1 for b in pt if 32 <= b < 127), '/', len(pt))

# try to find base64 segments
import re
s = pt.decode('latin1')
# extract printable runs
runs = re.findall(r'[A-Za-z0-9+/=]{8,}', s)
print('\nbase64-like runs:')
for r in runs:
    print('  ', r)
    # try decode
    try:
        d = base64.b64decode(r + '=' * ((4 - len(r) % 4) % 4))
        print('      decoded:', d.hex(), repr(d))
    except Exception as e:
        print('      decode fail:', e)
