#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile, struct

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()

# key string RVAs -> file offsets
keys = {'DecryptKey': 0x1fcf26, 'DecryptHeaderType': 0x1fcf4a,
        'decrypt_buff': 0x1ff0df, 'DecryptHeaderByte': 0x1ff091,
        'num_to_decrypt': 0x1ff11a, 'GetDecryptHeaderPtr': 0x1ff133}

def rva2off(rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + s.Misc_VirtualSize:
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

for name, rva in keys.items():
    off = rva2off(rva)
    if off is None:
        continue
    print(f'=== {name} @ RVA 0x{rva:x} file 0x{off:x} ===')
    # dump surrounding 96 bytes
    region = data[off-32:off+96]
    print('  raw:', region.hex())
    # look for pointers (aligned dwords pointing into .text VA 0x1000..0x253cb0)
    base = rva - 32
    for i in range(0, len(region)-4, 4):
        d = struct.unpack('<I', region[i:i+4])[0]
        rva_at = base + i
        if 0x1000 <= d <= 0x253cb0:
            print(f'    ptr @ RVA 0x{rva_at:x} -> 0x{d:x}')
