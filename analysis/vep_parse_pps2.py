#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Re-parse PPS with CORRECT ue decoding
class BR:
    def __init__(self, d): self.d, self.p = d, 0
    def bit(self):
        b = (self.d[self.p//8] >> (7-self.p%8)) & 1; self.p += 1; return b
    def ue(self):
        z = 0
        while self.bit() == 0: z += 1
        suffix = 0
        for _ in range(z): suffix = (suffix<<1) | self.bit()
        return (1<<z) - 1 + suffix
    def se(self):
        cn = self.ue()
        return (cn+1)//2 if cn & 1 else -(cn//2)

pps = bytes.fromhex('68eb e72c8b'.replace(' ',''))[1:]  # skip NAL header
# 68 eb e7 2c 8b
pps = bytes.fromhex('ebe72c8b')
br = BR(pps)
print('pps_id:', br.ue())
print('sps_id:', br.ue())
print('entropy_coding_mode_flag:', br.bit())
print('bottom_field_pic_order_in_frame_present_flag:', br.bit())
print('num_slice_groups_minus1:', br.ue())
print('num_ref_idx_l0_default_active_minus1:', br.ue())
print('num_ref_idx_l1_default_active_minus1:', br.ue())
print('weighted_pred_flag:', br.bit())
print('weighted_bipred_idc:', (br.bit()<<1)|br.bit())
print('pic_init_qp_minus26:', br.se())
print('pic_init_qs_minus26:', br.se())
print('chroma_qp_index_offset:', br.se())
print('deblocking_filter_control_present_flag:', br.bit())
print('constrained_intra_pred_flag:', br.bit())
print('redundant_pic_cnt_present_flag:', br.bit())
