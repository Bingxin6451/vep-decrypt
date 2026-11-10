#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()

def u32be(off):
    return struct.unpack('>I', data[off:off+4])[0]

# ---- properly parse the audio trak @912787 ----
# trak: size@912783, type@912787, then children
trak_start = 912783
trak_size = u32be(912783)
trak_end = trak_start + trak_size
print('audio trak: start', trak_start, 'size', trak_size, 'end', trak_end)

# walk children of trak
def walk(start, end, depth=0, maxatoms=60):
    off = start
    seen = 0
    while off + 8 <= end and seen < maxatoms:
        size = u32be(off)
        typ = data[off+4:off+8]
        if size < 8 or size > end - off + 8:
            break
        print('  '*depth + f'{typ.decode("latin1")} @{off} size={size}')
        if typ in (b'mdia', b'minf', b'stbl'):
            walk(off+8, off+size, depth+1)
        elif typ in (b'stsd', b'stts', b'stsc', b'stsz', b'stco', b'stss'):
            # parse entry counts
            if typ == b'stsd':
                cnt = u32be(off+12)
                print('  '*(depth+1) + f'  -> entry_count={cnt}')
            elif typ in (b'stts', b'stsc', b'stsz', b'stco', b'stss'):
                cnt = u32be(off+12)
                print('  '*(depth+1) + f'  -> entry_count={cnt}')
                if typ == b'stts' and cnt < 50:
                    for i in range(cnt):
                        a = u32be(off+16+i*8)
                        b = u32be(off+20+i*8)
                        print('  '*(depth+2) + f'  stts[{i}] sample_count={a} delta={b}')
                if typ == b'stsc' and cnt < 50:
                    for i in range(cnt):
                        a = u32be(off+16+i*12)
                        b = u32be(off+20+i*12)
                        c = u32be(off+24+i*12)
                        print('  '*(depth+2) + f'  stsc[{i}] first_chunk={a} spc={b} sdi={c}')
        off += size
        seen += 1

walk(trak_start+8, trak_end)
