#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, hashlib
from Crypto.Cipher import AES

key = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')
target16 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee6')

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
hdr16 = data[0:16]  # "CRYP" + params

# derive key candidates
derived = {}
derived['raw'] = key
derived['md5(key)'] = hashlib.md5(key).digest()
derived['sha256(key)16'] = hashlib.sha256(key).digest()[:16]
derived['key_xor_hdr16'] = bytes(a^b for a,b in zip(key, hdr16))
derived['key_xor_CRYP'] = bytes(a^b for a,b in zip(key, b'CRYP'*4))
derived['md5(key+hdr16)'] = hashlib.md5(key + hdr16).digest()
derived['md5(hdr16+key)'] = hashlib.md5(hdr16 + key).digest()
derived['md5(key+673)'] = hashlib.md5(key + struct.pack('<I', 673)).digest()
derived['md5(key+18727)'] = hashlib.md5(key + struct.pack('<I', 18727)).digest()
derived['md5(key+81920)'] = hashlib.md5(key + struct.pack('<I', 81920)).digest()

def rc4(key, n=32):
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

# IV candidates for block modes (16 bytes)
ivs = {}
ivs['zero'] = b'\x00'*16
ivs['hdr16'] = hdr16
ivs['params_le'] = struct.pack('<IIII', 81920, 673, 18727, 0)
ivs['params_be'] = struct.pack('>IIII', 81920, 673, 18727, 0)
ivs['vep_magic'] = b'vep.' + b'\x00'*12
ivs['tail_params'] = struct.pack('<IIII', 158, 32, 190, 347)
ivs['673_le'] = struct.pack('<I', 673) + b'\x00'*12
ivs['18727_le'] = struct.pack('<I', 18727) + b'\x00'*12
ivs['81920_le'] = struct.pack('<I', 81920) + b'\x00'*12

found = False
for dname, dkey in derived.items():
    if len(dkey) not in (16, 24, 32):
        continue
    # RC4
    if rc4(dkey, 16) == target16:
        print('*** RC4 MATCH derived', dname); found = True
    # AES-CTR with each IV (nonce=iv[:8], counter from 0 big-endian)
    for iname, iv in ivs.items():
        try:
            s = AES.new(dkey, AES.MODE_CTR, nonce=iv[:8], initial_value=0).encrypt(bytes(16))
            if s == target16:
                print('*** AES-CTR MATCH derived', dname, 'iv', iname); found = True
        except Exception:
            pass
        # nonce=iv[:4], counter from 0
        try:
            s = AES.new(dkey, AES.MODE_CTR, nonce=iv[:4], initial_value=0).encrypt(bytes(16))
            if s == target16:
                print('*** AES-CTR(4) MATCH derived', dname, 'iv', iname); found = True
        except Exception:
            pass
        # ECB encrypt iv directly (key stream = AES_enc(iv || counter))
        try:
            blk = iv[:16]
            s = AES.new(dkey, AES.MODE_ECB).encrypt(blk)
            if s == target16:
                print('*** AES-ECB(iv) MATCH derived', dname, 'iv', iname); found = True
        except Exception:
            pass
        # ECB encrypt iv+1
        try:
            blk = iv[:15] + bytes([iv[15]+1 if len(iv)>=16 else 0])
            s = AES.new(dkey, AES.MODE_ECB).encrypt(blk)
            if s == target16:
                print('*** AES-ECB(iv+1) MATCH derived', dname, 'iv', iname); found = True
        except Exception:
            pass

if not found:
    print('no match with', len(derived), 'derived keys x', len(ivs), 'IVs')

# Print reference values for cross-check
print('\ntarget16:', target16.hex())
print('AES-ECB(raw_key, iv=zero):', AES.new(key, AES.MODE_ECB).encrypt(b'\x00'*16).hex())
print('AES-ECB(raw_key, iv=hdr16):', AES.new(key, AES.MODE_ECB).encrypt(hdr16).hex())
print('AES-CTR(raw_key, nonce=0):', AES.new(key, AES.MODE_CTR, nonce=b'\x00'*8, initial_value=0).encrypt(bytes(16)).hex())
