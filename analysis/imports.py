#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)

print('=== 导入的 DLL 和加密相关函数 ===')
if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll = entry.dll.decode()
        funcs = [imp.name.decode() if imp.name else f'ord{imp.ordinal}' for imp in entry.imports]
        crypto = [f for f in funcs if any(k in f.lower() for k in ['crypt', 'aes', 'rc4', 'evp', 'md5', 'sha', 'rand', 'des', 'blow', 'hash', 'seed', 'cipher'])]
        if crypto:
            print(f'\n[{dll}] ({len(funcs)} funcs):')
            print('  crypto相关:', crypto)
