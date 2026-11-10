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

# build first 3 samples: sample0=IDR, sample1=P, sample2=P
vid = bytearray()
si = 0
for ci in range(1, 3):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)

# sample boundaries
s0 = vsizes[0]  # 47221
print('sample0 (IDR) size', s0, 'sample1 (P) size', vsizes[1], 'sample2 (P) size', vsizes[2])

# P frame sample1: at stream offset s0 = 47221
p1 = vid[s0:s0+vsizes[1]]
print('P1 first 20 bytes:', p1[:20].hex(' '))

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
        suffix = 0
        for _ in range(z): suffix = (suffix<<1)|self.bit()
        return (1<<z) - 1 + suffix
    def se(self):
        c = self.ue()
        return (c+1)//2 if c%2 else -(c//2)

# P slice header (skip NAL header byte)
sh = p1[1:1+60]
br = BR(sh)
print('first_mb:', br.ue())
st = br.ue()
print('slice_type:', st)
print('pps_id:', br.ue())
print('frame_num:', br.bits(4))
# poc type 0, lsb 12 bits
print('poc_lsb:', br.bits(12))
# non-IDR: no idr_pic_id
# num_ref_idx_active_override_flag
print('num_ref_override:', br.bit())
if br.d[br.p//8] is None: pass
# if override, num_ref_l0
# ref_pic_list_modification
print('ref_list_mod_flag_l0:', br.bit())
# pred_weight_table (weighted_pred_flag=1 for P slice)
print('luma_log2_weight_denom:', br.ue())
print('chroma_log2_weight_denom:', br.ue())
print('consumed bits:', br.p)
