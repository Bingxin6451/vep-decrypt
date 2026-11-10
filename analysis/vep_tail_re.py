#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, base64

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
n = len(data)
tail = data[n-541:]
print('tail length:', len(tail))
print('tail[0:40]:', tail[0:40].hex())
print('tail[0:40] repr:', repr(tail[0:40]))
print()
print('tail[14:30]:', tail[14:30].hex())
vals = struct.unpack('<4I', tail[14:30])
print('4 params LE:', vals)
vals_be = struct.unpack('>4I', tail[14:30])
print('4 params BE:', vals_be)
print()
# key blob at tail[158:158+32]
blob = tail[158:190]
print('key blob [158:190]:', blob)
print('key blob repr:', repr(blob))
# auth block
auth = tail[190:190+347]
print()
print('auth block [190:537] first 100:', auth[:100].hex())
print('auth block repr:', repr(auth[:100]))
# try single and double base64 decode of blob
for depth, b in [('raw', blob)]:
    print(f'blob {depth}:', repr(b))
try:
    d1 = base64.b64decode(blob)
    print('b64 decode 1:', d1.hex(), repr(d1))
    try:
        d2 = base64.b64decode(d1)
        print('b64 decode 2:', d2.hex(), repr(d2))
    except Exception as e:
        print('b64 decode 2 fail:', e)
except Exception as e:
    print('b64 decode 1 fail:', e)
