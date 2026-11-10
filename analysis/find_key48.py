#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

# 搜索 0x602000~0x608000 范围内引用 +0x48 字段的指令
lo, hi = 0x602000, 0x608000
off0 = pe.get_offset_from_rva(lo - 0x400000)
off1 = pe.get_offset_from_rva(hi - 0x400000)
code = data[off0:off1]

hits = []
for insn in md.disasm(code, lo):
    ops = insn.op_str
    if '+ 0x48]' in ops or ', 0x48' in ops:
        hits.append((insn.address, insn.mnemonic, ops))
    if insn.address > hi:
        break

print(f'found {len(hits)} refs to +0x48 in 0x602000-0x608000:')
for va, m, o in hits:
    print(f'  0x{va:08x}: {m:8s} {o}')
