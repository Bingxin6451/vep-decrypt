# VEP 逆向笔记（大黄蜂云课堂加密视频）

> 目标：把大黄蜂云课堂 .vep 加密视频解码为普通 MP4。
> 结论：文件主体 99.8% 明文，只有头部 80KB + 176 个关键帧被加密。
> 现状：已用「跳过加密帧 + 重建 SPS」方案产出 98% 可看的 MP4；完整 100% 解密
> 正在逆向加密助手 qencrypt.exe 找算法（突破口已定位，见第 6 节）。

---

## 1. 文件格式（已完全破解）

```
文件 = [CRYP头 16B] + [加密区 81920B] + [明文 moov 后半] + [mdat 视频音频] + [尾部 541B]

CRYP头:  'CRYP' + u32le(加密区长度=81920) + u32le(673) + u32le(18727)
         hex: 43 52 59 50 00 40 01 00 a1 02 00 00 27 49 00 00

加密区:  data[16 : 16+81920] = ftyp + moov前半(mvhd/tkhd/mdhd/视频轨stsd含avcC=SPS)
         XOR 流加密，密钥流算法未公开（第 6 节是突破口）

明文区:  moov 后半 = 视频轨 stts/stss/stsc/stsz/stco + 音频轨全部索引
         mdat = 视频/音频数据（99.8% 明文）

尾部541B: tail[0:4]='vep.'  tail[14:30]=4个u32le=(158,32,190,347)
          tail[158:190] = 双重base64密钥
          tail[190:537] = 授权块(347B, 周期25 XOR加密)
```

## 2. 关键 atom 偏移（本例文件，55MB）

| 项 | 值 |
|---|---|
| 视频轨 stsz | 580658（type位置），entries=580674，count=72625 |
| 视频轨 stco | 871178（type），offsets=871190，count=10375，**需+16修正** |
| 视频轨 stsc | 580606，=(1,8,1)(2,7,1)(10375,6,1) |
| 视频轨 stss | 579378（关键帧索引，306个） |
| 音频轨 stsz | 928925，count=206859 |
| 音频轨 stco | 1756381，count=10375，+16修正 |
| 音频轨 stsc | 913165，=(1,22,1)(2,21,1)... |
| mdat | 1797897 |
| 视频参数 | 1920x1080, High profile, 15.12fps, x264 core 148 |
| 音频参数 | AAC-LC, 44100Hz, 双声道, ASC=121056e500 |

注意：stsz 的 entries 在 type+16；stco 的 offsets 在 type+12（stco 少一个 sample_size 字段）。

## 3. 加密发现

### 3.1 头部密钥流（硬证据）

用 ftyp 已知明文恢复的密钥流前 24 字节：


```
bd4f3cc58051b0805cb957fa82bb0ee61e6dc0f0f1683d7e
```
（ftyp 明文 = 000000186674797069736f6d0000020069736f6d69736f32）

解密后 moov 头完全正确：
- moov size=1797857, mvhd timescale=1000, duration=4803000（4803秒）
- creation_time=0x6A7A0000（2026年）

### 3.2 加密关键帧（176 个 sample）
- chunk 3826~3831（42 sample）+ chunk 7907~7926（134 sample）
- 精确识别：chunk 7907 只有第 7 个 sample 加密（前 6 个明文！）
- 识别方法：AVCC sample 内 NAL 长度前缀序列无法完整解析 = 加密
- 这些是关键帧（IDR），跳过导致约 2×15 秒花屏

### 3.3 尾部密钥 P
```
tail[158:190] = 'dGtFRG9rc1cwVVB5UVdSOE80eW5QZz09'  (32字符base64)
  → base64解码1 = 'tkEDoksW0UPyQWR8O4ynPg=='  (24字符)
  → base64解码2 = b64103a24b16d143f241647c3b8ca73e  (16字节，记为P)
```
P 疑似机器码的 MD5，**不是**头部密钥流的直接 key（已排除 P 的各种 AES/RC4/XOR 用法）。

