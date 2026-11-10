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
for ci in range(1, 5):
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

offsets = [0]
for i in range(20):
    offsets.append(offsets[-1] + vsizes[i])

def parse(sidx, fnb, fmof, plsb):
    off = offsets[sidx]
    p = vid[off:off+vsizes[sidx]]
    sh = p[5:5+120]
    br = BR(sh)
    try:
        fm = br.ue()
        st = br.ue()
        pps = br.ue()
        fn = br.bits(fnb)
        if fmof == 0:
            br.bit()
        is_idr = st in (2,4,7,9)
        if is_idr:
            br.ue()  # idr_pic_id
        poc = br.bits(plsb)
        if is_idr:
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
        return (st, luma, chroma, nr0, br.p)
    except Exception:
        return None

# just check luma/chroma validity across several P frames (sidx 1,2,3,4,5)
for fnb in [4,5,6,8]:
    for fmof in [0,1]:
        for plsb in [4,6,8,10,12,16]:
            good = 0
            detail = []
            for sidx in [1,2,3,4,5]:
                r = parse(sidx, fnb, fmof, plsb)
                if r and r[0] == 5 and 0 <= r[1] <= 7 and 0 <= r[2] <= 7:
                    good += 1
                    detail.append((r[1], r[2], r[3]))
            if good >= 4:
                print(f'fnb={fnb} fmof={fmof} plsb={plsb}: {good}/5 good, details={detail}')
