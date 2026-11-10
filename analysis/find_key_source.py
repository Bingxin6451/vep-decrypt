#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
IMG = pe.OPTIONAL_HEADER.ImageBase

target = 0x604544

# 1. search data pointers == target
print('=== 数据节区里指向 0x604544 的指针 ===')
for s in pe.sections:
    raw = s.PointerToRawData
    size = s.SizeOfRawData
    for i in range(0, size-4, 4):
        v = struct.unpack('<I', data[raw+i:raw+i+4])[0]
        if v == target:
            print(f'  {s.Name.decode().strip()} file 0x{raw+i:x} RVA 0x{s.VirtualAddress+i:x}')

# 2. search all call instructions with target near 0x604544
print('=== call 到 0x604540~0x604550 的指令 ===')
for s in pe.sections:
    if b'.text' in s.Name:
        td = data[s.PointerToRawData:s.PointerToRawData+s.Misc_VirtualSize]
        tva = s.VirtualAddress
        break
for insn in md.disasm(td, 0):
    if insn.mnemonic == 'call':
        for op in insn.operands:
            if op.type == 1:  # imm
                tgt = op.imm
                if 0x604540 <= tgt <= 0x604560:
                    va = IMG + tva + insn.address
                    print(f'  0x{va:08x}: call 0x{tgt:x}')
