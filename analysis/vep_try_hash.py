#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib, struct

target24 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')
target16 = target24[:16]

def try_hash(s, label):
    for hname in ['md5', 'sha1', 'sha256', 'sha512']:
        h = getattr(hashlib, hname)(s).digest()
        for prefix in [16, 20, 24, 32]:
            if h[:prefix] == target24[:prefix]:
                print(f'*** MATCH {hname}({label})[:{prefix}] ***')
        if h[:16] == target16:
            print(f'*** MATCH {hname}({label})[:16] ***')

strings = [
    b'dahuangfeng', b'dhf', b'DHF', b'HBPlayer', b'hbplayer', b'vep', b'CRYP',
    b'dhf123456', b'123456', b'12345678', b'888888', b'666666', b'000000',
    b'2024', b'2025', b'2026', b'2023',
    b'dahuangfeng2024', b'dhf2024', b'dhf2025', b'dhf2026',
    b'jiaren', b'jiazhen', b'douyin',
    '大黄蜂'.encode('utf-8'), '大黄蜂'.encode('gbk'),
    'INSTRUCTOR'.encode('utf-8'), 'INSTRUCTOR'.encode('gbk'),
    '抖音'.encode('utf-8'), '抖音'.encode('gbk'),
    b'DahuangFeng', b'DAHUANGFENG', b'DHF123', b'dhf123',
    b'huangfeng', b'huangfengkeji',
]

for s in strings:
    try_hash(s, s)

# also try header ints as strings and byte sequences
for v in [81920, 673, 18727, 0x14000, 0x2a1, 0x4927]:
    for fmt in ['<I', '>I']:
        try_hash(struct.pack(fmt, v), f'int{fmt}{v}')
    try_hash(str(v).encode(), f'str{v}')

# C-style MT19937 (different init from Python)
def c_mt19937(seed, nbytes):
    mt = [0]*624
    mt[0] = seed & 0xffffffff
    for i in range(1, 624):
        mt[i] = (1812433253 * (mt[i-1] ^ (mt[i-1] >> 30)) + i) & 0xffffffff
    out = bytearray()
    idx = 624
    while len(out) < nbytes:
        if idx >= 624:
            for i in range(624):
                y = (mt[i] & 0x80000000) | (mt[(i+1) % 624] & 0x7fffffff)
                mt[i] = mt[(i+397) % 624] ^ (y >> 1)
                if y & 1:
                    mt[i] ^= 0x9908b0df
            idx = 0
        y = mt[idx]
        idx += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= y >> 18
        out += struct.pack('<I', y & 0xffffffff)
    return bytes(out)

for seed in [673, 18727, 81920, 0, 1]:
    s = c_mt19937(seed, 24)
    if s == target24:
        print('*** C MT19937 MATCH seed', seed)
    # also big-endian
    s2 = c_mt19937(seed, 24)
    s2be = b''.join(struct.pack('>I', struct.unpack('<I', s2[i:i+4])[0]) for i in range(0, 24, 4))
    if s2be == target24:
        print('*** C MT19937 BE MATCH seed', seed)

print('target16:', target16.hex())
print('md5(dahuangfeng):', hashlib.md5(b'dahuangfeng').hexdigest())
print('md5(大黄蜂 utf8):', hashlib.md5('大黄蜂'.encode('utf-8')).hexdigest())
