#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o):
    return struct.unpack('>I', data[o:o+4])[0]

stsz = 580658
nsamp = u32be(stsz+12)
vsizes = [u32be(stsz+16+4*i) for i in range(nsamp)]
stco = 871178
nchunk = u32be(stco+8)
vchunks = [u32be(stco+12+4*i) + 16 for i in range(nchunk)]

vid = bytearray()
ci = 0; si = 0
for ci in range(60):
    ns = 8 if ci == 0 else 7
    base = vchunks[ci]
    for j in range(ns):
        if si >= len(vsizes): break
        vid += data[base : base+vsizes[si]]
        base += vsizes[si]
        si += 1
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

def parse_p(nal, fnb=4, plsb=12):
    br = BR(nal)
    first = br.ue()
    st = br.ue()
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
    return first, st, pps, fn, poc, ov, nr0, luma, chroma

# Walk samples, parse NALs inside each sample
off = 0
cnt = 0
print("sample | nal | first_mb | st | fn | poc | nr0 | luma | chroma")
for s in range(0, 420):
    sz = vsizes[s]
    sample = vid[off:off+sz]
    # iterate NALs inside sample
    p = 0
    while p + 4 <= len(sample):
        nlen = struct.unpack('>I', sample[p:p+4])[0]
        nal = sample[p+4:p+4+nlen]
        p += 4 + nlen
        if len(nal) == 0: break
        nt = nal[0] & 0x1f
        if nt == 1:
            r = parse_p(nal[1:])
            print(f"{s:6d} | {nt} | {r[0]:8d} | {r[1]:2d} | {r[3]:2d} | {r[4]:5d} | {r[6]:3d} | {r[7]:4d} | {r[8]:6d}")
            cnt += 1
            if cnt >= 30: break
    off += sz
    if cnt >= 30: break
