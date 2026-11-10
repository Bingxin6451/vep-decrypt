#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Parse the PPS (68 eb e7 2c 8b) to get encoding params
class BitReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0
    def read_bit(self):
        b = (self.data[self.pos // 8] >> (7 - self.pos % 8)) & 1
        self.pos += 1
        return b
    def read_bits(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.read_bit()
        return v
    def ue(self):
        zeros = 0
        while self.read_bit() == 0:
            zeros += 1
        v = (1 << zeros) - 1
        for _ in range(zeros):
            v = (v << 1) | self.read_bit()
        return v
    def se(self):
        codeNum = self.ue()
        return (codeNum + 1) // 2 if codeNum % 2 == 1 else -(codeNum // 2)

pps = bytes.fromhex('68ebe72c8b')
# strip NAL header (first byte) and emulation prevention
rbsp = pps[1:]
br = BitReader(rbsp)
print('PPS parse:')
print('  pps_id:', br.ue())
print('  sps_id:', br.ue())
print('  entropy_coding_mode_flag (CABAC):', br.read_bit())
print('  bottom_field_pic_order_in_frame_present_flag:', br.read_bit())
print('  num_slice_groups_minus1:', br.ue())
print('  num_ref_idx_l0_default_active_minus1:', br.ue())
print('  num_ref_idx_l1_default_active_minus1:', br.ue())
print('  weighted_pred_flag:', br.read_bit())
print('  weighted_bipred_idc:', br.read_bits(2))
print('  pic_init_qp_minus26:', br.se())
print('  pic_init_qs_minus26:', br.se())
print('  chroma_qp_index_offset:', br.se())
print('  deblocking_filter_control_present_flag:', br.read_bit())
print('  constrained_intra_pred_flag:', br.read_bit())
print('  redundant_pic_cnt_present_flag:', br.read_bit())
print('  total bits consumed:', br.pos, '/', len(rbsp)*8)
