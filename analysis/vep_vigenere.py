#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[55068983:]
auth = tail[190:190+347]

# Try key periods, do per-column single-byte XOR with English/Chinese-ish scoring
# Common chars in machine-code / hex / JSON-ish text
def score_char(x):
    # strongly favor printable ASCII
    if 32 <= x <= 126:
        return 2
    if x in (9, 10, 13, 0):
        return 1
    return -1

def crack_period(P):
    key = bytearray(P)
    for col in range(P):
        col_bytes = [auth[i] for i in range(col, len(auth), P)]
        best_k = 0
        best_s = -9999
        for k in range(256):
            s = sum(score_char(b ^ k) for b in col_bytes)
            if s > best_s:
                best_s = s
                best_k = k
        key[col] = best_k
    dec = bytes(auth[i] ^ key[i % P] for i in range(len(auth)))
    return bytes(key), dec

for P in [25, 50, 75]:
    k, dec = crack_period(P)
    printable = sum(1 for x in dec if 32 <= x <= 126)
    print(f'=== period {P}: printable={printable}/347 ===')
    print('key:', k.hex(' '))
    print('dec:', repr(dec))
    print()
