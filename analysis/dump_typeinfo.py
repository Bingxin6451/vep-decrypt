#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pefile, struct

fn = 'samples/dhf_encryption_helper.bin'
pe = pefile.PE(fn)
data = open(fn, 'rb').read()
IMG = pe.OPTIONAL_HEADER.ImageBase

def rva2off(rva):
    return pe.get_offset_from_rva(rva)

# dump 0x40109c region
for va in [0x40109c, 0x40104c, 0x4010b4]:
    off = rva2off(va - IMG)
    if off is None:
        continue
    raw = data[off:off+48]
    print(f'VA 0x{va:x}: {raw.hex()}')
    print(f'  ascii: {raw!r}')
    print()

# Also: Delphi type info - look at what 0x40109c points to
# TTypeInfo: Kind(1) + Name(ShortString)
off = rva2off(0x40109c - IMG)
if off:
    kind = data[off]
    name_len = data[off+1]
    name = data[off+2:off+2+name_len]
    print(f'0x40109c as TTypeInfo: kind={kind} name={name}')
