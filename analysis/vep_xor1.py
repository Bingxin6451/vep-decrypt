#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[len(data)-541:]
auth = tail[190:190+347]

# task-1: best-effort key
best_key = bytes.fromhex('404202071a10040a5010411941684001281000071108040042')
print('best_key len:', len(best_key))

pt = bytes(a ^ best_key[i % len(best_key)] for i, a in enumerate(auth))
print('decrypt with best key:')
print(repr(pt))
print()
print('printable:', sum(1 for b in pt if 32 <= b < 127), '/', len(pt))

# Verify XOR 0x01 relation: auth tail unit XOR 1 == something in auth head
unit = b'2dzfgdzlfg212asifj8()&(#*'
u1 = bytes(b ^ 0x01 for b in unit)
print('\nunit XOR 0x01 =', repr(u1))
# find it in auth
idx = auth.find(u1)
print('found at offset:', idx)
# also check the reverse: does auth head region XOR 1 match unit?
head = auth[18:18+25]
print('auth[18:43] =', repr(head))
print('auth[18:43] XOR 1 =', repr(bytes(b ^ 1 for b in head)))
print('== unit?', bytes(b ^ 1 for b in head) == unit)
