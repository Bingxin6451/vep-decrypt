#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

# dump S-box table at VA 0x667c6c
tbl_va = 0x667c6c
off = pe.get_offset_from_rva(tbl_va - 0x400000)
table = struct.unpack('<256I', data[off:off+1024])
print('S-box table (256 uint32):')
print(' '.join(f'{v:08x}' for v in table[:64]))
print('...')
print(' '.join(f'{v:08x}' for v in table[64:80]))
print()

# check if it's a CRC32 table (poly 0xEDB88320) or custom
# CRC32 table first entries would be 0, 0x77073096, 0xee0e612c...
print('first 4:', [f'{v:08x}' for v in table[:4]])
print('CRC32 poly table check:', 'yes' if table[1] == 0x77073096 else 'no')

# find code that WRITES to [reg+0x178] / [reg+0x17c] / [reg+0x180] (init/seed)
print('\n=== 搜索初始化 state 字段的代码 ===')
for s in pe.sections:
    if b'.text' in s.Name:
        text_data = data[s.PointerToRawData:s.PointerToRawData+s.Misc_VirtualSize]
        text_va = s.VirtualAddress
        break
cnt = 0
for insn in md.disasm(text_data, 0):
    ops = insn.op_str
    if '+ 0x178' in ops or '+ 0x17c' in ops or '+ 0x180' in ops:
        va = text_va + insn.address + 0x400000
        print(f'  0x{va:08x}: {insn.mnemonic} {insn.op_str}')
        cnt += 1
        if cnt >= 30:
            break
