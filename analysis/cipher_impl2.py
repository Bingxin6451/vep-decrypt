#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct, zlib

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

# 验证 crc32_update 与 zlib.crc32 一致（非补码 vs 补码）
test_crc = 0x12345678
for b in b'hello world':
    test_crc = crc32_update(test_crc, b)
# print('crc32_update:', hex(test_crc), 'zlib~:', hex(zlib.crc32(b'hello world', 0x12345678) ^ 0xFFFFFFFF))

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
        self.s17c = ((self.s17c + (self.s178 & 0xFF)) & 0xFFFFFFFF)
        self.s17c = (self.s17c * 0x8088405 + 1) & 0xFFFFFFFF
        self.s180 = crc32_update(self.s180, (self.s17c >> 24) & 0xFF)

    def decrypt(self, data):
        out = bytearray()
        for b in data:
            k = self._key_byte()
            p = b ^ k
            out.append(p)
            self._advance(p)
        return bytes(out)

if __name__ == '__main__':
    fn = '/path/to/sample.vep'
    data = open(fn, 'rb').read()
    enc = data[16:16+81920]
    ftyp = bytes.fromhex('000000186674797069736f6d0000020069736f6d69736f32')

    candidates = [b'', b'dahuangfeng', b'DahuangFeng', b'dhf', b'360dhf', b'HBPlayer',
                  b'dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09', b'tkEDoksW0UPyQWR8O4ynPg==',
                  bytes.fromhex('b64103a24b16d143f241647c3b8ca73e'),
                  b'123456', b'password', b'key', b'qencrypt', b'qencrypt_win']
    for key in candidates:
        c = DahuangfengCipher(key)
        out = c.decrypt(enc[:24])
        match = out == ftyp
        print(f'{key!r}: {"MATCH!" if match else "no"} out[:8]={out[:8].hex()}')
        if match:
            break
