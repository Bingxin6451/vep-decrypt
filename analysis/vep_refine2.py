#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import string, base64

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
auth = data[55069173:55069520]

B64 = set(string.ascii_letters + string.digits + '+/=')

# initial frequency-based key for period 50
def freq_key(period):
    key = bytearray(period)
    for col in range(period):
        samples = [auth[i] for i in range(col, len(auth), period)]
        best_k, best_s = 0, -9999
        for k in range(256):
            s = sum(1 for b in samples if (b ^ k) in B64)
            if s > best_s:
                best_s, best_k = s, k
        key[col] = best_k
    return bytes(key)

def refine(period, keybytes, rounds=4):
    key = bytearray(keybytes)
    for _ in range(rounds):
        for col in range(period):
            best_k, best_s = key[col], -1
            for k in range(256):
                test = bytearray(key); test[col] = k
                dec = bytes(auth[i] ^ test[i % period] for i in range(len(auth)))
                s = sum(1 for x in dec if x in B64)
                if s > best_s:
                    best_s, best_k = s, k
            key[col] = best_k
    return bytes(key)

for period in [25, 50]:
    k0 = freq_key(period)
    key = refine(period, k0, 5)
    dec = bytes(auth[i] ^ key[i % period] for i in range(len(auth)))
    b64c = sum(1 for x in dec if x in B64)
    print(f'=== period {period}: base64={b64c}/{len(dec)} ===')
    print(dec.decode('latin1'))
    print()
