# VEP 格式逆向笔记（大黄蜂云课堂加密视频）

> 目标：把大黄蜂云课堂 .vep 加密视频还原为标准 MP4。
> 结构：文件主体为明文，加密部分集中在头部 81920 字节（ftyp + moov 前半 + 视频轨 avcC/SPS）
> 与少量关键帧样本；索引表、音频轨与 mdat 均为明文。
> 方案：定位加密区边界 → 重建 SPS → 提取原始 PPS → 校验并分流样本 → ffmpeg 重新封装。

---

## 1. 文件格式

```
文件 = [CRYP头 16B] + [加密区 81920B] + [明文 moov 后半] + [mdat 视频音频] + [尾部 541B]

CRYP头:  'CRYP' + u32le(加密区长度=81920) + u32le(A) + u32le(B)
         A/B 为文件级校验字段，随文件变化
         观测值: 673/18727 与 2106/36308

加密区:  data[16 : 16+81920] = ftyp + moov前半(mvhd/tkhd/mdhd/视频轨stsd含avcC=SPS)

明文区:  moov 后半 = 视频轨 stts/stss/stsc/stsz/stco + 音频轨全部索引
         mdat = 视频/音频数据

尾部541B: tail[0:4]='vep.'  tail[14:30]=4个u32le=(158,32,190,347)
          tail[158:190] = 双重base64密钥 P (16字节)
          tail[190:537] = 授权块(347B, 周期25 XOR)
```

## 2. 关键 atom 偏移（55MB 样本实测）

| 项 | 值 |
|---|---|
| 视频轨 stsz | 580658（type位置），entries=580674，count=72625 |
| 视频轨 stco | 871178（type），offsets=871190，count=10375，**需 +16 修正** |
| 视频轨 stsc | 580606，=(1,8,1)(2,7,1)(10375,6,1) |
| 视频轨 stss | 579378（关键帧索引，306个） |
| 音频轨 stsz | 928925，count=206859 |
| 音频轨 stco | 1756381，count=10375，+16 修正 |
| 音频轨 stsc | 913165，=(1,22,1)(2,21,1)… |
| mdat | 1797897 |
| 视频参数 | 1920x1080, High profile, 15.12fps, x264 core 148 |
| 音频参数 | AAC-LC, 44100Hz, 双声道, ASC=121056e500 |

注意：stsz 的 entries 在 type+16；stco 的 offsets 在 type+12（stco 少一个 sample_size 字段）。
stco 内所有偏移都要 +16，因为原文件头部插入了 16 字节 CRYP 头。

## 3. 加密结构

### 3.1 头部密钥流

用 ftyp 已知明文恢复的密钥流前 24 字节（硬证据）：

```
bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e
```

（ftyp 明文 = 000000186674797069736f6d0000020069736f6d69736f32）

解密后 moov 头完全正确：
- moov size=1797857, mvhd timescale=1000, duration=4803000（4803秒）
- creation_time=0x6A7A0000
- 加密区为 XOR 流构造，密钥流由平台自研算法生成

### 3.2 加密样本分布

识别方法：AVCC sample 内 NAL 长度前缀序列若无法精确走到样本末尾，即为加密样本。

实测 73 分钟样本（67044 视频 sample）加密段：

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

合计 305 个样本，集中分布在课程的分节边界处。

### 3.3 尾部密钥 P

```
tail[158:190] = 'dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09'  (32字符base64)
  → base64解码1 = 'tkEDoksW0UPyQWR8O4ynPg=='  (24字符)
  → base64解码2 = b64103a24b16d143f241647c3b8ca73e  (16字节，记为P)
```

P 与加密区密钥流为独立构造，非直接 key 关系。

### 3.4 授权块（347B）

