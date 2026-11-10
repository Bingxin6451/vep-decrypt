#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
IMG = pe.OPTIONAL_HEADER.ImageBase

targets = {0x6044f8: 'decrypt_loop', 0x604484: 'advance', 0x6044dc: 'key_byte',
           0x60478c: 'crc_update', 0x604544: 'init_kdf'}

for s in pe.sections:
    if b'.text' in s.Name:
        td = data[s.PointerToRawData:s.PointerToRawData+s.Misc_VirtualSize]
        tva = s.VirtualAddress
        break

hits = {t: [] for t in targets}
for insn in md.disasm(td, 0):
    if insn.mnemonic == 'call':
        for op in insn.operands:
            if op.type == 1:
                tgt = op.imm
                if tgt in targets:
                    va = IMG + tva + insn.address
                    hits[tgt].append(va)

for t, name in targets.items():
    print(f'=== {name} (0x{t:x}) 调用者: ===')
    for va in hits[t]:
        print(f'  from 0x{va:08x}')
    if not hits[t]:
        print('  (无)')
