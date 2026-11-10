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

vid = bytearray(); si = 0
for ci in range(1, 3):
    n = spc(ci); base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]; vid += data[base:base+sz]; base += sz; si += 1
vid = bytes(vid)

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
        s = 0
        for _ in range(z): s = (s<<1)|self.bit()
        return (1<<z) - 1 + s
    def se(self):
        c = self.ue()
        return (c+1)//2 if c%2 else -(c//2)

s0 = vsizes[0]
p1 = vid[s0:s0+vsizes[1]]
sh = p1[5:5+80]  # skip 4-byte len + 1-byte NAL header
br = BR(sh)

print('first_mb:', br.ue())
print('slice_type:', br.ue())
print('pps_id:', br.ue())
print('frame_num:', br.bits(4))
print('poc_lsb:', br.bits(12))
override = br.bit()
print('num_ref_override:', override)
num_ref_l0 = 4  # default = pps num_ref_idx_l0_default_active_minus1 + 1 = 3+1
if override:
    num_ref_l0 = br.ue() + 1
    print('num_ref_l0_active:', num_ref_l0)
print('ref_list_mod_flag_l0:', br.bit())
# ref_pic_list_modification loop
idc = br.ue()
mod_count = 0
while idc != 3 and mod_count < 20:
    if idc == 0 or idc == 1:
        br.ue()  # abs_diff_pic_num_minus1
    elif idc == 2:
        br.ue()  # long_term_pic_num
    idc = br.ue()
    mod_count += 1
print('ref_list_mod loop ended after', mod_count, 'entries, idc', idc)
print('luma_log2_weight_denom:', br.ue())
print('chroma_log2_weight_denom:', br.ue())
for i in range(num_ref_l0):
    lf = br.bit()
    if lf:
        br.se(); br.se()  # luma_weight, luma_offset
    cf = br.bit()
    if cf:
        br.se(); br.se(); br.se(); br.se()  # chroma_weight[2], chroma_offset[2]
print('after pred_weight_table, bitpos:', br.p)
print('dec_ref_pic_marking adaptive flag:', br.bit())
print('cabac_init_idc:', br.ue())
print('slice_qp_delta:', br.se())
print('final bitpos:', br.p)
