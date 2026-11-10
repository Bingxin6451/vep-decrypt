#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess

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
for ci in range(1, 300):
    n = spc(ci); base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]; vid += data[base:base+sz]; base += sz; si += 1
vid = bytes(vid)

pps = bytes.fromhex('68ebe72c8b')

from vep_build_sps import BW

def build_sps2(width, height, log2poclsb=8, maxref=4, fmof=1):
    bw = BW()
    bw.put(100, 8)
    bw.put(0, 4); bw.put(0, 4)
    bw.put(40, 8)
    bw.ue(0)  # sps_id
    bw.ue(1)  # chroma_format_idc
    bw.ue(0); bw.ue(0)  # bit depths
    bw.put(0, 1); bw.put(0, 1)  # bypass, scaling matrix
    bw.ue(0)  # log2_max_frame_num_minus4
    bw.ue(0)  # poc_type
    bw.ue(log2poclsb)  # log2_max_pic_order_cnt_lsb_minus4
    bw.ue(maxref)
    bw.put(0, 1)  # gaps
    mbs_w = (width+15)//16; mbs_h = (height+15)//16
    bw.ue(mbs_w-1); bw.ue(mbs_h-1)
    bw.put(fmof, 1)  # frame_mbs_only_flag
    bw.put(1, 1)  # direct_8x8
    crop_b = mbs_h*16 - height
    if crop_b:
        bw.put(1, 1); bw.ue(0); bw.ue(0); bw.ue(0); bw.ue(crop_b//2)
    else:
        bw.put(0, 1)
    bw.put(0, 1)  # vui
    rbsp = bw.to_bytes()
    nal = bytearray([0x67]); zc = 0
    for b in rbsp:
        if zc >= 2 and b <= 3:
            nal.append(0x03); zc = 0
        nal.append(b)
        zc = zc+1 if b == 0 else 0
    return bytes(nal)

def test(log2poclsb, maxref, fmof, w=1920, h=1080):
    sps = build_sps2(w, h, log2poclsb, maxref, fmof)
    annexb = bytearray()
    for nal in [sps, pps]:
        annexb += b'\x00\x00\x00\x01' + nal
    pos = 0
    while pos + 4 <= len(vid):
        L = struct.unpack('>I', vid[pos:pos+4])[0]
        if not (0 < L < 0x1000000) or pos+4+L > len(vid):
            break
        annexb += b'\x00\x00\x00\x01' + vid[pos+4:pos+4+L]
        pos += 4 + L
    fn = '/tmp/sps_v2.h264'
    open(fn, 'wb').write(annexb)
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', fn, '-frames:v', '100', '-f', 'null', '-'],
                       capture_output=True, timeout=120)
    err = r.stderr.decode(errors='replace')
    nerr = len([l for l in err.split('\n') if l.strip()])
    return sps.hex(), nerr

for log2poclsb in [2, 4, 6, 8, 10, 12]:
    for maxref in [1, 2, 3, 4, 8, 16]:
        for fmof in [0, 1]:
            sps, nerr = test(log2poclsb, maxref, fmof)
            if nerr < 50:
                print(f'log2poclsb={log2poclsb} maxref={maxref} fmof={fmof}: errlines={nerr} SPS={sps}')
