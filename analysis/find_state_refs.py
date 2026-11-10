#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
IMG = pe.OPTIONAL_HEADER.ImageBase

for s in pe.sections:
    if b'.text' in s.Name:
        text_data = data[s.PointerToRawData:s.PointerToRawData+s.Misc_VirtualSize]
        text_va = s.VirtualAddress
        break

# search instructions referencing +0x178 / +0x17c / +0x180
hits = []
for insn in md.disasm(text_data, 0):
    ops = insn.op_str
    if '0x178' in ops or '0x17c' in ops or '0x180' in ops:
        va = IMG + text_va + insn.address
        hits.append((va, insn.mnemonic, ops))
        if len(hits) >= 60:
            break

print(f'found {len(hits)} references:')
for va, m, ops in hits:
    print(f'  0x{va:08x}: {m:8s} {ops}')
