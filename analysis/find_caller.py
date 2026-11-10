#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
IMG = pe.OPTIONAL_HEADER.ImageBase

target = 0x604544
for s in pe.sections:
    if b'.text' in s.Name:
        text_data = data[s.PointerToRawData:s.PointerToRawData+s.Misc_VirtualSize]
        text_va = s.VirtualAddress
        break

# search for direct call / mov / push referencing target
hits = []
for insn in md.disasm(text_data, 0):
    ops = insn.op_str
    if insn.mnemonic == 'call' and insn.operands and insn.operands[0].type == 1:  # imm (rel)
        tgt = insn.operands[0].imm
        if tgt == target:
            hits.append((IMG+text_va+insn.address, 'call', ops))
    elif hex(target) in ops and insn.mnemonic in ('mov', 'push', 'lea'):
        hits.append((IMG+text_va+insn.address, insn.mnemonic, ops))
    if len(hits) >= 40:
        break

print(f'found {len(hits)} references to 0x{target:x}:')
for va, m, ops in hits:
    print(f'  0x{va:08x}: {m:6s} {ops}')
