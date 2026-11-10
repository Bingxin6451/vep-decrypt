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

s0 = vsizes[0]
p1 = vid[s0:s0+vsizes[1]]

def try_params(fnb, ptype, plsb):
    sh = p1[5:5+80]
    br = BR(sh)
    try:
        fm = br.ue()
        st = br.ue()
        pps = br.ue()
        fn = br.bits(fnb)
        if ptype == 0:
            poc = br.bits(plsb)
        ov = br.bit()
        nr0 = 4
        if ov:
            nr0 = br.ue() + 1
        flag = br.bit()
        if flag:
            idc = br.ue()
            cnt = 0
            while idc != 3 and cnt < 30:
                if idc in (0,1): br.ue()
                elif idc == 2: br.ue()
                idc = br.ue()
                cnt += 1
        luma = br.ue()
        chroma = br.ue()
        return (st, fm, luma, chroma, nr0)
    except Exception:
        return None

for ptype in [0, 1, 2]:
    for fnb in [4,5,6,8,10,12]:
        for plsb in [4,6,8,10,12,16]:
            r = try_params(fnb, ptype, plsb)
            if r and r[0] == 5 and 0 <= r[2] <= 7 and 0 <= r[3] <= 7:
                print(f'GOOD fnb={fnb} ptype={ptype} plsb={plsb}: slice_type={r[0]} first_mb={r[1]} luma={r[2]} chroma={r[3]} numref={r[4]}')
