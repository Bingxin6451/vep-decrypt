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

# 找写入 [reg + 0x48] 字段的指令（正偏移，排除 ebp/esp 局部变量）
hits = []
for insn in md.disasm(td, 0):
    ops = insn.op_str
    # 写字段: mov [reg+0x48], ... 或 lea reg2, [reg+0x48]（字符串赋值准备）
    if (insn.mnemonic in ('mov', 'lea') and '+ 0x48]' in ops
            and '[ebp' not in ops and '[esp' not in ops and 'dword ptr [ebp' not in ops
            and ', 0x48' not in ops):
        hits.append((tva + insn.address, insn.mnemonic, ops))

print(f'found {len(hits)} writes/leas to [reg+0x48]:')
for rva, m, o in hits:
    print(f'  0x{rva+IMG:08x}: {m:8s} {o}')
