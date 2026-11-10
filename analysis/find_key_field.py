#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True
IMG = pe.OPTIONAL_HEADER.ImageBase

for s in pe.sections:
    if b'.text' in s.Name:
        td = data[s.PointerToRawData:s.PointerToRawData+s.Misc_VirtualSize]
        tva = s.VirtualAddress
        break

# search instructions referencing +0x48 (key string field)
hits = []
for insn in md.disasm(td, 0):
    ops = insn.op_str
    if '0x48' in ops and ('mov' in insn.mnemonic or 'lea' in insn.mnemonic):
        hits.append((tva + insn.address, insn.mnemonic, ops))
    if len(hits) >= 50:
        break

print(f'found {len(hits)} refs to +0x48:')
for rva, m, ops in hits:
    print(f'  0x{rva+IMG:08x}: {m:8s} {ops}')
