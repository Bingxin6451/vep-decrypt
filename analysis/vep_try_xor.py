#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

# encrypted header region starts at offset 16
enc_hdr = data[16:16+81920]
# encrypted video chunk 3826 data
chunk3826_off = u32be(871190 + 3825*4) + 16
enc_chunk = data[chunk3826_off:chunk3826_off+65109]

# candidate ftyp plaintexts
ftyp24 = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')
ftyp32 = bytes.fromhex('000000206674797069736f6d0000020069736f6d69736f32617663316d703431')

for name, ftyp in [('ftyp24', ftyp24), ('ftyp32', ftyp32)]:
    # recover key stream assuming plaintext starts with ftyp
    key = bytes(a ^ b for a, b in zip(enc_hdr[:len(ftyp)], ftyp))
    print(f'--- {name}: recovered key ({len(key)} bytes) ---')
    print('key:', key.hex(' '))
    # try XOR this key onto the video chunk
    dec = bytes(a ^ b for a, b in zip(enc_chunk[:len(key)], key))
    print('video chunk dec first', len(key), 'bytes:', dec.hex(' '))
    print('   ascii:', ''.join(chr(b) if 32 <= b < 127 else '.' for b in dec))

# Also: check if the SAME key (from ftyp) decrypts header into a valid moov-like structure
# by extending key assumption: XOR with repeating key period = 16/24/32
for period in [16, 24, 32]:
    keyp = bytes(a ^ b for a, b in zip(enc_hdr[:period], ftyp24[:period]))
    dec = bytes(enc_hdr[i] ^ keyp[i % period] for i in range(256))
    print(f'\nrepeating key period {period}, first 256 dec:')
    print(''.join(chr(b) if 32 <= b < 127 else '.' for b in dec))
