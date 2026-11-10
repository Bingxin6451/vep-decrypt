#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()

def dump_str(va, n=64):
    off = pe.get_offset_from_rva(va - 0x400000)
    raw = data[off:off+n]
    print(f'=== VA 0x{va:x} ===')
    print('  hex:', raw.hex())
    # 尝试 ASCII
    ascii_s = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw)
    print('  ascii:', ascii_s)
    # 尝试 UTF-16
    try:
        u16 = raw.decode('utf-16-le', errors='replace')
        print('  utf16:', repr(u16[:40]))
    except:
        pass
    print()

# 密钥字符串 + 相邻字符串
dump_str(0x6167e0, 64)
dump_str(0x61675c, 48)
dump_str(0x616790, 48)
dump_str(0x6167fc, 48)
dump_str(0x616824, 48)
