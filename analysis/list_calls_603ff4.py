#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

# 反汇编 0x603ff4~0x604471，grep 所有 call
off = pe.get_offset_from_rva(0x603ff4 - 0x400000)
off2 = pe.get_offset_from_rva(0x604471 - 0x400000)
code = data[off:off2]
for insn in md.disasm(code, 0x603ff4):
    if insn.mnemonic == 'call':
        # 解析目标
        import re
        m = re.search(r'0x([0-9a-f]+)', insn.op_str)
        tgt = int(m.group(1), 16) if m else None
        print(f'  0x{insn.address:08x}: call {insn.op_str}')
