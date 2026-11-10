#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct
from collections import Counter

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[55068983:]
auth = tail[190:190+347]

# period analysis: find period P where auth[i] == auth[i+P] frequently
print('=== period analysis ===')
for P in [8, 16, 26, 32, 64]:
    same = sum(1 for i in range(len(auth)-P) if auth[i] == auth[i+P])
    print(f'period {P}: {same}/{len(auth)-P} match')

# find exact period by autocorrelation
best = []
for P in range(2, 128):
    same = sum(1 for i in range(len(auth)-P) if auth[i] == auth[i+P])
    best.append((same, P))
best.sort(reverse=True)
print('top periods by autocorr:', best[:10])

# single-byte XOR frequency analysis
print('\n=== single-byte XOR candidates ===')
def score_plaintext(b):
    # score: printable ascii + common chars
    s = 0
    for x in b:
        if 32 <= x <= 126:
            s += 1
        elif x in (9, 10, 13):
            s += 1
    return s

results = []
for k in range(256):
    dec = bytes(x ^ k for x in auth)
    sc = score_plaintext(dec)
    results.append((sc, k, dec))
results.sort(reverse=True)
for sc, k, dec in results[:8]:
    print(f'key=0x{k:02x} score={sc}/{len(auth)}: {repr(dec[:60])}')
