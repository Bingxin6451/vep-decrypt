#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import struct

FN = '/path/to/sample.vep'
data = open(FN, 'rb').read()
enc = data[16:16+81920]

# hypothesis: plaintext[673:681] = stts atom: size=18727 (0x4927) + "stts"
# key[673:681] = enc[673:681] XOR (00 00 49 27 73 74 74 73)
pt = struct.pack('>I', 18727) + b'stts'
key_at_673 = bytes(enc[673+i] ^ pt[i] for i in range(8))
print('enc[673:681]:', enc[673:681].hex(' '))
print('key[673:681]  =', key_at_673.hex(' '))

# compare with known key at other positions: is there any alignment?
# known key[0:24]
key0 = bytes.fromhex('bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e')
print('key[0:24]     =', key0.hex())

# check if key_at_673 matches key0 at some offset (period test)
for off in range(24):
    if key_at_673[:4] == key0[off:off+4]:
        print(f'key[673:677] matches key0[{off}:{off+4}]')

# Alternative hypothesis: maybe 673 = offset where stts STARTS, but let's also check
# plaintext[673:677] could be a size field. Try: is key[673:677] == key at some known pos?
print('\nkey[673:677]:', key_at_673[:4].hex())
print('key[677:681]:', key_at_673[4:8].hex())

# Check: if key has period P, key[673] = key[673 % P]. Test P = 673 and 18727 impossible directly.
# Instead, verify by decrypting a stretch and checking if it looks like stts entries.
# Decrypt plaintext[673:673+64] using a KEY REPEAT of some period? We don't know key there.
# So instead: recover key via stts structure and check stts entry plausibility.

# stts: after size+type+verflags(12 bytes), entry_count (4), then entries (count, delta) x N
# plaintext[685:689] = entry_count, plaintext[689:697] = first entry
# We can't verify without key. But we CAN check: does key[673:681] look "continuous" with
# the key stream if we assume some simple PRNG? Print for reference.

# Try the hypothesis that key stream = RC4 with key = some bytes we haven't tried.
# Let's extract a LONGER known-plaintext region using the stts hypothesis + mvhd knowns,
# then check if it's a known stream.

# Actually, let's verify the 673/18727 hypothesis differently:
# If plaintext[673:] is stts with ~2339 entries, entries are (count, delta) pairs where
# count is small and delta relates to framerate. Let's try to recover key assuming
# entry_count = N (unknown) and see if key stream becomes periodic/known.

# recover key[685:689] assuming entry_count: try common N values
enc685 = enc[685:689]
print('\nenc[685:689]:', enc685.hex(' '))
# entry_count N: total samples 72625 spread over N stts entries
for N in [2338, 2339, 2340]:
    k = bytes(enc685[i] ^ struct.pack('>I', N)[i] for i in range(4))
    print(f'  key[685:689] if N={N}:', k.hex())
