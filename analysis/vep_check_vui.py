#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from decode_vep import build_sps, BW

sps = build_sps(1920, 1080)
print('SPS:', sps.hex())

# parse SPS to verify VUI
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

# remove NAL header + emulation prevention
rbsp = bytearray()
zc = 0
for b in sps[1:]:
    if zc >= 2 and b == 3:
        zc = 0
        continue
    rbsp.append(b)
    zc = zc+1 if b == 0 else 0
rbsp = bytes(rbsp)
print('RBSP:', rbsp.hex())

br = BR(rbsp)
prof = br.bits(8); cons = br.bits(8); level = br.bits(8)
spsid = br.ue()
chroma = br.ue()
bd_l = br.ue(); bd_c = br.ue()
bypass = br.bit(); scal = br.bit()
fn = br.ue(); poc = br.ue(); poclsb = br.ue(); maxref = br.ue(); gaps = br.bit()
mw = br.ue(); mh = br.ue()
fmof = br.bit(); d8 = br.bit()
cropf = br.bit()
if cropf:
    br.ue(); br.ue(); br.ue(); cropb = br.ue()
else:
    cropb = 0
vui = br.bit()
print(f'profile={prof} level={level} sps_id={spsid} chroma={chroma} poclsb={poclsb} maxref={maxref}')
print(f'width_mbs={mw+1} height_mbs={mh+1} fmof={fmof} crop_bottom={cropb} vui_flag={vui}')
if vui:
    ar = br.bit(); ov = br.bit(); vs = br.bit(); cl = br.bit(); ti = br.bit()
    print(f'  aspect={ar} overscan={ov} video_signal={vs} chroma_loc={cl} timing={ti}')
    if ti:
        nuit = br.bits(32); ts = br.bits(32); ffr = br.bit()
        print(f'  num_units_in_tick={nuit} time_scale={ts} fixed_frame_rate={ffr}')
        print(f'  -> fps = {ts}/{nuit} = {ts/nuit if nuit else 0}')
