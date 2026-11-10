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
md.skipdata_setup = ('.db', None, None)
IMG = pe.OPTIONAL_HEADER.ImageBase

for s in pe.sections:
    if b'.text' in s.Name:
        td = data[s.PointerToRawData:s.PointerToRawData+s.Misc_VirtualSize]
        tva = s.VirtualAddress
        break

targets = {0x6044f8:'decrypt_loop', 0x604484:'advance', 0x6044dc:'key_byte',
           0x60478c:'crc_update', 0x604544:'init_kdf', 0x5fa100:'block_fn'}
hits = {t: [] for t in targets}
for insn in md.disasm(td, 0):
    if insn.mnemonic == 'call' and insn.operands and insn.operands[0].type == 2:
        imm = insn.operands[0].imm
        if imm in targets:
            hits[imm].append(IMG + tva + insn.address)

for t, name in targets.items():
    print(f'{name} (0x{t:x}): {len(hits[t])} callers')
    for va in hits[t]:
        print(f'  from 0x{va:08x}')