### 3.4 授权块（347B，已破解）
- 周期 25 XOR 加密
- 密钥（25字节）：404202071a10040a5010411941684001281000071108040042
- 明文 = base64 + 二进制混合结构（含 64 字节加密二进制字段）
- 明文尾部重复单元：reRvgckdbgpqpctsvn2x9g1bB（×4，水印/填充）
- 密文尾部重复单元：2dzfgdzlfg212asifj8()&(#*（×4）

## 4. SPS 重建（关键！视频流缺 SPS，必须构造）

正确参数（穷举 + 反推 slice header 得出）：
```
profile=100(High) level=40
chroma_format_idc=1(4:2:0) bit_depth=8
log2_max_frame_num_minus4=0   (frame_num 4bit)
pic_order_cnt_type=0
log2_max_pic_order_cnt_lsb_minus4=2   (poc_lsb 6bit)  ← 关键，之前误猜12
max_num_ref_frames=4
frame_mbs_only_flag=1 (逐行)
direct_8x8_inference=1
frame_cropping: bottom=4 (1088-1080)
VUI: timing_info, num_units_in_tick=500, time_scale=帧率×1000
     ← 注意 ffmpeg 用 2×num_units_in_tick 算帧率，故写 500 得 15.12fps
```

坑：High profile SPS 在 sps_id 后**必须**有 chroma_format_idc/bit_depth 字段（漏了会解析失败）。
坑：PPS 里 bottom_field_pic_order_in_frame_present_flag=0 → slice header 无 delta_poc 字段。

PPS（从明文视频流提取，每个IDR前重复）：68ebe72c8b

## 5. 已排除的算法（穷举无匹配）

- AES-128/192/256 全模式（ECB/CBC/CFB/OFB/CTR，1205种nonce/counter布局）
- RC4（含 drop 变体、常见字符串key）、SM4、ChaCha20/Salsa20
- TEA/XTEA/XXTEA、Blowfish/3DES/CAST
- MT19937（Python/C版，单种子+init_by_array）、MT19937-64
- LCG（7组常量）、xorshift32/64/128/128+、xoroshiro128+、splitmix64、PCG32
- hash链、HMAC、PBKDF2、P的各种派生

结论：头部密钥流是**自定义算法**（或非常规参数的标准算法）。

## 6. 突破口：加密助手 qencrypt.exe（Delphi + OpenSSL）

从 https://www.360dhf.cn/download.php?type=encryption-helper 下载（3.3MB PE32）。

关键字符串（strings 提取）：
```
DecryptHeaderByte / DecryptHeaderByteByPtr / DecryptHeaderType / DecryptKey / GetDecryptHeaderPtr
EncryptionStrength / FEncryptionStrength / TEncryptStrength   ← 快速/完整加密
num_to_decrypt   ← 解密帧数（对应176个关键帧）
EIdOpenSSLAPICryptoError / EIdOSSLUnderlyingCryptoError   ← Indy OpenSSL 组件
"AES:ALL:!aNULL:!eNULL:+RC4:@STRENGTH"   ← OpenSSL 密码套件
decrypt_buff / key_material / in_handshake
MainProg = "qencrypt.exe"  SoftId = "qencrypt_win"
```

程序是 Delphi 编写（TDictionary<TKeyCollection> 等 Delphi 泛型痕迹）。

下一步：反汇编 DecryptHeaderByte / DecryptKey，找到：
1. 加密算法（AES-CTR? RC4? 自定义XOR?）
2. 密钥来源（硬编码? 机器码派生? 授权块派生?）

播放器本体 V7.0.7 也从 https://www.360dhf.cn/download.php?type=windows-player 下载了（99MB）。

## 7. 解码方案（当前可交付）

decode_vep.py 流程：
1. 检查 CRYP 头 → 找 mdat → 定位视频/音频轨 stbl（自动解析 atom）
2. 视频：逐 sample 检查 NAL 合法性，跳过加密 sample
3. 从明文流提取 PPS（第一个 type-8 NAL）
4. 分辨率自动检测（候选分辨率 × ffmpeg 解码，选错误最少的）
5. 音频：从 esds 解析 ASC，生成 ADTS 头
6. 帧率 = 视频帧数 / 音频时长，写入 SPS VUI
7. ffmpeg -c copy 封装 MP4

成品 exe 打包：Windows 上 build_exe.bat（PyInstaller + ffmpeg.exe）
```

## 8. 待办

- [ ] 反汇编 qencrypt.exe 的 DecryptHeaderByte，确定算法+密钥
- [ ] 攻破头部密钥流 → 解密真实 SPS（替代重建）
- [ ] 攻破 176 个关键帧 → 100% 无花屏解码
- [ ] 更新 decode_vep.py 为完整解密版
