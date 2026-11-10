#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess
from decode_vep import VepDecoder, build_sps, u32

d = VepDecoder('sample.vep')
d.parse_trak()
d.decode('x.mp4')

# video annexb
sps = build_sps(1920, 1080)
pps = bytes.fromhex('68ebe72c8b')
ab = bytearray()
for n in [sps, pps]:
    ab += b'\x00\x00\x00\x01' + n
pos = 0; v = d.vid
while pos+4 <= len(v):
    L = u32(v, pos)
    if not (0 < L < 0x1000000) or pos+4+L > len(v):
        break
    ab += b'\x00\x00\x00\x01' + v[pos+4:pos+4+L]
    pos += 4 + L
open('/tmp/v.h264', 'wb').write(ab)

# audio (from main logic)
asz_off, aco_off, acc = d.audio
acount = u32(d.data, asz_off + 12)
asizes = [u32(d.data, asz_off + 16 + 4*i) for i in range(acount)]
achunks = [u32(d.data, aco_off + 12 + 4*i) + 16 for i in range(acc)]
astsc = d._parse_stsc(d._find_stsc(asz_off))
adts = bytearray()
si = 0
for ci in range(acc):
    ns = d._samples_per_chunk(astsc, ci+1)
    base = achunks[ci]
    for k in range(ns):
        if si >= acount: break
        sz = asizes[si]
        if base + sz <= d.n:
            raw = d.data[base:base+sz]
            fl = sz + 7
            adts += bytes([0xFF, 0xF1, (1<<6)|(4<<2)|(2>>2), ((2&3)<<6)|((fl>>11)&3),
                           (fl>>3)&0xFF, ((fl&7)<<5)|0x1F, 0xFC]) + raw
        base += sz
        si += 1
open('/tmp/a.aac', 'wb').write(adts)
print('h264:', len(ab), 'aac:', len(adts))

r = subprocess.run(['ffprobe','-v','error','-show_entries','stream=r_frame_rate,avg_frame_rate,nb_frames,duration','-of','csv=p=0','/tmp/v.h264'],capture_output=True,text=True)
print('h264 probe:', r.stdout.strip())
r2 = subprocess.run(['ffprobe','-v','error','-show_entries','stream=sample_rate,channels,duration','-of','csv=p=0','/tmp/a.aac'],capture_output=True,text=True)
print('aac probe:', r2.stdout.strip())

# test mux with different params
for label, extra in [
    ('copy', ['-c','copy']),
    ('copy-r15.12', ['-c','copy','-r','15120/1000']),
    ('genpts', ['-c','copy','-fflags','+genpts']),
]:
    out = f'/tmp/test_{label}.mp4'
    cmd = ['ffmpeg','-y','-v','error','-i','/tmp/v.h264','-i','/tmp/a.aac'] + extra + ['-movflags','+faststart', out]
    subprocess.run(cmd, capture_output=True)
    rr = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out],capture_output=True,text=True)
    print(f'{label}: duration = {rr.stdout.strip()}')