- 周期 25 XOR
- 密钥（25字节）：404202071a10040a5010411941684001281000071108040042
- 明文 = base64 + 二进制混合结构（含 64 字节加密二进制字段）
- 明文尾部重复单元：reRvgckdbgpqpctsvn2x9g1bB（×4，水印/填充）
- 密文尾部重复单元：2dzfgdzlfg212asifj8()&(#*（×4）

## 4. SPS 重建

明文视频流中不含 SPS，需按片源实际参数构造：

```
profile=100(High) level=40
chroma_format_idc=1(4:2:0) bit_depth=8
log2_max_frame_num_minus4=0   (frame_num 4bit)
pic_order_cnt_type=0
log2_max_pic_order_cnt_lsb_minus4=2   (poc_lsb 6bit)  ← 关键
max_num_ref_frames=4
frame_mbs_only_flag=1 (逐行)
direct_8x8_inference=1
frame_cropping: bottom=4 (1088-1080)
VUI: timing_info, num_units_in_tick=500, time_scale=帧率×1000
```

坑：
- High profile SPS 在 sps_id 后**必须**有 chroma_format_idc/bit_depth 字段（漏了会解析失败）。
- PPS 里 bottom_field_pic_order_in_frame_present_flag=0 → slice header 无 delta_poc 字段。
- poc_lsb 必须是 6bit，写成 12bit 会让所有 slice header 位偏移错位。
- ffmpeg 用 2×num_units_in_tick 算帧率，故写 500 得到实际速率。

PPS（从明文视频流提取，每个 IDR 前重复）：68ebe72c8b

## 5. 算法指纹比对

对下列标准构造做过全量比对，确认密钥流为平台自研：

- AES-128/192/256 全模式（ECB/CBC/CFB/OFB/CTR，1205种nonce/counter布局）
- RC4（含 drop 变体、常见字符串key）、SM4、ChaCha20/Salsa20
- TEA/XTEA/XXTEA、Blowfish/3DES/CAST
- MT19937（Python/C版，单种子+init_by_array）、MT19937-64
- LCG（7组常量）、xorshift32/64/128/128+、xoroshiro128+、splitmix64、PCG32
- hash链、HMAC、PBKDF2、P的各种派生

比对脚本保留在 analysis/ 下，可作算法指纹库复用。

## 6. 加密助手 qencrypt.exe（Delphi + OpenSSL）

来源：https://www.360dhf.cn/download.php?type=encryption-helper （3.3MB PE32）。

关键字符串：
```
DecryptHeaderByte / DecryptHeaderByteByPtr / DecryptHeaderType
DecryptKey / GetDecryptHeaderPtr / decrypt_buff
EncryptionStrength / FEncryptionStrength / TEncryptStrength   ← 快速/完整加密 两档
num_to_decrypt
EIdOpenSSLAPICryptoError / EIdOSSLUnderlyingCryptoError       ← Indy OpenSSL 组件
"AES:ALL:!aNULL:!eNULL:+RC4:@STRENGTH"
key_material / in_handshake
MainProg = "qencrypt.exe"  SoftId = "qencrypt_win"
```

程序为 Delphi 编写（TDictionary<TKeyCollection> 等 Delphi 泛型痕迹）。

符号地址：

| 符号 | RVA |
|---|---|
| DecryptKey | 0x1FCF26 |
| DecryptHeaderType | 0x1FCF4A |
| DecryptHeaderByte | 0x1FF091 |
| num_to_decrypt | 0x1FF11A |
| GetDecryptHeaderPtr | 0x1FF133 |
| decrypt_buff | 0x1FF0DF |

EncryptionStrength 两档含义：
- 快速加密：仅处理头部 + 关键帧样本（本文档针对的类型）
- 完整加密：处理全文件

播放器本体 V7.0.7 同样可从 https://www.360dhf.cn/download.php?type=windows-player 获取。

## 7. 解码流程（decode_vep.py）

1. 检查 CRYP 头 → 定位 mdat → 自动解析视频/音频轨 stbl
2. 视频：逐 sample 校验 NAL 长度链，按结果分流样本
3. 从明文流提取 PPS（第一个 type-8 NAL）
4. 分辨率自动检测（候选分辨率 × ffmpeg 解码，取错误最少者）
5. 音频：从 esds 解析 ASC，生成 ADTS 头
6. 帧率 = 视频帧数 / 音频时长，写入 SPS VUI
7. ffmpeg -c copy 封装 MP4

成品 exe 打包：build_exe.bat（PyInstaller + ffmpeg.exe）

## 8. 复现要点

- 不同文件的 A/B 字段与尾部密钥 P 都会变化，所有常量必须从当前文件实时解析，不可硬编码。
- 换编码器或分辨率时需重新反推 SPS 参数，工具内置候选分辨率试错可覆盖常见情况。
- 批量处理时每个文件独立解析，样本间互不共享状态。
