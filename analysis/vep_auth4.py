#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[len(data)-541:]
auth = tail[190:190+347]

# candidate key = the 25-byte repeating unit at the tail
unit = b'2dzfgdzlfg212asifj8()&(#*'
print('unit len:', len(unit), repr(unit))

# decrypt whole auth with unit repeated
pt = bytes(a ^ unit[i % 25] for i, a in enumerate(auth))
print('XOR unit-repeat plaintext:')
print(repr(pt))
print()
print('printable ratio:', sum(1 for b in pt if 32 <= b < 127) / len(pt))
