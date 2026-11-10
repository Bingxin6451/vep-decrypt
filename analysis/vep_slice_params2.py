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

vid = bytearray()
si = 0
for ci in range(1, 10):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
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
        suffix = 0
        for _ in range(z): suffix = (suffix<<1)|self.bit()
        return (1<<z) - 1 + suffix
    def se(self):
        c = self.ue()
        return (c+1)//2 if c%2 else -(c//2)

# slice header from vid[724]
sh = vid[724:724+120]

def parse(fnb, ptype, plsb):
    br = BR(sh)
    r = {}
    r['first_mb'] = br.ue()
    r['slice_type'] = br.ue()
    r['pps_id'] = br.ue()
    r['frame_num'] = br.bits(fnb)
    r['idr_pic_id'] = br.ue()
    if ptype == 0:
        r['poc_lsb'] = br.bits(plsb)
        r['delta_poc_bottom'] = br.se()
    elif ptype == 1:
        r['delta_poc0'] = br.se()
        r['delta_poc1'] = br.se()
    r['no_prior'] = br.bit()
    r['long_term'] = br.bit()
    r['bitpos'] = br.p
    return r

for fnb in [4,5,6,7,8,10,12]:
    for ptype in [0,1,2]:
        for plsb in [4,6,8,10,12,16]:
            try:
                r = parse(fnb, ptype, plsb)
                ok = (0 <= r['slice_type'] <= 9 and r['pps_id'] <= 3
                      and abs(r.get('delta_poc_bottom',0)) < 1000
                      and abs(r.get('delta_poc0',0)) < 1000
                      and abs(r.get('delta_poc1',0)) < 1000)
                if ok:
                    print(f'*** fnb={fnb} ptype={ptype} plsb={plsb}: {r}')
            except Exception as e:
                pass

# also print all for fnb=4 ptype=0
print('\nall combos slice_type/pps_id (to see which give sane values):')
for fnb in [4,5,6,8]:
    for ptype in [0,1,2]:
        for plsb in [4,8,12]:
            r = parse(fnb, ptype, plsb)
            print(f'  fnb={fnb} ptype={ptype} plsb={plsb}: slice_type={r["slice_type"]} pps_id={r["pps_id"]} frame_num={r["frame_num"]} idr_pic_id={r["idr_pic_id"]}')
