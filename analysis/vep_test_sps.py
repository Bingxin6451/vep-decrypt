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

# build first 500 chunks of plaintext video
vid = bytearray()
si = 0
for ci in range(1, 500):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)

pps = bytes.fromhex('68ebe72c8b')

from vep_build_sps import build_sps

def test_res(w, h):
    sps = build_sps(w, h)
    # build annexb: SPS + PPS + video
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
    fn = f'/tmp/sps_test_{w}x{h}.h264'
    open(fn, 'wb').write(annexb)
    # decode test: count frames, check errors
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', fn, '-frames:v', '50', '-f', 'null', '-'],
                       capture_output=True, timeout=90)
    err = r.stderr.decode(errors='replace')
    # count error lines
    errlines = [l for l in err.split('\n') if l.strip()]
    r2 = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                         '-show_entries', 'stream=nb_read_frames,width,height', '-of', 'csv=p=0', fn],
                        capture_output=True, timeout=60)
    info = r2.stdout.decode().strip()
    return info, len(errlines), err[:200]

for res in ['1920x1080', '1280x720', '854x480', '640x360', '1024x576', '1440x900']:
    w, h = map(int, res.split('x'))
    info, nerr, err = test_res(w, h)
    print(f'{res}: {info} | errlines={nerr} | {err[:100]}')
