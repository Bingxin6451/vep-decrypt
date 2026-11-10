#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)
IMG = pe.OPTIONAL_HEADER.ImageBase

def rva(va): return pe.get_offset_from_rva(va - IMG)

# 0x667c6c stores the table base pointer
ptr = struct.unpack('<I', data[rva(0x667c6c):rva(0x667c6c)+4])[0]
print(f'[0x667c6c] -> table base = 0x{ptr:x}')

# dump the 256-entry table at that pointer
tbl_off = rva(ptr)
table = struct.unpack('<256I', data[tbl_off:tbl_off+1024])
print('S-box table (256 uint32):')
for i in range(0, 256, 8):
    print('  ' + ' '.join(f'{v:08x}' for v in table[i:i+8]))
