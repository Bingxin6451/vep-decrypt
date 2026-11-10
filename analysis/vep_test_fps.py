#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess
from decode_vep import VepDecoder, build_sps, u32, BW

d = VepDecoder('sample.vep')
d.parse_trak()
d.decode('x.mp4')
print('vid len:', len(d.vid), 'enc samples:', len(d.enc_samples))

# audio
asz_off, aco_off, acc = d.audio
acount = u32(d.data, asz_off + 12)
asizes = [u32(d.data, asz_off + 16 + 4*i) for i in range(acount)]
achunks = [u32(d.data, aco_off + 12 + 4*i) + 16 for i in range(acc)]
astsc = d._parse_stsc(d._find_stsc(asz_off))
adts = bytearray(); si = 0
for ci in range(acc):
    ns = d._samples_per_chunk(astsc, ci+1)
    base = achunks[ci]
    for k in range(ns):
        if si >= acount: break
        sz = asizes[si]
        if base + sz <= d.n:
            raw = d.data[base:base+sz]
            fl = sz + 7
            adts += bytes([0xFF,0xF1,(1<<6)|(4<<2)|(2>>2),((2&3)<<6)|((fl>>11)&3),(fl>>3)&0xFF,((fl&7)<<5)|0x1F,0xFC])+raw
        base += sz; si += 1
open('/tmp/a.aac','wb').write(adts)

pps = bytes.fromhex('68ebe72c8b')

def make_annexb(sps):
    ab = bytearray()
    for n in [sps, pps]: ab += b'\x00\x00\x00\x01'+n
    pos = 0; v = d.vid
    while pos+4 <= len(v):
        L = u32(v, pos)
        if not (0 < L < 0x1000000) or pos+4+L > len(v): break
        ab += b'\x00\x00\x00\x01'+v[pos+4:pos+4+L]; pos += 4+L
    return bytes(ab)

# test different num_units_in_tick
for nuit in [250, 500, 1000, 2000]:
    sps = build_sps(1920, 1080, time_scale=15120, num_units_in_tick=nuit)
    ab = make_annexb(sps)
    open('/tmp/v.h264','wb').write(ab)
    r = subprocess.run(['ffprobe','-v','error','-show_entries','stream=r_frame_rate','-of','csv=p=0','/tmp/v.h264'],capture_output=True,text=True)
    out = f'/tmp/t_{nuit}.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-i','/tmp/v.h264','-i','/tmp/a.aac','-c','copy','-movflags','+faststart',out],capture_output=True)
    rr = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out],capture_output=True,text=True)
    print(f'nuit={nuit}: r_frame_rate={r.stdout.strip()} -> mp4 duration={rr.stdout.strip()}')
