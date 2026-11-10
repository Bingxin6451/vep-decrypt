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

# IDR NAL data starts at 723 (0x65 = NAL header), slice header starts 724
sh = vid[724:724+120]  # slice header bytes

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

def parse(fnb, ptype, plsb):
    br = BR(sh)
    r = {}
    r['first_mb'] = br.ue()
    r['slice_type'] = br.ue()
    r['pps_id'] = br.ue()
    r['frame_num'] = br.bits(fnb)
    if r['slice_type'] in (2,4,7,9):  # I/IDR
        r['idr_pic_id'] = br.ue()
        if ptype == 0:
            r['poc_lsb'] = br.bits(plsb)
            r['delta_poc_bottom'] = br.se()
        elif ptype == 1:
            r['delta_poc0'] = br.se()
            r['delta_poc1'] = br.se()
        # no_output_of_prior_pics_flag, long_term_reference_flag
        r['no_prior'] = br.bit()
        r['long_term'] = br.bit()
    else:
        # non-IDR
        if ptype == 0:
            r['poc_lsb'] = br.bits(plsb)
        elif ptype == 1:
            r['delta_poc0'] = br.se()
        r['pos_after_header'] = br.p
    r['bitpos'] = br.p
    return r

# try combos, score by: slice_type valid (0-9), pps_id small, frame_num small, fields sane
for fnb in [4,5,6,7,8,10,12]:
    for ptype in [0,1,2]:
        for plsb in [4,6,8,10,12,16]:
            try:
                r = parse(fnb, ptype, plsb)
                ok = (0 <= r.get('slice_type',99) <= 9 and r.get('pps_id',99) <= 3
                      and abs(r.get('delta_poc_bottom', 0)) < 100 and abs(r.get('delta_poc0', 0)) < 100)
                flag = 'OK' if ok else '  '
                print(f'fnb={fnb} ptype={ptype} plsb={plsb}: {flag} {r}')
            except Exception as e:
                print(f'fnb={fnb} ptype={ptype} plsb={plsb}: ERR {e}')
