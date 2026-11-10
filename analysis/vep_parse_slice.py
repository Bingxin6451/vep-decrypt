#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

vsizes = [u32be(580674 + i*4) for i in range(72625)]
vcoffs = [u32be(871190 + i*4) for i in range(10375)]
def spc(ci):
    if ci == 1: return 8
    if ci <= 10374: return 7
    return 6

# build first ~100KB of plaintext video stream
vid = bytearray()
si = 0
for ci in range(1, 200):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)

# first IDR: @719 len 46498, NAL header 65
# dump IDR slice data (after NAL header)
idr = vid[723:723+60]
print('IDR slice first 60 bytes:', idr.hex(' '))

class BR:
    def __init__(self, d): self.d = d; self.p = 0
    def bit(self):
        b = (self.d[self.p//8] >> (7-self.p%8)) & 1
        self.p += 1
        return b
    def bits(self, n):
        v = 0
        for _ in range(n): v = (v<<1)|self.bit()
        return v
    def ue(self):
        z = 0
        while self.bit() == 0: z += 1
        v = (1<<z) - 1
        for _ in range(z): v = (v<<1)|self.bit()
        return v
    def se(self):
        c = self.ue()
        return (c+1)//2 if c%2 else -(c//2)

# slice header (nal_ref_idc=3, type=5 IDR)
br = BR(idr)
print('first_mb_in_slice:', br.ue())
st = br.ue()
print('slice_type:', st)
print('pps_id:', br.ue())
# frame_num: assume log2_max_frame_num_minus4 = 0 (4 bits) first
print('frame_num (4 bits):', br.bits(4))
print('idr_pic_id:', br.ue())
print('idr_pic_order_cnt_lsb (4 bits guess):', br.bits(4))
print('consumed bits:', br.p)
