#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
print('ImageBase:', hex(pe.OPTIONAL_HEADER.ImageBase))
print('EntryPoint:', hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint))
print('sections:')
for s in pe.sections:
    print(f'  {s.Name.decode().strip():10s} VA={hex(s.VirtualAddress)} size={hex(s.Misc_VirtualSize)} raw={hex(s.PointerToRawData)}')

# find key strings and their RVA
targets = [b'DecryptHeaderByte', b'DecryptKey', b'DecryptHeaderType', b'num_to_decrypt',
           b'EncryptionStrength', b'GetDecryptHeaderPtr', b'decrypt_buff']
print('\nstring locations:')
data = open(fn, 'rb').read()
for t in targets:
    found = []
    start = 0
    while True:
        i = data.find(t, start)
        if i < 0:
            break
        found.append(i)
        start = i + 1
    for off in found:
        rva = pe.get_rva_from_offset(off)
        print(f'  {t.decode():24s} file=0x{off:x} RVA=0x{rva:x}')
