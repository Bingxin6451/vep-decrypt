# vep-decrypt

`.vep` 加密视频格式的逆向分析与解码实验项目 —— 把 **大黄蜂云课堂** 的 `.vep` 课程视频还原成普通 MP4。

> 逆向学习 / 格式研究用途。仅用于解码你自己已购买、有合法授权的课程内容。

---

## 项目状态一览

| 模块 | 状态 | 说明 |
|---|---|---|
| 文件容器格式 | ✅ 完全破解 | CRYP 头 + 加密区 + 明文索引 + mdat + 尾部授权块 |
| MP4 atom 定位 | ✅ 自动解析 | stsz / stco / stsc / stss / esds 全自动 |
| 视频/音频分离 | ✅ 可用 | 视频 AVCC sample、音频 AAC → ADTS |
| SPS 重建 | ✅ 可用 | High profile level 4.0，参数由反推 slice header 得出 |
| 头部密钥流算法 | ❌ 未破 | 81920 字节 XOR 流，自定义算法 |
| 关键帧解密 | ❌ 未破 | 约 0.2% 的 IDR sample 被加密 |
| 可用产出 | ⚠️ 98% | 跳过加密帧 → 每处约 1~2 秒花屏 |

**当前交付水平**：分辨率、时长、音轨完全正确，画面 98% 以上完好。剩下 2% 是加密的关键帧，跳过它们会导致后续帧无法独立解码。

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

打包成单文件 exe（需在 Windows 上执行）：

```bash
cd decoder && build_exe.bat
# -> dist/vep解码器.exe （双击或把 .vep 拖上去即可）
```

---

## 文件格式（已破解部分）

```
┌──────────────┬────────────────────────┬──────────────┬─────────────┬──────────┐
│ CRYP 头 16B  │ 加密区（默认 81920B）  │ 明文 moov 后半│   mdat      │ 尾部 541B│
└──────────────┴────────────────────────┴──────────────┴─────────────┴──────────┘
   ↑ 参数          ↑ XOR 流加密              ↑ stts/stss/   ↑ 99.8% 明文    ↑ 密钥+授权
                     ftyp + moov 前半          stsc/stsz/    仅关键帧加密
                     + 视频轨 avcC(SPS)        stco
```

### CRYP 头

```
43 52 59 50 | u32le(加密区长度) | u32le(A) | u32le(B)
'C' 'R' 'Y' 'P'
```

- 加密区长度**恒为 81920**（不同文件一致）
- `A` / `B` 两个字段**随文件变化**（观测到 `673 / 18727` 与 `2106 / 36308` 两组），用途待定，疑似授权/质检校验值，不影响解码
- 因此：**尾部密钥 P、授权块布局很可能是按文件派生的，不是全局常量** —— 这是早期用固定 P 去推密钥流一直失败的直接原因

### 加密区

`data[16 : 16+81920]`，包含 `ftyp`、`moov` 前半（`mvhd` / `tkhd` / `mdhd` / 视频轨 `stsd` 内的 `avcC`，也就藏着真正的 SPS）。

用 `ftyp` 已知明文可恢复密钥流前 24 字节（硬证据）：

```
密文 ^ 明文 = bd 4f 3c c5 80 51 b0 80 5c b9 57 fa 82 bb 0e e6 1e 6d c0 f0 f1 68 3d 7e
```

明文 `ftyp` = `00000018 66747970 69736f6d 00000200 69736f6d 69736f32`

### 尾部 541 字节

```
tail[0:4]    = 'vep.'                     魔数
tail[14:30]  = 4 × u32le                   (偏移表，如 158/32/190/347)
tail[158:190]= 双重 base64 密钥（记为 P）   解码两次得 16 字节
tail[190:537]= 授权块 347B                 周期 25 的 XOR 加密
```

密钥 P 解出示例：`dGtFRG9rc1cwVVB5UVdR...` → base64×2 → 16 字节 `b64103a2…8ca73e`。
**P 不是头部密钥流的直接 key**（各种 AES/RC4/XOR 用法已穷举排除）。

### 授权块

347 字节，周期 **25** XOR。观测到的 25 字节密钥：

```
404202071a10040a5010411941684001281000071108040042
```

明文 = base64 与二进制混合结构，含 64 字节加密二进制字段，尾部有重复水印单元 `reRvgckdbgpqpctsvn2x9g1bB` ×4。

---

## SPS 重建（关键，必须手工构造）

`.vep` 的明文视频流里**没有 SPS**（SPS 在加密区的 avcC 里），必须按下列参数重建：

```
profile_idc              = 100 (High)
level_idc                = 40  (4.0)
chroma_format_idc        = 1   (4:2:0)
bit_depth_luma/chroma    = 8
log2_max_frame_num_minus4      = 0   (frame_num 4bit)
pic_order_cnt_type             = 0
log2_max_pic_order_cnt_lsb_minus4 = 2   (poc_lsb 6bit)   ← 关键
max_num_ref_frames             = 4
frame_mbs_only_flag            = 1   (逐行)
direct_8x8_inference_flag      = 1
frame_cropping: bottom = 4 (1088 → 1080)
VUI: timing_info, num_units_in_tick=500, time_scale=fps×1000
```

坑位记录：

1. **High profile 的 SPS 在 `sps_id` 之后必须有** `chroma_format_idc` / `bit_depth_*` 字段（按 Baseline 写会解析失败）。
2. `poc_lsb` 是 **6 bit**（`minus4=2`），早期误猜 12 bit 导致全部 slice header 错位。
3. PPS 里 `bottom_field_pic_order_in_frame_present_flag = 0` → slice header 中**没有** `delta_pic_order_cnt` 字段。
4. ffmpeg 用 `2 × num_units_in_tick` 算帧率，所以写 `500` 才能得到约 15.1 fps 的实际速率。
5. PPS 从明文流第一个 `type-8` NAL 提取（每个 IDR 前重复出现），示例 `68eb e72c 8b`。

