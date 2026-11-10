# vep-decrypt

`.vep` 视频格式逆向与解码工具 —— 把 **大黄蜂云课堂** 的 `.vep` 课程视频还原成标准 MP4。

解密后可用任意播放器（PotPlayer / MPC / 手机 / 电视）直接播放，无需登录授权、无需专用客户端。

> 逆向学习 / 格式研究用途。请仅用于解码你自己已购买、有合法授权的内容。

---

## 特性

| 能力 | 说明 |
|---|---|
| CRYP 容器解析 | 自动识别头部结构、加密区边界、尾部授权块 |
| MP4 atom 定位 | 全自动扫描 `stsz` / `stco` / `stsc` / `stss` / `esds`，无需手工填偏移 |
| SPS 智能重建 | 按片源实际参数重建 H.264 序列参数集 |
| PPS 自动提取 | 从明文流定位并复用原始 PPS |
| 加密样本识别 | 逐 sample 校验 NAL 长度链，精确区分加密与明文帧 |
| 分辨率自动检测 | 候选分辨率 × ffmpeg 解码试错，取错误最少者 |
| 帧率对齐 | 由视频帧数 / 音频时长反推，写入 VUI |
| AAC → ADTS | 从 `esds` 解析 AudioSpecificConfig，自动生成 ADTS 头 |
| 批量处理 | 通配符 / 多文件拖拽 |
| 单文件分发 | PyInstaller 打包成独立 exe，内置 ffmpeg |

实测：73 分钟 1080p 课程，解码耗时 **2.3 秒**，输出 MP4 音视频同步、时长精确。

---

## 快速开始

```bash
pip install pycryptodome pefile capstone

python decoder/decode_vep.py 你的课程.vep
# -> 你的课程_解码.mp4

# 批量
python decoder/decode_vep.py *.vep

# 指定 ffmpeg
python decoder/decode_vep.py in.vep out.mp4 --ffmpeg /usr/local/bin/ffmpeg
```

打包成单文件 exe（Windows 上执行）：

```bash
cd decoder && build_exe.bat
# -> dist/vep解码器.exe
```

打包后双击即可用：把 `.vep` 拖到 exe 上，同目录自动生成 `原文件名_解码.mp4`。

---

## 文件格式

```
┌──────────────┬────────────────────────┬──────────────┬─────────────┬──────────┐
│ CRYP 头 16B  │ 加密区（默认 81920B）  │ 明文 moov 后半│   mdat      │ 尾部 541B│
└──────────────┴────────────────────────┴──────────────┴─────────────┴──────────┘
   ↑ 参数          ↑ ftyp + moov 前半      ↑ stts/stss/  ↑ 视频/音频    ↑ 密钥+授权
                     + 视频轨 avcC(SPS)      stsc/stsz/stco   数据
```

### CRYP 头

```
43 52 59 50 | u32le(加密区长度) | u32le(A) | u32le(B)
'C' 'R' 'Y' 'P'
```

- 加密区长度恒为 **81920**
- `A` / `B` 随文件变化（观测到 `673 / 18727` 与 `2106 / 36308`），属于文件级校验字段，解码流程不依赖其取值

### 加密区

`data[16 : 16+81920]`，包含 `ftyp`、`moov` 前半（`mvhd` / `tkhd` / `mdhd` / 视频轨 `stsd` 内的 `avcC`）。

### 尾部 541 字节

```
tail[0:4]     = 'vep.'                     魔数
tail[14:30]   = 4 × u32le                  偏移表（158 / 32 / 190 / 347）
tail[158:190] = 双重 base64 密钥 P         解码两次得 16 字节
tail[190:537] = 授权块 347B                周期 25 的 XOR
```

密钥 P 解出示例：`dGtFRG9rc1cwVVB5UVdR…` → base64×2 → 16 字节 `b64103a2…8ca73e`。

授权块解密后的明文是 base64 与二进制混合结构，含 64 字节加密字段，尾部带重复水印单元 `reRvgckdbgpqpctsvn2x9g1bB` ×4。

---

## SPS 重建参数

明文视频流里不含 SPS（SPS 在加密区的 `avcC` 内），工具按下列参数重建：

```
profile_idc                        = 100 (High)
level_idc                          = 40  (4.0)
chroma_format_idc                  = 1   (4:2:0)
bit_depth_luma / chroma            = 8
log2_max_frame_num_minus4          = 0   (frame_num 4bit)
pic_order_cnt_type                 = 0
log2_max_pic_order_cnt_lsb_minus4  = 2   (poc_lsb 6bit)
max_num_ref_frames                 = 4
frame_mbs_only_flag                = 1   (逐行)
direct_8x8_inference_flag          = 1
frame_cropping: bottom = 4         (1088 → 1080)
VUI: timing_info, num_units_in_tick=500, time_scale=fps×1000
```

实现要点（改这个文件前必读）：

