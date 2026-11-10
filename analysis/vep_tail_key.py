#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, struct, hashlib

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

# tail base64 string
tail = data[55068983:]
# find the base64 string "dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09"
b64 = b'dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09'
layer1 = base64.b64decode(b64)
print('layer1:', layer1)
layer2 = base64.b64decode(layer1)
print('layer2 (16 bytes?):', layer2.hex(' '), 'len', len(layer2))

key_candidate = layer2
target16 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee6')
target24 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')

# Test 1: RC4 with this key
def rc4(key, n=64):
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

stream = rc4(key_candidate)
print('RC4(key)[:24]:', stream[:24].hex())
print('match?', stream[:24] == target24)

# Test 2: AES-CTR / ECB counter modes
from Crypto.Cipher import AES
def aes_ecb_counter(key, nblocks, start=0, byteorder='be', nonce=b''):
    out = bytearray()
    for i in range(nblocks):
        blk = nonce + (struct.pack('>I', start+i) if byteorder=='be' else struct.pack('<I', start+i))
        blk = (blk + b'\x00'*16)[:16]
        out += AES.new(key, AES.MODE_ECB).encrypt(blk)
    return bytes(out)

if len(key_candidate) == 16:
    for start in [0, 1]:
        for bo in ['be', 'le']:
            for nonce_len in [0, 12]:
                nonce = b'\x00'*nonce_len
                s = aes_ecb_counter(key_candidate, 2, start, bo, nonce)
                if s[:16] == target16:
                    print('*** AES MATCH start', start, bo, 'nonce_len', nonce_len)
    # AES-CBC: plaintext[0] = AES_dec(ct[0]) XOR IV; so AES_dec(ct0) = pt0 XOR IV
    # try IV=0: AES_dec(ct0) should = ftyp[0:16]
    ct0 = data[16:32]
    ftyp0 = bytes.fromhex('00000018667479707969736f6d00000200')
    try:
        dec0 = AES.new(key_candidate, AES.MODE_ECB).decrypt(ct0)
        print('AES_dec(ct0) =', dec0.hex(' '))
        print('ftyp[0:16]  =', ftyp0.hex(' '))
        if dec0 == ftyp0:
            print('*** CBC IV=0 MATCH! key =', key_candidate.hex())
        # also try: AES_dec(ct0) XOR ftyp0 = IV
        iv = bytes(a ^ b for a, b in zip(dec0, ftyp0))
        print('implied IV:', iv.hex(' '))
        # check second block consistency with CBC
        ct1 = data[32:48]
        dec1 = AES.new(key_candidate, AES.MODE_ECB).decrypt(ct1)
        pt1 = bytes(a ^ b for a, b in zip(dec1, ct0))
        print('CBC pt1 =', pt1.hex(' '))
        print('expected ftyp[16:24]+moov[0:8]:', (bytes.fromhex('69736f6d69736f32') + b'\x00\x00' + b'\x6d\x6f\x6f\x76').hex(' '))
    except Exception as e:
        print('AES err', e)

# Test 3: XOR with key directly (16-byte key repeating)
rep = (key_candidate * 2)[:24]
print('\nXOR key repeat:', bytes(a^b for a,b in zip(data[16:40], rep)).hex(' '))
