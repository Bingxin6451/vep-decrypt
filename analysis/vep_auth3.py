#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[len(data)-541:]
auth = tail[190:190+347]
P = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')

print('auth block len:', len(auth))
print('auth full repr:')
print(repr(auth))
print()

# 1. period analysis via autocorrelation
def autocorr(seq, p):
    n = len(seq) - p
    if n <= 0: return 0
    return sum(1 for i in range(n) if seq[i] == seq[i+p]) / n

print('autocorrelation:')
for p in [5, 10, 20, 25, 30, 40, 50, 60, 75, 100]:
    print(f'  period {p:3d}: {autocorr(auth, p):.3f}')

# 2. try XOR with P repeated
pt = bytes(a ^ P[i % 16] for i, a in enumerate(auth))
print('\nXOR P-repeat:', repr(pt[:120]))

# 3. try XOR with common strings repeated
for s in ['dahuangfeng', 'HBPlayer', 'vep', 'CRYP']:
    kb = s.encode()
    pt2 = bytes(a ^ kb[i % len(kb)] for i, a in enumerate(auth))
    print(f'\nXOR {s}:', repr(pt2[:120]))