---

## 加密 sample 识别方法

视频轨用 AVCC 格式（每个 NAL 前 4 字节大端长度）。逐 sample 尝试完整解析长度前缀链：

```
pos = 0; nals = 0
while pos + 4 <= len(sample):
    L = be32(sample[pos:pos+4])
    if L == 0 or L > 0xFFFFFF or pos+4+L > len(sample): → 加密
    pos += 4 + L; nals += 1
若 pos == len(sample) → 明文样本
```

这个方法判加密样本零误报——真明文 sample 的长度链一定严丝合缝走到末尾。

实测样本（73 分钟 / 67044 视频 sample）加密分布：

| sample 区间 | 帧数 | 时间点 |
|---|---|---|
| 7764–7777 | 14 | 515s |
| 16784–16846 | 63 | 1114s |
| 25823–25835 | 13 | 1715s |
| 34882–34961 | 80 | 2316s |
| 45448–45528 | 81 | 3018s |
| 53037–53081 | 45 | 3522s |
| 58798–58804 | 7 | 3904s |
| 64858–64859 | 2 | 4307s |

合计 305 个样本，占 0.45%，但都是 IDR，跳过就断片。

---

## 已排除的算法（穷举无匹配）

以下几点是实打实跑过的，免得后来者重复踩：

- **AES-128/192/256** 全模式 ECB/CBC/CFB/OFB/CTR，1205 种 nonce/counter 布局
- **RC4**（含 drop 变体、各种常见字符串 key）、**SM4**、**ChaCha20/Salsa20**
- **TEA / XTEA / XXTEA**、**Blowfish / 3DES / CAST**
- **MT19937**（Python 与 C 实现、单种子 + init_by_array）、**MT19937-64**
- **LCG**（7 组常量）、**xorshift32/64/128/128+**、**xoroshiro128+**、**splitmix64**、**PCG32**
- hash 链、HMAC、PBKDF2、以及密钥 P 的各种派生方式

结论：头部密钥流是**自定义算法**，或用了非常规参数的标准算法。

---

## 突破口：qencrypt.exe

官方加密助手（`qencrypt.exe`，约 3.2MB PE32，**Delphi** 编写，走 Indy OpenSSL 组件）是拿到算法的唯一确定路径。

已提取到的关键符号：

```
DecryptHeaderByte / DecryptHeaderByteByPtr / DecryptHeaderType
DecryptKey / GetDecryptHeaderPtr / decrypt_buff
EncryptionStrength / FEncryptionStrength / TEncryptStrength   ← 快速/完整 两档加密
num_to_decrypt                                                 ← 解密帧数
EIdOpenSSLAPICryptoError / EIdOSSLUnderlyingCryptoError
"AES:ALL:!aNULL:!eNULL:+RC4:@STRENGTH"
key_material / in_handshake
MainProg = "qencrypt.exe"   SoftId = "qencrypt_win"
```

`EncryptionStrength` 证实存在两档：「快速加密」= 只加密头部 + 关键帧（本项目针对的就是这类）；「完整加密」= 全文件加密。

**下一步（尚未完成）**：

1. 定位 `DecryptHeaderByte`（RVA `0x1FF091`）、`DecryptKey`（RVA `0x1FCF26`）的交叉引用，追到调用点
2. 判定是自实现流密码还是 OpenSSL EVP 封装 —— 字符串里有 `key_material`，密钥应由此派生
3. 动态验证：Windows 下跑 `qencrypt.exe` 加密一个自造小 mp4，在 `EVP_EncryptUpdate` / `EVP_DecryptUpdate` 下断点，直接抓明文/密文/密钥三件套
4. 多文件交叉对比：确认 81920 字节密钥流是否随文件/机器变化 → 判定是固定 key 还是按文件头派生

---

## 目录结构

```
.
├── REVERSE_NOTES.md        逆向全过程笔记（格式/加密/排除清单/坑位）
├── decoder/
│   ├── decode_vep.py       解码器主程序（395 行，可命令行/批量）
│   ├── build_exe.bat       PyInstaller 打包脚本
│   └── README_vep解码器.txt 面向使用者的说明
└── analysis/               141 个分析脚本，按阶段命名
    ├── vep_*               格式解析、密钥流恢复、算法尝试、诊断
    ├── disasm_*            针对 qencrypt.exe 指定地址的反汇编片段
    ├── find_*              交叉引用 / 字符串 / 函数指针搜索
    └── dump_*              SBOX、类型信息、数据结构 dump
```

`analysis/` 保留原始探索痕迹（包括走错的路），作为逆向过程记录。

---

## 依赖

- Python 3.8+
- `pycryptodome`（算法尝试）
- `pefile` + `capstone`（PE 分析与反汇编）
- `ffmpeg`（重新封装）

---

## 已知限制

- 只适用于「快速加密」类 `.vep`。「完整加密」类整个文件都是密文，本工具无效。
- 加密关键帧未解密 → 对应位置必然花屏，这是跳过方案的固有代价，不是 bug。
- 头部 80KB 未解密 → SPS 只能重建。重建参数虽然在本样本上完全正确，换编码器/分辨率可能需要重新反推。
- 不同文件的 CRYP 头 `A/B` 字段与尾部密钥都会变，硬编码单文件常量对其他文件无效。

---

## 免责声明

本项目为视频容器格式的逆向工程学习记录。`.vep` 是商业课程平台的版权保护容器，请仅用于解码**你自己已购买并获得授权**的内容。不得用于传播他人付费课程。
