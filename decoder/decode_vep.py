#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大黄蜂云课堂 .vep 视频解码器 (通用版 v2)
==========================================
原理：
  .vep = CRYP头(16B) + 加密区(ftyp/moov头/视频轨avcC含SPS) + 明文moov后半(stts/stss/stsc/stsz/stco)
        + mdat(99%明文视频/音频，仅关键帧被加密) + 尾部授权块
  本工具：跳过加密关键帧 + 构造 SPS + 从明文流提取 PPS → 重建 MP4。
  加密关键帧约 0.2% 帧，跳过处约 1-2 秒画面花屏，其余完好。

用法：
  python decode_vep.py input.vep [output.mp4] [--ffmpeg /path/to/ffmpeg]
  python decode_vep.py *.vep            # 批量
"""
import struct, sys, os, subprocess, tempfile, shutil


def find_ffmpeg():
    """Locate ffmpeg binary: env / PyInstaller bundle / same dir / PATH."""
    if os.environ.get('VEP_FFMPEG'):
        return os.environ['VEP_FFMPEG']
    # PyInstaller onefile bundle dir
    base = getattr(sys, '_MEIPASS', None)
    if base:
        for name in ('ffmpeg.exe', 'ffmpeg'):
            p = os.path.join(base, name)
            if os.path.exists(p):
                return p
    # same dir as script/exe
    here = os.path.dirname(os.path.abspath(sys.argv[0]))
    for name in ('ffmpeg.exe', 'ffmpeg'):
        p = os.path.join(here, name)
        if os.path.exists(p):
            return p
    return shutil.which('ffmpeg')


FFMPEG = find_ffmpeg()


def u32(data, o):
    return struct.unpack('>I', data[o:o+4])[0]


def find_atom(data, typ, start, end):
    res = []
    i = start
    while True:
        p = data.find(typ, i, end)
        if p < 0:
            break
        res.append(p)
        i = p + 1
    return res


class BW:
    def __init__(self):
        self.bits = []
    def put(self, v, n):
        for i in range(n-1, -1, -1):
            self.bits.append((v >> i) & 1)
    def ue(self, v):
        cn = v + 1
        nb = cn.bit_length()
        self.bits.extend([0]*(nb-1))
        self.put(cn, nb)
    def to_bytes(self):
        self.bits.append(1)
        while len(self.bits) % 8:
            self.bits.append(0)
        out = bytearray()
        for i in range(0, len(self.bits), 8):
            b = 0
            for j in range(8):
                b = (b << 1) | self.bits[i+j]
            out.append(b)
        return bytes(out)


def build_sps(w, h, time_scale=15120, num_units_in_tick=500):
    bw = BW()
    bw.put(100, 8); bw.put(0, 4); bw.put(0, 4); bw.put(40, 8)
    bw.ue(0); bw.ue(1); bw.ue(0); bw.ue(0); bw.put(0, 1); bw.put(0, 1)
    bw.ue(0); bw.ue(0); bw.ue(2); bw.ue(4); bw.put(0, 1)
    mw = (w+15)//16; mh = (h+15)//16
    bw.ue(mw-1); bw.ue(mh-1)
    bw.put(1, 1); bw.put(1, 1)
    cb = mh*16 - h
    if cb:
        bw.put(1, 1); bw.ue(0); bw.ue(0); bw.ue(0); bw.ue(cb//2)
    else:
        bw.put(0, 1)
    bw.put(1, 1)
    bw.put(0, 1); bw.put(0, 1); bw.put(0, 1); bw.put(0, 1)
    bw.put(1, 1)
    bw.put(num_units_in_tick, 32); bw.put(time_scale, 32); bw.put(1, 1)
    bw.put(0, 1); bw.put(0, 1); bw.put(0, 1)
    bw.put(1, 1)
    bw.put(1, 1); bw.ue(0); bw.ue(0); bw.ue(16); bw.ue(16); bw.ue(2); bw.ue(4)
    rbsp = bw.to_bytes()
    nal = bytearray([0x67]); zc = 0
    for b in rbsp:
        if zc >= 2 and b <= 3:
            nal.append(0x03); zc = 0
        nal.append(b)
        zc = zc+1 if b == 0 else 0
    return bytes(nal)


def annexb_from_avcc(vid, sps, pps):
    ab = bytearray()
    for n in [sps, pps]:
        ab += b'\x00\x00\x00\x01' + n
    pos = 0
    while pos + 4 <= len(vid):
        L = u32(vid, pos)
        if not (0 < L < 0x1000000) or pos+4+L > len(vid):
            break
        ab += b'\x00\x00\x00\x01' + vid[pos+4:pos+4+L]
        pos += 4 + L
    return bytes(ab)


class VepDecoder:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.data = f.read()
        if self.data[:4] != b'CRYP':
            raise ValueError('不是有效的 .vep 文件（缺 CRYP 头）')
        self.enc_len = struct.unpack('<I', self.data[4:8])[0]
        self.n = len(self.data)

    def parse_trak(self):
        mdat = self.data.find(b'mdat', self.enc_len + 16)
        self.mdat = mdat if mdat > 0 else self.n
        lo = self.enc_len + 16
        stszs = find_atom(self.data, b'stsz', lo, self.mdat)
        stcos = find_atom(self.data, b'stco', lo, self.mdat)
        result = {}
        for ssz in stszs:
            cnt = u32(self.data, ssz + 12)
            if cnt <= 0:
                continue
            sco = None
            for c in stcos:
                if c > ssz:
                    sco = c
                    break
            if sco is None:
                continue
            ccount = u32(self.data, sco + 8)
            result.setdefault(cnt, []).append((ssz, sco, ccount))
        self.video = None
        self.audio = None
        for cnt in sorted(result.keys(), reverse=True):
            for ssz, sco, cc in result[cnt]:
                if self.audio is None and cnt > 150000:
                    self.audio = (ssz, sco, cc)
                elif self.video is None and cnt > 20000:
                    self.video = (ssz, sco, cc)
        cands = []
        for cnt, lst in result.items():
            for ssz, sco, cc in lst:
                cands.append((cnt, ssz, sco, cc))
        cands.sort(key=lambda x: -x[0])
        if not self.video and cands:
            self.video = cands[0][1:]
        if not self.audio and len(cands) >= 2:
            self.audio = cands[1][1:]
        if not self.video:
            raise ValueError('未找到视频轨')

    def extract_video(self):
        vsz_off, vco_off, vcc = self.video
        vcount = u32(self.data, vsz_off + 12)
        vsizes = [u32(self.data, vsz_off + 16 + 4*i) for i in range(vcount)]
        vchunks = [u32(self.data, vco_off + 12 + 4*i) + 16 for i in range(vcc)]
        vstsc = self._parse_stsc(self._find_stsc(vsz_off))
        vid = bytearray()
        self.enc_samples = set()
        self.pps = None
        si = 0
        for ci in range(vcc):
            ns = self._samples_per_chunk(vstsc, ci+1)
            base = vchunks[ci]
            for k in range(ns):
                if si >= vcount:
                    break
                sz = vsizes[si]
                smp = self.data[base:base+sz] if base + sz <= self.n else b''
                ok, nals = self._sample_ok(smp)
                if ok:
                    vid += smp
                    if self.pps is None:
                        self.pps = self._find_pps(smp)
                else:
                    self.enc_samples.add(si)
                base += sz
                si += 1
        self.vid = bytes(vid)
        self.vcount = vcount
        if self.pps is None:
            self.pps = bytes.fromhex('68ebe72c8b')

    def extract_audio(self):
        if not self.audio:
            self.adts = b''
            self.acount = 0
            self.samplerate = 44100
            return
        asz_off, aco_off, acc = self.audio
        acount = u32(self.data, asz_off + 12)
        asizes = [u32(self.data, asz_off + 16 + 4*i) for i in range(acount)]
        achunks = [u32(self.data, aco_off + 12 + 4*i) + 16 for i in range(acc)]
        astsc = self._parse_stsc(self._find_stsc(asz_off))
        # parse AudioSpecificConfig from esds
        profile, sf_idx, chan = 1, 4, 2
        mp4a = self.data.find(b'mp4a', max(0, asz_off - 600), asz_off)
        if mp4a >= 0:
            esds = self.data.find(b'esds', mp4a, min(mp4a + 200, self.n))
            if esds >= 0:
                i = esds + 8
                while i < esds + 60:
                    if self.data[i] == 0x05:
                        ln = 0; j = i+1
                        while j < self.n:
                            b = self.data[j]; ln = (ln << 7) | (b & 0x7f); j += 1
                            if not (b & 0x80):
                                break
                        asc = self.data[j:j+ln]
                        if len(asc) >= 2:
                            aot = (asc[0] >> 3) & 0x1f
                            fidx = ((asc[0] & 7) << 1) | (asc[1] >> 7)
                            ch = (asc[1] >> 3) & 0xf
                            profile = max(1, aot - 1)
                            sf_idx = fidx if fidx < 13 else 4
                            chan = ch if ch > 0 else 2
                        break
                    i += 1
        freqs = [96000,88200,64000,48000,44100,32000,24000,22050,16000,12000,11025,8000,7350]
        self.samplerate = freqs[sf_idx] if sf_idx < 13 else 44100
        adts = bytearray()
        si = 0
        for ci in range(acc):
            ns = self._samples_per_chunk(astsc, ci+1)
            base = achunks[ci]
            for k in range(ns):
                if si >= acount:
                    break
                sz = asizes[si]
                if base + sz <= self.n:
                    raw = self.data[base:base+sz]
                    fl = sz + 7
                    adts += bytes([0xFF, 0xF1,
                                   (profile << 6) | (sf_idx << 2) | (chan >> 2),
                                   ((chan & 3) << 6) | ((fl >> 11) & 3),
                                   (fl >> 3) & 0xFF,
                                   ((fl & 7) << 5) | 0x1F, 0xFC]) + raw
                base += sz
                si += 1
        self.adts = bytes(adts)
        self.acount = acount

    def _find_pps(self, sample):
        pos = 0
        while pos + 4 <= len(sample):
            L = u32(sample, pos)
            if not (0 < L < 0x1000000) or pos+4+L > len(sample):
                break
            nal = sample[pos+4:pos+4+L]
            if nal and (nal[0] & 0x1f) == 8:
                return nal
            pos += 4 + L
        return None

    @staticmethod
    def _sample_ok(sample):
        pos = 0
        nals = 0
        while pos + 4 <= len(sample):
            L = struct.unpack('>I', sample[pos:pos+4])[0]
            if not (0 < L < 0x1000000) or pos + 4 + L > len(sample):
                return False, nals
            nals += 1
            pos += 4 + L
        return (pos == len(sample)), nals

    def _find_stsc(self, stsz_off):
        best = -1
        for p in find_atom(self.data, b'stsc', self.enc_len+16, stsz_off):
            best = p
        return best

    def _parse_stsc(self, off):
        if off < 0:
            return [(1, 1, 1)]
        n = u32(self.data, off + 8)
        out = []
        for k in range(n):
            out.append((u32(self.data, off+12+12*k), u32(self.data, off+16+12*k), u32(self.data, off+20+12*k)))
        return out

    def _samples_per_chunk(self, stsc, ci):
        spc = 1
        for fc, s, d in stsc:
            if ci < fc:
                break
            spc = s
        return spc

    def detect_resolution(self, ffmpeg):
        candidates = [(1920,1080),(1280,720),(854,480),(640,360),(1366,768),
                      (1024,768),(960,540),(1280,960),(800,600)]
        # use first ~800 samples for testing
        vid_head = self.vid[:1500000]
        best = (1920, 1080, 10**9)
        for w, h in candidates:
            sps = build_sps(w, h)
            ab = annexb_from_avcc(vid_head, sps, self.pps)
            fn = '/tmp/_r.h264'
            open(fn, 'wb').write(ab)
            try:
                r = subprocess.run([ffmpeg, '-v', 'error', '-i', fn,
                                    '-frames:v', '60', '-f', 'null', '-'],
                                   capture_output=True, timeout=30)
                err = len([l for l in r.stderr.decode(errors='replace').split('\n') if l.strip()])
            except Exception:
                err = 10**9
            if err < best[2]:
                best = (w, h, err)
        return best[0], best[1]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    args = list(sys.argv[1:])
    ffmpeg = FFMPEG
    if '--ffmpeg' in args:
        i = args.index('--ffmpeg')
        ffmpeg = args[i+1]
        del args[i:i+2]
    if not ffmpeg:
        print('错误: 找不到 ffmpeg，请用 --ffmpeg 指定路径')
        sys.exit(1)
    inputs = [a for a in args if a.lower().endswith('.vep')]
    if not inputs:
        print('未找到 .vep 文件')
        sys.exit(1)
    for inp in inputs:
        out = os.path.splitext(inp)[0] + '_解码.mp4'
        print(f'[解码] {inp}')
        d = VepDecoder(inp)
        d.parse_trak()
        d.extract_video()
        d.extract_audio()
        w, h = d.detect_resolution(ffmpeg)
        print(f'  视频: {d.vcount} samples, {len(d.enc_samples)} 加密sample(跳过), 分辨率 {w}x{h}')
        print(f'  音频: {d.acount} samples, {d.samplerate}Hz')
        # frame rate aligned to audio duration
        nframes = 0
        pos = 0
        while pos + 4 <= len(d.vid):
            L = u32(d.vid, pos)
            if not (0 < L < 0x1000000) or pos+4+L > len(d.vid):
                break
            if d.vid[pos+4] & 0x1f in (1, 5):
                nframes += 1
            pos += 4 + L
        aud_dur = d.acount * 1024 / d.samplerate if d.acount else (nframes / 15.0)
        fps = nframes / aud_dur if aud_dur > 0 else 15.0
        sps = build_sps(w, h, time_scale=round(fps * 1000), num_units_in_tick=500)
        annexb = annexb_from_avcc(d.vid, sps, d.pps)
        tmpdir = tempfile.mkdtemp()
        h264 = os.path.join(tmpdir, 'v.h264')
        aac = os.path.join(tmpdir, 'a.aac')
        open(h264, 'wb').write(annexb)
        if d.adts:
            open(aac, 'wb').write(d.adts)
        if d.adts:
            subprocess.run([ffmpeg, '-y', '-v', 'error', '-i', h264, '-i', aac,
                            '-c', 'copy', '-movflags', '+faststart', out], check=True)
        else:
            subprocess.run([ffmpeg, '-y', '-v', 'error', '-i', h264,
                            '-c', 'copy', '-movflags', '+faststart', out], check=True)
        print(f'  -> {out}')
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    main()
