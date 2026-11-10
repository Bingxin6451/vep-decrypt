#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, struct

fn = 'samples/dhf_encryption_helper.bin'
data = open(fn, 'rb').read()

# 收集长度 4-20 的可打印候选字符串
cands = set()
for m in re.finditer(rb'[ -~]{4,20}', data):
    s = m.group()
    cands.add(s)
# 也收集 UTF-16 字符串（Delphi UnicodeString）
for m in re.finditer(rb'(?:[ -~]\x00){3,20}', data):
    s = m.group().decode('utf-16-le', errors='ignore')
    if s:
        cands.add(s.encode())

print(f'候选字符串数: {len(cands)}')

# 读密文
fn2 = '/path/to/sample.vep'
d2 = open(fn2, 'rb').read()
enc = d2[16:16+81920]
ftyp = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')

def crc32_table():
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        t.append(c)
    return t
CRC = crc32_table()
def upd(crc, b):
    return ((crc >> 8) ^ CRC[(crc ^ b) & 0xFF]) & 0xFFFFFFFF

def decrypt(key, data):
    s178, s17c, s180 = 0x12345678, 0x23456789, 0x34567890
    for b in key:
        s178 = upd(s178, b)
        s17c = ((s17c + (s178 & 0xFF)) * 0x8088405 + 1) & 0xFFFFFFFF
        s180 = upd(s180, (s17c >> 24) & 0xFF)
    out = bytearray()
    for b in data:
        a = (s180 & 0xFFFF) | 2
        k = ((((a ^ 1) * a) & 0xFFFF) >> 8) & 0xFF
        p = b ^ k
        out.append(p)
        s178 = upd(s178, p)
        s17c = ((s17c + (s178 & 0xFF)) * 0x8088405 + 1) & 0xFFFFFFFF
        s180 = upd(s180, (s17c >> 24) & 0xFF)
    return bytes(out)

# 批量测试
found = 0
for key in sorted(cands, key=len):
    out = decrypt(key, enc[:4])
    if out[:4] == ftyp[:4]:
        print(f'候选 {key!r} 前4字节匹配!')
        out24 = decrypt(key, enc[:24])
        if out24 == ftyp:
            print(f'★★★ 密钥找到: {key!r} ★★★')
            found = 1
            break
if not found:
    print('未找到匹配密钥（密钥可能是二进制或非短字符串）')
