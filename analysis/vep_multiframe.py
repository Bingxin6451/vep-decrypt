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

# build first 8 samples (sample0=IDR, then P frames)
vid = bytearray(); si = 0
for ci in range(1, 4):
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

# sample offsets
offsets = [0]
for i in range(8):
    offsets.append(offsets[-1] + vsizes[i])

def parse_p(sample_idx, fnb, fmof, ptype, plsb):
    off = offsets[sample_idx]
    p = vid[off:off+vsizes[sample_idx]]
    sh = p[5:5+100]  # skip len + nal header
    br = BR(sh)
    try:
        fm = br.ue()
        st = br.ue()
        pps = br.ue()
        fn = br.bits(fnb)
        if fmof == 0:
            fp = br.bit()  # field_pic_flag
        if st in (2,4,7,9):  # IDR/I
            iid = br.ue()
        if ptype == 0:
            poc = br.bits(plsb)
            if st in (2,4,7,9):
                br.se()  # delta_poc_bottom
        ov = br.bit()
        nr0 = 4
        if ov:
            nr0 = br.ue() + 1
        flag = br.bit()
        if flag:
            idc = br.ue(); cnt = 0
            while idc != 3 and cnt < 30:
                if idc in (0,1): br.ue()
                elif idc == 2: br.ue()
                idc = br.ue(); cnt += 1
        luma = br.ue()
        chroma = br.ue()
        # also parse weight entries (4 refs)
        for i in range(min(nr0, 8)):
            lf = br.bit()
            if lf: br.se(); br.se()
            cf = br.bit()
            if cf: br.se(); br.se(); br.se(); br.se()
        # dec_ref_pic_marking
        if st not in (2,4,7,9):
            adaptive = br.bit()
        cabac = br.ue()
        qp = br.se()
        return (st, luma, chroma, nr0, cabac, qp)
    except Exception:
        return None

# test combos on multiple P frames
best = []
for fnb in [4,5,6,8]:
    for fmof in [0,1]:
        for ptype in [0,1,2]:
            for plsb in [4,6,8,10,12,16]:
                ok = 0
                for sidx in [1,2,3]:
                    r = parse_p(sidx, fnb, fmof, ptype, plsb)
                    if r and r[0]==5 and 0<=r[1]<=7 and 0<=r[2]<=7 and r[3]==4 and 0<=r[4]<=2 and -10<=r[5]<=10:
                        ok += 1
                if ok >= 3:
                    best.append((ok, fnb, fmof, ptype, plsb, r))
best.sort(reverse=True)
for b in best[:15]:
    print('GOOD', b)
