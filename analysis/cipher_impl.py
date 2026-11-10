#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大黄蜂 .vep 流密码算法 Python 实现 + 密钥反推"""
import struct, zlib

# 标准 CRC32 表（poly 0xEDB88320）
def crc32_table():
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        t.append(c)
    return t
CRC = crc32_table()

def crc32_update(crc, byte):
    return ((crc >> 8) ^ CRC[(crc ^ byte) & 0xFF]) & 0xFFFFFFFF

class DahuangfengCipher:
    def __init__(self, key: bytes):
        self.s178 = 0x12345678
        self.s17c = 0x23456789
        self.s180 = 0x34567890
        for b in key:
            self._advance(b)

    def _key_byte(self):
        a = (self.s180 & 0xFFFF) | 2
        c = ((a ^ 1) * a) & 0xFFFF
        return (c >> 8) & 0xFF

    def _advance(self, byte):
        self.s178 = crc32_update(self.s178, byte)
        self.s17c = ((self.s17c + (self.s178 & 0xFF)) * 0x8088405 + 1) & 0xFFFFFFFF
        self.s180 = crc32_update(self.s180, (self.s17c >> 24) & 0xFF)

    def decrypt(self, data):
        out = bytearray()
        for b in data:
            k = self._key_byte()
            p = b ^ k
            out.append(p)
            self._advance(p)
        return bytes(out)

    def encrypt(self, data):
        out = bytearray()
        for b in data:
            k = self._key_byte()
            c = b ^ k
            out.append(c)
            self._advance(b)  # 反馈明文
        return bytes(out)

if __name__ == '__main__':
    # 读取加密区，测试密钥
    fn = '/path/to/sample.vep'
    data = open(fn, 'rb').read()
    enc = data[16:16+81920]
    ftyp_plain = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')

    # 测试常见密钥
    candidates = [
        b'dahuangfeng', b'DahuangFeng', b'dhf', b'360dhf', b'HBPlayer',
        b'dahuangfeng.com', b'www.360dhf.cn', b'360dhf.cn',
        b'dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09', b'tkEDoksW0UPyQWR8O4ynPg==',
        bytes.fromhex('b64103a24b16d143f241647c3b8ca73e'),
        b'123456', b'password', b'key',
    ]
    for key in candidates:
        c = DahuangfengCipher(key)
        out = c.decrypt(enc[:24])
        if out == ftyp_plain:
            print(f'KEY FOUND: {key!r}')
            break
        else:
            # 检查前4字节
            match = out[:4] == ftyp_plain[:4]
            print(f'{key!r}: {"前4字节匹配!" if match else "不匹配"} out[:8]={out[:8].hex()}')
