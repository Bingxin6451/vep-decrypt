#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# known keystream up to 240 (ftyp+moov+mvhd+tkhd)
ks = bytearray()
ks += bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')
ks += bytes.fromhex('c7eb92323d300c7c')
def build_mvhd(ctime, mtime, ts=1000, dur=4803000):
    pt = bytearray()
    pt += struct.pack('>I', 108) + b'mvhd' + bytes(4)
    pt += struct.pack('>I', ctime) + struct.pack('>I', mtime)
    pt += struct.pack('>I', ts) + struct.pack('>I', dur)
    pt += struct.pack('>I', 0x00010000) + bytes.fromhex('0100') + bytes(2) + bytes(8)
    pt += struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x40000000)
    pt += bytes(24) + struct.pack('>I', 2)
    return bytes(pt)
ks += bytes(a ^ b for a, b in zip(enc[32:32+108], build_mvhd(0x6A7A0000, 0x6A7A0000)))
# tkhd at 148
def build_tkhd(ctime, mtime, track_id, dur, width, height):
    pt = bytearray()
    pt += struct.pack('>I', 92) + b'tkhd' + struct.pack('>I', 0x00000007)
    pt += struct.pack('>I', ctime) + struct.pack('>I', mtime)
    pt += struct.pack('>I', track_id) + bytes(4) + struct.pack('>I', dur)
    pt += bytes(8) + bytes(2) + bytes(2) + bytes(4)
    pt += struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x00010000) + bytes(4)*3 + struct.pack('>I', 0x40000000)
    pt += struct.pack('>I', width<<16) + struct.pack('>I', height<<16)
    return bytes(pt)
ks += bytes(8)  # gap 140..148 (trak size+type) -- placeholder
ks += bytes(a ^ b for a, b in zip(enc[148:148+92], build_tkhd(0x6A7A0000, 0x6A7A0000, 1, 4803000, 1920, 1080)))
ks = bytes(ks)

# mdhd starts at offset 240 (after tkhd: 148+92=240)
# mdhd: size(4) + 'mdhd'(4) + verflags(4) + ctime(4) + mtime(4) + timescale(4) + duration(4) + lang(2) + predef(2)
mdhd_ct = enc[240:240+32]
# known: size=32, 'mdhd', verflags=0, lang likely 0x55C4 'und'
mdhd_pt = bytearray(struct.pack('>I', 32) + b'mdhd' + bytes(4))
mdhd_pt += bytes(8)  # ctime+mtime unknown
mdhd_pt += bytes(8)  # timescale+duration unknown
mdhd_pt += struct.pack('>H', 0x55C4) + bytes(2)
ks_mdhd = bytes(a ^ b for a, b in zip(mdhd_ct, mdhd_pt))
print('mdhd keystream [240:272]:', ks_mdhd.hex())

# decrypt timescale & duration using ks_mdhd bytes 12..20
timescale = struct.unpack('>I', mdhd_ct[12:16])[0] ^ struct.unpack('>I', ks_mdhd[12:16])[0]
duration = struct.unpack('>I', mdhd_ct[16:20])[0] ^ struct.unpack('>I', ks_mdhd[16:20])[0]
print('video mdhd timescale =', timescale)
print('video mdhd duration  =', duration)
print('frame rate =', timescale, '/', duration, '->', timescale/ (duration/72625) if duration else '?')
