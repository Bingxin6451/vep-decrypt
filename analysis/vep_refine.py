#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import string, base64

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
auth = data[55069173:55069520]

B64 = set(string.ascii_letters + string.digits + '+/=')

def score_key_candidate(period, keybytes):
    dec = bytes(auth[i] ^ keybytes[i % period] for i in range(len(auth)))
    s = sum(1 for x in dec if x in B64)
    return s

# Iterative refinement: start from period-50 frequency result, then refine each column
# using base64 scoring
def refine(period, keybytes, rounds=3):
    key = bytearray(keybytes)
    for _ in range(rounds):
        for col in range(period):
            best_k = key[col]
            best_s = -1
            for k in range(256):
                test = bytearray(key)
                test[col] = k
                dec = bytes(auth[i] ^ test[i % period] for i in range(len(auth)))
                s = sum(1 for x in dec if x in B64)
                if s > best_s:
                    best_s = s
                    best_k = k
            key[col] = best_k
    return bytes(key)

# start with period-50 frequency-derived key
key50 = bytes.fromhex('40400000000040404040404040000000000000000000400040002020200040004000400040002000000000000040')
key = refine(50, key50, 4)
dec = bytes(auth[i] ^ key[i % 50] for i in range(len(auth)))
b64count = sum(1 for x in dec if x in B64)
print('period 50 refined: base64 chars', b64count, '/', len(dec))
print('plaintext:')
print(dec.decode('latin1'))
print()
# try base64-decode the whole thing (strip non-b64)
clean = ''.join(chr(x) for x in dec if x in B64)
try:
    raw = base64.b64decode(clean + '=' * (-len(clean) % 4))
    print('b64 decoded bytes:', raw.hex(' '))
    print('b64 decoded ascii:', ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw))
except Exception as e:
    print('b64 decode err', e)
