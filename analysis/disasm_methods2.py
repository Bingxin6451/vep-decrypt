#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

def disasm(va, n=50):
    off = pe.get_offset_from_rva(va - 0x400000)
    if off is None:
        print(f'bad va {va:x}')
        return
    code = data[off:off+n*8]
    print(f'--- VA 0x{va:x} ---')
    cnt = 0
    for insn in md.disasm(code, va):
        print(f'  0x{insn.address:08x}: {insn.mnemonic:8s} {insn.op_str}')
        cnt += 1
        if insn.mnemonic == 'ret' and cnt > 2:
            break
        if cnt >= n:
            break

for a in [0x6044f8, 0x605dc8, 0x60469c, 0x604660]:
    disasm(a, 35)
    print()
