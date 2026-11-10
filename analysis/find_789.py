#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

# 1. 反汇编赋值函数 0x408090
def disasm(va, n=30):
    off = pe.get_offset_from_rva(va - 0x400000)
    code = data[off:off+n*8]
    print(f'=== 0x408090 赋值函数 ===')
    cnt = 0
    for insn in md.disasm(code, va):
        print(f'  0x{insn.address:08x}: {insn.mnemonic:8s} {insn.op_str}')
        cnt += 1
        if insn.mnemonic == 'ret' and cnt > 2:
            break
        if cnt >= n:
            break
    print()

disasm(0x408090)

# 2. 搜索 "789789" 的所有出现（UTF-16 和 ASCII）
print('=== "789789" 出现位置 ===')
for pat, name in [(b'7\x008\x009\x007\x008\x009\x00', 'UTF16LE'), 
                  (b'\x007\x008\x009\x007\x008\x009', 'UTF16BE'),
                  (b'789789', 'ASCII')]:
    for m in re.finditer(re.escape(pat), data):
        print(f'  {name} @ file 0x{m.start():x}')
