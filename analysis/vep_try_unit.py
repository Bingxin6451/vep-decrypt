#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
auth = data[55069173:55069520]

# repeat unit (25 bytes) from the tail of auth block
unit = bytes.fromhex('32647a6667647a6c6667323132617369666a3828292628232a')
print('unit:', unit)

# hypothesis A: plaintext repeat = zeros -> key = unit
# hypothesis B: plaintext repeat = spaces -> key = unit ^ 0x20
# hypothesis C: plaintext repeat = 'A' -> key = unit ^ 0x41
for name, key in [('A:pt=0x00', unit),
                  ('B:pt=0x20', bytes(x ^ 0x20 for x in unit)),
                  ('C:pt=0x41', bytes(x ^ 0x41 for x in unit))]:
    dec = bytes(auth[i] ^ key[i % 25] for i in range(len(auth)))
    printable = sum(1 for x in dec if 32 <= x <= 126)
    print(f'--- {name} ---')
    print('  printable:', printable, '/', len(dec))
    print('  dec:', repr(dec[:120]))

# hypothesis D: maybe the key is the 16-byte key expanded to 25 via some simple extension
key16 = bytes.fromhex('b64103a24b16d143f241647c3b8ca73e')
# extend 16->25 by repeating then padding
for pad in [0x00, 0xff]:
    key25 = key16 + bytes([pad]) * 9
    dec = bytes(auth[i] ^ key25[i % 25] for i in range(len(auth)))
    printable = sum(1 for x in dec if 32 <= x <= 126)
    print(f'--- D: key16+pad0x{pad:02x} ---')
    print('  printable:', printable, '/', len(dec))
    print('  dec:', repr(dec[:120]))