1. High profile 的 SPS 在 `sps_id` 之后**必须**跟 `chroma_format_idc` / `bit_depth_*`，按 Baseline 结构写会解析失败。
2. `poc_lsb` 是 **6 bit**（`minus4 = 2`）。写成 12 bit 会让所有 slice header 位偏移错位。
3. PPS 内 `bottom_field_pic_order_in_frame_present_flag = 0`，因此 slice header 中**没有** `delta_pic_order_cnt` 字段。
4. ffmpeg 按 `2 × num_units_in_tick` 折算帧率，写 `500` 才能得到实际速率。
5. PPS 从明文流第一个 `type-8` NAL 提取（每个 IDR 前重复出现），示例 `68eb e72c 8b`。

---

## 加密样本识别算法

视频轨为 AVCC 格式（每个 NAL 前 4 字节大端长度）。逐 sample 校验长度前缀链是否严丝合缝：

```python
pos = 0
while pos + 4 <= len(sample):
    L = be32(sample[pos:pos+4])
    if L == 0 or L > 0xFFFFFF or pos + 4 + L > len(sample):
        return ENCRYPTED
    pos += 4 + L
return CLEAR if pos == len(sample) else ENCRYPTED
```

真明文 sample 的长度链必然精确走到样本末尾，因此该判定零误报。解码器用同一逻辑分流每个样本，再按 `stsc` / `stsz` / `stco` 重建完整的访问单元序列。

---

## 算法验证记录

逆向过程中对这些算法做过全量比对，用于确认密钥流不是标准构造：

- AES-128/192/256 全模式（ECB / CBC / CFB / OFB / CTR），1205 种 nonce / counter 布局
- RC4（含 drop 变体）、SM4、ChaCha20 / Salsa20
- TEA / XTEA / XXTEA、Blowfish / 3DES / CAST
- MT19937（Python 与 C 实现、单种子 + init_by_array）、MT19937-64
- LCG（7 组常量）、xorshift32/64/128/128+、xoroshiro128+、splitmix64、PCG32
- hash 链、HMAC、PBKDF2，以及密钥 P 的各类派生

结论：头部密钥流为平台自研构造。

相关脚本全部保留在 `analysis/` 下，可作为算法指纹比对工具复用。

---

## 加密助手参考

官方加密工具 `qencrypt.exe`（约 3.2MB PE32，Delphi 编写，基于 Indy OpenSSL 组件）已完整提取符号表：

```
DecryptHeaderByte / DecryptHeaderByteByPtr / DecryptHeaderType
DecryptKey / GetDecryptHeaderPtr / decrypt_buff
EncryptionStrength / FEncryptionStrength / TEncryptStrength
num_to_decrypt
EIdOpenSSLAPICryptoError / EIdOSSLUnderlyingCryptoError
"AES:ALL:!aNULL:!eNULL:+RC4:@STRENGTH"
key_material / in_handshake
MainProg = "qencrypt.exe"   SoftId = "qencrypt_win"
```

`EncryptionStrength` 对应两档模式：「快速加密」仅处理头部与关键帧，「完整加密」处理全文件。本工具面向快速加密类 `.vep`。

关键符号地址（供二次分析）：

| 符号 | RVA |
|---|---|
| `DecryptKey` | `0x1FCF26` |
| `DecryptHeaderType` | `0x1FCF4A` |
| `DecryptHeaderByte` | `0x1FF091` |
| `num_to_decrypt` | `0x1FF11A` |
| `GetDecryptHeaderPtr` | `0x1FF133` |
| `decrypt_buff` | `0x1FF0DF` |

---

## 目录结构

```
.
├── README.md                 本文件
├── REVERSE_NOTES.md          逆向全过程笔记（格式 / 加密 / 参数推导 / 坑位）
├── decoder/
│   ├── decode_vep.py         解码器主程序（395 行）
│   ├── build_exe.bat         PyInstaller 打包脚本
│   ├── kfc8p_pack.exp        远程打包执行脚本
│   └── README_vep解码器.txt   面向使用者的中文说明
└── analysis/                 141 个分析脚本，按阶段组织
    ├── vep_*                 格式解析、密钥流恢复、参数推导、诊断
    ├── disasm_*              针对 qencrypt.exe 指定地址的反汇编
    ├── find_*                交叉引用 / 字符串 / 函数指针搜索
    ├── dump_*                SBOX、类型信息、数据结构导出
    └── cipher_impl*.py       自研密码构造的参考实现
```

`analysis/` 保留原始探索痕迹，可作为该格式后续研究的起点。

---

## 依赖

- Python 3.8+
- `pycryptodome` — 算法比对
- `pefile` + `capstone` — PE 分析与反汇编
- `ffmpeg` — 重新封装

---

## 免责声明

本项目为视频容器格式的逆向工程学习记录。`.vep` 是商业课程平台的版权保护容器，请仅用于解码**你自己已购买并获得授权**的内容。不得用于传播他人付费课程。
