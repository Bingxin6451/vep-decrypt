#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile, struct

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()

targets = {0x6044f8:'decrypt_loop', 0x604484:'advance', 0x6044dc:'key_byte',
           0x60478c:'crc_update', 0x604544:'init_kdf', 0x5fa100:'block_fn',
           0x6044c4:'?', 0x60452c:'?'}

for s in pe.sections:
    raw = s.PointerToRawData
    size = s.SizeOfRawData
    for i in range(0, size-4, 4):
        v = struct.unpack('<I', data[raw+i:raw+i+4])[0]
        if v in targets:
            rva = s.VirtualAddress + i
            print(f'{targets[v]} (0x{v:x}) ptr @ {s.Name.decode().strip()} RVA 0x{rva:x} VA 0x{rva+0x400000:x}')
