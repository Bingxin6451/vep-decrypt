#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct
from Crypto.Cipher import ARC4

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

ks = bytearray()
ks += bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')
ks += bytes.fromhex('c7eb92323d300c7c')
def build_mvhd(ctime, mtime, ts=1000, dur=4803000):
    pt = bytearray()
    pt += struct.pack('>I', 108) + b'mvhd' + bytes(4)
    pt += struct.pack('>I', ctime) + struct.pack('>I', mtime)
    pt += struct.pack('>I', ts) + struct.pack('>I', dur)
    pt += struct.pack('>I', 0x00010000)
    pt += bytes.fromhex('0100') + bytes(2) + bytes(8)
    pt += struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x40000000)
    pt += bytes(24) + struct.pack('>I', 2)
    return bytes(pt)
ks += bytes(a ^ b for a, b in zip(enc[32:32+108], build_mvhd(0x6A7A0000, 0x6A7A0000)))

# trak + tkhd at offset 140
def build_tkhd(ctime, mtime, track_id, dur, width, height, volume=0):
    pt = bytearray()
    pt += struct.pack('>I', 92) + b'tkhd' + struct.pack('>I', 0x00000007)
    pt += struct.pack('>I', ctime) + struct.pack('>I', mtime)
    pt += struct.pack('>I', track_id) + bytes(4) + struct.pack('>I', dur)
    pt += bytes(8) + bytes(2) + bytes(2)
    pt += struct.pack('>H', volume) + bytes(2)
    pt += struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x40000000)
    pt += struct.pack('>I', width<<16) + struct.pack('>I', height<<16)
    return bytes(pt)

trak_pt = struct.pack('>I', 0) + b'trak'  # size unknown, skip 4
# Actually trak size unknown; only recover from 'trak' onward for known parts
# offset 144 is 'trak' type. tkhd starts at 148
tkhd_pt = build_tkhd(0x6A7A0000, 0x6A7A0000, 1, 4803000, 1920, 1080, 0)
# tkhd at offset 148 (trak size + 'trak')
ks_tkhd = bytes(a ^ b for a, b in zip(enc[148:148+92], tkhd_pt))
print('tkhd keystream [148:240]:')
for i in range(0, 92, 16):
    print(f'  {148+i:4d}: {ks_tkhd[i:i+16].hex()}')

# full keystream assembled: 0..140 known + 148..240 known (gap 140..148 = trak size+type)
ks_full = ks + bytes(8) + ks_tkhd  # rough

# Test RC4 with common string keys
TARGET = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')
strings = ['dahuangfeng', 'dahuangfeng.com', 'HBPlayer', 'hbplayer', 'vep', 'CRYP',
           'dahuangfeng2020', 'dahuangfeng2021', 'dahuangfeng2022', 'dahuangfeng2023',
           'dahuangfeng2024', 'dahuangfeng2025', 'dahuangfeng2026', 'DahuangFeng',
           'dahf', 'dhf', 'huangfeng', 'dahuangfeng.cn', 'www.dahuangfeng.com',
           'dahuangfeng_crypt', 'tkEDoksW0UPyQWR8O4ynPg==', 'tkEDoksW0UPyQWR8O4ynPg',
           'b64103a24b16d143f241647c3b8ca73e']
import hashlib
print('\nRC4 with common keys:')
for s in strings:
    for kb in [s.encode(), hashlib.md5(s.encode()).digest(), hashlib.sha256(s.encode()).digest()]:
        try:
            out = ARC4.new(kb).encrypt(bytes(24))
            if out == TARGET:
                print(f'  RC4({s!r}) MATCH!')
            elif out[:3] == TARGET[:3]:
                print(f'  RC4({s!r}) first3: {out.hex()}')
        except Exception:
            pass
print('done')
