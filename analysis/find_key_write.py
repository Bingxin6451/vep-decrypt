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

# 找 lea edx/ecx, [reg + 0x48]（正偏移，字符串字段写入准备）
insns = list(md.disasm(td, 0))
hits = []
for i, insn in enumerate(insns):
    ops = insn.op_str
    if insn.mnemonic == 'lea' and '+ 0x48]' in ops and 'ebp' not in ops and 'esp' not in ops:
        # 打印接下来的 4 条指令，看字符串常量
        ctx = []
        for j in range(i, min(i+5, len(insns))):
            ctx.append((tva+insns[j].address, insns[j].mnemonic, insns[j].op_str))
        hits.append(ctx)

print(f'found {len(hits)} lea [reg+0x48]:')
for ctx in hits[:20]:
    for rva, m, o in ctx:
        print(f'  0x{rva+IMG:08x}: {m:8s} {o}')
    print('  ---')
