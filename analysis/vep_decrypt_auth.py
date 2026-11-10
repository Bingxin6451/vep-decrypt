#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, struct
from Crypto.Cipher import AES

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

tail = data[55068983:]
key = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')

# auth block: tail[190:190+347]
auth = tail[190:190+347]
print('auth block len', len(auth))
print('auth first 64:', auth[:64].hex(' '))

def rc4(key, n):
    S = list(range(256)); j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0; out = bytearray()
    for _ in range(n):
        i = (i+1) % 256; j = (j+S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(S[(S[i]+S[j]) % 256])
    return bytes(out)

def show(name, b):
    print(f'--- {name} ---')
    print('  hex:', b[:48].hex(' '))
    print('  ascii:', ''.join(chr(x) if 32 <= x < 127 else '.' for x in b[:80]))

# 1. XOR with key repeating
show('XOR key16 repeat', bytes(auth[i] ^ key[i % 16] for i in range(len(auth))))

# 2. RC4(key)
show('RC4(key)', bytes(auth[i] ^ rc4(key, len(auth))[i] for i in range(len(auth))))

# 3. AES-CTR(key)
ctr = AES.new(key, AES.MODE_CTR, nonce=b'\x00'*8, initial_value=0)
show('AES-CTR(key)', ctr.decrypt(auth))

# 4. AES-CBC(key, iv=0)
show('AES-CBC(key,iv0)', AES.new(key, AES.MODE_CBC, b'\x00'*16).decrypt(auth))

# 5. AES-ECB(key)
show('AES-ECB(key)', AES.new(key, AES.MODE_ECB).decrypt(auth))

# 6. XOR with header params as key (673, 18727)
for name, k in [('hdr673', struct.pack('<I', 673)), ('hdr18727', struct.pack('<I', 18727))]:
    show(f'XOR {name} repeat', bytes(auth[i] ^ k[i % 4] for i in range(len(auth))))
