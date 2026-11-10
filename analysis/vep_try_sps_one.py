#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess, re, sys

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
for ci in range(1, 3826):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)

orig_pps = bytes.fromhex('68ebe72c8b')

# generate SPS for one resolution
def gen_sps(w, h):
    cmd = ['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={w}x{h}:d=0.1',
           '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'ultrafast',
           '-x264-params', 'keyint=1', '-frames:v', '1', '-f', 'h264', 'pipe:1']
    out = subprocess.run(cmd, capture_output=True, timeout=30).stdout
    for m in re.finditer(b'\x00\x00\x00\x01\x67', out):
        start = m.start() + 4
        end = out.find(b'\x00\x00\x00\x01', start)
        if end == -1:
            end = len(out)
        sps = out[start:end].rstrip(b'\x00')
        return sps
    return None

res = sys.argv[1] if len(sys.argv) > 1 else '1920x1080'
w, h = map(int, res.split('x'))
sps = gen_sps(w, h)
print(f'{res}: SPS={sps.hex() if sps else None}')

if sps:
    # build AVCC stream with SPS + PPS + video, convert annexb
    avcc = bytearray()
    for nal in [sps, orig_pps]:
        avcc += struct.pack('>I', len(nal)) + nal
    avcc += vid
    annexb = bytearray()
    pos = 0
    while pos + 4 <= len(avcc):
        L = struct.unpack('>I', avcc[pos:pos+4])[0]
        if not (0 < L < 0x1000000) or pos + 4 + L > len(avcc):
            break
        annexb += b'\x00\x00\x00\x01' + avcc[pos+4:pos+4+L]
        pos += 4 + L
    fn = f'/tmp/test_{w}x{h}.h264'
    open(fn, 'wb').write(annexb)
    # decode only 30 frames max
    cmd = ['ffmpeg', '-v', 'error', '-i', fn, '-frames:v', '30', '-f', 'null', '-']
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    err = r.stderr.decode()
    cmd2 = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
            '-show_entries', 'stream=nb_read_frames,width,height,pix_fmt', '-of', 'csv=p=0', fn]
    r2 = subprocess.run(cmd2, capture_output=True, timeout=30)
    print(f'  decode result: frames={r2.stdout.decode().strip()} err={err[:120] if err else "OK"}')
