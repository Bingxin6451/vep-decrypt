#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct
from Crypto.Cipher import AES

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
tail = data[55068983:]
key = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')
auth = tail[190:190+347]

# AES OFB / CFB on auth block (these don't need padding)
for mode_name, c in [('OFB', AES.new(key, AES.MODE_OFB, b'\x00'*16)),
                     ('CFB', AES.new(key, AES.MODE_CFB, b'\x00'*16, segment_size=128)),
                     ('CTR', AES.new(key, AES.MODE_CTR, nonce=b'\x00'*8, initial_value=0))]:
    dec = c.decrypt(auth)
    printable = sum(1 for x in dec if 32 <= x <= 126)
    print(f'{mode_name}: printable={printable}/347')
    print(f'  {dec[:80]!r}')

# period 25 analysis: check if auth has 25-byte period
print('\n=== period 25 detail ===')
for base in [0, 25, 50, 75, 100]:
    print(f'auth[{base}:{base+25}]:', auth[base:base+25].hex(' '))
# compare auth[0:25] with auth[25:50], [50:75], [75:100]
for off in [25, 50, 75, 100, 125, 150]:
    same = sum(1 for i in range(25) if auth[i] == auth[off+i])
    print(f'auth[0:25] vs auth[{off}:{off+25}]: {same}/25 same')

# keyed XOR with 25-byte key? try deriving 25-byte key from the 16-byte key via repeat+extension
key25 = (key + key[:9])
dec = bytes(auth[i] ^ key25[i % 25] for i in range(len(auth)))
print('\nXOR key25:', repr(dec[:80]))
