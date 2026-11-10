#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, struct
from Crypto.Cipher import AES

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

key = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')
enc = data[16:16+81920]
ftyp = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')
target16 = ftyp[:16]

# parse tail structure precisely
tail = data[55068983:]
print('=== tail structure ===')
print('tail[0:32]:', tail[0:32].hex(' '))
# find base64 location
idx = tail.find(b'dGtF')
print('base64 at tail offset', idx)

# The 4 params at tail[14:30]: 158, 32, 190, 347
params = struct.unpack('<IIII', tail[14:30])
print('tail params:', params)

# Test AES modes with the key + various IVs
def try_mode(mode_name, make_cipher):
    for iv in [b'\x00'*16, b'\x00'*8, struct.pack('<I', 673)+b'\x00'*12, struct.pack('<I', 18727)+b'\x00'*12,
               struct.pack('<IIII', 158, 32, 190, 347), data[0:16], bytes.fromhex('43525950')+b'\x00'*8]:
        try:
            if mode_name in ('CTR',):
                c = AES.new(key, AES.MODE_CTR, nonce=iv[:8], initial_value=0)
                s = c.encrypt(bytes(16))
            else:
                c = make_cipher(iv)
                s = c.decrypt(data[16:32])
            if s[:16] == target16:
                print('***', mode_name, 'MATCH iv=', iv.hex())
                return True
        except Exception as e:
            pass
    return False

try_mode('CBC', lambda iv: AES.new(key, AES.MODE_CBC, iv))
try_mode('CFB', lambda iv: AES.new(key, AES.MODE_CFB, iv, segment_size=128))
try_mode('OFB', lambda iv: AES.new(key, AES.MODE_OFB, iv))

# CTR with various nonce/counter layouts
from Crypto.Util import Counter
found = False
for prefix_len in [0, 4, 8, 12]:
    for initial in [0, 1, 673, 18727]:
        for bo in ['big', 'little']:
            try:
                ctr = Counter.new(128, initial_value=initial, prefix=b'\x00'*prefix_len, little_endian=(bo=='little'))
                c = AES.new(key, AES.MODE_CTR, counter=ctr)
                s = c.encrypt(bytes(16))
                if s[:16] == target16:
                    print('*** CTR MATCH prefix', prefix_len, 'init', initial, bo)
                    found = True
            except Exception:
                pass
print('done AES modes')

# Also test: is the 16-byte key itself XORed against the header params to derive real key?
# e.g. real_key = key XOR MD5(param) etc.
import hashlib
for p in [673, 18727, 81920]:
    for seed in [struct.pack('<I', p), struct.pack('>I', p)]:
        derived = hashlib.md5(key + seed).digest()
        c = AES.new(derived, AES.MODE_ECB)
        if c.decrypt(data[16:32]) == target16:
            print('*** derived key match param', p)
        # SM4-like: skip

# Try XOR of key with tail repeated region to decrypt it
rep_start = 55068983 + idx + len(b'dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09')
print('\nregion after base64:', tail[idx+36:idx+36+64].hex(' '))
# the repeated region appears later; try XOR with key repeat
rpt = data[55068983 + 240 : 55068983 + 400]
dec = bytes(rpt[i] ^ key[i % 16] for i in range(len(rpt)))
print('XOR(key) of repeated region:', ''.join(chr(b) if 32 <= b < 127 else '.' for b in dec))
