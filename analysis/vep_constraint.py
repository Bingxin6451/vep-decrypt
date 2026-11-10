#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[55068983:]
auth = tail[190:190+347]

B64 = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
# extended: also allow whitespace, JSON punctuation
EXTRA = set(b' \t\n\r{}[]\":,.-_')

def solve(period, charset):
    key = bytearray()
    for col in range(period):
        samples = [auth[i] for i in range(col, len(auth), period)]
        candidates = []
        for k in range(256):
            if all((s ^ k) in charset for s in samples):
                candidates.append(k)
        if len(candidates) == 1:
            key.append(candidates[0])
        elif len(candidates) == 0:
            key.append(None)
        else:
            key.append(candidates)
    return key

for period in [25, 50, 75]:
    k = solve(period, B64)
    print(f'=== period {period}, strict base64 charset ===')
    for i, v in enumerate(k):
        if v is None:
            print(f'  col {i}: NO CANDIDATE')
        elif isinstance(v, list):
            print(f'  col {i}: {len(v)} candidates {[hex(x) for x in v]}')
        else:
            print(f'  col {i}: key=0x{v:02x}')
