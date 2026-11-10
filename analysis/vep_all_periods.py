#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import string, math
from collections import Counter

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
auth = data[55069173:55069520]

B64 = set(string.ascii_letters + string.digits + '+/=')

def entropy(b):
    c = Counter(b); n = len(b)
    return -sum((v/n)*math.log2(v/n) for v in c.values())

def try_period(P):
    key = bytearray(P)
    for col in range(P):
        samples = [auth[i] for i in range(col, len(auth), P)]
        best_k, best_s = 0, -1
        for k in range(256):
            # score: count of printable + common punctuation
            s = 0
            for b in samples:
                x = b ^ k
                if 32 <= x <= 126:
                    s += 2
                elif x in (9, 10, 13):
                    s += 1
            if s > best_s:
                best_s, best_k = s, k
        key[col] = best_k
    dec = bytes(auth[i] ^ key[i % P] for i in range(len(auth)))
    printable = sum(1 for x in dec if 32 <= x <= 126)
    b64 = sum(1 for x in dec if x in B64)
    e = entropy(dec)
    return printable, b64, e, dec, bytes(key)

best = []
for P in range(1, 101):
    printable, b64, e, dec, key = try_period(P)
    best.append((printable, b64, e, P))

best.sort(key=lambda x: (-x[0], -x[1]))
print('top periods by printable:')
for printable, b64, e, P in best[:15]:
    print(f'  period {P}: printable={printable}/347 b64={b64} entropy={e:.2f}')

# show best 3 decryptions
for printable, b64, e, P in best[:3]:
    _, _, _, dec, key = try_period(P)
    print(f'\n=== period {P} (printable {printable}) ===')
    print('key:', key.hex())
    print('dec:', dec.decode('latin1', errors='replace'))
