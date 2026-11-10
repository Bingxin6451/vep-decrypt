#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, base64, re

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[len(data)-541:]
auth = tail[190:190+347]

best_key = bytes.fromhex('404202071a10040a5010411941684001281000071108040042')
pt = bytes(a ^ best_key[i % 25] for i, a in enumerate(auth))
print('decrypted auth (best key):')
print(repr(pt))
print()
s = pt.decode('latin1')
# base64 runs
runs = re.findall(r'[A-Za-z0-9+/=]{6,}', s)
print('base64 runs:')
for r in runs:
    pad = '=' * ((4 - len(r) % 4) % 4)
    try:
        d = base64.b64decode(r + pad)
        print(f'  {r!r} -> {d.hex()}  {d!r}')
    except Exception as e:
        print(f'  {r!r} -> fail {e}')

# The repeating tail unit
unit = b'reRvgckdbgpqpctsvn2x9g1bB'
print('\ntail unit b64 decode:', base64.b64decode(unit + b'===').hex())
