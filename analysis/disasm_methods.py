#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()

md = Cs(CS_ARCH_X86, CS_MODE_32)

def disasm(va, n=60):
    off = pe.get_offset_from_rva(va - 0x400000)
    if off is None:
        print(f'bad va {va:x}')
        return
    code = data[off:off+n*10]
    print(f'--- VA 0x{va:x} ---')
    cnt = 0
    for insn in md.disasm(code, va):
        print(f'  0x{insn.address:08x}: {insn.mnemonic:8s} {insn.op_str}')
        cnt += 1
        if insn.mnemonic == 'ret' and cnt > 2:
            break
        if cnt >= n:
            break

# candidate method addresses found in RTTI region
addrs = [0x40598c, 0x405994, 0x41c784, 0x405ba8, 0x405bc8, 0x405bcc, 0x405bd0, 0x405bc4, 0x405868, 0x405884, 0x4102d4]
for a in addrs:
    disasm(a, 25)
    print()
