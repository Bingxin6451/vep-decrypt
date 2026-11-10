#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(o): return struct.unpack('>I', data[o:o+4])[0]

vsizes = [u32be(580674 + i*4) for i in range(72625)]
vcoffs = [u32be(871190 + i*4) for i in range(10375)]
def spc(ci):
    return 8 if ci == 1 else (7 if ci <= 10374 else 6)

# encrypted chunks (1-based): 3826..3831 and 7908..7926
enc_chunks = set(range(3826, 3832)) | set(range(7908, 7927))

# rebuild video stream, skipping encrypted chunks (insert placeholder)
vid = bytearray()
si = 0
for ci in range(1, 10376):
    n = spc(ci)
    base = vcoffs[ci-1] + 16
    if ci in enc_chunks:
        # skip these samples (encrypted) - will be handled separately
        for k in range(n):
            si += 1
        continue
    for k in range(n):
        sz = vsizes[si]
        vid += data[base:base+sz]
        base += sz
        si += 1
vid = bytes(vid)
print('plaintext video stream bytes:', len(vid))

# build correct SPS
class BW:
    def __init__(self): self.bits = []
    def put(self, v, n):
        for i in range(n-1, -1, -1): self.bits.append((v >> i) & 1)
    def ue(self, v):
        codeNum = v + 1; nbits = codeNum.bit_length()
        self.bits.extend([0] * (nbits - 1)); self.put(codeNum, nbits)
    def to_bytes(self):
        self.bits.append(1)
        while len(self.bits) % 8: self.bits.append(0)
        out = bytearray()
        for i in range(0, len(self.bits), 8):
            b = 0
            for j in range(8): b = (b << 1) | self.bits[i+j]
            out.append(b)
        return bytes(out)

def build_sps(w, h):
    bw = BW()
    bw.put(100, 8); bw.put(0, 4); bw.put(0, 4); bw.put(40, 8)
    bw.ue(0); bw.ue(1); bw.ue(0); bw.ue(0); bw.put(0,1); bw.put(0,1)
    bw.ue(0); bw.ue(0); bw.ue(2); bw.ue(4); bw.put(0,1)  # log2poclsb=2 maxref=4
    mw=(w+15)//16; mh=(h+15)//16
    bw.ue(mw-1); bw.ue(mh-1); bw.put(1,1); bw.put(1,1)
    cb = mh*16-h
    if cb: bw.put(1,1); bw.ue(0); bw.ue(0); bw.ue(0); bw.ue(cb//2)
    else: bw.put(0,1)
    bw.put(0,1)
    rbsp = bw.to_bytes()
    nal = bytearray([0x67]); zc=0
    for b in rbsp:
        if zc>=2 and b<=3: nal.append(0x03); zc=0
        nal.append(b); zc = zc+1 if b==0 else 0
    return bytes(nal)

sps = build_sps(1920, 1080)
pps = bytes.fromhex('68ebe72c8b')
print('SPS:', sps.hex())

# assemble annexb
annexb = bytearray()
for n in [sps, pps]:
    annexb += b'\x00\x00\x00\x01' + n
pos = 0
while pos + 4 <= len(vid):
    L = struct.unpack('>I', vid[pos:pos+4])[0]
    if not (0 < L < 0x1000000) or pos+4+L > len(vid): break
    annexb += b'\x00\x00\x00\x01' + vid[pos+4:pos+4+L]
    pos += 4 + L
open('/tmp/full.h264', 'wb').write(annexb)
print('annexb size:', len(annexb))

# decode with ffmpeg, count errors
r = subprocess.run(['ffmpeg','-v','error','-i','/tmp/full.h264','-f','null','-'],
                   capture_output=True, timeout=300)
err = r.stderr.decode(errors='replace')
errlines = [l for l in err.split('\n') if l.strip()]
print('ffmpeg error lines:', len(errlines))
for l in errlines[:5]:
    print('  ', l[:120])

# probe
r2 = subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,nb_frames','-of','csv=p=0','/tmp/full.h264'],
                    capture_output=True, timeout=60)
print('probe:', r2.stdout.decode().strip(), r2.stderr.decode().strip())
