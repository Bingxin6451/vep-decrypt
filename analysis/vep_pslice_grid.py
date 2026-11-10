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
for ci in range(1, 40):
    n = spc(ci); base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]; vid += data[base:base+sz]; base += sz; si += 1
vid = bytes(vid)

class BR:
    def __init__(self, d): self.d, self.p = d, 0
    def bit(self):
        b = (self.d[self.p//8] >> (7-self.p%8)) & 1; self.p += 1; return b
    def bits(self, n):
        v = 0
        for _ in range(n): v = (v<<1) | self.bit()
        return v
    def ue(self):
        z = 0
        while self.bit() == 0: z += 1
        s = 0
        for _ in range(z): s = (s<<1) | self.bit()
        return (1<<z)-1+s
    def se(self):
        c = self.ue()
        return (c+1)//2 if c & 1 else -(c//2)

def parse_pslice(nal, fnb=4, plsb=12):
    """Parse a P-slice header (slice_type=5), return luma/chroma denoms."""
    br = BR(nal)
    first = br.ue()
    st = br.ue()
    if st != 5: return None  # not P slice
    pps = br.ue()
    fn = br.bits(fnb)
    poc = br.bits(plsb)
    ov = br.bit()
    nr0 = 3
    if ov: nr0 = br.ue()+1
    flag = br.bit()
    if flag:
        while True:
            idc = br.ue()
            if idc == 3: break
            if idc in (0,1,2): br.ue()
    luma = br.ue()
    chroma = br.ue()
    return (st, fn, poc, ov, nr0, luma, chroma)

# get NALs for samples 1..30, find P slices (slice_type=5)
def get_pslices():
    pslices = []
    off = vsizes[0]  # skip sample 0 (SEI + IDR)
    for s in range(1, 40):
        sz = vsizes[s]
        sample = vid[off:off+sz]
        p = 0
        while p+4 <= len(sample):
            nlen = struct.unpack('>I', sample[p:p+4])[0]
            nal = sample[p+4:p+4+nlen]
            p += 4+nlen
            if len(nal) < 2: break
            nt = nal[0] & 0x1f
            if nt == 1:
                pslices.append((s, nal[1:]))
        off += sz
    return pslices

pslices = get_pslices()
print(f"found {len(pslices)} non-IDR slice NALs")

# try to identify P slices (slice_type==5) via first few ue fields
for fnb in [4,5,6,7,8]:
    for plsb in range(4, 21):
        ok = []
        for s, nal in pslices:
            r = parse_pslice(nal, fnb, plsb)
            if r is None: continue
            st, fn, poc, ov, nr0, luma, chroma = r
            if luma <= 7 and chroma <= 7:
                ok.append((s, nr0, luma, chroma))
        if len(ok) >= 5:
            print(f"fnb={fnb} plsb={plsb}: {len(ok)} good pslices: {ok[:6]}")
