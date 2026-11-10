#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess, os, re

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

# build plaintext video stream
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

# extract original PPS (68 eb e7 2c 8b)
orig_pps = bytes.fromhex('68ebe72c8b')

# generate SPS for various resolutions via ffmpeg + x264
resolutions = ['1920x1080', '1280x720', '1024x768', '1366x768', '1440x900',
               '800x600', '640x480', '960x540', '854x480', '1600x900', '1152x720', '1024x576']

def gen_sps(w, h):
    cmd = ['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={w}x{h}:d=0.1',
           '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'ultrafast',
           '-x264-params', 'keyint=1:ref=3', '-frames:v', '1', '-f', 'h264', 'pipe:1']
    out = subprocess.run(cmd, capture_output=True).stdout
    # find SPS NAL (annexb: 00 00 00 01 67 ...)
    sps_list = []
    for m in re.finditer(b'\x00\x00\x00\x01\x67', out):
        start = m.start() + 4
        end = out.find(b'\x00\x00\x00\x01', start)
        if end == -1:
            end = len(out)
        sps = out[start:end]
        # remove trailing zeros
        sps = sps.rstrip(b'\x00')
        sps_list.append(sps)
    return sps_list[0] if sps_list else None

def build_avcc(sps, pps):
    # avcC box content
    avcc = b'\x01' + sps[1:4] + b'\xff\xe1'  # configVersion, profile, compat, level, numSPS=1
    avcc += struct.pack('>H', len(sps)) + sps
    avcc += b'\x01' + struct.pack('>H', len(pps)) + pps
    return avcc

def inject_sps(sps):
    # build AVCC stream: SPS + PPS + original stream, then convert to annexb for ffmpeg
    avcc_stream = bytearray()
    for nal in [sps, orig_pps]:
        avcc_stream += struct.pack('>I', len(nal))
        avcc_stream += nal
    avcc_stream += vid
    # convert to annexb
    annexb = bytearray()
    pos = 0
    while pos + 4 <= len(avcc_stream):
        L = struct.unpack('>I', avcc_stream[pos:pos+4])[0]
        if not (0 < L < 0x1000000) or pos + 4 + L > len(avcc_stream):
            break
        annexb += b'\x00\x00\x00\x01'
        annexb += avcc_stream[pos+4:pos+4+L]
        pos += 4 + L
    return bytes(annexb), pos

for res in resolutions:
    w, h = map(int, res.split('x'))
    sps = gen_sps(w, h)
    if not sps:
        print(f'{res}: failed to gen SPS')
        continue
    annexb, consumed = inject_sps(sps)
    fn = f'/tmp/test_{w}x{h}.h264'
    open(fn, 'wb').write(annexb)
    # ffmpeg decode test: count decoded frames
    cmd = ['ffmpeg', '-v', 'error', '-i', fn, '-f', 'null', '-']
    r = subprocess.run(cmd, capture_output=True)
    err = r.stderr.decode()
    # count frames decoded via -f framemd5? simpler: check no 'error'
    has_err = ('error' in err.lower() or 'invalid' in err.lower() or 'corrupt' in err.lower())
    # get frame count
    cmd2 = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
            '-show_entries', 'stream=nb_read_frames,width,height', '-of', 'csv=p=0', fn]
    r2 = subprocess.run(cmd2, capture_output=True)
    info = r2.stdout.decode().strip()
    print(f'{res}: SPS={sps.hex()} frames={info} err={err[:80] if err else "none"}')
