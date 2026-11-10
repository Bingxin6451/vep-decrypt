#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()

# key string RVAs
targets = {
    0x1ff091: 'DecryptHeaderByte',
    0x1ff184: 'DecryptHeaderByte2',
    0x1fcf26: 'DecryptKey',
    0x1fcf4a: 'DecryptHeaderType',
    0x1ff11a: 'num_to_decrypt',
    0x1ff133: 'GetDecryptHeaderPtr',
    0x1ff0df: 'decrypt_buff',
}

# get .text section data
for s in pe.sections:
    if b'.text' in s.Name:
        text_va = s.VirtualAddress
        text_raw = s.PointerToRawData
        text_size = s.Misc_VirtualSize
        text_data = data[text_raw:text_raw+text_size]
        break

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

# scan for references: push imm32, lea, mov with these RVAs
refs = {}
for insn in md.disasm(text_data, 0):
    # push imm32
    if insn.mnemonic == 'push' and insn.operands and insn.operands[0].type == 2:  # imm
        imm = insn.operands[0].imm
        if imm in targets:
            va = text_va + insn.address
            refs.setdefault(imm, []).append(va)
    # lea eax/ecx/edx, [imm]
    if insn.mnemonic == 'lea' and insn.operands:
        op = insn.operands[1]
        if op.type == 3:  # memory
            if op.mem.disp in targets:
                va = text_va + insn.address
                refs.setdefault(op.mem.disp, []).append(va)

for imm, name in targets.items():
    if imm in refs:
        print(f'{name} (0x{imm:x}):')
        for va in refs[imm]:
            print(f'    referenced at VA 0x{va:x}')
    else:
        print(f'{name} (0x{imm:x}): no direct ref found')
