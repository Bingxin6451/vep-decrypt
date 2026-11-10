#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, subprocess

class BW:
    def __init__(self): self.bits = []
    def put(self, v, n):
        for i in range(n-1, -1, -1):
            self.bits.append((v >> i) & 1)
    def ue(self, v):
        codeNum = v + 1
        nbits = codeNum.bit_length()
        self.bits.extend([0] * (nbits - 1))
        self.put(codeNum, nbits)
    def se(self, v):
        codeNum = 2*v - 1 if v > 0 else -2*v
        self.ue(codeNum)
    def to_bytes(self):
        self.bits.append(1)  # rbsp_stop_one_bit
        while len(self.bits) % 8 != 0:
            self.bits.append(0)
        out = bytearray()
        for i in range(0, len(self.bits), 8):
            b = 0
            for j in range(8):
                b = (b << 1) | self.bits[i+j]
            out.append(b)
        return bytes(out)

def build_sps(width, height, profile=100, level=40):
    bw = BW()
    bw.put(profile, 8)
    bw.put(0, 4)       # constraint_set0..3
    bw.put(0, 4)       # reserved
    bw.put(level, 8)
    bw.ue(0)           # sps_id
    # High-profile extra fields
    bw.ue(1)           # chroma_format_idc = 1 (4:2:0)
    bw.ue(0)           # bit_depth_luma_minus8
    bw.ue(0)           # bit_depth_chroma_minus8
    bw.put(0, 1)       # qpprime_y_zero_transform_bypass_flag
    bw.put(0, 1)       # seq_scaling_matrix_present_flag
    bw.ue(0)           # log2_max_frame_num_minus4 -> frame_num 4 bits
    bw.ue(0)           # pic_order_cnt_type
    bw.ue(8)           # log2_max_pic_order_cnt_lsb_minus4 -> 12 bits
    bw.ue(4)           # max_num_ref_frames
    bw.put(0, 1)       # gaps_in_frame_num_value_allowed_flag
    mbs_w = (width + 15) // 16
    mbs_h = (height + 15) // 16
    bw.ue(mbs_w - 1)
    bw.ue(mbs_h - 1)
    bw.put(1, 1)       # frame_mbs_only_flag
    bw.put(1, 1)       # direct_8x8_inference_flag
    crop_b = mbs_h * 16 - height
    if crop_b or width % 16 or height % 16:
        bw.put(1, 1)
        bw.ue(0); bw.ue(0); bw.ue(0); bw.ue(crop_b // 2)
    else:
        bw.put(0, 1)
    bw.put(0, 1)       # vui_parameters_present_flag
    rbsp = bw.to_bytes()

    # NAL + emulation prevention
    nal = bytearray([0x67])
    zero_count = 0
    for b in rbsp:
        if zero_count >= 2 and b <= 3:
            nal.append(0x03)
            zero_count = 0
        nal.append(b)
        if b == 0:
            zero_count += 1
        else:
            zero_count = 0
    return bytes(nal)

if __name__ == '__main__':
    for res in ['1920x1080', '1280x720', '854x480', '640x360', '1024x576', '1440x900']:
        w, h = map(int, res.split('x'))
        sps = build_sps(w, h)
        print(f'{res}: SPS = {sps.hex()}')
